"""Sinyal reputasi rule-based untuk flag engine CekLoker.

Modul ini MURNI FUNGSI (pure functions): tanpa database, tanpa network,
tanpa I/O. Inputnya data yang SUDAH dikumpulkan secara legal oleh lapisan
lain (entri manual Giga, API resmi, atau RSS publik) — modul ini hanya
mengubah data itu menjadi sinyal + poin.

Aturan main (lihat docs/adr/ADR-0005 dan ADR-0006):
1.  Setiap sinyal WAJIB membawa bukti (evidence_url + evidence_date +
    source). Tanpa bukti, fungsi mengembalikan ``None`` — skor tanpa bukti
    tidak tampil.
2.  Satu ulasan tidak pernah menggerakkan skor sendirian. Rating butuh
    n >= 5 untuk poin apa pun; keluhan berulang butuh >= 3 ulasan berbeda.
3.  Kata kunci dicocokkan dengan pelindung negasi ("tidak pernah telat"
    bukan bukti "gaji telat") dan konteks biaya ("staff administrasi"
    bukan bukti "biaya administrasi").
4.  Tidak ada sentimen ML di sini — sengaja. Lihat ADR-0005 § "Kenapa
    sentimen ML ditunda".
5.  Tidak ada data pribadi yang diproses: fungsi ini tidak menerima nama
    reviewer, email, telepon, atau isi DM/grup tertutup. Kutipan
    (evidence_text) dibatasi <= 280 karakter oleh pemanggil; fungsi
    ``_truncate_quote`` memotong bila lebih.
6.  ``evidence_text`` boleh None (tidak ada kutipan) — dan untuk sumber
    ``google_places`` WAJIB kosong (None/""): Places API Policies melarang
    menyimpan teks ulasan; yang boleh disimpan hanya rating, jumlah,
    place_id, dan tautan. Pelanggaran DITOLAK keras (``ValueError``),
    bukan diam-diam dikosongkan (K4, ADR-0006).
7.  Total skor DINORMALISASI (D7, disetujui Giga 15 Nov 2026 — lihat
    ADR-0005 Amandemen D7): ``100 × perolehan / cap terukur``. "Cap
    terukur" = jumlah cap kategori yang punya sinyal penentu. Bila 0
    kategori terukur, total = None (bukan 0) dan label "Belum cukup data".

Penggunaan:
    from social_signals import score_rating, detect_complaints, ...

Semua tanggal memakai ``datetime.date``. ``evidence_date`` boleh berupa
``date`` atau string ISO ``YYYY-MM-DD``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date
from typing import Iterable, Mapping, Sequence

__all__ = [
    "Signal",
    "Confidence",
    "CATEGORY_CAPS",
    "SOURCE_GOOGLE_PLACES",
    "COMPLAINT_CLUSTERS",
    "FEE_PATTERNS",
    "EVERGREEN_ROLE_KEYWORDS",
    "score_rating",
    "score_recommend_rate",
    "detect_complaints",
    "detect_fee_request",
    "score_ghost_job",
    "score_news_event",
    "normalized_total",
    "aggregate_signals",
]

# ---------------------------------------------------------------------------
# Konstanta rubrik (diputuskan di ADR-0005; JANGAN ubah angka diam-diam —
# perubahan ambang wajib lewat ADR baru + kalibrasi ulang Fase 2).
# ---------------------------------------------------------------------------

#: Batas poin per kategori (total 100). Lihat docs/SCORING.md.
CATEGORY_CAPS: dict[str, int] = {
    "reputasi": 25,
    "transparansi": 25,
    "stabilitas": 20,
    "praktik_rekrutmen": 15,
    "gaji_benefit": 15,
}

#: Sumber ulasan Google (Places API). Satu-satunya sumber yang
#: evidence_text-nya WAJIB kosong — lihat K4 di Signal.__post_init__.
SOURCE_GOOGLE_PLACES = "google_places"

#: Label skor. "Belum cukup data" bila sinyal penentu < 3 (ARCHITECTURE §5).
LABEL_GREEN_MIN = 70
LABEL_MIXED_MIN = 40

#: Jumlah ulasan minimum agar rating boleh memberi poin penuh / setengah.
RATING_MIN_N_FULL = 20
RATING_MIN_N_HALF = 5

#: Ambang rating (skala 1-5). Batas bawah tiap tingkat.
RATING_GREEN_MIN = 4.0
RATING_OK_MIN = 3.5
RATING_BAD_MAX = 2.5

#: Keluhan berulang: butuh minimal 3 ulasan berbeda untuk -5, dan
#: >= 5 ulasan DAN pangsa >= 10% dari sampel untuk -15.
COMPLAINT_MIN_N_WARN = 3
COMPLAINT_MIN_N_SEVERE = 5
COMPLAINT_MIN_SHARE_SEVERE = 0.10

#: Ghost job: lowongan yang sama tayang > 90 hari tanpa perubahan.
GHOST_JOB_DAYS = 90
#: ... dan butuh >= 3 lowongan basi sekaligus agar memberi poin (-10).
#: Satu lowongan basi saja = konteks, bukan poin.
GHOST_JOB_MIN_STALE_COUNT = 3

#: Berita PHK/tutup: hanya dihitung bila masih dalam 12 bulan terakhir
#: dan dikuatkan >= 2 media independen (atau pernyataan resmi perusahaan).
NEWS_EVENT_WINDOW_MONTHS = 12

#: Panjang maksimum kutipan bukti (karakter). Kutipan lebih panjang
#: dipotong — kami mengutip, bukan menyalin isi ulasan.
MAX_QUOTE_CHARS = 280


class Confidence:
    """Tingkat kepercayaan sinyal (string biasa agar mudah diserialisasi)."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass(frozen=True)
class Signal:
    """Satu sinyal flag beserta bukti yang bisa diklik.

    ``points`` adalah kontribusi sinyal ini ke skor kategori (bisa negatif).
    ``red_override`` True berarti sinyal ini memicu label Red + peringatan
    apa pun skor lainnya (saat ini hanya ``fee_request`` — lowongan yang
    meminta biaya; lihat ARCHITECTURE.md §5).
    """

    category: str  # reputasi | transparansi | stabilitas | praktik_rekrutmen | gaji_benefit
    key: str  # mis. "rating_overall", "complaint_repeated"
    value: object  # angka / string / bool — nilai mentah yang diukur
    points: int
    evidence_url: str
    # Kutipan singkat (<= 280 karakter). Boleh None — artinya "tidak ada
    # kutipan" (mis. sinyal dari angka agregat saja). Untuk sumber
    # google_places WAJIB kosong (None atau "") — lihat __post_init__ (K4).
    evidence_text: str | None
    evidence_date: date | str | None
    source: str  # mis. "glassdoor", "jobstreet_review", "google_places", "google_news_rss"
    confidence: str  # "high" | "medium" | "low"
    red_override: bool = False
    notes: str = ""
    #: True bila sinyal ini cukup kuat untuk dihitung sebagai penentu
    #: label "Belum cukup data" (< 3 sinyal penentu). Rating dengan n < 5
    #: atau konteks tanpa poin -> False.
    decisive: bool = False

    def __post_init__(self) -> None:
        # K4 (ADR-0006 butir A-3): Google Places API Policies melarang
        # menyimpan teks ulasan — hanya place_id yang dikecualikan dari
        # larangan pre-fetch/cache/store. Karena itu sinyal dari
        # google_places yang membawa evidence_text terisi DITOLAK keras
        # (ValueError), BUKAN diam-diam dikosongkan: pemanggil yang
        # keliru mengirim teks ulasan harus langsung ketahuan dan
        # diperbaiki di sumbernya, bukan lolos tanpa jejak. Yang boleh
        # disimpan dari sumber ini: rating, jumlah ulasan, place_id,
        # dan tautan (lihat `value`/`evidence_url` — bukan teks).
        # Kosong yang diterima: None, "", atau hanya spasi.
        if self.source == SOURCE_GOOGLE_PLACES and (self.evidence_text or "").strip():
            raise ValueError(
                "sinyal google_places dilarang membawa evidence_text "
                "(Places API Policies: teks ulasan tidak boleh disimpan; "
                "hanya rating, jumlah, place_id, dan tautan yang boleh)"
            )


# ---------------------------------------------------------------------------
# Kata kunci keluhan berulang (Indonesia + Inggris).
#
# Satu "cluster" = satu jenis keluhan. Satu ulasan dihitung SEKALI per
# cluster tidak peduli berapa kali kata kuncinya muncul di ulasan itu —
# supaya satu ulasan marah yang mengulang kata yang sama tidak dihitung 5x.
# ---------------------------------------------------------------------------

#: cluster -> daftar pola regex (dicocokkan case-insensitive).
COMPLAINT_CLUSTERS: dict[str, tuple[str, ...]] = {
    "lembur_tidak_dibayar": (
        r"lembur\s+(tidak|tak|nggak|ngga|ga|gak)\s+dibayar",
        r"lembur\s+(tidak|tak|nggak|ngga|ga|gak)\s+dihitung",
        r"overtime\s+(tidak|tak|nggak|ngga|ga|gak)\s+dibayar",
        r"unpaid\s+overtime",
        r"lembur\s+gratis",
    ),
    "gaji_telat_atau_ditahan": (
        r"gaji(?:nya)?\s+(telat|terlambat|sering\s+telat|tidak\s+tepat\s+waktu)",
        r"gaji(?:nya)?\s+ditahan",
        r"gaji(?:nya)?\s+dipotong\s+(sepihak|tanpa\s+alasan)",
        r"salary\s+(late|delayed|withheld)",
        r"pay\s+is\s+(always\s+)?late",
    ),
    "phk_sepihak_tanpa_pesangon": (
        r"phk\s+sepihak",
        r"dipecat\s+sepihak",
        r"pemutusan\s+sepihak",
        r"di-phk\s+tanpa\s+pesangon",
        r"tanpa\s+pesangon",
        r"pesangon\s+(tidak|tak|nggak|ngga|ga|gak)\s+dibayar",
        r"unilateral\s+termination",
    ),
    "jam_kerja_berlebihan": (
        r"kerja\s+sampai\s+tengah\s+malam",
        r"pulang\s+tengah\s+malam",
        r"kerja\s+12\s+jam",
        r"tidak\s+ada\s+work[\s-]?life\s+balance",
        r"no\s+work[\s-]?life\s+balance",
        r"jam\s+kerja\s+tidak\s+manusiawi",
    ),
}

#: Pola negasi (regex dengan batas kata — BUKAN substring, supaya
#: "harga" tidak disangka mengandung "ga"). Dicek pada 25 karakter
#: SEBELUM awal kecocokan. Lihat grill G-4/G-5.
NEGATION_PATTERNS: tuple[str, ...] = (
    r"\btidak pernah\b",
    r"\bbelum pernah\b",
    r"\btidak\b",
    r"\btak\b",
    r"\bnggak\b",
    r"\bngga\b",
    r"\bgak\b",
    r"\bga\b",
    r"\bbukan\b",
    r"\bnever\b",
    r"\bnot\b",
    r"\bno\b",
)

#: Pola permintaan biaya dalam teks lowongan / proses rekrutmen.
#: Syarat keras: kata "adm" atau "administrasi" HANYA dihitung bila
#: berdampingan dengan "biaya"/"bayar"/"uang" — "staff administrasi"
#: (jabatan yang sah) tidak boleh memicu. Lihat grill G-5.
FEE_PATTERNS: tuple[str, ...] = (
    r"biaya\s+(pendaftaran|administrasi|adm|training|pelatihan|seragam|tes|psikotes|medical|check[\s-]?up|deposit|jaminan|materi)",
    r"(uang|dana)\s+(pendaftaran|administrasi|jaminan|deposit|training|pelatihan)",
    r"bayar\s+(biaya\s+)?(pendaftaran|administrasi|adm|training|pelatihan|seragam|deposit|jaminan)",
    r"transfer\s+(biaya\s+)?(pendaftaran|administrasi|adm|training|pelatihan|deposit)",
    r"dp\s+(pendaftaran|training|pelatihan|administrasi)",
    r"uang\s+muka\s+(untuk\s+)?(pendaftaran|training|pelatihan|administrasi)",
    r"biaya\s+adm\b",
    r"adm\s+sebesar\s+rp",
    r"rp\s?[\d\.,]+\s*(untuk\s+)?(biaya\s+)?(pendaftaran|administrasi|adm|training|pelatihan)",
)

#: Jabatan yang lowongannya WAJAR selalu tayang (rekrutmen bergulir /
#: turnover tinggi). Ghost-job tidak memberi poin untuk jabatan ini —
#: hanya konteks. Lihat grill G-6.
EVERGREEN_ROLE_KEYWORDS: tuple[str, ...] = (
    "sales",
    "driver",
    "kurir",
    "pengemudi",
    "telemarketing",
    "collector",
    "agen",
    "agent",
    "satpam",
    "security",
)


# ---------------------------------------------------------------------------
# Utilitas internal
# ---------------------------------------------------------------------------

def _truncate_quote(text: str | None) -> str | None:
    """Potong kutipan ke MAX_QUOTE_CHARS; tanpa pemotongan tidak tampil.

    None dipertahankan sebagai None (bukan diubah jadi "") — supaya
    pemanggil yang sengaja tidak memberi kutipan tetap tercatat "tidak
    ada kutipan" di model/skema, bukan "kutipan kosong". Lihat K4.
    """
    if text is None:
        return None
    text = " ".join(text.split())
    if len(text) <= MAX_QUOTE_CHARS:
        return text
    return text[: MAX_QUOTE_CHARS - 1].rstrip() + "…"


def _require_evidence(evidence_url: str, source: str) -> None:
    """Skor tanpa bukti tidak tampil — gagal keras, bukan diam-diam 0."""
    if not evidence_url or not str(evidence_url).strip():
        raise ValueError(f"sinyal dari {source} butuh evidence_url (skor tanpa bukti tidak tampil)")
    if not source or not str(source).strip():
        raise ValueError("sinyal butuh source")


def _has_negation_before(text_lower: str, match_start: int) -> bool:
    """True bila ada kata negasi dalam 25 karakter sebelum kecocokan."""
    window = text_lower[max(0, match_start - 25) : match_start]
    return any(re.search(p, window) for p in NEGATION_PATTERNS)


def _matches_cluster(text: str, patterns: Iterable[str]) -> bool:
    """True bila satu pola cocok TANPA negasi di depannya."""
    text_lower = text.lower()
    for pattern in patterns:
        for match in re.finditer(pattern, text_lower):
            if not _has_negation_before(text_lower, match.start()):
                return True
    return False


# ---------------------------------------------------------------------------
# Sinyal 1 — rating keseluruhan (Glassdoor / JobStreet Review / Google)
# ---------------------------------------------------------------------------

def score_rating(
    rating: float,
    n_reviews: int,
    *,
    source: str,
    evidence_url: str,
    evidence_date: date | str | None,
    evidence_text: str | None = "",
) -> Signal:
    """Skor dari rating agregat + jumlah ulasan.

    ``evidence_text`` boleh None (tidak ada kutipan); untuk sumber
    ``google_places`` WAJIB kosong — bila terisi, Signal menolak keras
    (ValueError, lihat K4 di ``Signal.__post_init__``).

    Poin penuh HANYA bila n >= 20 (galat baku rata-rata rating dengan
    simpangan baku ~1,0 pada n=20 adalah ~0,22 — cukup untuk membedakan
    4,0 dari 3,5. Pada n=5 galat bakunya ~0,45: terlalu berisik untuk
    poin penuh). n 5-19 -> setengah poin. n < 5 -> 0 poin, konteks saja.

    Justifikasi angka ini (bukan asal tebak) ada di ADR-0005; angka ini
    heuristik yang WAJIB dikalibrasi ulang di Fase 2 (50 perusahaan).
    """
    _require_evidence(evidence_url, source)
    if not 1.0 <= rating <= 5.0:
        raise ValueError(f"rating harus 1,0-5,0, dapat {rating!r}")
    if n_reviews < 0:
        raise ValueError("n_reviews tidak boleh negatif")

    if n_reviews >= RATING_MIN_N_FULL:
        confidence = Confidence.HIGH if n_reviews >= 50 else Confidence.MEDIUM
        factor = 1.0
    elif n_reviews >= RATING_MIN_N_HALF:
        confidence = Confidence.LOW
        factor = 0.5
    else:
        return Signal(
            category="reputasi",
            key="rating_overall",
            value=rating,
            points=0,
            evidence_url=evidence_url,
            evidence_text=_truncate_quote(evidence_text),
            evidence_date=evidence_date,
            source=source,
            confidence=Confidence.LOW,
            notes=f"n={n_reviews} < {RATING_MIN_N_HALF}: terlalu sedikit untuk poin, konteks saja.",
        )

    if rating >= RATING_GREEN_MIN:
        base = 15
    elif rating >= RATING_OK_MIN:
        base = 8
    elif rating > RATING_BAD_MAX:
        base = 0
    else:
        base = -10

    points = int(round(base * factor))
    return Signal(
        category="reputasi",
        key="rating_overall",
        value=rating,
        points=points,
        evidence_url=evidence_url,
        evidence_text=_truncate_quote(evidence_text),
        evidence_date=evidence_date,
        source=source,
        confidence=confidence,
        notes=f"rating {rating} dari n={n_reviews} ulasan ({source}).",
        decisive=True,
    )


# ---------------------------------------------------------------------------
# Sinyal 2 — % karyawan merekomendasikan perusahaan (JobStreet / Glassdoor)
# ---------------------------------------------------------------------------

def score_recommend_rate(
    pct_recommend: float,
    n_reviews: int,
    *,
    source: str,
    evidence_url: str,
    evidence_date: date | str | None,
    evidence_text: str | None = "",
) -> Signal:
    """Skor dari persentase 'merekomendasikan ke teman'.

    ``evidence_text`` boleh None; untuk ``google_places`` WAJIB kosong
    (K4 — lihat ``Signal.__post_init__``).

    n < 20 -> konteks saja (persentase dari segelintir orang menyesatkan:
    100% dari 4 orang bukan sinyal). Ambang 80% / 50% heuristik Fase 2.
    """
    _require_evidence(evidence_url, source)
    if not 0.0 <= pct_recommend <= 100.0:
        raise ValueError(f"pct_recommend harus 0-100, dapat {pct_recommend!r}")
    if n_reviews < 0:
        raise ValueError("n_reviews tidak boleh negatif")

    if n_reviews < RATING_MIN_N_FULL:
        return Signal(
            category="reputasi",
            key="recommend_rate",
            value=pct_recommend,
            points=0,
            evidence_url=evidence_url,
            evidence_text=_truncate_quote(evidence_text),
            evidence_date=evidence_date,
            source=source,
            confidence=Confidence.LOW,
            notes=f"n={n_reviews} < {RATING_MIN_N_FULL}: persentase belum stabil, konteks saja.",
        )

    if pct_recommend >= 80:
        points = 5
    elif pct_recommend >= 50:
        points = 0
    else:
        points = -5
    return Signal(
        category="reputasi",
        key="recommend_rate",
        value=pct_recommend,
        points=points,
        evidence_url=evidence_url,
        evidence_text=_truncate_quote(evidence_text),
        evidence_date=evidence_date,
        source=source,
        confidence=Confidence.MEDIUM,
        notes=f"{pct_recommend}% merekomendasikan (n={n_reviews}).",
        decisive=True,
    )


# ---------------------------------------------------------------------------
# Sinyal 3 — keluhan berulang dari teks ulasan
# ---------------------------------------------------------------------------

def detect_complaints(
    reviews: Sequence[Mapping[str, object]],
    *,
    source: str,
    evidence_url: str,
    evidence_date: date | str | None,
) -> Signal:
    """Deteksi keluhan berulang dari daftar ulasan.

    ``reviews``: list dict ``{"text": str, "date": ..., "url": ...}``.
    Satu ulasan dihitung SEKALI per cluster. Ambang (ADR-0005):
    >= 3 ulasan berbeda dengan keluhan yang sama -> -5;
    >= 5 ulasan DAN pangsa >= 10% dari sampel -> -15.
    Di bawah itu -> 0 poin, konteks saja (termasuk 1-2 ulasan ekstrem).

    Catatan K4: fungsi ini MEMBANGUN evidence_text dari teks ulasan,
    jadi JANGAN dipanggil dengan source="google_places" — teks ulasan
    Google dilarang disimpan (ADR-0006), dan Signal akan menolak keras
    (ValueError) bila kutipan keluhan berhasil dibentuk dari sumber itu.

    Nilai ``value`` adalah dict {cluster: jumlah ulasan} untuk cluster
    yang muncul. ``evidence_text`` berisi contoh kutipan pertama yang
    cocok (<= 280 karakter, tanpa nama reviewer).
    """
    _require_evidence(evidence_url, source)
    texts = [str(r.get("text") or "") for r in reviews]
    n = len(texts)

    counts: dict[str, int] = {}
    first_quote: dict[str, str] = {}
    for cluster, patterns in COMPLAINT_CLUSTERS.items():
        hit = 0
        for text in texts:
            if _matches_cluster(text, patterns):
                hit += 1
                if cluster not in first_quote:
                    first_quote[cluster] = _truncate_quote(text)
        if hit:
            counts[cluster] = hit

    total_distinct = 0
    seen_idx: set[int] = set()
    for i, text in enumerate(texts):
        if any(_matches_cluster(text, COMPLAINT_CLUSTERS[c]) for c in counts):
            seen_idx.add(i)
    total_distinct = len(seen_idx)

    share = (total_distinct / n) if n else 0.0
    if total_distinct >= COMPLAINT_MIN_N_SEVERE and share >= COMPLAINT_MIN_SHARE_SEVERE:
        points = -15
        level = "berat"
    elif total_distinct >= COMPLAINT_MIN_N_WARN:
        points = -5
        level = "ringan"
    else:
        points = 0
        level = "konteks"

    worst = max(counts, key=lambda c: counts[c]) if counts else ""
    quote = first_quote.get(worst, "")
    confidence = (
        Confidence.MEDIUM
        if (points != 0 and n >= RATING_MIN_N_FULL)
        else Confidence.LOW
    )
    return Signal(
        category="reputasi",
        key="complaint_repeated",
        value=counts,
        points=points,
        evidence_url=evidence_url,
        evidence_text=quote,
        evidence_date=evidence_date,
        source=source,
        confidence=confidence,
        notes=(
            f"keluhan {level}: {total_distinct} dari {n} ulasan mengandung "
            f"keluhan berulang {counts or '—'}."
        ),
        decisive=(points != 0),
    )


# ---------------------------------------------------------------------------
# Sinyal 4 — permintaan biaya (red flag langsung, override label Red)
# ---------------------------------------------------------------------------

def detect_fee_request(
    job_text: str,
    *,
    source: str,
    evidence_url: str,
    evidence_date: date | str | None,
) -> Signal:
    """Deteksi permintaan biaya pendaftaran/pelatihan/dsb. dalam teks lowongan.

    Bila cocok -> ``red_override=True``: label jadi Red + peringatan apa
    pun skor lainnya (ARCHITECTURE.md §5). Poin sinyal ini 0 — sanksinya
    berupa override, bukan pengurangan poin, supaya tidak bisa "ditebus"
    oleh poin positif lain.
    """
    _require_evidence(evidence_url, source)
    text_lower = (job_text or "").lower()
    matched: list[str] = []
    for pattern in FEE_PATTERNS:
        m = re.search(pattern, text_lower)
        if m and not _has_negation_before(text_lower, m.start()):
            matched.append(pattern)

    if matched:
        return Signal(
            category="transparansi",
            key="fee_request",
            value=True,
            points=0,
            evidence_url=evidence_url,
            evidence_text=_truncate_quote(job_text or ""),
            evidence_date=evidence_date,
            source=source,
            confidence=Confidence.HIGH,
            red_override=True,
            notes=(
                "Teks lowongan meminta biaya (pola: "
                + "; ".join(matched)
                + "). Bukan tuduhan 'penipu' — hanya fakta kutipan + peringatan."
            ),
            decisive=True,
        )
    return Signal(
        category="transparansi",
        key="fee_request",
        value=False,
        points=0,
        evidence_url=evidence_url,
        evidence_text="",
        evidence_date=evidence_date,
        source=source,
        confidence=Confidence.HIGH,
        notes="Tidak ditemukan permintaan biaya pada teks lowongan ini.",
    )


# ---------------------------------------------------------------------------
# Sinyal 5 — ghost job (lowongan hantu)
# ---------------------------------------------------------------------------

def score_ghost_job(
    days_visible: int,
    stale_job_count: int,
    *,
    job_title: str = "",
    source: str,
    evidence_url: str,
    evidence_date: date | str | None,
) -> Signal:
    """Ghost job: lowongan yang sama tayang > 90 hari tanpa perubahan.

    Poin -10 HANYA bila perusahaan punya >= 3 lowongan basi sekaligus
    DAN jabatan bukan evergreen (sales/driver/dsb. memang rekrutmen
    bergulir — menandainya ghost job adalah kesalahan, grill G-6).
    Selain itu -> 0 poin, konteks saja.
    """
    _require_evidence(evidence_url, source)
    title_lower = (job_title or "").lower()
    is_evergreen = any(k in title_lower for k in EVERGREEN_ROLE_KEYWORDS)

    if days_visible <= GHOST_JOB_DAYS:
        return Signal(
            category="praktik_rekrutmen",
            key="ghost_job",
            value=days_visible,
            points=0,
            evidence_url=evidence_url,
            evidence_text="",
            evidence_date=evidence_date,
            source=source,
            confidence=Confidence.HIGH,
            notes=f"Tayang {days_visible} hari (<= {GHOST_JOB_DAYS}): bukan ghost job.",
        )
    if is_evergreen:
        return Signal(
            category="praktik_rekrutmen",
            key="ghost_job",
            value=days_visible,
            points=0,
            evidence_url=evidence_url,
            evidence_text="",
            evidence_date=evidence_date,
            source=source,
            confidence=Confidence.LOW,
            notes=(
                f"Tayang {days_visible} hari tapi jabatan '{job_title}' termasuk "
                "evergreen (rekrutmen bergulir): konteks saja, tanpa poin."
            ),
        )
    if stale_job_count >= GHOST_JOB_MIN_STALE_COUNT:
        return Signal(
            category="praktik_rekrutmen",
            key="ghost_job",
            value=days_visible,
            points=-10,
            evidence_url=evidence_url,
            evidence_text="",
            evidence_date=evidence_date,
            source=source,
            confidence=Confidence.MEDIUM,
            notes=(
                f"Tayang {days_visible} hari tanpa perubahan; perusahaan punya "
                f"{stale_job_count} lowongan basi sekaligus."
            ),
            decisive=True,
        )
    return Signal(
        category="praktik_rekrutmen",
        key="ghost_job",
        value=days_visible,
        points=0,
        evidence_url=evidence_url,
        evidence_text="",
        evidence_date=evidence_date,
        source=source,
        confidence=Confidence.LOW,
        notes=(
            f"Tayang {days_visible} hari tapi baru {stale_job_count} lowongan "
            "basi: konteks saja, butuh >= 3 untuk poin."
        ),
    )


# ---------------------------------------------------------------------------
# Sinyal 6 — berita: PHK massal / tutup vs ekspansi / pendanaan
# ---------------------------------------------------------------------------

def score_news_event(
    event_type: str,
    *,
    n_outlets: int,
    within_months: int,
    source: str = "google_news_rss",
    evidence_url: str,
    evidence_date: date | str | None,
    evidence_text: str | None = "",
) -> Signal:
    """Sinyal dari berita (judul + media, BUKAN isi artikel penuh).

    ``evidence_text`` boleh None; untuk ``google_places`` WAJIB kosong
    (K4 — lihat ``Signal.__post_init__``).

    ``event_type``: "layoff_massal" | "tutup" | "ekspansi" | "pendanaan".
    Poin negatif HANYA bila >= 2 media independen (atau pernyataan resmi)
    DAN kejadian <= 12 bulan terakhir — satu artikel bisa jadi rumor
    (grill G-7). Di luar itu -> konteks saja.
    """
    _require_evidence(evidence_url, source)
    event_type = (event_type or "").strip().lower()
    known = {"layoff_massal", "tutup", "ekspansi", "pendanaan"}
    if event_type not in known:
        raise ValueError(f"event_type harus salah satu {sorted(known)}, dapat {event_type!r}")
    if n_outlets < 1:
        raise ValueError("n_outlets minimal 1 (satu artikel pun harus ada buktinya)")

    fresh = within_months <= NEWS_EVENT_WINDOW_MONTHS
    corroborated = n_outlets >= 2

    if event_type in ("layoff_massal", "tutup"):
        if fresh and corroborated:
            points, confidence = -15, Confidence.MEDIUM
            notes = f"Berita {event_type} dalam {within_months} bln terakhir, {n_outlets} media."
        else:
            points, confidence = 0, Confidence.LOW
            notes = (
                f"Berita {event_type} ({n_outlets} media, {within_months} bln lalu) "
                "belum memenuhi syarat poin (butuh >= 2 media & <= 12 bln): konteks saja."
            )
    else:  # ekspansi / pendanaan
        if fresh and corroborated:
            points, confidence = 5, Confidence.MEDIUM
            notes = f"Berita {event_type} dalam {within_months} bln terakhir, {n_outlets} media."
        else:
            points, confidence = 0, Confidence.LOW
            notes = (
                f"Berita {event_type} ({n_outlets} media, {within_months} bln lalu) "
                "belum memenuhi syarat poin: konteks saja."
            )

    return Signal(
        category="stabilitas",
        key=f"news_{event_type}",
        value=event_type,
        points=points,
        evidence_url=evidence_url,
        evidence_text=_truncate_quote(evidence_text),
        evidence_date=evidence_date,
        source=source,
        confidence=confidence,
        notes=notes,
        decisive=(points != 0),
    )


# ---------------------------------------------------------------------------
# Agregasi
# ---------------------------------------------------------------------------

def normalized_total(earned: int, measured_cap: int) -> int | None:
    """Total ternormalisasi D7 (disetujui Giga 15 Nov 2026 — ADR-0005
    Amandemen D7): ``100 × perolehan / cap terukur``, dijepit 0–100.

    Apa itu "cap terukur"?
    Jumlah cap kategori yang SUDAH PUNYA sinyal penentu (``decisive=True``)
    — bukan jumlah cap kelima kategori (100), dan bukan jumlah cap semua
    kategori yang punya sinyal apa pun. Sinyal konteks (0 poin, tidak
    penentu — mis. rating dari 2 ulasan) TIDAK membuat kategorinya
    terukur, karena konteks tidak membuktikan apa-apa tentang perusahaan
    itu. Kategori yang belum terukur tidak masuk penyebut, supaya
    "data belum diukur" tidak disamakan dengan "data buruk".

    Bila ``measured_cap`` == 0 (tidak ada satu pun kategori terukur):
    kembalikan None — JANGAN bagi nol, dan JANGAN kembalikan 0, karena
    0/100 akan dibaca sebagai "perusahaan paling buruk" padahal artinya
    "kami belum tahu apa-apa". Pemanggil (API/UI) wajib menampilkan
    label "Belum cukup data", bukan angka 0.

    Pembulatan memakai ``round()`` Python (half-even, ke genap terdekat);
    selisih dari nilai eksak maksimal 1 poin. Nilai tepat 39,5 / 69,5
    (yang akan mengubah label bila dibulatkan) tidak dapat terjadi
    dengan cap kategori 15/20/25 — jadi pembulatan tidak pernah mengubah
    label Green/Mixed/Red.
    """
    if measured_cap <= 0:
        return None
    return max(0, min(100, int(round(100 * earned / measured_cap))))


def aggregate_signals(signals: Sequence[Signal]) -> dict:
    """Gabungkan sinyal menjadi skor total + label.

    Rumus D7 (ADR-0005 Amandemen D7, disetujui Giga 15 Nov 2026) —
    total BUKAN penjumlahan mentah seperti draf ARCHITECTURE.md §5.
    Penjumlahan mentah menghukum data yang BELUM diukur seolah-olah itu
    data BURUK — perusahaan bagus yang baru terukur reputasinya (maks.
    25 poin) akan langsung berlabel Red (25/100). Karena itu total di
    sini DINORMALISASI terhadap kategori yang sudah terukur:

        total = 100 * (poin kategori) / (cap kategori yang terukur)

    "Cap terukur" (``measured_cap``) = jumlah cap kategori yang punya
    >= 1 sinyal penentu — lihat ``normalized_total`` untuk definisi
    lengkapnya. Bila 0 kategori terukur, total = None (bukan 0).

    Label diberikan bila ada >= 3 sinyal penentu dari >= 2 kategori
    berbeda; di bawah itu labelnya "Belum cukup data" (bukan Mixed/Red).
    Perhatian: total tetap dihitung (angka) walau labelnya "Belum cukup
    data" — angka itu hanya untuk debug/internal; UI wajib menampilkan
    labelnya, bukan angkanya. Fee (red_override) -> label "Red" +
    peringatan, apa pun totalnya.

    Kembalian: dict dengan kunci total (int | None), label, per_category,
    measured_cap, decisive_signals, decisive_categories, red_override,
    warnings, signals.
    """
    per_category: dict[str, int] = {c: 0 for c in CATEGORY_CAPS}
    decisive = 0
    decisive_categories: set[str] = set()
    red_override = False
    warnings: list[str] = []

    for s in signals:
        if s.category not in CATEGORY_CAPS:
            raise ValueError(f"kategori tidak dikenal: {s.category!r}")
        per_category[s.category] += s.points
        if s.red_override:
            red_override = True
            warnings.append(
                "Peringatan: ditemukan permintaan biaya dalam proses rekrutmen "
                f"(bukti: {s.evidence_url})."
            )
        if s.decisive:
            decisive += 1
            decisive_categories.add(s.category)

    per_category = {
        c: max(-cap, min(cap, total)) for c, total in per_category.items() for cap in [CATEGORY_CAPS[c]]
    }
    measured_cap = sum(CATEGORY_CAPS[c] for c in decisive_categories)
    earned = sum(per_category[c] for c in decisive_categories)
    total = normalized_total(earned, measured_cap)

    if red_override:
        label = "Red"
    elif decisive < 3 or len(decisive_categories) < 2:
        label = "Belum cukup data"
    elif total is not None and total >= LABEL_GREEN_MIN:
        label = "Green"
    elif total is not None and total >= LABEL_MIXED_MIN:
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
        "signals": list(signals),
    }
