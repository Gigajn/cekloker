"""Test skor ternormalisasi (ADR-0005, D7) + perbaikan K4 di level DB."""

from __future__ import annotations

import pytest
from datetime import date
from sqlalchemy.exc import IntegrityError

from app.models import Signal
from app.services import scoring


def test_score_company_pakai_flag_engine(db, seeded):
    result = scoring.score_company(db, seeded["maju"].id)
    assert result["engine"] == "flag-engine"
    assert result["total"] == 56
    assert result["label"] == "Mixed"
    assert result["measured_cap"] == 45  # reputasi 25 + stabilitas 20
    assert result["decisive_signals"] == 3
    assert result["decisive_categories"] == ["reputasi", "stabilitas"]


def test_belum_cukup_data_score_null(db, seeded):
    result = scoring.score_company(db, seeded["fiktif"].id)
    assert result["label"] == "Belum cukup data"
    assert scoring.public_score(result) is None
    assert isinstance(result["total"], int) and 0 <= result["total"] <= 100


def test_fallback_rumus_sama_dengan_flag_engine(db, seeded):
    """Jalur darurat (flag-engine tidak ada) harus memberi angka yang
    sama dengan jalur utama untuk data yang sama — bila tidak, itu bug."""
    from app.services.scoring import _row_to_dict, _aggregate_fallback

    rows = db.query(Signal).filter(Signal.company_id == seeded["maju"].id).all()
    dicts = [_row_to_dict(r) for r in rows]
    fallback = _aggregate_fallback(dicts)

    import social_signals as ss

    signals = [ss.Signal(**{**d, "evidence_text": d["evidence_text"]}) for d in dicts]
    utama = ss.aggregate_signals(signals)
    for kunci in ("total", "label", "measured_cap", "decisive_signals",
                  "decisive_categories", "red_override"):
        assert fallback[kunci] == utama[kunci], kunci


def test_fee_override_menjadi_red(db, seeded):
    import social_signals as ss

    perusahaan = seeded["fiktif"]
    signal = ss.detect_fee_request(
        "Biaya pendaftaran Rp 250.000, transfer sebelum wawancara.",
        source="glints",
        evidence_url="https://contoh.invalid/fiktif/fee",
        evidence_date=date(2026, 11, 13),
    )
    assert signal.red_override is True
    db.add(Signal(
        company_id=perusahaan.id,
        category=signal.category,
        key=signal.key,
        value=signal.value,
        points=signal.points,
        evidence_url=signal.evidence_url,
        evidence_text=signal.evidence_text or None,
        evidence_date=date(2026, 11, 13),
        source=signal.source,
        confidence=signal.confidence,
        decisive=signal.decisive,
        red_override=signal.red_override,
        notes=signal.notes,
    ))
    db.commit()
    result = scoring.score_company(db, perusahaan.id)
    assert result["red_override"] is True
    assert result["label"] == "Red"
    assert result["warnings"]


def test_k4_google_places_teks_ditolak_db(db, seeded):
    """CHECK constraint: google_places + evidence_text terisi HARUS gagal
    di level database (bukan cuma di kode aplikasi)."""
    row = Signal(
        company_id=seeded["maju"].id,
        category="reputasi",
        key="rating_overall",
        value=4.0,
        points=15,
        evidence_url="https://contoh.invalid/x",
        evidence_text="kutipan ulasan — dilarang disimpan",
        source="google_places",
        confidence="high",
    )
    db.add(row)
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()


def test_k4_google_places_teks_kosong_ok(db, seeded):
    row = Signal(
        company_id=seeded["maju"].id,
        category="reputasi",
        key="rating_overall",
        value=4.0,
        points=15,
        evidence_url="https://contoh.invalid/x",
        evidence_text=None,
        source="google_places",
        confidence="high",
    )
    db.add(row)
    db.commit()  # tidak boleh raise
