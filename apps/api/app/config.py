"""Konfigurasi API CekLoker — semua dari environment, tanpa default rahasia.

Aturan keras (ARCHITECTURE.md §8, D10): tidak ada credential / API key di
file mana pun. Nilai yang tidak di-set di env memakai default yang AMAN
untuk dev lokal (SQLite file lokal, admin HARUS dibuat lewat seed dengan
env — lihat scripts/seed.py).
"""

from __future__ import annotations

import os
from functools import lru_cache


def _env(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


class Settings:
    # Database. Default dev lokal: SQLite file di ./data/cekloker.db.
    # Produksi / docker-compose: DATABASE_URL=postgresql+psycopg2://...
    DATABASE_URL: str = _env(
        "DATABASE_URL", "sqlite:///./data/cekloker.db"
    )
    # Sesi admin: berapa hari token login berlaku.
    ADMIN_SESSION_DAYS: int = int(_env("ADMIN_SESSION_DAYS", "7") or 7)
    # Worker: jeda antar kunjungan ulang (detik) dalam satu run --once.
    WORKER_DELAY_S: float = float(_env("WORKER_DELAY_S", "3") or 3)
    # Batas default refresh admin.
    REFRESH_DEFAULT_LIMIT: int = int(_env("REFRESH_DEFAULT_LIMIT", "20") or 20)
    REFRESH_MAX_LIMIT: int = 100
    APP_VERSION: str = "0.1.0"


@lru_cache
def get_settings() -> Settings:
    return Settings()
