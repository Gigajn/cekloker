"""Normalisasi RawJob -> baris DB (dipakai seed + worker nanti).

Satu tempat yang mengubah `RawJob` (scraper_core.base — JANGAN ubah
definisinya di sini) menjadi Company + Job. Aturan:
- Perusahaan dicari dari `company_norm` (nama ternormalisasi, K8:
  fingerprint memakai company_norm). Bila belum ada, dibuat dengan
  slug dari nama mentah + alias [nama mentah].
- Lowongan dicari dari `source_url` (UNIQUE). Bila sudah ada, hanya
  `last_seen_at` + `status` yang diperbarui (idempotent — seed boleh
  dijalankan 2x).
- `first_seen_at` diisi sekarang untuk data seed (ini data contoh dari
  fixture, bukan pengamatan live — dicatat di seed).
- `fingerprint` dari RawJob.fingerprint() (32 karakter, ADR-0002).
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from ..models import Company, Job, JobSnapshot, Source
from .scraper_import import RawJob, slugify_company


def get_or_create_source(db: Session, slug: str, name: str | None = None) -> Source:
    src = db.query(Source).filter(Source.slug == slug).first()
    if src is None:
        src = Source(slug=slug, name=name or slug, enabled=True)
        db.add(src)
        db.flush()
    return src


def get_or_create_company(db: Session, raw: RawJob) -> Company:
    """Cari perusahaan dari nama ternormalisasi; bila belum ada, buat."""
    norm = (raw.company_norm or raw.company_raw or "").strip()
    slug = slugify_company(raw.company_raw or norm)
    company = db.query(Company).filter(Company.slug == slug).first()
    if company is None:
        company = Company(
            name=(raw.company_raw or norm).strip(),
            slug=slug,
            aliases=[raw.company_raw.strip()] if raw.company_raw.strip() else [],
        )
        db.add(company)
        db.flush()
    return company


def upsert_job(db: Session, raw: RawJob, source_slug: str, board_url: str | None = None) -> Job:
    """Simpan RawJob; kembalikan baris Job. Idempotent per source_url."""
    source = get_or_create_source(db, source_slug)
    company = get_or_create_company(db, raw)
    now = datetime.now(timezone.utc)
    job = db.query(Job).filter(Job.source_url == raw.source_url).first()
    if job is None:
        job = Job(
            company_id=company.id,
            source_id=source.id,
            source_url=raw.source_url,
            board_url=board_url,
            title=raw.title.strip(),
            location=raw.location or "",
            work_type=raw.work_type or "",
            salary_min=raw.salary_min,
            salary_max=raw.salary_max,
            salary_currency=raw.salary_currency or "IDR",
            posted_at=raw.posted_at,
            posted_at_certain=raw.posted_at_certain,
            description_text=raw.description_text or "",
            fingerprint=raw.fingerprint(),
            first_seen_at=now,
            last_seen_at=now,
            status="active" if raw.is_active else "closed",
        )
        db.add(job)
        db.flush()
        db.add(JobSnapshot(job_id=job.id, seen_at=now, status=job.status))
    else:
        job.last_seen_at = now
        job.status = "active" if raw.is_active else "closed"
        job.title = raw.title.strip()
        job.location = raw.location or ""
    db.flush()
    return job
