"""Titik masuk FastAPI CekLoker.

Jalankan dari apps/api/:
    .venv/bin/uvicorn app.main:app --reload --port 8000

Skema DB dibuat lewat migrasi (migrations/001_init.sql) atau, untuk
dev cepat, `python -c "from app.models import Base; from app.database
import engine; Base.metadata.create_all(engine)"` — lihat README.
"""

from __future__ import annotations

from fastapi import FastAPI
from sqlalchemy import text

from .config import get_settings
from .database import engine
from .errors import register_error_handlers
from .routers import admin, companies, jobs, signals
from .schemas import HealthOut

app = FastAPI(
    title="CekLoker API",
    version=get_settings().APP_VERSION,
    description=(
        "API daftar lowongan aktif + skor Green/Red Flag perusahaan. "
        "Alat pribadi (D8) — endpoint admin butuh login 1 akun Giga."
    ),
)

register_error_handlers(app)

app.include_router(jobs.router, prefix="/api/v1")
app.include_router(companies.router, prefix="/api/v1")
app.include_router(signals.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")


def _db_ok() -> bool:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


@app.get("/health", response_model=HealthOut, tags=["meta"])
@app.get("/api/v1/health", response_model=HealthOut, tags=["meta"])
def health():
    return HealthOut(
        status="ok", version=get_settings().APP_VERSION, db="ok" if _db_ok() else "error"
    )
