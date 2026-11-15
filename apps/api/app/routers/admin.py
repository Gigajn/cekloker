"""Router /api/v1/admin — login + refresh (butuh auth admin Giga).

POST /admin/refresh memicu recheck sinkron dan TERBATAS (default 20,
maks 100 lowongan per panggilan) — sengaja sinkron + berbatas karena
ini alat pribadi 1 pengguna, bukan antrean produksi. Bila suatu hari
refresh harus menangani ribuan lowongan, pindahkan ke antrean
(Redis + RQ, ARCH §2) — jangan naikkan limit diam-diam.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import worker as worker_mod
from ..auth import authenticate, create_session, get_current_admin
from ..database import get_db
from ..models import AdminUser
from ..schemas import LoginIn, LoginOut, RefreshIn, RefreshOut
from ..errors import ApiError
from fastapi import status as http_status

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/login", response_model=LoginOut)
def login(body: LoginIn, db: Session = Depends(get_db)):
    user = authenticate(db, body.email, body.password)
    if user is None:
        # Pesan sama untuk email salah / password salah — jangan bocorkan
        # mana yang salah.
        raise ApiError(
            http_status.HTTP_401_UNAUTHORIZED,
            "invalid_credentials",
            "Email atau password salah.",
        )
    token, expires_at = create_session(db, user)
    return LoginOut(token=token, expires_at=expires_at)


@router.post("/refresh", response_model=RefreshOut)
def refresh(
    body: RefreshIn | None = None,
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin),
):
    body = body or RefreshIn()
    from ..config import get_settings

    limit = body.limit or get_settings().REFRESH_DEFAULT_LIMIT
    limit = min(limit, get_settings().REFRESH_MAX_LIMIT)
    summary = worker_mod.refresh_jobs(db, limit=limit, job_id=body.job_id)
    return RefreshOut(
        checked=summary["checked"],
        still_active=summary["still_active"],
        closed=summary["closed"],
        unknown=summary["unknown"],
        skipped=summary["skipped"],
        results=summary["results"],
    )


@router.post("/logout")
def logout(db: Session = Depends(get_db), admin: AdminUser = Depends(get_current_admin)):
    """Cabut SEMUA sesi admin ini (keluar di semua perangkat)."""
    from ..models import AdminSession

    db.query(AdminSession).filter(AdminSession.user_id == admin.id).delete()
    db.commit()
    return {"ok": True}
