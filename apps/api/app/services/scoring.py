"""Skor perusahaan — dibaca dari flag-engine (ADR-0005, D7), bukan dihitung
ulang dengan rumus tandingan.

Sumber kebenaran: `packages/flag-engine/social_signals.py`,
fungsi `aggregate_signals`. Modul itu pure function; service ini hanya
memetakan baris `signals` di DB menjadi dataclass `Signal` lalu
memanggilnya. Jadi bila Tim Normalisasi / flag-engine mengubah ambang
lewat ADR, skor API ikut berubah tanpa edit di sini.

Jalur darurat: bila `social_signals` tidak bisa diimpor (mis. API
dijalankan tanpa mount paket flag-engine), dipakai rumus lokal yang
SAMA persis dengan ADR-0005 (`100 x perolehan / cap terukur`, label
butuh >= 3 sinyal penentu dari >= 2 kategori) dan hasilnya ditandai
`engine="fallback"` supaya ketahuan di log/respons — sesuai perintah
tugas ("tandai di kode sebagai menunggu Tim Normalisasi, rumus sama
dengan ADR-0005"). Jalur ini BUKAN sumber kebenaran kedua: ia hanya
pengaman, dan test memverifikasi kedua jalur memberi angka yang sama
untuk data yang sama (lihat tests/test_scoring.py).
"""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

from sqlalchemy.orm import Session

from ..models import Signal as SignalRow

# Cap poin per kategori — SALINAN dari social_signals.CATEGORY_CAPS,
# dipakai HANYA oleh jalur fallback. Bila flag-engine tersedia, nilai
# yang dipakai adalah dari sana.
CATEGORY_CAPS: dict[str, int] = {
    "reputasi": 25,
    "transparansi": 25,
    "stabilitas": 20,
    "praktik_rekrutmen": 15,
    "gaji_benefit": 15,
}
LABEL_GREEN_MIN = 70
LABEL_MIXED_MIN = 40

_ENGINE: str | None = None


def _load_flag_engine():
    """Impor social_signals; bila belum ada di sys.path, coba tambahkan
    packages/flag-engine relatif terhadap repo ini."""
    global _ENGINE
    try:
        import social_signals

        _ENGINE = "flag-engine"
        return social_signals
    except ImportError:
        pass
    repo_root = Path(__file__).resolve().parents[3]
    flag_dir = repo_root / "packages" / "flag-engine"
    if flag_dir.is_dir() and str(flag_dir) not in sys.path:
        sys.path.insert(0, str(flag_dir))
    try:
        import social_signals  # noqa: F811

        _ENGINE = "flag-engine"
        return social_signals
    except ImportError:
        _ENGINE = "fallback"
        return None


def _aggregate_fallback(signals: list[dict]) -> dict:
    """Rumus yang SAMA dengan aggregate_signals (ADR-0005 §3).

    Dipakai hanya bila flag-engine tidak bisa diimpor. Lihat docstring
    modul. Total = 100 x perolehan / cap kategori terukur (kategori
    tanpa sinyal penentu tidak masuk penyebut), dijepit 0-100.
    """
    per_category: dict[str, int] = {c: 0 for c in CATEGORY_CAPS}
    decisive = 0
    decisive_categories: set[str] = set()
    red_override = False
    warnings: list[str] = []
    for s in signals:
        cat = s["category"]
        if cat not in CATEGORY_CAPS:
            raise ValueError(f"kategori tidak dikenal: {cat!r}")
        per_category[cat] += int(s["points"])
        if s.get("red_override"):
            red_override = True
            warnings.append(
                "Peringatan: ditemukan permintaan biaya dalam proses rekrutmen "
                f"(bukti: {s['evidence_url']})."
            )
        if s.get("decisive"):
            decisive += 1
            decisive_categories.add(cat)
    per_category = {
        c: max(-cap, min(cap, total))
        for c, total in per_category.items()
        for cap in [CATEGORY_CAPS[c]]
    }
    measured_cap = sum(CATEGORY_CAPS[c] for c in decisive_categories)
    earned = sum(per_category[c] for c in decisive_categories)
    total = (
        int(round(100 * earned / measured_cap)) if measured_cap > 0 else None
    )
    total = max(0, min(100, total)) if total is not None else None
    if red_override:
        label = "Red"
    elif decisive < 3 or len(decisive_categories) < 2:
        label = "Belum cukup data"
    elif total >= LABEL_GREEN_MIN:
        label = "Green"
    elif total >= LABEL_MIXED_MIN:
        label = "Mixed"
    else:
        label = "Red"
    return {
        "total": total,
        "label": label,
        "per_category": per_category,
        "measured_cap": measured_cap,
        "decisive_signals": decisive,
        "decisive_categories": sorted(decisive_categories),
        "red_override": red_override,
        "warnings": warnings,
    }


def _row_to_dict(row: SignalRow) -> dict:
    return {
        "category": row.category,
        "key": row.key,
        "value": row.value,
        "points": row.points,
        "evidence_url": row.evidence_url,
        "evidence_text": row.evidence_text or "",
        "evidence_date": row.evidence_date,
        "source": row.source,
        "confidence": row.confidence,
        "red_override": row.red_override,
        "notes": row.notes or "",
        "decisive": row.decisive,
    }


def score_company(db: Session, company_id) -> dict:
    """Hitung skor ternormalisasi satu perusahaan dari sinyalnya di DB.

    Kembalian: total, label, per_category, measured_cap,
    decisive_signals, decisive_categories, red_override, warnings,
    engine ("flag-engine" | "fallback").
    """
    rows = (
        db.query(SignalRow)
        .filter(SignalRow.company_id == company_id)
        .order_by(SignalRow.created_at)
        .all()
    )
    engine = _load_flag_engine()
    dicts = [_row_to_dict(r) for r in rows]
    if engine is not None:
        signals = [
            engine.Signal(
                category=d["category"],
                key=d["key"],
                value=d["value"],
                points=d["points"],
                evidence_url=d["evidence_url"],
                evidence_text=d["evidence_text"],
                evidence_date=d["evidence_date"],
                source=d["source"],
                confidence=d["confidence"],
                red_override=d["red_override"],
                notes=d["notes"],
                decisive=d["decisive"],
            )
            for d in dicts
        ]
        result = engine.aggregate_signals(signals)
        result = {k: v for k, v in result.items() if k != "signals"}
    else:
        result = _aggregate_fallback(dicts)
    result["engine"] = _ENGINE or "fallback"
    return result


def public_score(result: dict) -> int | None:
    """Skor yang tampil ke publik: None bila 'Belum cukup data'
    (kontrak bersama Tim Web — skor null = kami belum tahu, bukan 0)."""
    if result["label"] == "Belum cukup data":
        return None
    return result["total"]


def signal_to_public(row: SignalRow) -> dict:
    """Serialisasi satu sinyal sesuai kontrak Tim Web."""
    evidence_date: date | None = row.evidence_date
    return {
        "category": row.category,
        "key": row.key,
        "points": row.points,
        "evidence_url": row.evidence_url,
        "evidence_text": row.evidence_text,  # boleh null (K4)
        "evidence_date": evidence_date.isoformat() if evidence_date else None,
        "source": row.source,
        "confidence": row.confidence,
    }
