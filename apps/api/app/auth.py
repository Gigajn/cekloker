"""Auth admin v1 — 1 akun Giga dulu (D8, ADR-0009).

Desain (hasil grill):
- BUKAN OAuth Google, BUKAN layanan auth berbayar (D10, $0).
- Password di-hash PBKDF2-HMAC-SHA256 stdlib (600.000 iterasi, salt
  16 byte acak) — tanpa dependensi bcrypt/passlib, tanpa menyimpan
  password mentah di mana pun.
- Login menghasilkan token acak (secrets, 32 byte); yang disimpan di DB
  hanya SHA-256 token itu, bukan tokennya — token bocor dari log tidak
  bisa dipakai ulang tanpa akses DB, dan token bisa dicabut dengan
  menghapus baris sesi.
- Token berlaku 7 hari (ADMIN_SESSION_DAYS), dikirim sebagai
  `Authorization: Bearer <token>`.

Yang sengaja TIDAK ada di v1: refresh token, multi-user, peran/role,
rate-limit login (Fase 3). Kegagalan login selalu 401 yang sama —
tanpa membocorkan apakah emailnya ada atau tidak.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from .config import get_settings
from .database import get_db
from .models import AdminSession, AdminUser

PBKDF2_ITERATIONS = 600_000
_SALT_BYTES = 16

_bearer = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    """`pbkdf2_sha256$iterasi$salt_hex$hash_hex`."""
    salt = secrets.token_bytes(_SALT_BYTES)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS
    )
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        algo, iterations, salt_hex, hash_hex = stored.split("$")
    except ValueError:
        return False
    if algo != "pbkdf2_sha256":
        return False
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        bytes.fromhex(salt_hex),
        int(iterations),
    )
    return hmac.compare_digest(digest.hex(), hash_hex)


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_session(db: Session, user: AdminUser) -> tuple[str, datetime]:
    """Buat sesi baru; kembalikan (token mentah — hanya terlihat SEKALI,
    saat login, expires_at)."""
    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(
        days=get_settings().ADMIN_SESSION_DAYS
    )
    db.add(
        AdminSession(
            user_id=user.id, token_hash=_hash_token(token), expires_at=expires_at
        )
    )
    db.commit()
    return token, expires_at


def authenticate(db: Session, email: str, password: str) -> AdminUser | None:
    user = db.query(AdminUser).filter(AdminUser.email == email.strip().lower()).first()
    if user is None or not verify_password(password, user.password_hash):
        return None
    return user


def get_current_admin(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> AdminUser:
    """Dependency endpoint admin. 401 bila token tidak ada / tidak dikenal /
    kedaluwarsa. Sesi kedaluwarsa dihapus saat ditemukan (bersih-bersih)."""
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Butuh login admin.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise unauthorized
    session = (
        db.query(AdminSession)
        .filter(AdminSession.token_hash == _hash_token(credentials.credentials))
        .first()
    )
    now = datetime.now(timezone.utc)
    if session is None:
        raise unauthorized
    if session.expires_at.tzinfo is None:
        expires = session.expires_at.replace(tzinfo=timezone.utc)
    else:
        expires = session.expires_at
    if expires <= now:
        db.delete(session)
        db.commit()
        raise unauthorized
    user = db.get(AdminUser, session.user_id)
    if user is None:
        raise unauthorized
    return user
