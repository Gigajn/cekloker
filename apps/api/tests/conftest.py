"""Fixture test API CekLoker.

Batas yang dicatat jujur: test memakai SQLite in-memory, BUKAN
Postgres — karena docker TIDAK tersedia di VM ini (lihat laporan).
CHECK constraint yang sama (termasuk K4 google_places) tetap diuji
di sini karena SQLite menegakkan CHECK; tipe Postgres-spesifik
(jsonb, gen_random_uuid) hanya ada di migrations/001_init.sql dan
diverifikasi secara statis di tests/test_migration.py.
"""

from __future__ import annotations

import os
import sys
from datetime import date, datetime, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

API_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(API_DIR))
REPO_ROOT = API_DIR.parent.parent
sys.path.insert(0, str(REPO_ROOT / "packages" / "flag-engine"))
sys.path.insert(0, str(REPO_ROOT / "packages" / "scraper-core"))

os.environ.setdefault("DATABASE_URL", "sqlite://")

from app import auth as auth_mod  # noqa: E402
from app.database import get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models import AdminUser, Base, Company, Job, Signal, Source  # noqa: E402

import social_signals as ss  # noqa: E402


@pytest.fixture()
def engine():
    # StaticPool: SATU koneksi dipakai bersama semua thread — tanpa ini,
    # endpoint TestClient (jalan di threadpool) mendapat DB kosong
    # ("no such table") karena :memory: per-koneksi.
    eng = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(eng)
    yield eng
    eng.dispose()


@pytest.fixture()
def db(engine):
    Session = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    session = Session()
    yield session
    session.close()


@pytest.fixture()
def client(db):
    def _override():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = _override
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c
    app.dependency_overrides.clear()


def _company(db, name, slug):
    company = Company(name=name, slug=slug, aliases=[name])
    db.add(company)
    db.flush()
    return company


def _source(db, slug, enabled=True):
    src = Source(slug=slug, name=slug, enabled=enabled)
    db.add(src)
    db.flush()
    return src


def _job(db, company, source, title, **kwargs):
    now = datetime.now(timezone.utc)
    job = Job(
        company_id=company.id,
        source_id=source.id,
        source_url=kwargs.pop("source_url", f"https://contoh.invalid/{title}".replace(" ", "-")),
        title=title,
        location=kwargs.pop("location", "Jakarta"),
        work_type=kwargs.pop("work_type", "onsite"),
        salary_min=kwargs.pop("salary_min", None),
        salary_max=kwargs.pop("salary_max", None),
        salary_currency="IDR",
        posted_at=kwargs.pop("posted_at", date(2026, 11, 13)),
        posted_at_certain=kwargs.pop("posted_at_certain", True),
        first_seen_at=now,
        last_seen_at=now,
        status=kwargs.pop("status", "active"),
        fingerprint="0" * 32,
        **kwargs,
    )
    db.add(job)
    db.flush()
    return job


def _signal_row(db, company, signal: "ss.Signal"):
    row = Signal(
        company_id=company.id,
        category=signal.category,
        key=signal.key,
        value=signal.value,
        points=signal.points,
        evidence_url=signal.evidence_url,
        evidence_text=None if signal.source == "google_places" else (signal.evidence_text or None),
        evidence_date=signal.evidence_date if isinstance(signal.evidence_date, date) else None,
        source=signal.source,
        confidence=signal.confidence,
        decisive=signal.decisive,
        red_override=signal.red_override,
        notes=signal.notes,
    )
    db.add(row)
    db.flush()
    return row


@pytest.fixture()
def seeded(db):
    """2 perusahaan + 3 lowongan + 1 admin. Kembalikan dict."""
    glints = _source(db, "glints")
    maju = _company(db, "PT Contoh Maju Bersama", "pt-contoh-maju-bersama")
    fiktif = _company(db, "PT Fiktif Teknologi Nusantara", "pt-fiktif-teknologi-nusantara")
    # Maju: Mixed 56 (contoh ADR-0005).
    _signal_row(db, maju, ss.score_rating(
        4.4, 155, source="jobstreet_review",
        evidence_url="https://contoh.invalid/maju/rating",
        evidence_date=date(2026, 11, 10)))
    _signal_row(db, maju, ss.score_recommend_rate(
        82.0, 155, source="jobstreet_review",
        evidence_url="https://contoh.invalid/maju/rekomendasi",
        evidence_date=date(2026, 11, 10)))
    _signal_row(db, maju, ss.score_news_event(
        "ekspansi", n_outlets=2, within_months=3,
        evidence_url="https://contoh.invalid/maju/ekspansi",
        evidence_date=date(2026, 10, 20),
        evidence_text="Buka kantor baru."))
    # Fiktif: Belum cukup data (rating n=8 + google_places K4).
    _signal_row(db, fiktif, ss.score_rating(
        4.2, 8, source="jobstreet_review",
        evidence_url="https://contoh.invalid/fiktif/rating",
        evidence_date=date(2026, 11, 12)))
    _signal_row(db, fiktif, ss.score_rating(
        4.0, 25, source="google_places",
        evidence_url="https://contoh.invalid/fiktif/places",
        evidence_date=date(2026, 11, 12), evidence_text=""))

    job1 = _job(db, maju, glints, "Staff Programmer",
                salary_min=5_000_000, salary_max=8_000_000,
                source_url="https://glints.com/id/job/staff-programmer-1")
    job2 = _job(db, maju, glints, "Staf Administrasi",
                salary_min=None, salary_max=None,
                source_url="https://glints.com/id/job/staf-admin-1",
                location="Bandung")
    job3 = _job(db, fiktif, glints, "Backend Engineer",
                salary_min=10_000_000, salary_max=15_000_000,
                source_url="https://glints.com/id/job/backend-1",
                status="closed")
    admin = AdminUser(email="giga@contoh.invalid",
                      password_hash=auth_mod.hash_password("rahasia-kuat"))
    db.add(admin)
    db.commit()
    return {
        "maju": maju, "fiktif": fiktif, "glints": glints,
        "job1": job1, "job2": job2, "job3": job3, "admin": admin,
    }


@pytest.fixture()
def admin_token(client, seeded):
    resp = client.post("/api/v1/admin/login", json={
        "email": "giga@contoh.invalid", "password": "rahasia-kuat",
    })
    assert resp.status_code == 200, resp.text
    return resp.json()["token"]
