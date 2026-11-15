"""Test seed dari fixture + test statis migrasi Postgres.

Migrasi 001_init.sql TIDAK bisa dijalankan di VM ini (tidak ada
Postgres/docker) — test ini memverifikasi isinya secara statis supaya
typo/penyimpangan ketahuan, dan mencatat dengan jujur bahwa eksekusi
live di Postgres masih menunggu docker-compose di mesin Giga.
Lihat ADR-0009 § "Yang belum terverifikasi".
"""

from __future__ import annotations

from pathlib import Path

API_DIR = Path(__file__).resolve().parent.parent


def test_migrasi_memuat_semua_tabel():
    sql = (API_DIR / "migrations" / "001_init.sql").read_text(encoding="utf-8")
    for tabel in (
        "companies", "sources", "jobs", "job_snapshots", "signals",
        "admin_users", "admin_sessions",
    ):
        assert f"CREATE TABLE IF NOT EXISTS {tabel}" in sql, tabel


def test_migrasi_memuat_perbaikan_k4():
    sql = (API_DIR / "migrations" / "001_init.sql").read_text(encoding="utf-8")
    assert "ck_signals_google_places_no_text" in sql
    assert "source <> 'google_places' OR evidence_text IS NULL" in sql
    # evidence_text tidak NOT NULL:
    assert "evidence_text text NOT NULL" not in sql


def test_migrasi_memuat_check_status_dan_sumber_disabled():
    sql = (API_DIR / "migrations" / "001_init.sql").read_text(encoding="utf-8")
    assert "status IN ('active','closed','expired','unknown')" in sql
    assert "('jobstreet', 'JobStreet', false)" in sql
    assert "('indeed', 'Indeed', false)" in sql
    assert "missed_checks int NOT NULL DEFAULT 0" in sql
    assert "posted_at_certain boolean NOT NULL DEFAULT true" in sql


def test_seed_menghasilkan_9_lowongan_dari_fixture(tmp_path, monkeypatch):
    import os
    import sys

    sys.path.insert(0, str(API_DIR / "scripts"))
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path}/seed.db")
    monkeypatch.setenv("CEKLOKER_ADMIN_EMAIL", "giga@contoh.invalid")
    monkeypatch.setenv("CEKLOKER_ADMIN_PASSWORD", "rahasia-kuat")
    import seed as seed_mod

    assert seed_mod.main() == 0

    from app.database import make_engine
    from app.models import Company, Job, Signal
    from sqlalchemy.orm import sessionmaker

    Session = sessionmaker(bind=make_engine(f"sqlite:///{tmp_path}/seed.db"))
    db = Session()
    try:
        assert db.query(Job).count() == 9
        assert db.query(Company).count() == 3
        assert db.query(Signal).count() == 8  # 3 maju + 2 fiktif + 3 contoh
        assert db.query(Job).filter(Job.status == "active").count() == 9
        from app.services.scoring import score_company, public_score

        maju = db.query(Company).filter(Company.slug == "pt-contoh-maju-bersama").one()
        assert public_score(score_company(db, maju.id)) == 56
        fiktif = db.query(Company).filter(
            Company.slug == "pt-fiktif-teknologi-nusantara").one()
        assert public_score(score_company(db, fiktif.id)) is None
        contoh = db.query(Company).filter(Company.slug == "contoh-corp").one()
        assert public_score(score_company(db, contoh.id)) == 0
    finally:
        db.close()
