"""Router /api/v1/signals — daftar sinyal (bukti) per perusahaan."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Company, Signal
from ..errors import not_found
from ..schemas import SignalOut
from ..services.scoring import signal_to_public

router = APIRouter(prefix="/signals", tags=["signals"])


@router.get("", response_model=list[SignalOut])
def list_signals(
    company_id: UUID,
    category: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    company = db.query(Company).filter(Company.id == company_id).first()
    if company is None:
        raise not_found("Perusahaan tidak ditemukan.")
    query = db.query(Signal).filter(Signal.company_id == company_id)
    if category:
        query = query.filter(Signal.category == category)
    rows = query.order_by(Signal.created_at).all()
    return [SignalOut(**signal_to_public(r)) for r in rows]
