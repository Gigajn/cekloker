"""Skema Pydantic — bentuk request/response API.

Kontrak bersama Tim Web (JANGAN diubah sepihak):
- job = {id, title, company{name,slug}, location, work_type,
  salary_min, salary_max, salary_currency, posted_at,
  posted_at_certain, first_seen_at, last_seen_at, status, source,
  source_url}
- company = {id, slug, name, score (null bila belum cukup data), label,
  signals:[{category, key, points, evidence_url, evidence_text,
  evidence_date, source, confidence}]}
"""

from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field


class CompanyRef(BaseModel):
    name: str
    slug: str


class JobOut(BaseModel):
    id: UUID
    title: str
    company: CompanyRef
    location: str
    work_type: str
    salary_min: int | None
    salary_max: int | None
    salary_currency: str
    posted_at: date | None
    posted_at_certain: bool
    first_seen_at: datetime
    last_seen_at: datetime
    status: str
    source: str
    source_url: str


class PageOut(BaseModel):
    items: list
    total: int
    page: int
    per_page: int
    pages: int


class SignalOut(BaseModel):
    category: str
    key: str
    points: int
    evidence_url: str
    evidence_text: str | None
    evidence_date: date | None
    source: str
    confidence: str


class CompanyOut(BaseModel):
    id: UUID
    slug: str
    name: str
    score: int | None = Field(
        default=None,
        description="Skor ternormalisasi 0-100; null bila 'Belum cukup data'.",
    )
    label: str
    signals: list[SignalOut] = []
    # Tambahan di luar kontrak inti (web boleh abaikan): peringatan
    # keselamatan, mis. permintaan biaya (red_override, ADR-0005).
    warnings: list[str] = []
    # Amandemen koordinator Fase 1-lanjutan (K-W1/K-W4): agar web bisa
    # memverifikasi syarat label tanpa menghitung ulang skor.
    measured_categories: list[str] = []
    decisive_signals: int = 0
    red_override: bool = False


class CompanyListItem(BaseModel):
    id: UUID
    slug: str
    name: str
    score: int | None = None
    label: str


class LoginIn(BaseModel):
    email: str
    password: str


class LoginOut(BaseModel):
    token: str
    expires_at: datetime


class RefreshIn(BaseModel):
    job_id: UUID | None = None
    limit: int | None = Field(default=None, ge=1, le=100)


class RefreshOut(BaseModel):
    checked: int
    still_active: int
    closed: int
    unknown: int
    skipped: int
    results: list[dict] = []


class HealthOut(BaseModel):
    status: str = "ok"
    version: str
    db: str = "ok"
