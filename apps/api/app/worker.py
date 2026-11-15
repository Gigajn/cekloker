"""Worker recheck lowongan — apps/api/app/worker.py.

Tugasnya SATU: untuk tiap lowongan aktif, tanya adapter `check_active`,
lalu perbarui status di DB sesuai ADR-0002 + ARCH §3:

- `check_active` True  -> masih buka: `last_seen_at` = sekarang,
  `missed_checks` = 0, status tetap `active`.
- `check_active` False -> SATU kunjungan hilang: `missed_checks` += 1.
  Status baru jadi `closed` bila ini kunjungan hilang ke-2
  berturut-turut (aturan 2x, ARCH §3). Sebelum itu status tetap
  `active` tapi `last_seen_at` TIDAK diperbarui — supaya "terakhir
  terlihat buka" tetap jujur.
- Gagal teknis (SourceFetchError / SourceBlockedError: timeout, 5xx,
  403/429) -> status `unknown`, `last_seen_at` tidak berubah.
  "Tidak bisa dicek" TIDAK PERNAH jadi "tutup".
- Adapter dimatikan (SourceNotPermittedError: JobStreet/Indeed) ->
  `skipped`, tidak diubah apa pun.

Setiap kunjungan dicatat sebagai JobSnapshot (append-only, bukti).

Dijalankan manual (JANGAN otomatis massal saat dev):
    python -m app.worker --once [--limit N] [--source glints]
    python -m app.worker --interval 3600 [--limit 50]   # loop sopan
"""

from __future__ import annotations

import argparse
import logging
import time
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from .database import SessionLocal
from .config import get_settings
from .models import Job, JobSnapshot, Source
from .services.scraper_import import (
    RawJob,  # noqa: F401  (dipakai pengetik / dokumentasi kontrak)
    SourceBlockedError,
    SourceFetchError,
    SourceNotPermittedError,
)

log = logging.getLogger("cekloker.worker")

#: Berapa kunjungan hilang berturut-turut sebelum lowongan dinyatakan tutup.
MISSED_TO_CLOSE = 2


def _load_adapters():
    """Registry adapter job-board + career page (scraper-core).

    Diimpor malas supaya `python -m app.worker --help` tetap jalan walau
    paket scraper-core belum ter-mount. Bila paket tidak ada, kembalikan
    registry kosong — recheck lalu `skipped` semua (lihat scraper_import).
    """
    try:
        from scraper_core.adapters import ADAPTERS, CareerPageAdapter
    except ImportError:
        return (), None
    return ADAPTERS, CareerPageAdapter


def get_adapter_for_job(job: Job):
    """Kembalikan instance adapter untuk satu job, atau None bila
    tidak bisa di-recheck (alasan dicatat pemanggil sebagai skipped).

    - glints / kalibrr: adapter job-board, tanpa argumen.
    - career-<platform>: CareerPageAdapter butuh board_url; bila
      jobs.board_url kosong, kembalikan None (skipped).
    - jobstreet / indeed / lainnya: adapter dimatikan -> None.
    """
    ADAPTERS, CareerPageAdapter = _load_adapters()
    slug = job.source.slug if job.source else ""
    for cls in ADAPTERS:
        if cls.source_id == slug:
            if not cls.enabled:
                return None
            return cls()
    if slug.startswith("career-"):
        if CareerPageAdapter is None:
            return None
        if not job.board_url:
            log.warning(
                "job %s tanpa board_url — recheck dilewati (skipped)", job.id
            )
            return None
        company_name = job.company.name if job.company else ""
        return CareerPageAdapter(company_name, job.board_url)
    return None


def recheck_job(db: Session, job: Job, adapter=None) -> dict:
    """Cek ulang SATU lowongan; kembalikan ringkasan hasil.

    `adapter` boleh di-inject (dipakai test — supaya test tidak kena
    HTTP live). Bila None, adapter diambil dari registry.
    """
    now = datetime.now(timezone.utc)
    if adapter is None:
        adapter = get_adapter_for_job(job)
    if adapter is None:
        return {
            "job_id": str(job.id),
            "outcome": "skipped",
            "reason": "adapter tidak tersedia / dimatikan / tanpa board_url",
            "status": job.status,
        }
    try:
        still_open = adapter.check_active(job.source_url)
    except SourceNotPermittedError as exc:
        return {
            "job_id": str(job.id),
            "outcome": "skipped",
            "reason": str(exc),
            "status": job.status,
        }
    except (SourceFetchError, SourceBlockedError) as exc:
        log.warning("recheck %s gagal teknis: %s", job.id, exc)
        job.status = "unknown"
        db.add(JobSnapshot(job_id=job.id, seen_at=now, status="unknown"))
        db.commit()
        return {"job_id": str(job.id), "outcome": "unknown", "status": "unknown"}
    except Exception as exc:  # gagal tak terduga dari adapter: jangan tutup
        log.exception("recheck %s gagal tak terduga", job.id)
        job.status = "unknown"
        db.add(JobSnapshot(job_id=job.id, seen_at=now, status="unknown"))
        db.commit()
        return {
            "job_id": str(job.id),
            "outcome": "unknown",
            "reason": f"gagal tak terduga: {exc}",
            "status": "unknown",
        }

    if still_open:
        job.status = "active"
        job.last_seen_at = now
        job.missed_checks = 0
        db.add(JobSnapshot(job_id=job.id, seen_at=now, status="active"))
        db.commit()
        return {"job_id": str(job.id), "outcome": "still_active", "status": "active"}

    job.missed_checks = (job.missed_checks or 0) + 1
    if job.missed_checks >= MISSED_TO_CLOSE:
        job.status = "closed"
        db.add(JobSnapshot(job_id=job.id, seen_at=now, status="closed"))
        db.commit()
        return {
            "job_id": str(job.id),
            "outcome": "closed",
            "missed_checks": job.missed_checks,
            "status": "closed",
        }
    db.add(JobSnapshot(job_id=job.id, seen_at=now, status="missed"))
    db.commit()
    return {
        "job_id": str(job.id),
        "outcome": "still_active",
        "missed_checks": job.missed_checks,
        "status": job.status,
        "note": "1 kunjungan hilang (belum 2x) — status tetap, last_seen_at tidak diubah",
    }


def refresh_jobs(
    db: Session,
    limit: int = 20,
    job_id=None,
    source_slug: str | None = None,
    delay_s: float | None = None,
    adapter_factory=None,
) -> dict:
    """Cek ulang lowongan aktif (atau satu job bila job_id diisi).

    Urutan: yang paling lama tidak dicek dulu (last_seen_at paling tua).
    `adapter_factory(job)` bila diisi dipakai test untuk meng-inject
    adapter palsu tanpa HTTP live.
    """
    settings = get_settings()
    delay = settings.WORKER_DELAY_S if delay_s is None else delay_s
    if job_id is not None:
        jobs = db.query(Job).filter(Job.id == job_id).all()
    else:
        query = db.query(Job).join(Job.source).filter(Job.status == "active")
        if source_slug:
            query = query.filter(Source.slug == source_slug)
        jobs = query.order_by(Job.last_seen_at.asc()).limit(limit).all()
    results = []
    counts = {"checked": 0, "still_active": 0, "closed": 0, "unknown": 0, "skipped": 0}
    for i, job in enumerate(jobs):
        if i > 0 and delay > 0:
            time.sleep(delay)  # sopan: jeda antar request ke sumber
        adapter = adapter_factory(job) if adapter_factory else None
        result = recheck_job(db, job, adapter=adapter)
        results.append(result)
        counts["checked"] += 1
        counts[result["outcome"]] = counts.get(result["outcome"], 0) + 1
    return {**counts, "results": results}


def _parse_args(argv=None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Worker recheck CekLoker (cek ulang lowongan aktif).")
    p.add_argument("--once", action="store_true", help="satu run lalu berhenti")
    p.add_argument("--interval", type=int, default=0,
                   help="loop tiap N detik (bila > 0, jalan terus sampai Ctrl+C)")
    p.add_argument("--limit", type=int, default=20, help="maks lowongan per run")
    p.add_argument("--source", default=None, help="hanya sumber ini (mis. glints)")
    p.add_argument("--job-id", default=None, help="cek ulang satu lowongan (UUID)")
    return p.parse_args(argv)


def main(argv=None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    args = _parse_args(argv)
    if not args.once and args.interval <= 0:
        print("Pilih --once atau --interval N (detik). Lihat --help.")
        return 2
    from uuid import UUID

    job_uuid = UUID(args.job_id) if args.job_id else None
    while True:
        db = SessionLocal()
        try:
            summary = refresh_jobs(
                db, limit=args.limit, job_id=job_uuid, source_slug=args.source
            )
        finally:
            db.close()
        log.info("recheck selesai: %s", {k: v for k, v in summary.items() if k != "results"})
        if args.once or args.interval <= 0:
            return 0
        time.sleep(args.interval)


if __name__ == "__main__":
    raise SystemExit(main())
