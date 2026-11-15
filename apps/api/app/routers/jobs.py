"""Router /api/v1/jobs — daftar + detail lowongan.

Aturan filter (hasil grill, ADR-0009):
- `status` default `active` — janji produk #1: yang tampil default
  adalah lowongan yang masih buka (ARCH §3).
- `q` mencari di judul + nama perusahaan + lokasi (ILIKE, case-insensitive).
- `gaji_min` = gaji minimum yang ditawarkan perusahaan harus >= nilai
  ini (filter `salary_min >= gaji_min`; lowongan tanpa gaji tidak
  tampil bila filter ini dipakai — dicatat, bukan ditebak).
  Alias Inggris `salary_min` diterima dan artinya sama (web mengirim
  itu; amandemen koordinator Fase 1-lanjutan — kontrak K-W3).
- `skor_min` = skor ternormalisasi perusahaan >= nilai ini.
  Alias Inggris `score_min` diterima dan artinya sama (K-W3). Skor
  dihitung per perusahaan di Python (bukan di SQL) karena rumusnya
  tinggal di flag-engine; untuk skala v1 (ribuan lowongan) ini cukup,
  dan dicatat sebagai batas yang harus dipindah ke kolom terdenormalisasi
  bila daftar sudah puluhan ribu (lihat ADR-0009).
- `posted_from` / `posted_to` = rentang tanggal buka (klaim sumber).
- Paginasi: `page` (mulai 1), `per_page` (default 20, maks 100).
"""

from __future__ import annotations

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from ..database import get_db
from ..errors import not_found
from ..models import Company, Job
from ..schemas import JobOut, PageOut
from ..services.scoring import public_score, score_company

router = APIRouter(prefix="/jobs", tags=["jobs"])

VALID_STATUS = ("active", "closed", "expired", "unknown")


def _job_to_out(job: Job, db: Session) -> JobOut:
    return JobOut(
        id=job.id,
        title=job.title,
        company={"name": job.company.name, "slug": job.company.slug},
        location=job.location,
        work_type=job.work_type,
        salary_min=job.salary_min,
        salary_max=job.salary_max,
        salary_currency=job.salary_currency,
        posted_at=job.posted_at,
        posted_at_certain=job.posted_at_certain,
        first_seen_at=job.first_seen_at,
        last_seen_at=job.last_seen_at,
        status=job.status,
        source=job.source.slug,
        source_url=job.source_url,
    )


@router.get("", response_model=PageOut)
def list_jobs(
    status: str = Query(default="active", description="active|closed|expired|unknown"),
    q: str | None = None,
    location: str | None = None,
    gaji_min: int | None = Query(default=None, ge=0),
    skor_min: int | None = Query(default=None, ge=0, le=100),
    # Alias Inggris (dikirim web) — kanonik tetap gaji_min/skor_min.
    salary_min: int | None = Query(default=None, ge=0, include_in_schema=False),
    score_min: int | None = Query(default=None, ge=0, le=100, include_in_schema=False),
    posted_from: date | None = None,
    posted_to: date | None = None,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    if status not in VALID_STATUS:
        from ..errors import ApiError
        from fastapi import status as http_status

        raise ApiError(
            http_status.HTTP_422_UNPROCESSABLE_ENTITY,
            "validation_error",
            f"status harus salah satu: {', '.join(VALID_STATUS)}.",
        )
    query = (
        db.query(Job)
        .join(Company, Job.company_id == Company.id)
        .options(joinedload(Job.company), joinedload(Job.source))
        .filter(Job.status == status)
    )
    if q:
        like = f"%{q.strip()}%"
        query = query.filter(
            or_(
                Job.title.ilike(like),
                Company.name.ilike(like),
                Job.location.ilike(like),
            )
        )
    if location:
        query = query.filter(Job.location.ilike(f"%{location.strip()}%"))
    effective_gaji_min = gaji_min if gaji_min is not None else salary_min
    if effective_gaji_min is not None:
        query = query.filter(
            Job.salary_min.isnot(None), Job.salary_min >= effective_gaji_min
        )
    if posted_from is not None:
        query = query.filter(Job.posted_at.isnot(None), Job.posted_at >= posted_from)
    if posted_to is not None:
        query = query.filter(Job.posted_at.isnot(None), Job.posted_at <= posted_to)

    rows = query.order_by(Job.last_seen_at.desc()).all()
    items = rows
    effective_skor_min = skor_min if skor_min is not None else score_min
    if effective_skor_min is not None:
        # Skor dihitung per perusahaan (flag-engine) — cache per request.
        cache: dict[UUID, int | None] = {}
        kept = []
        for job in rows:
            if job.company_id not in cache:
                cache[job.company_id] = public_score(score_company(db, job.company_id))
            score = cache[job.company_id]
            if score is not None and score >= effective_skor_min:
                kept.append(job)
        items = kept

    total = len(items)
    pages = max(1, -(-total // per_page))
    start = (page - 1) * per_page
    page_items = items[start : start + per_page]
    return PageOut(
        items=[_job_to_out(j, db) for j in page_items],
        total=total,
        page=page,
        per_page=per_page,
        pages=pages,
    )


@router.get("/{job_id}", response_model=JobOut)
def get_job(job_id: UUID, db: Session = Depends(get_db)):
    job = (
        db.query(Job)
        .options(joinedload(Job.company), joinedload(Job.source))
        .filter(Job.id == job_id)
        .first()
    )
    if job is None:
        raise not_found("Lowongan tidak ditemukan.")
    return _job_to_out(job, db)
