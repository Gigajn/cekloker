"""Kolektor sinyal lowongan dari profil publik perusahaan di media sosial.

Cakupan modul ini SENGAJA sempit (lihat ADR-0004):
  * Instagram: HANYA lewat Instagram Graph API resmi — endpoint
    Business Discovery — yang membaca akun Bisnis/Kreator LAIN yang
    bersifat publik. Butuh token akses aplikasi sendiri (diberikan
    caller saat runtime, TIDAK disimpan di file ini / repo).
  * LinkedIn: TIDAK ADA pengambilan otomatis sama sekali. LinkedIn
    User Agreement §8.2 melarang scraping & bot secara eksplisit, dan
    API resminya tidak memberi akses baca postingan perusahaan lain
    tanpa persetujuan partner. Yang disediakan di sini hanya tipe
    `ManualSocialLead`: operator manusia yang membuka halaman publik
    dan mencatat URL + teks + tanggal yang ia lihat sendiri.
  * TIDAK PERNAH: login palsu, instaloader/instagrapi (login dengan
    password = otomatisasi tak resmi), DM/grup tertutup, akun pribadi,
    menyimpan nama/email/telepon siapa pun, menyimpan foto/caption
    utuh untuk dipublikasikan ulang.

Apa yang modul ini hasilkan: BUKAN lowongan. Hasilnya adalah "lead":
petunjuk bahwa perusahaan mungkin sedang membuka lowongan, lengkap
dengan URL sumber + tanggal posting + peringatan keandalan tanggal.
Lead TIDAK BOLEH mengisi `posted_at` suatu lowongan — tanggal posting
IG/LinkedIn bukan tanggal buka lowongan (caption bisa diedit, tanggal
posting ≠ tanggal buka; lihat Hasil Grill di docs/fase1-riset-direct.md).
Lead hanya memicu verifikasi ke halaman karier / board ATS perusahaan.

Hanya stdlib Python. Tanpa kredensial di file mana pun.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

from .career_page import KNOWN_ATS_HOSTS

# ---------------------------------------------------------------------------
# Heuristik klasifikasi caption (teks publik perusahaan)
# ---------------------------------------------------------------------------

_JOB_KEYWORDS = (
    # Bahasa Indonesia
    "lowongan", "loker", "dibuka", "sedang merekrut", "kami merekrut",
    "kesempatan berkarier", "bergabung dengan kami", "join our team",
    "we are hiring", "we're hiring", "we are looking for",
    "now hiring", "open roles", "open positions", "job opening",
    "hiring alert", "apply now", "lamar sekarang", "we're looking for",
    "career opportunity", "join us",
)


_NEGATION_PHRASES = (
    "bukan lowongan", "bukan loker", "tidak ada lowongan", "tidak sedang merekrut",
    "not hiring", "no vacancy", "no open roles", "not a job",
)


def classify_caption_as_job_post(caption: Optional[str]) -> bool:
    """True bila caption postingan publik perusahaan kemungkinan besar
    mengumumkan lowongan (heuristik kata kunci — bukan kepastian).

    Heuristik ini rapuh: postingan "we're hiring" bisa untuk 1 lowongan
    yang sudah tutup, atau untuk lowongan yang tidak pernah diposting
    di board. Hasil True = lead untuk diverifikasi, bukan fakta.
    Frasa negasi ("bukan lowongan", "not hiring") membatalkan klasifikasi
    — caption "Suasana kantor. Bukan lowongan." bukan pengumuman rekrutmen.
    """
    if not caption:
        return False
    lowered = caption.lower()
    if any(phrase in lowered for phrase in _NEGATION_PHRASES):
        return False
    return any(keyword in lowered for keyword in _JOB_KEYWORDS)


_URL_RE = re.compile(r"https?://[^\s\"'<>)\]]+", re.IGNORECASE)


def extract_links(text: Optional[str]) -> list[str]:
    """Ambil semua URL dari sebuah teks (caption / bio)."""
    if not text:
        return []
    seen: list[str] = []
    for match in _URL_RE.findall(text):
        cleaned = match.rstrip(".,;:!?")
        if cleaned not in seen:
            seen.append(cleaned)
    return seen


def is_job_link(url: str) -> bool:
    """True bila URL kemungkinan mengarah ke lowongan / halaman karier:
    domain ATS dikenal, atau path mengandung /careers, /jobs, /karir,
    /lowongan, /loker, /rekrutmen."""
    lowered = url.lower()
    if any(host in lowered for host in KNOWN_ATS_HOSTS):
        return True
    return bool(re.search(r"/(careers?|jobs?|karir|lowongan|loker|rekrutmen|join-us)\b",
                          lowered))


def extract_job_links(text: Optional[str]) -> list[str]:
    """URL dari teks yang kemungkinan mengarah ke lowongan / halaman karier."""
    return [url for url in extract_links(text) if is_job_link(url)]


# ---------------------------------------------------------------------------
# Tipe data hasil
# ---------------------------------------------------------------------------

@dataclass
class PublicCompanyPost:
    """Satu postingan publik perusahaan (Instagram via Graph API resmi).

    `posted_at`: tanggal posting di platform (BUKAN tanggal buka lowongan).
    `date_reliability`: selalu "post_date_only" — tanggal ini TIDAK BOLEH
    dipakai sebagai `posted_at` lowongan.
    `caption_excerpt`: kutipan SINGKAT (maks 500 karakter) untuk bukti,
    bukan salinan penuh (hormati hak cipta).
    """
    platform: str  # "instagram"
    company_handle: str
    post_url: str
    posted_at: Optional[datetime] = None
    caption_excerpt: str = ""
    job_links: list[str] = field(default_factory=list)
    is_job_announcement: bool = False
    date_reliability: str = "post_date_only"
    media_type: Optional[str] = None


@dataclass
class ManualSocialLead:
    """Lead sosial yang dicatat MANUAL oleh operator manusia.

    Dipakai untuk LinkedIn (dan untuk IG bila Graph API tidak tersedia):
    operator membuka halaman publik perusahaan di browser, lalu mencatat
    URL + tanggal lihat + kutipan singkat. TIDAK ADA request otomatis
    ke LinkedIn dari modul ini — dengan sengaja tidak ada fetcher
    LinkedIn. Bila suatu hari LinkedIn memberi akses API resmi untuk
    membaca postingan perusahaan, barulah tipe ini diganti adapter API.
    """
    platform: str  # "linkedin" | "instagram"
    company_name: str
    post_url: str
    seen_at: datetime
    posted_at_claimed: Optional[datetime] = None
    caption_excerpt: str = ""
    job_links: list[str] = field(default_factory=list)
    is_job_announcement: bool = False
    recorded_by: str = "operator-manual"
    date_reliability: str = "post_date_only"
    note: str = ("Dicatat manual dari halaman publik. Tanggal posting "
                 "bukan tanggal buka lowongan; verifikasi ke halaman karier.")


def _parse_iso_datetime(value: Any) -> Optional[datetime]:
    if not value or not isinstance(value, str):
        return None
    text = value.strip()
    try:
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        parsed = datetime.fromisoformat(text)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed
    except ValueError:
        return None


def parse_instagram_business_discovery(payload: dict,
                                       company_handle: str) -> list[PublicCompanyPost]:
    """Parse respons Instagram Graph API — Business Discovery.

    Bentuk respons resmi (developers.facebook.com, endpoint
    `/{ig-user-id}?fields=business_discovery.username({handle})`
    `{username,biography,media{caption,timestamp,permalink,media_type}}`):
    hanya akun Bisnis/Kreator lain yang bisa dibaca, dan hanya field
    publiknya. Butuh token aplikasi sendiri + App Review untuk fitur
    Public Content Access bila memakai Hashtag Search (bukan modul ini).

    CATATAN VERIFIKASI (K-D6): halaman dokumen resmi Meta menolak dibaca
    langsung pada 15 Nov 2026 (HTTP 403 dari sisi Meta). Bentuk di bawah
    mengikuti ringkasan sekunder yang konsisten (Meta for Developers
    via shortsintel/osher, Nov 2026) — PERLU uji live dengan token
    sendiri sebelum dipakai produksi.
    """
    discovery = payload.get("business_discovery") or {}
    media = discovery.get("media") or {}
    items = media.get("data") or []
    posts: list[PublicCompanyPost] = []
    for item in items:
        caption = item.get("caption") or ""
        posts.append(PublicCompanyPost(
            platform="instagram",
            company_handle=company_handle,
            post_url=item.get("permalink") or "",
            posted_at=_parse_iso_datetime(item.get("timestamp")),
            caption_excerpt=caption[:500],
            job_links=extract_job_links(caption),
            is_job_announcement=classify_caption_as_job_post(caption),
            media_type=item.get("media_type"),
        ))
    return posts


def instagram_profile_job_links(biography: Optional[str]) -> list[str]:
    """Link lowongan dari bio profil IG perusahaan (mis. linktr.ee ke
    halaman karier). Bio adalah teks publik; yang diambil hanya URL-nya,
    bukan data pribadi."""
    return extract_job_links(biography)


def to_job_lead(post: PublicCompanyPost) -> dict:
    """Ubah postingan sosial jadi LEAD verifikasi (bukan lowongan).

    Lead ini TIDAK mengandung `posted_at` lowongan — sengaja None —
    supaya tidak ada kode hilir yang salah memakai tanggal posting IG
    sebagai tanggal buka lowongan. Yang dibawa: URL sumber + tanggal
    posting (untuk konteks) + link karier yang ditemukan di caption.
    """
    return {
        "kind": "social_lead",
        "platform": post.platform,
        "company_handle": post.company_handle,
        "source_url": post.post_url,
        "posted_on_platform_at": (post.posted_at.isoformat()
                                  if post.posted_at else None),
        "job_links_found": post.job_links,
        "is_job_announcement": post.is_job_announcement,
        "caption_excerpt": post.caption_excerpt,
        # Dengan sengaja: tidak ada posted_at lowongan di sini.
        "job_posted_at": None,
        "date_reliability": post.date_reliability,
        "next_step": ("Verifikasi manual/otomatis ke halaman karier atau "
                      "board ATS perusahaan sebelum ditampilkan sebagai lowongan."),
    }


def to_job_lead_manual(lead: ManualSocialLead) -> dict:
    """Versi manual (LinkedIn / IG tanpa API) dari `to_job_lead`."""
    return {
        "kind": "social_lead_manual",
        "platform": lead.platform,
        "company_name": lead.company_name,
        "source_url": lead.post_url,
        "seen_at": lead.seen_at.isoformat(),
        "posted_on_platform_at": (lead.posted_at_claimed.isoformat()
                                  if lead.posted_at_claimed else None),
        "job_links_found": lead.job_links,
        "is_job_announcement": lead.is_job_announcement,
        "caption_excerpt": lead.caption_excerpt[:500],
        "job_posted_at": None,
        "date_reliability": lead.date_reliability,
        "recorded_by": lead.recorded_by,
        "note": lead.note,
        "next_step": ("Verifikasi ke halaman karier atau board ATS perusahaan "
                      "sebelum ditampilkan sebagai lowongan."),
    }
