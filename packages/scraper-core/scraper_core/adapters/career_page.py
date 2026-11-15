"""Adapter halaman karier perusahaan langsung (direct / company career page).

Sumber: halaman karier perusahaan sendiri — bukan job board agregator.
Jalur utama: feed JSON publik dari ATS yang dipakai perusahaan
(Greenhouse, Lever, Ashby, Workable, SmartRecruiters, Workday, Recruitee).
Jalur fallback: halaman karier custom yang memakai JSON-LD JobPosting
(schema.org) di HTML-nya.

DISATUKAN koordinator Fase 1 (15 Nov 2026): memakai RawJob +
JobSourceAdapter bersama dari scraper_core.base; field
platform/platform_job_id/job_key/department/repost_hint/raw kini
ada di base RawJob. Tidak ada lagi definisi lokal.

Hanya stdlib Python (urllib, json, re, html, datetime) — tanpa httpx /
BeautifulSoup — supaya bisa jalan di lingkungan minimal dan mudah dites.

Aturan kepatutan (ARCHITECTURE.md §8):
  * Hanya endpoint publik tanpa login yang dibaca. Tidak ada bypass
    login / paywall / CAPTCHA. Endpoint yang butuh kunci akun perusahaan
    (mis. Lever Data API v1, Greenhouse Harvest, Workable SPI v3)
    TIDAK dipakai di sini.
  * User-Agent mengidentifikasi diri + kontak (ubah KONTAK di bawah
    sebelum dipakai produksi).
  * Jeda antar-request per host: lihat `POLITE_DELAY_SECONDS`.
  * Tidak menyimpan data pribadi apa pun. Yang disimpan hanya data
    lowongan publik (judul, lokasi, tanggal, URL, deskripsi).

Status verifikasi (15 Nov 2026, lihat docs/fase1-riset-direct.md):
  * Endpoint + field Greenhouse/Lever/Ashby/Workable TERVERIFIKASI dari
    dokumen resmi vendor. Workday/SmartRecruiters/Recruitee baru dari
    sumber sekunder (referensi ATS yang memverifikasi live) — perlu uji
    live sebelum dipakai produksi.
  * `posted_at` TIDAK sama dengan `first_seen_at`. Lihat docstring
    `parse_*` untuk apa arti tanggal tiap platform — Ashby `publishedAt`
    artinya "terakhir dipublikasikan", BUKAN pertama kali dibuka.

UJI LIVE 15 Nov 2026 (lihat docs/fase1-lanjutan-uji-live.md):
  * Greenhouse board "discord": 26 lowongan, `first_published` ADA di
    daftar untuk 26/26 — asumsi K-D1 ("hanya di endpoint satu job")
    ternyata TIDAK BERLAKU di data live; fallback satu job tetap ada
    untuk board yang tidak menyertakannya.
  * Lever board "spotify": 87 lowongan, `createdAt` (epoch ms) ADA di
    87/87 — K-D2 TERJAWAB: field itu nyata di respons live meski tidak
    ada di tabel README resmi.
  * Ashby board "ashby": 76 lowongan, `publishedAt` ADA; lowongan
    pertama terdaftar punya publishedAt 2024-03-04 (sudah >1,5 tahun)
    — bukti langsung K-D3: publishedAt = terakhir dipublikasikan,
    bukan tanggal buka; jangan tampilkan sebagai tanggal buka pasti.
  * Workable board "huggingface": 6 lowongan, `published_on` tanggal
    saja (YYYY-MM-DD), mis. 2026-05-29.
  * GoTo Indonesia BUKAN di Lever: `api.lever.co/v0/postings/goto`
    -> HTTP 404 — klaim MulaJob (K-D5) TERBANTAH. Board Lever milik
    Lever sendiri (slug "lever") mengembalikan 200 dengan 0 lowongan
    — board kosong TIDAK sama dengan "perusahaan tidak merekrut"
    (K-D4 ditegaskan lagi).
"""

from __future__ import annotations

import html
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from typing import Any, Callable, Optional

# ---------------------------------------------------------------------------
# Kontrak adapter + RawJob bersama (disatukan koordinator Fase 1):
# satu definisi di scraper_core/base.py dipakai semua adapter.
# `job_fingerprint` diimpor ulang di sini sebagai re-export supaya kode lama
# (`from scraper_core.adapters.career_page import job_fingerprint`) tetap
# jalan; definisi TUNGGAL-nya ada di scraper_core/base.py (K8).
from ..base import (  # noqa: F401
    JobSourceAdapter,
    RawJob,
    SourceBlockedError,
    SourceFetchError,
    job_fingerprint,
    user_agent,
)
from ..parsers import normalize_company

# ---------------------------------------------------------------------------
# Konfigurasi kesopanan
# ---------------------------------------------------------------------------

USER_AGENT = user_agent()  # jujur; kontak lewat env CEKLOKER_CONTACT
POLITE_DELAY_SECONDS = 2.0
REQUEST_TIMEOUT_SECONDS = 20

# ---------------------------------------------------------------------------
# Deteksi platform ATS dari URL
# ---------------------------------------------------------------------------

# Pola host -> platform. Urutan penting: pola paling spesifik dulu.
_PLATFORM_HOST_PATTERNS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"(?:^|\.)boards\.greenhouse\.io$"), "greenhouse"),
    (re.compile(r"(?:^|\.)job-boards\.greenhouse\.io$"), "greenhouse"),
    (re.compile(r"(?:^|\.)boards\.eu\.greenhouse\.io$"), "greenhouse"),
    (re.compile(r"(?:^|\.)jobs\.lever\.co$"), "lever"),
    (re.compile(r"(?:^|\.)jobs\.eu\.lever\.co$"), "lever"),
    (re.compile(r"(?:^|\.)jobs\.ashbyhq\.com$"), "ashby"),
    (re.compile(r"(?:^|\.)apply\.workable\.com$"), "workable"),
    (re.compile(r"(?:^|\.)\w+\.workable\.com$"), "workable"),
    (re.compile(r"(?:^|\.)jobs\.smartrecruiters\.com$"), "smartrecruiters"),
    (re.compile(r"\.myworkdayjobs\.com$"), "workday"),
    (re.compile(r"(?:^|\.)\w+\.recruitee\.com$"), "recruitee"),
    (re.compile(r"(?:^|\.)\w+\.jobs\.personio\.de$"), "personio"),
    (re.compile(r"(?:^|\.)\w+\.bamboohr\.com$"), "bamboohr"),
]

# Endpoint feed JSON publik per platform (tanpa login).
# Status: greenhouse/lever/ashby/workable = dokumen resmi vendor (15 Nov 2026).
# smartrecruiters/workday/recruitee/personio/bamboohr = sumber sekunder.
BOARD_API_URL: dict[str, str] = {
    "greenhouse": "https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true",
    "lever": "https://api.lever.co/v0/postings/{slug}?mode=json&limit=500",
    "ashby": "https://api.ashbyhq.com/posting-api/job-board/{slug}?includeCompensation=true",
    "workable": "https://apply.workable.com/api/v1/widget/accounts/{slug}?details=true",
    "smartrecruiters": "https://api.smartrecruiters.com/v1/companies/{slug}/postings?limit=100&offset=0",
    "recruitee": "https://{slug}.recruitee.com/api/offers/",
    "personio": "https://{slug}.jobs.personio.de/xml",
    "bamboohr": "https://{slug}.bamboohr.com/careers/list",
    # Workday: tidak ada pola slug yang bisa ditebak (butuh tenant+site+shard
    # dari URL board asli). Lihat detect_workday_board().
}

# Domain ATS yang dikenal — dipakai social_company.py untuk memilah link.
KNOWN_ATS_HOSTS = (
    "boards.greenhouse.io", "job-boards.greenhouse.io",
    "jobs.lever.co", "jobs.eu.lever.co",
    "jobs.ashbyhq.com", "apply.workable.com",
    "jobs.smartrecruiters.com", "myworkdayjobs.com",
    "recruitee.com", "jobs.personio.de", "bamboohr.com",
)


def detect_platform(url: str) -> Optional[str]:
    """Tebak platform ATS dari URL halaman karier / board.

    Mengembalikan nama platform (mis. ``"greenhouse"``) atau ``"custom"``
    bila host bukan ATS yang dikenal, atau None bila URL tidak valid.
    """
    try:
        host = urllib.parse.urlparse(url).netloc.lower().split(":")[0]
    except Exception:
        return None
    if not host:
        return None
    for pattern, platform in _PLATFORM_HOST_PATTERNS:
        if pattern.search(host):
            return platform
    return "custom"


def extract_slug(url: str, platform: Optional[str] = None) -> Optional[str]:
    """Ambil board slug / token dari URL board ATS.

    Contoh: ``boards.greenhouse.io/acme`` -> ``"acme"``,
    ``jobs.lever.co/acme`` -> ``"acme"``,
    ``apply.workable.com/acme`` -> ``"acme"``.
    Untuk Workday mengembalikan None (slug tidak bisa ditebak).
    """
    platform = platform or detect_platform(url)
    if not platform or platform in ("custom", "workday"):
        return None
    parsed = urllib.parse.urlparse(url)
    path = parsed.path.strip("/")
    if platform == "recruitee":
        # slug = subdomain: acme.recruitee.com
        return parsed.netloc.split(".")[0] or None
    if platform in ("personio", "bamboohr"):
        return parsed.netloc.split(".")[0] or None
    if not path:
        return None
    # Slug umumnya segmen pertama; segmen kedua dst. adalah id/detail job.
    first = path.split("/")[0]
    if first in ("embed", "job_board"):
        # boards.greenhouse.io/embed/job_board?for=<slug>
        query = urllib.parse.parse_qs(parsed.query)
        return query.get("for", [None])[0]
    return first or None


def detect_workday_board(url: str) -> Optional[dict[str, str]]:
    """Pecah URL board Workday jadi tenant/site/shard.

    Workday adalah SATU-SATUNYA platform di sini yang slug-nya tidak bisa
    ditebak dari nama perusahaan: butuh URL board asli yang ditemukan
    manusia, mis. ``https://intel.wd1.myworkdayjobs.com/External``.
    """
    parsed = urllib.parse.urlparse(url)
    host = parsed.netloc.lower()
    m = re.match(r"^([\w-]+)\.(wd\d+)\.myworkdayjobs\.com$", host)
    if not m:
        return None
    site = parsed.path.strip("/").split("/")[0] if parsed.path.strip("/") else None
    if not site:
        return None
    return {"tenant": m.group(1), "shard": m.group(2), "site": site}


def board_api_url(platform: str, slug: str) -> Optional[str]:
    """URL feed JSON publik untuk satu board ATS (tanpa login)."""
    template = BOARD_API_URL.get(platform)
    if template is None:
        return None
    return template.format(slug=slug)


# ---------------------------------------------------------------------------
# Util tanggal & teks
# ---------------------------------------------------------------------------

def parse_iso_date(value: Any) -> Optional[date]:
    """Parse tanggal ISO 8601 (dengan / tanpa jam & zona) jadi date."""
    if not value or not isinstance(value, str):
        return None
    text = value.strip()
    if not text:
        return None
    try:
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        return datetime.fromisoformat(text).date()
    except ValueError:
        pass
    try:
        return datetime.strptime(text[:10], "%Y-%m-%d").date()
    except ValueError:
        return None


def parse_epoch_ms(value: Any) -> Optional[date]:
    """Parse timestamp epoch milidetik (Lever `createdAt`) jadi date."""
    if value is None:
        return None
    try:
        ms = int(value)
    except (TypeError, ValueError):
        return None
    try:
        return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).date()
    except (OverflowError, OSError, ValueError):
        return None


def parse_relative_posted_on(text: str, today: Optional[date] = None) -> Optional[date]:
    """Parse tanggal relatif gaya Workday: 'Posted Yesterday',
    'Posted 20 Days Ago', 'Posted Today' -> date absolut.

    Peringatan: ini perkiraan dari teks relatif — simpan sebagai
    posted_at hanya bila tidak ada tanggal absolut, dan jangan pernah
    klaim presisi lebih dari ±1 hari.
    """
    if not isinstance(text, str):
        return None
    today = today or date.today()
    lowered = text.strip().lower()
    if "today" in lowered:
        return today
    if "yesterday" in lowered:
        return today - timedelta(days=1)
    m = re.search(r"(\d+)\s+days?\s+ago", lowered)
    if m:
        return today - timedelta(days=int(m.group(1)))
    m = re.search(r"(\d+)\s+hours?\s+ago", lowered)
    if m:
        return today
    return None


def strip_html_to_text(value: Optional[str]) -> str:
    """Bersihkan HTML jadi teks polos. Decode entity DUA kali.

    Greenhouse mengembalikan `content` yang di-encode DUA kali
    (terverifikasi dari dokumen resmi + referensi live): ``&amp;lt;p&amp;gt;``
    harus di-unescape dua kali sebelum jadi ``<p>``.
    """
    if not value:
        return ""
    text = html.unescape(html.unescape(value))
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n\n", text)
    return text.strip()


def _work_type_from_text(location: Optional[str], workplace: Optional[str]) -> Optional[str]:
    # Medan eksplisit (workplaceType ATS) lebih tepercaya daripada teks
    # lokasi: lokasi "Remote (Indonesia)" pada lowongan Hybrid akan
    # salah tertebak "remote" bila lokasi dibaca duluan.
    if workplace:
        lowered_wp = workplace.lower()
        if "remote" in lowered_wp:
            return "remote"
        if "hybrid" in lowered_wp:
            return "hybrid"
        if "on-site" in lowered_wp or "onsite" in lowered_wp or "in-person" in lowered_wp:
            return "onsite"
    text = (location or "").lower()
    if "remote" in text:
        return "remote"
    if "hybrid" in text:
        return "hybrid"
    if "on-site" in text or "onsite" in text or "in-person" in text:
        return "onsite"
    return None


# ---------------------------------------------------------------------------
# Parser per platform: JSON board -> list[RawJob]
# (murni, tanpa I/O — mudah dites dengan fixture)
# ---------------------------------------------------------------------------

def parse_greenhouse_board(payload: dict, slug: str,
                           board_url: Optional[str] = None) -> list[RawJob]:
    """Parse respons Greenhouse Job Board API.

    Dokumen resmi (developers.greenhouse.io/job-board.html, dicek 15 Nov 2026):
    GET boards-api.greenhouse.io/v1/boards/{token}/jobs, tanpa auth.
    `?content=true` menambah deskripsi + departemen + kantor.

    JEBAKAN DOKUMENTASI (K-D1): contoh respons LIST di dokumen resmi
    TIDAK memuat `first_published` — field itu hanya muncul di contoh
    endpoint SATU job (`GET .../jobs/{job_id}`). Jadi `posted_at` dari
    daftar bisa None; `fetch_job()` memanggil endpoint satu job untuk
    mengambil `first_published`. `updated_at` BUKAN tanggal buka.
    KOREKSI UJI LIVE 15 Nov 2026 (board "discord", 26 lowongan):
    `first_published` ternyata ADA di daftar untuk 26/26 lowongan
    (contoh: "2026-11-13T15:33:44-05:00"). Contoh di dokumen resmi
    tidak lengkap — data live lebih lengkap. Fallback endpoint satu
    job tetap dipertahankan untuk board yang tidak menyertakannya.
    """
    jobs: list[RawJob] = []
    for item in payload.get("jobs", []) or []:
        url = item.get("absolute_url") or (
            f"https://boards.greenhouse.io/{slug}/jobs/{item.get('id')}"
            if item.get("id") else (board_url or "")
        )
        location = (item.get("location") or {}).get("name")
        departments = [d.get("name") for d in item.get("departments", []) or [] if d.get("name")]
        job = RawJob(
            source_id="greenhouse",
            source_url=url,
            title=(item.get("title") or "").strip(),
            company_raw=(item.get("company_name") or ""),
            company_norm=normalize_company(item.get("company_name")) if item.get("company_name") else "",
            location=location,
            work_type=_work_type_from_text(location, None),
            # first_published biasanya TIDAK ada di list; diisi fetch_job().
            posted_at=parse_iso_date(item.get("first_published")),
            description_text=strip_html_to_text(item.get("content")) or None,
            platform="greenhouse",
            platform_job_id=str(item.get("id")) if item.get("id") is not None else None,
            department=departments[0] if departments else None,
            raw=item,
        )
        job.job_key = f"greenhouse:{slug}:{job.platform_job_id}"
        jobs.append(job)
    return jobs


def parse_greenhouse_single_job(payload: dict, slug: str) -> RawJob:
    """Parse SATU job Greenhouse (`GET .../jobs/{job_id}`).

    Di sinilah `first_published` (tanggal pertama dipublikasikan) dan
    `pay_transparency` (`pay_input_ranges`, butuh ?pay_transparency=true)
    tersedia menurut dokumen resmi.
    """
    url = payload.get("absolute_url") or f"https://boards.greenhouse.io/{slug}/jobs/{payload.get('id')}"
    location = (payload.get("location") or {}).get("name")
    salary_min = salary_max = None
    currency = None
    ranges = payload.get("pay_input_ranges") or []
    if ranges:
        first = ranges[0]
        currency = first.get("currency_type")
        # min/max dalam sen (cents).
        if first.get("min_cents") is not None:
            salary_min = int(first["min_cents"]) // 100
        if first.get("max_cents") is not None:
            salary_max = int(first["max_cents"]) // 100
    job = RawJob(
        source_id="greenhouse",
        source_url=url,
        title=(payload.get("title") or "").strip(),
        company_raw=(payload.get("company_name") or ""),
        company_norm=normalize_company(payload.get("company_name")) if payload.get("company_name") else "",
        location=location,
        work_type=_work_type_from_text(location, None),
        salary_min=salary_min,
        salary_max=salary_max,
        salary_currency=currency,
        posted_at=parse_iso_date(payload.get("first_published")),
        description_text=strip_html_to_text(payload.get("content")) or None,
        platform="greenhouse",
        platform_job_id=str(payload.get("id")) if payload.get("id") is not None else None,
        raw=payload,
    )
    job.job_key = f"greenhouse:{slug}:{job.platform_job_id}"
    return job


def parse_lever_board(payload: Any, slug: str) -> list[RawJob]:
    """Parse respons Lever Postings API.

    Dokumen resmi (github.com/lever/postings-api, dicek 15 Nov 2026):
    GET api.lever.co/v0/postings/{site}?mode=json, tanpa auth.
    "All job postings in the `published` state are publicly viewable.
    These jobs may be scraped by third parties." — izin tertulis Lever.

    JEBAKAN (K-D2): tabel field di README resmi TIDAK mencantumkan
    `createdAt`, tapi respons live memuatnya (epoch milidetik). Kami
    membaca `createdAt` bila ada; bila tidak ada, posted_at = None
    (jangan ditebak). EU board: host api.eu.lever.co.
    TERKONFIRMASI LIVE 15 Nov 2026 (board "spotify", 87 lowongan):
    `createdAt` ada di 87/87 (contoh: 1792767640768 -> 2026-10-23).
    """
    jobs: list[RawJob] = []
    items = payload if isinstance(payload, list) else (payload or {}).get("postings", [])
    for item in items or []:
        cats = item.get("categories") or {}
        location = cats.get("location")
        salary = item.get("salaryRange") or {}
        job = RawJob(
            source_id="lever",
            source_url=item.get("hostedUrl") or item.get("applyUrl") or "",
            title=(item.get("text") or "").strip(),
            company_raw="",
            company_norm="",  # Lever tidak mengembalikan nama perusahaan.
            location=location,
            work_type=_work_type_from_text(location, item.get("workplaceType")),
            salary_min=salary.get("min"),
            salary_max=salary.get("max"),
            salary_currency=salary.get("currency"),
            posted_at=parse_epoch_ms(item.get("createdAt")),
            description_text=(item.get("descriptionPlain")
                              or strip_html_to_text(item.get("description"))) or None,
            platform="lever",
            platform_job_id=str(item.get("id")) if item.get("id") is not None else None,
            department=cats.get("department") or cats.get("team"),
            raw=item,
        )
        job.job_key = f"lever:{slug}:{job.platform_job_id}"
        jobs.append(job)
    return jobs


def parse_ashby_board(payload: dict, slug: str) -> list[RawJob]:
    """Parse respons Ashby Job Postings API.

    Dokumen resmi (developers.ashbyhq.com/docs/public-job-posting-api,
    dicek 15 Nov 2026): GET api.ashbyhq.com/posting-api/job-board/{name},
    tanpa auth; `?includeCompensation=true` menambah gaji.

    JEBAKAN (K-D3): dokumen resmi mendefinisikan `publishedAt` sebagai
    "ISO DateTime when the job was LAST published" — jadi tanggal ini
    BERUBAH bila lowongan di-republish. BUKAN tanggal pertama dibuka.
    CekLoker menyimpan `posted_at` = publishedAt + `first_seen_at`
    sendiri, dan menandai repost bila id sama tapi publishedAt meloncat.
    BUKTI LIVE 15 Nov 2026 (board "ashby", 76 lowongan): lowongan
    pertama terdaftar punya publishedAt 2024-03-04 — sudah >1,5 tahun
    tapi masih terdaftar. `publishedAt` lama + masih terdaftar = ciri
    lowongan evergreen/stale; JANGAN tampilkan sebagai "baru dibuka".
    """
    jobs: list[RawJob] = []
    for item in payload.get("jobs", []) or []:
        locations = [item.get("location")] + [
            s.get("location") for s in item.get("secondaryLocations", []) or []
        ]
        locations = [loc for loc in locations if loc]
        salary_min = salary_max = None
        currency = None
        comp = item.get("compensation") or {}
        for tier in comp.get("compensationTiers", []) or []:
            for c in tier.get("components", []) or []:
                if c.get("compensationType") == "Salary":
                    salary_min = c.get("minValue")
                    salary_max = c.get("maxValue")
                    currency = c.get("currencyCode")
                    break
        job = RawJob(
            source_id="ashby",
            source_url=item.get("jobUrl") or item.get("applyUrl") or "",
            title=(item.get("title") or "").strip(),
            company_raw="",
            company_norm="",
            location=", ".join(locations) if locations else None,
            work_type=_work_type_from_text(
                ", ".join(locations), item.get("workplaceType")),
            salary_min=salary_min,
            salary_max=salary_max,
            salary_currency=currency,
            posted_at=parse_iso_date(item.get("publishedAt")),
            description_text=(item.get("descriptionPlain")
                              or strip_html_to_text(item.get("descriptionHtml"))) or None,
            platform="ashby",
            platform_job_id=str(item.get("id")) if item.get("id") is not None else None,
            department=item.get("department"),
            raw=item,
        )
        job.job_key = f"ashby:{slug}:{job.platform_job_id}"
        jobs.append(job)
    return jobs


def parse_workable_board(payload: dict, slug: str) -> list[RawJob]:
    """Parse respons Workable widget API.

    Dokumen resmi Workable (help.workable.com, artikel "Using the Workable
    API to create a careers page", dicek 15 Nov 2026): endpoint publik
    `GET https://www.workable.com/api/accounts/{subdomain}?details=true`
    (tanpa kunci) — server mengembalikan 302 ke widget endpoint
    `apply.workable.com/api/v1/widget/accounts/{slug}`. robots.txt
    apply.workable.com mengizinkan semua (`Disallow:` kosong).
    `published_on` adalah tanggal (YYYY-MM-DD). Tidak ada gaji terstruktur.
    TERKONFIRMASI LIVE 15 Nov 2026 (board "huggingface", 6 lowongan):
    `published_on` ada, mis. "2026-05-29".
    """
    jobs: list[RawJob] = []
    for item in payload.get("jobs", []) or []:
        parts = [item.get("city"), item.get("state"), item.get("country")]
        location = ", ".join(p for p in parts if p) or None
        job = RawJob(
            source_id="workable",
            source_url=item.get("application_url") or "",
            title=(item.get("title") or "").strip(),
            company_raw=(payload.get("name") or ""),
            company_norm=normalize_company(payload.get("name")) if payload.get("name") else "",
            location=location,
            work_type="remote" if item.get("telecommuting") else _work_type_from_text(location, None),
            posted_at=parse_iso_date(item.get("published_on")),
            description_text=strip_html_to_text(item.get("description")) or None,
            platform="workable",
            platform_job_id=str(item.get("shortcode")) if item.get("shortcode") else None,
            department=item.get("department"),
            raw=item,
        )
        job.job_key = f"workable:{slug}:{job.platform_job_id}"
        jobs.append(job)
    return jobs


def parse_smartrecruiters_board(payload: dict, slug: str) -> list[RawJob]:
    """Parse respons SmartRecruiters (sumber sekunder — perlu uji live).

    GET api.smartrecruiters.com/v1/companies/{id}/postings?limit=&offset=.
    `releasedDate` = tanggal rilis (ISO). Daftar TIDAK berisi deskripsi
    (butuh 1 request per job). Board kosong ambigu: 200 + totalFound 0
    bisa berarti "bukan pelanggan" ATAU "0 lowongan".
    """
    jobs: list[RawJob] = []
    for item in payload.get("content", []) or []:
        loc = item.get("location") or {}
        job = RawJob(
            source_id="smartrecruiters",
            source_url=(item.get("applyUrl") or item.get("jobAd", {}).get("url") or ""),
            title=(item.get("name") or "").strip(),
            company_raw=((item.get("company") or {}).get("name") or ""),
            company_norm=normalize_company((item.get("company") or {}).get("name")) if (item.get("company") or {}).get("name") else "",
            location=loc.get("fullLocation") or loc.get("city"),
            work_type=("remote" if loc.get("remote") else
                       "hybrid" if loc.get("hybrid") else None),
            posted_at=parse_iso_date(item.get("releasedDate")),
            description_text=None,  # butuh detail call per job
            platform="smartrecruiters",
            platform_job_id=str(item.get("id")) if item.get("id") is not None else None,
            department=(item.get("department") or {}).get("label"),
            raw=item,
        )
        job.job_key = f"smartrecruiters:{slug}:{job.platform_job_id}"
        jobs.append(job)
    return jobs


def parse_recruitee_board(payload: dict, slug: str) -> list[RawJob]:
    """Parse respons Recruitee (sumber sekunder — perlu uji live).

    GET https://{slug}.recruitee.com/api/offers/ (trailing slash penting).
    `published_at` ISO. Lokasi: percaya array `locations`, bukan field
    datar `city` (keduanya kadang tidak cocok).
    """
    jobs: list[RawJob] = []
    for item in payload.get("offers", []) or []:
        locs = [loc.get("name") for loc in item.get("locations", []) or [] if loc.get("name")]
        location = ", ".join(locs) if locs else item.get("city")
        job = RawJob(
            source_id="recruitee",
            source_url=item.get("careers_url") or "",
            title=(item.get("title") or "").strip(),
            company_raw="",
            company_norm="",
            location=location,
            work_type="remote" if item.get("remote") else None,
            posted_at=parse_iso_date(item.get("published_at")),
            description_text=strip_html_to_text(
                item.get("requirements") or item.get("description")) or None,
            platform="recruitee",
            platform_job_id=str(item.get("id")) if item.get("id") is not None else None,
            department=item.get("department"),
            raw=item,
        )
        job.job_key = f"recruitee:{slug}:{job.platform_job_id}"
        jobs.append(job)
    return jobs


_PARSERS: dict[str, Callable] = {
    "greenhouse": parse_greenhouse_board,
    "lever": parse_lever_board,
    "ashby": parse_ashby_board,
    "workable": parse_workable_board,
    "smartrecruiters": parse_smartrecruiters_board,
    "recruitee": parse_recruitee_board,
}


def parse_board(platform: str, payload: Any, slug: str) -> list[RawJob]:
    """Dispatch parser board berdasarkan platform. Raise ValueError bila
    platform tidak dikenal / tidak punya parser JSON."""
    parser = _PARSERS.get(platform)
    if parser is None:
        raise ValueError(f"tidak ada parser board JSON untuk platform: {platform}")
    if platform == "lever":
        return parser(payload, slug)
    return parser(payload, slug)


# ---------------------------------------------------------------------------
# Halaman karier custom: JSON-LD JobPosting (schema.org)
# ---------------------------------------------------------------------------

_JSON_LD_RE = re.compile(
    r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
    re.IGNORECASE | re.DOTALL,
)


def extract_json_ld_job_postings(html_text: str) -> list[dict]:
    """Ambil semua blok JSON-LD bertipe JobPosting dari HTML halaman.

    Banyak halaman karier custom (termasuk yang dibuat dengan Next.js /
    WordPress) menanam schema.org JobPosting untuk SEO — ini jalur paling
    sopan membaca halaman custom: 1 request, data terstruktur, tanpa
    menebak-nebak selector CSS yang rapuh.
    """
    postings: list[dict] = []
    for block in _JSON_LD_RE.findall(html_text or ""):
        try:
            data = json.loads(block.strip())
        except (json.JSONDecodeError, ValueError):
            continue
        candidates = data if isinstance(data, list) else [data]
        # @graph: [...]
        if isinstance(data, dict) and isinstance(data.get("@graph"), list):
            candidates = data["@graph"]
        for item in candidates:
            if isinstance(item, dict) and item.get("@type") == "JobPosting":
                postings.append(item)
    return postings


def _json_ld_location(item: dict) -> Optional[str]:
    loc = item.get("jobLocation")
    if isinstance(loc, dict):
        addr = loc.get("address") or {}
        if isinstance(addr, dict):
            parts = [addr.get("addressLocality"), addr.get("addressRegion"),
                     addr.get("addressCountry")]
            return ", ".join(p for p in parts if p) or loc.get("name")
        return loc.get("name")
    if isinstance(loc, list) and loc:
        return _json_ld_location({"jobLocation": loc[0]})
    if isinstance(loc, str):
        return loc
    return None


def parse_json_ld_job_posting(item: dict, page_url: str,
                              source_id: str = "career-custom") -> RawJob:
    """Satu blok JSON-LD JobPosting -> RawJob.

    `datePosted` = tanggal yang diklaim halaman. `validThrough` (bila ada)
    adalah tanggal kedaluwarsa yang diklaim — BUKAN bukti lowongan masih
    buka; status aktif tetap ditentukan `check_active()` (halaman masih
    ada + masih berisi JobPosting).
    """
    org = item.get("hiringOrganization") or {}
    company = org.get("name") if isinstance(org, dict) else None
    salary = item.get("baseSalary") or {}
    value = salary.get("value") or {} if isinstance(salary, dict) else {}
    return RawJob(
        source_id=source_id,
        source_url=page_url,
        title=(item.get("title") or "").strip(),
        company_raw=(company or ""),
        company_norm=normalize_company(company) if company else "",
        location=_json_ld_location(item),
        work_type=_work_type_from_text(
            _json_ld_location(item), item.get("employmentType")),
        salary_min=value.get("minValue"),
        salary_max=value.get("maxValue"),
        salary_currency=(value.get("currency") if isinstance(value, dict) else None)
        or (salary.get("currency") if isinstance(salary, dict) else None),
        posted_at=parse_iso_date(item.get("datePosted")),
        description_text=strip_html_to_text(item.get("description")) or None,
        platform="custom",
        platform_job_id=None,
        department=None,
        raw=item,
    )


# ---------------------------------------------------------------------------
# HTTP (stdlib) — fetcher bisa diganti di test
# ---------------------------------------------------------------------------

Fetcher = Callable[[str], tuple[int, bytes, str]]  # (status, body, final_url)


def default_fetcher(url: str) -> tuple[int, bytes, str]:
    """GET sopan dengan User-Agent pengenal. Kembalikan (status, body, url_akhir).

    TIDAK mengikuti redirect ke domain lain secara diam-diam? — urllib
    mengikuti redirect HTTP standar; redirect Personio/BambooHR (307/302
    ke marketing site) dideteksi pemanggil dari status + final_url.
    """
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT_SECONDS) as resp:
            return resp.status, resp.read(), resp.geturl()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read() if exc.fp else b"", url
    except (urllib.error.URLError, TimeoutError, OSError):
        return 0, b"", url


# ---------------------------------------------------------------------------
# Adapter utama
# ---------------------------------------------------------------------------

class CareerPageAdapter(JobSourceAdapter):
    """Adapter satu perusahaan lewat halaman karier / board ATS-nya.

    Cara pakai:
        adapter = CareerPageAdapter(
            company_name="Contoh Corp",
            board_url="https://boards.greenhouse.io/contoh",
        )
        urls = adapter.discover()          # URL lowongan aktif
        job = adapter.fetch_job(urls[0])   # detail + posted_at
        adapter.check_active(urls[0])      # masih buka?

    Deteksi baru vs repost (lihat docs/fase1-riset-direct.md § Hasil Grill):
    adapter TIDAK memutuskan "baru" sendirian. Yang adapter berikan:
      * `job_key` stabil per (platform, slug, id ATS),
      * `posted_at` klaim sumber,
      * fingerprint judul+perusahaan+lokasi (lihat `job_fingerprint`).
    Scheduler + normalizer yang memutuskan: id ATS baru + fingerprint
    lama = repost; id baru + fingerprint baru = lowongan baru.
    """

    def __init__(self, company_name: str, board_url: str,
                 platform: Optional[str] = None,
                 slug: Optional[str] = None,
                 fetcher: Optional[Fetcher] = None,
                 polite_delay: float = POLITE_DELAY_SECONDS):
        self.company_name = company_name
        self.board_url = board_url.rstrip("/")
        self.platform = platform or detect_platform(board_url) or "custom"
        self.slug = slug or extract_slug(board_url, self.platform)
        self._fetcher: Fetcher = fetcher or default_fetcher
        self._polite_delay = polite_delay
        self._board_cache: Optional[list[RawJob]] = None
        self.source_id = f"career-{self.platform}"

    # -- util internal -----------------------------------------------------
    def _get_json(self, url: str) -> tuple[int, Any]:
        time.sleep(self._polite_delay)
        status, body, _ = self._fetcher(url)
        if status != 200 or not body:
            return status, None
        try:
            return status, json.loads(body.decode("utf-8", "replace"))
        except (json.JSONDecodeError, ValueError):
            return status, None

    def _fetch_board(self) -> list[RawJob]:
        if self._board_cache is not None:
            return self._board_cache
        jobs: list[RawJob] = []
        if self.platform == "workday":
            # Butuh POST JSON ke endpoint tenant — belum diimplementasi
            # sampai ada board Workday Indonesia nyata untuk diuji.
            # Sengaja gagal eksplisit, bukan diam-diam kosong.
            raise NotImplementedError(
                "Workday butuh tenant/site/shard dari URL board asli; "
                "parser POST belum diaktifkan (perlu uji live).")
        if self.platform == "custom":
            status, body, _ = self._fetcher(self.board_url)
            if status != 200:
                self._board_cache = []
                return []
            text = body.decode("utf-8", "replace")
            for item in extract_json_ld_job_postings(text):
                jobs.append(parse_json_ld_job_posting(item, self.board_url))
            self._board_cache = jobs
            return jobs
        api_url = board_api_url(self.platform, self.slug or "")
        if api_url is None:
            raise ValueError(f"platform {self.platform} tidak punya feed JSON publik")
        status, payload = self._get_json(api_url)
        if status == 404 or payload is None:
            self._board_cache = []
            return []
        jobs = parse_board(self.platform, payload, self.slug or "")
        # Greenhouse: lengkapi first_published via endpoint satu job
        # (list resmi tidak menjamin field itu ada) — 1 request per job,
        # hanya bila posted_at masih kosong.
        if self.platform == "greenhouse":
            for job in jobs:
                if job.posted_at is None and job.platform_job_id:
                    single_url = (
                        f"https://boards-api.greenhouse.io/v1/boards/"
                        f"{self.slug}/jobs/{job.platform_job_id}"
                    )
                    s2, p2 = self._get_json(single_url)
                    if s2 == 200 and isinstance(p2, dict):
                        detailed = parse_greenhouse_single_job(p2, self.slug or "")
                        job.posted_at = detailed.posted_at
                        job.salary_min = detailed.salary_min
                        job.salary_max = detailed.salary_max
                        job.salary_currency = detailed.salary_currency
        self._board_cache = jobs
        return jobs

    # -- kontrak JobSourceAdapter -------------------------------------------
    def discover(self, keywords: str = "", location: str = "", max_pages: int = 1) -> list[str]:
        """URL lowongan yang ada di board saat ini (= masih dipublikasikan)."""
        return [job.source_url for job in self._fetch_board() if job.source_url]

    def fetch_job(self, url: str) -> RawJob:
        """Detail satu lowongan. Untuk board ATS: dari cache board.
        Untuk halaman custom: baca ulang halaman + JSON-LD-nya."""
        if self.platform == "custom":
            status, body, _ = self._fetcher(url)
            if status != 200:
                raise ValueError(f"halaman lowongan tidak bisa dibaca ({status}): {url}")
            postings = extract_json_ld_job_postings(body.decode("utf-8", "replace"))
            if not postings:
                raise ValueError(f"tidak ada JSON-LD JobPosting di: {url}")
            return parse_json_ld_job_posting(postings[0], url)
        for job in self._fetch_board():
            if job.source_url.rstrip("/") == url.rstrip("/"):
                return job
        raise ValueError(f"lowongan tidak ditemukan di board {self.platform}: {url}")

    def check_active(self, url: str) -> bool:
        """Masih buka? = masih ada di board (ATS) / halaman masih 200 dan
        masih berisi JobPosting (custom) pada kunjungan ulang.

        Dua kunjungan berturut-turut False -> scheduler menandai `closed`
        (aturan di ARCHITECTURE.md §3). Kegagalan TEKNIS (board tidak
        bisa dibaca / halaman tidak bisa diparse) BUKAN bukti tutup:
        di sini dilempar SourceFetchError supaya worker menandai
        `unknown`, bukan `closed` (amandemen koordinator Fase 1-lanjutan;
        lihat ADR-0002). Hanya 404 / lowongan benar-benar tidak ada di
        board yang berarti False."""
        if self.platform == "custom":
            try:
                self.fetch_job(url)
                return True
            except ValueError as exc:
                msg = str(exc)
                if "tidak bisa dibaca (404)" in msg:
                    return False
                if "tidak bisa dibaca" in msg or "tidak ada JSON-LD" in msg:
                    raise SourceFetchError(
                        f"check_active gagal teknis: {exc}"
                    ) from exc
                return False
        self._board_cache = None  # paksa baca ulang, jangan pakai cache
        try:
            return url.rstrip("/") in {u.rstrip("/") for u in self.discover()}
        except (SourceFetchError, SourceBlockedError):
            raise
        except (NotImplementedError, ValueError) as exc:
            raise SourceFetchError(
                f"check_active gagal teknis (board tidak bisa dibaca): {exc}"
            ) from exc
