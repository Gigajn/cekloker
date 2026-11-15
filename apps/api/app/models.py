"""Model SQLAlchemy CekLoker — cerminan ARCHITECTURE.md §4 + ADR-0009.

Penyimpangan dari ARCH §4 yang disengaja (dicatat di ADR-0009):
1. `companies.aliases` disimpan sebagai JSON, bukan `text[]` — supaya
   model yang sama jalan di SQLite (test) dan PostgreSQL (produksi).
   Di migrasi SQL Postgres kolom ini `jsonb`.
2. `jobs.missed_checks` (int) — tambahan untuk aturan "2x kunjungan
   hilang -> closed" (ARCH §3, ADR-0002 §2).
3. `jobs.board_url` (nullable) — URL board ATS / halaman karier asal,
   dipakai worker untuk menghidupkan CareerPageAdapter saat recheck.
4. `signals.value` disimpan sebagai JSON (`jsonb` di Postgres), bukan
   `numeric` — karena nilai sinyal flag-engine bisa dict/bool
   (mis. jumlah keluhan per cluster), bukan hanya angka.
5. `signals.decisive` + `red_override` — kolom yang dibaca langsung
   dari flag-engine (ADR-0005), supaya skor bisa dihitung dari DB
   tanpa memanggil ulang fungsi sosial.
6. Tabel tambahan: `sources`, `admin_users`, `admin_sessions`
   (auth 1 akun Giga, ADR-0009).
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

# Uuid generik SQLAlchemy: UUID native di Postgres, CHAR(32) di SQLite.
# Satu model untuk kedua DB — test SQLite tetap mewakili skema produksi.


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    slug: Mapped[str] = mapped_column(String(120), nullable=False, unique=True, index=True)
    aliases: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    website: Mapped[str | None] = mapped_column(Text)
    linkedin_url: Mapped[str | None] = mapped_column(Text)
    glassdoor_url: Mapped[str | None] = mapped_column(Text)
    industry: Mapped[str | None] = mapped_column(Text)
    size_range: Mapped[str | None] = mapped_column(String(60))
    location_hq: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now, nullable=False)

    jobs: Mapped[list["Job"]] = relationship("Job", back_populates="company")
    signals: Mapped[list["Signal"]] = relationship("Signal", back_populates="company")


class Source(Base):
    __tablename__ = "sources"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    slug: Mapped[str] = mapped_column(String(60), nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, nullable=False)

    jobs: Mapped[list["Job"]] = relationship("Job", back_populates="source")


class Job(Base):
    __tablename__ = "jobs"
    __table_args__ = (
        Index("ix_jobs_fingerprint", "fingerprint"),
        Index("ix_jobs_status_posted", "status", "posted_at"),
        CheckConstraint(
            "status IN ('active','closed','expired','unknown')",
            name="ck_jobs_status",
        ),
        CheckConstraint(
            "work_type IN ('','onsite','hybrid','remote')",
            name="ck_jobs_work_type",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("companies.id"), nullable=False, index=True)
    source_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("sources.id"), nullable=False, index=True)
    source_url: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    board_url: Mapped[str | None] = mapped_column(Text)  # ADR-0009: asal board ATS
    title: Mapped[str] = mapped_column(Text, nullable=False)
    location: Mapped[str] = mapped_column(Text, nullable=False, default="")
    work_type: Mapped[str] = mapped_column(String(20), nullable=False, default="")
    salary_min: Mapped[int | None] = mapped_column(Integer)
    salary_max: Mapped[int | None] = mapped_column(Integer)
    salary_currency: Mapped[str] = mapped_column(String(10), nullable=False, default="IDR")
    posted_at: Mapped[date | None] = mapped_column(Date)
    posted_at_certain: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    expires_at: Mapped[date | None] = mapped_column(Date)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, nullable=False)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active", index=True)
    missed_checks: Mapped[int] = mapped_column(Integer, nullable=False, default=0)  # ADR-0009
    description_text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    fingerprint: Mapped[str] = mapped_column(String(32), nullable=False, default="")
    raw_snapshot_key: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now, nullable=False)

    company: Mapped[Company] = relationship("Company", back_populates="jobs")
    source: Mapped[Source] = relationship("Source", back_populates="jobs")
    snapshots: Mapped[list["JobSnapshot"]] = relationship("JobSnapshot", back_populates="job")


class JobSnapshot(Base):
    """Bukti historis kunjungan — append-only, jangan dihapus/diubah."""

    __tablename__ = "job_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    job_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("jobs.id"), nullable=False, index=True)
    seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)  # active|closed|unknown|missed
    snapshot_key: Mapped[str | None] = mapped_column(Text)
    hash: Mapped[str | None] = mapped_column(String(64))

    job: Mapped[Job] = relationship("Job", back_populates="snapshots")


class Signal(Base):
    __tablename__ = "signals"
    __table_args__ = (
        # K4 (fase1-konsolidasi.md §3) + ADR-0006: google_places WAJIB
        # evidence_text kosong — Places API melarang menyimpan teks ulasan.
        CheckConstraint(
            "(source <> 'google_places' OR evidence_text IS NULL)",
            name="ck_signals_google_places_no_text",
        ),
        CheckConstraint(
            "confidence IN ('high','medium','low')",
            name="ck_signals_confidence",
        ),
        Index("ix_signals_company_category", "company_id", "category"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("companies.id"), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(40), nullable=False)
    key: Mapped[str] = mapped_column(String(80), nullable=False)
    value: Mapped[object] = mapped_column(JSON, nullable=True)
    points: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    evidence_url: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_text: Mapped[str | None] = mapped_column(Text)  # NULLABLE (K4)
    evidence_date: Mapped[date | None] = mapped_column(Date)
    source: Mapped[str] = mapped_column(String(60), nullable=False)
    confidence: Mapped[str] = mapped_column(String(10), nullable=False, default="medium")
    decisive: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    red_override: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    notes: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, nullable=False)

    company: Mapped[Company] = relationship("Company", back_populates="signals")


class AdminUser(Base):
    __tablename__ = "admin_users"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(200), nullable=False, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, nullable=False)

    sessions: Mapped[list["AdminSession"]] = relationship("AdminSession", back_populates="user")


class AdminSession(Base):
    __tablename__ = "admin_sessions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("admin_users.id"), nullable=False, index=True)
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, nullable=False)

    user: Mapped[AdminUser] = relationship("AdminUser", back_populates="sessions")


__all__ = [
    "Base",
    "Company",
    "Source",
    "Job",
    "JobSnapshot",
    "Signal",
    "AdminUser",
    "AdminSession",
]
