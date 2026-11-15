"""Router /api/v1/companies — daftar + detail perusahaan beserta skor.

Skor berasal dari flag-engine via services.scoring (ADR-0005, D7):
total ternormalisasi, label butuh >= 3 sinyal penentu dari >= 2 kategori.
Bila label "Belum cukup data", `score` = null (kontrak Tim Web).
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..errors import not_found
from ..models import Company, Signal
from ..schemas import CompanyListItem, CompanyOut, PageOut
from ..services.scoring import public_score, score_company, signal_to_public

router = APIRouter(prefix="/companies", tags=["companies"])


def _label_and_score(db: Session, company_id: UUID) -> tuple[int | None, str, dict]:
    result = score_company(db, company_id)
    return public_score(result), result["label"], result


@router.get("", response_model=PageOut)
def list_companies(
    skor_min: int | None = Query(default=None, ge=0, le=100),
    skor_max: int | None = Query(default=None, ge=0, le=100),
    label: str | None = Query(default=None, description="Green|Mixed|Red|Belum cukup data"),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    companies = db.query(Company).order_by(Company.name).all()
    items: list[CompanyListItem] = []
    for company in companies:
        score, company_label, _ = _label_and_score(db, company.id)
        if skor_min is not None and (score is None or score < skor_min):
            continue
        if skor_max is not None and (score is None or score > skor_max):
            continue
        if label is not None and company_label != label:
            continue
        items.append(
            CompanyListItem(
                id=company.id, slug=company.slug, name=company.name,
                score=score, label=company_label,
            )
        )
    total = len(items)
    pages = max(1, -(-total // per_page))
    start = (page - 1) * per_page
    return PageOut(
        items=items[start : start + per_page],
        total=total, page=page, per_page=per_page, pages=pages,
    )


@router.get("/{slug}", response_model=CompanyOut)
def get_company(slug: str, db: Session = Depends(get_db)):
    company = db.query(Company).filter(Company.slug == slug).first()
    if company is None:
        raise not_found("Perusahaan tidak ditemukan.")
    score, company_label, result = _label_and_score(db, company.id)
    signals = (
        db.query(Signal)
        .filter(Signal.company_id == company.id)
        .order_by(Signal.created_at)
        .all()
    )
    return CompanyOut(
        id=company.id,
        slug=company.slug,
        name=company.name,
        score=score,
        label=company_label,
        signals=[signal_to_public(s) for s in signals],
        warnings=result["warnings"],
        measured_categories=sorted(result.get("decisive_categories") or []),
        decisive_signals=int(result.get("decisive_signals") or 0),
        red_override=bool(result.get("red_override") or False),
    )
