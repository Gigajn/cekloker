"""Koneksi database + session per-request.

Satu engine untuk Postgres (produksi) dan SQLite (dev/test). SQLite
dipakai file lokal di dev; test memakai SQLite in-memory (lihat
tests/conftest.py). Batas yang dicatat jujur: test SQLite TIDAK menguji
CHECK constraint Postgres yang spesifik (mis. tipe jsonb) — skema
Postgres penuh ada di migrations/001_init.sql dan diverifikasi
strukturnya lewat test_smoke migrasi (lihat tests/test_migration.py).
"""

from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from .config import get_settings


def make_engine(database_url: str | None = None) -> Engine:
    url = database_url or get_settings().DATABASE_URL
    connect_args = {}
    if url.startswith("sqlite"):
        # SQLite single-threaded di TestClient: izinkan pemakaian lintas thread.
        connect_args = {"check_same_thread": False}
    return create_engine(url, connect_args=connect_args, future=True)


engine: Engine = make_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_db():
    """Dependency FastAPI: satu session per request, ditutup setelahnya."""
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
