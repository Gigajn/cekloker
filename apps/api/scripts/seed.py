"""Seed database CekLoker dari fixture Fase 1 (BUKAN data live massal,
BUKAN data pribadi).

Sumber data: parser PURE scraper-core atas fixture buatan di
packages/scraper-core/tests/fixtures/ (perusahaan FIKTIF: "PT Contoh
Maju Bersama", "PT Fiktif Teknologi Nusantara", "Contoh Corp").
Sinyal dihitung lewat flag-engine (social_signals) supaya poin +
decisive konsisten dengan ADR-0005.

Isi seed:
- 9 lowongan: Glints 1, Kalibrr 1, Greenhouse 2, Lever 2, Ashby 1,
  Workable 1, halaman karier custom 1.
- 3 perusahaan dengan sinyal:
  * PT Contoh Maju Bersama — Mixed (56): rating 4,4 (n=155) + rekomendasi
    82% + berita ekspansi 2 media (contoh ADR-0005).
  * PT Fiktif Teknologi Nusantara — "Belum cukup data": rating kecil
    (n=8) + rating Google Places (evidence_text WAJIB kosong, K4).
  * Contoh Corp — Red (0): rating 2,4 (n=30) + keluhan lembur berulang
    5 dari 30 ulasan + berita PHK massal 2 media.
- 1 akun admin dari env CEKLOKER_ADMIN_EMAIL / CEKLOKER_ADMIN_PASSWORD
  (WAJIB di-set; password TIDAK PERNAH ditulis di file).

Jalankan dari apps/api/:
    DATABASE_URL=... CEKLOKER_ADMIN_EMAIL=a@b.id CEKLOKER_ADMIN_PASSWORD='...' \
        .venv/bin/python scripts/seed.py [--reset]
Idempotent tanpa --reset (upsert per source_url). --reset menghapus isi
tabel jobs/signals/companies dulu (HANYA untuk dev).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import date
from pathlib import Path

API_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(API_DIR))
REPO_ROOT = API_DIR.parent.parent
sys.path.insert(0, str(REPO_ROOT / "packages" / "scraper-core"))
sys.path.insert(0, str(REPO_ROOT / "packages" / "flag-engine"))

os.environ.setdefault("DATABASE_URL", "sqlite:///./data/cekloker.db")

from app.auth import hash_password  # noqa: E402
from app.database import make_engine  # noqa: E402
from app.models import AdminUser, Base, Company, Job, JobSnapshot, Signal, Source  # noqa: E402
from app.services.jobs import get_or_create_source, upsert_job  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

from scraper_core.adapters.career_page import (  # noqa: E402
    extract_json_ld_job_postings,
    parse_board,
    parse_json_ld_job_posting,
)
from scraper_core.adapters.glints import parse_glints_job  # noqa: E402
from scraper_core.adapters.kalibrr import parse_kalibrr_job  # noqa: E402

import social_signals as ss  # noqa: E402

FIXTURES = REPO_ROOT / "packages" / "scraper-core" / "tests" / "fixtures"
REF_DATE = date(2026, 11, 15)  # "hari ini" versi fixture (sama seperti test)

GLINTS_URL = (
    "https://glints.com/id/en/opportunities/jobs/staff-programmer/"
    "ad093d00-3e7d-4f25-a56e-be88fda4632d"
)
KALIBRR_URL = (
    "https://www.kalibrr.id/c/pt-fiktif-teknologi-nusantara/"
    "jobs/100001/backend-engineer"
)

SOURCES_SEED = [
    ("glints", "Glints", True),
    ("kalibrr", "Kalibrr", True),
    ("jobstreet", "JobStreet", False),  # TUNDA — ToS SEEK (K-JB1)
    ("indeed", "Indeed", False),  # TUNDA — ToS §D.21
    ("career-greenhouse", "Greenhouse (halaman karier)", True),
    ("career-lever", "Lever (halaman karier)", True),
    ("career-ashby", "Ashby (halaman karier)", True),
    ("career-workable", "Workable (halaman karier)", True),
    ("career-custom", "Halaman karier custom (JSON-LD)", True),
]

EVIDENCE_BASE = "https://contoh.invalid/cekloker/bukti"


def _read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def _load_json(name: str):
    return json.loads(_read(name))


def collect_raw_jobs() -> list[tuple[object, str, str | None]]:
    """Kembalikan [(RawJob, source_slug, board_url)]."""
    out = []
    out.append((
        parse_glints_job(_read("glints_job.html"), GLINTS_URL, ref=REF_DATE),
        "glints", None,
    ))
    out.append((
        parse_kalibrr_job(_read("kalibrr_job.html"), KALIBRR_URL, ref=REF_DATE),
        "kalibrr", None,
    ))
    for platform, fixture, board_url in [
        ("greenhouse", "greenhouse_board.json", "https://boards.greenhouse.io/contohcorp"),
        ("lever", "lever_board.json", "https://jobs.lever.co/contohcorp"),
        ("ashby", "ashby_board.json", "https://jobs.ashbyhq.com/contohcorp"),
        ("workable", "workable_board.json", "https://apply.workable.com/contohcorp"),
    ]:
        for raw in parse_board(platform, _load_json(fixture), "contohcorp"):
            # Lever/Ashby tidak mengembalikan nama perusahaan di feed-nya
            # (company_raw kosong). Seed tahu pemilik board ini: Contoh Corp.
            # Di produksi, nama diisi normalizer dari konfigurasi board
            # (tugas Tim Normalisasi), bukan ditebak dari slug.
            if not (raw.company_raw or "").strip():
                raw.company_raw = "Contoh Corp"
                raw.company_norm = "Contoh Corp"
            out.append((raw, f"career-{platform}", board_url))
    postings = extract_json_ld_job_postings(_read("custom_career_page.html"))
    out.append((
        parse_json_ld_job_posting(
            postings[0], "https://careers.contohcorp.id/mobile-engineer"
        ),
        "career-custom", "https://careers.contohcorp.id",
    ))
    return out


def _signal_row(company: Company, signal: "ss.Signal") -> Signal:
    """Satu sinyal flag-engine -> baris DB.

    K4: sumber google_places WAJIB evidence_text NULL (bukan string kosong).
    """
    evidence_text = signal.evidence_text or None
    if signal.source == "google_places":
        evidence_text = None
    return Signal(
        company_id=company.id,
        category=signal.category,
        key=signal.key,
        value=signal.value,
        points=signal.points,
        evidence_url=signal.evidence_url,
        evidence_text=evidence_text,
        evidence_date=(
            signal.evidence_date
            if isinstance(signal.evidence_date, date)
            else None
        ),
        source=signal.source,
        confidence=signal.confidence,
        decisive=signal.decisive,
        red_override=signal.red_override,
        notes=signal.notes,
    )


def seed_signals(db, companies: dict[str, Company]) -> int:
    """Sinyal contoh untuk 3 perusahaan. Kembalikan jumlah sinyal."""
    db.query(Signal).delete()
    rows: list[Signal] = []

    # 1) PT Contoh Maju Bersama — Mixed (56). Contoh ADR-0005.
    maju = companies["PT Contoh Maju Bersama"]
    rows.append(_signal_row(maju, ss.score_rating(
        4.4, 155, source="jobstreet_review",
        evidence_url=f"{EVIDENCE_BASE}/maju/rating",
        evidence_date=date(2026, 11, 10),
    )))
    rows.append(_signal_row(maju, ss.score_recommend_rate(
        82.0, 155, source="jobstreet_review",
        evidence_url=f"{EVIDENCE_BASE}/maju/rekomendasi",
        evidence_date=date(2026, 11, 10),
    )))
    rows.append(_signal_row(maju, ss.score_news_event(
        "ekspansi", n_outlets=2, within_months=3,
        evidence_url=f"{EVIDENCE_BASE}/maju/ekspansi",
        evidence_date=date(2026, 10, 20),
        evidence_text="Contoh Maju Bersama buka kantor baru di Surabaya.",
    )))

    # 2) PT Fiktif Teknologi Nusantara — "Belum cukup data".
    #    Rating n=8 (setengah poin) + rating Google Places (K4: teks kosong).
    fiktif = companies["PT Fiktif Teknologi Nusantara"]
    rows.append(_signal_row(fiktif, ss.score_rating(
        4.2, 8, source="jobstreet_review",
        evidence_url=f"{EVIDENCE_BASE}/fiktif/rating",
        evidence_date=date(2026, 11, 12),
    )))
    rows.append(_signal_row(fiktif, ss.score_rating(
        4.0, 25, source="google_places",
        evidence_url=f"{EVIDENCE_BASE}/fiktif/google-places",
        evidence_date=date(2026, 11, 12),
        evidence_text="",  # WAJIB kosong — disimpan NULL (K4)
    )))

    # 3) Contoh Corp — Red (0): rating rendah + keluhan lembur berulang.
    contoh = companies["Contoh Corp"]
    rows.append(_signal_row(contoh, ss.score_rating(
        2.4, 30, source="glassdoor",
        evidence_url=f"{EVIDENCE_BASE}/contoh/rating",
        evidence_date=date(2026, 11, 5),
    )))
    reviews = (
        [{"text": "Lembur tidak dibayar tiap akhir bulan, parah."}] * 5
        + [{"text": "Kerja biasa saja, fasilitas standar."}] * 25
    )
    rows.append(_signal_row(contoh, ss.detect_complaints(
        reviews, source="glassdoor",
        evidence_url=f"{EVIDENCE_BASE}/contoh/keluhan",
        evidence_date=date(2026, 11, 5),
    )))
    # Sinyal penentu ke-3 dari kategori ke-2 (stabilitas) — supaya label
    # Red benar-benar keluar (ADR-0005: label butuh >= 3 sinyal penentu
    # dari >= 2 kategori; tanpa ini labelnya "Belum cukup data").
    rows.append(_signal_row(contoh, ss.score_news_event(
        "layoff_massal", n_outlets=2, within_months=2,
        evidence_url=f"{EVIDENCE_BASE}/contoh/phk",
        evidence_date=date(2026, 9, 15),
        evidence_text="Contoh Corp PHK 200 karyawan.",
    )))

    db.add_all(rows)
    return len(rows)


def seed_admin(db) -> str:
    email = os.environ.get("CEKLOKER_ADMIN_EMAIL", "").strip().lower()
    password = os.environ.get("CEKLOKER_ADMIN_PASSWORD", "")
    if not email or not password:
        raise SystemExit(
            "Seed butuh CEKLOKER_ADMIN_EMAIL dan CEKLOKER_ADMIN_PASSWORD di env. "
            "Password TIDAK BOLEH ditulis di file — set di shell / .env (yang tidak di-commit)."
        )
    user = db.query(AdminUser).filter(AdminUser.email == email).first()
    if user is None:
        db.add(AdminUser(email=email, password_hash=hash_password(password)))
        db.flush()
        return f"admin baru: {email}"
    user.password_hash = hash_password(password)
    return f"admin diperbarui: {email}"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Seed DB CekLoker dari fixture Fase 1.")
    parser.add_argument("--reset", action="store_true",
                        help="hapus isi jobs/signals/companies dulu (dev saja)")
    args = parser.parse_args(argv if argv is not None else [])

    db_path = Path("data")
    db_path.mkdir(exist_ok=True)
    # Baca DATABASE_URL langsung dari env (BUKAN get_settings() yang
    # ter-cache) — supaya seed test dengan DATABASE_URL sementara jalan.
    engine = make_engine(
        os.environ.get("DATABASE_URL", "sqlite:///./data/cekloker.db")
    )
    Base.metadata.create_all(engine)
    # Session diikat ke engine yang BARU dibuat di atas (bukan SessionLocal
    # dari app.database — supaya seed selalu menulis ke DATABASE_URL yang
    # aktif saat ini, termasuk saat dipanggil dari test).
    db = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)()
    try:
        if args.reset:
            db.query(JobSnapshot).delete()
            db.query(Job).delete()
            db.query(Signal).delete()
            db.query(Company).delete()
            db.commit()
        for slug, name, enabled in SOURCES_SEED:
            src = get_or_create_source(db, slug, name)
            src.enabled = enabled
        db.commit()

        companies: dict[str, Company] = {}
        n_jobs = 0
        for raw, source_slug, board_url in collect_raw_jobs():
            job = upsert_job(db, raw, source_slug, board_url)
            companies[job.company.name] = job.company
            n_jobs += 1
        db.commit()
        n_signals = seed_signals(db, companies)
        db.commit()
        admin_info = seed_admin(db)
        db.commit()
        print(f"seed selesai: {n_jobs} lowongan, {len(companies)} perusahaan, "
              f"{n_signals} sinyal, {admin_info}")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    import sys as _sys

    raise SystemExit(main(_sys.argv[1:]))
