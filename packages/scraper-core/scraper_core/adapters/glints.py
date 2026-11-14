"""Adapter Glints (glints.com / glints.id) — status: BANGUN.

Jalur akses (urut paling resmi -> paling rapuh), diverifikasi 15 Nov 2026:
1. **Sitemap** — `https://glints.com/sitemap_index.xml` dideklarasikan di
   `https://glints.com/robots.txt` (dibaca langsung 15 Nov 2026).
   `discover()` memakai ini untuk daftar URL lowongan.
2. **Halaman detail publik** — pola URL terverifikasi dari hasil pencarian:
   `https://glints.com/id/en/opportunities/jobs/<slug>/<uuid>`
   (mis. `.../staff-programmer/ad093d00-3e7d-4f25-a56e-be88fda4632d`).
   Halaman ini TIDAK ada di daftar Disallow robots.txt Glints (yang
   dilarang hanya `.../jobs/recommended$`, `.../jobs/bookmarked$`,
   `.../jobs/explore?*`, `/settings`, `/oauth2`, `/user/`, dsb).
3. **JSON-LD** — data lowongan diharapkan tersemat sebagai
   `application/ld+json` tipe `JobPosting` di halaman detail
   (pola standar situs lowongan; pola ini **ASUMSI, perlu uji live** —
   fetch teks browser 15 Nov 2026 tidak menampilkan blok JSON-LD-nya,
   jadi adapter memakai fallback parsing HTML bila JSON-LD tak ada).

Yang SENGAJA TIDAK dipakai:
- GraphQL `glints.com/api/graphql` — tidak terdokumentasi, hasil
  reverse-engineering (PR career-ops-hq/career-ops #1086, Jun 2026).
  Skema bisa berubah tanpa pemberitahuan; "bisa diakses tanpa auth"
  BUKAN berarti "diizinkan". Lihat K-JB2.
- Halaman explore ber-query (`/opportunities/jobs/explore?*`) —
  DILARANG robots.txt.

ToS Glints: **TIDAK TERVERIFIKASI** 15 Nov 2026 (pencarian tidak
mengembalikan teks ToS glints.com; lihat K-JB6). Adapter ini jalan
dengan asumsi pemakaian sopan (1 pengguna, delay 3 dtk, robots
dipatuhi). Giga perlu membaca ToS Glints sebelum rilis publik.

Penanda tutup (terverifikasi dari halaman contoh 15 Nov 2026):
halaman lowongan yang tutup menampilkan teks "This job was closed".
"""

from __future__ import annotations

import json
import re
from datetime import date
from html.parser import HTMLParser
from typing import Optional

from ..base import JobSourceAdapter, RawJob, SourceFetchError
from ..parsers import normalize_company, normalize_location, parse_posted_at, parse_salary

SITEMAP_INDEX = "https://glints.com/sitemap_index.xml"
JOB_URL_RE = re.compile(
    r"https://glints\.com/(?:id/)?(?:en/)?opportunities/jobs/"
    r"[a-z0-9-]+/[0-9a-f-]{36}", re.IGNORECASE
)
CLOSED_MARKERS = (
    "this job was closed",
    "lowongan ini sudah ditutup",
    "pekerjaan ini sudah ditutup",
)


# ---------------------------------------------------------------------------
# Parser HTML (stdlib): ambil JSON-LD + fallback teks
# ---------------------------------------------------------------------------


class _GlintsPageParser(HTMLParser):
    """Kumpulkan: blok JSON-LD, <title>, <h1>, dan seluruh teks halaman
    (untuk penanda tutup + fallback "Posted X ago" / gaji)."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.json_ld: list[dict] = []
        self._in_ld_json = False
        self._ld_buf: list[str] = []
        self._in_title = False
        self._in_h1 = False
        self.title = ""
        self.h1 = ""
        self.text_parts: list[str] = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "script" and attrs.get("type") == "application/ld+json":
            self._in_ld_json = True
            self._ld_buf = []
        elif tag == "title":
            self._in_title = True
        elif tag == "h1":
            self._in_h1 = True

    def handle_endtag(self, tag):
        if tag == "script" and self._in_ld_json:
            self._in_ld_json = False
            try:
                data = json.loads("".join(self._ld_buf))
            except (json.JSONDecodeError, ValueError):
                return
            items = data if isinstance(data, list) else [data]
            for item in items:
                if isinstance(item, dict):
                    self.json_ld.append(item)
        elif tag == "title":
            self._in_title = False
        elif tag == "h1":
            self._in_h1 = False

    def handle_data(self, data):
        if self._in_ld_json:
            self._ld_buf.append(data)
        elif self._in_title:
            self.title += data
        elif self._in_h1:
            self.h1 += data
        self.text_parts.append(data)

    @property
    def text(self) -> str:
        return " ".join(p for p in self.text_parts if p.strip())


def parse_sitemap(xml_text: str) -> list[str]:
    """Ambil URL lowongan dari sitemap (index maupun sitemap biasa).

    Hanya URL yang cocok pola `/opportunities/jobs/<slug>/<uuid>` yang
    dikembalikan — URL perusahaan/blog disaring keluar.
    """
    urls = re.findall(r"<loc>\s*(https?://[^<\s]+)\s*</loc>", xml_text)
    return [u for u in urls if JOB_URL_RE.match(u)]


def _jobposting_from_ld_json(blocks: list[dict]) -> Optional[dict]:
    for b in blocks:
        if b.get("@type") == "JobPosting":
            return b
        graph = b.get("@graph")
        if isinstance(graph, list):
            for item in graph:
                if isinstance(item, dict) and item.get("@type") == "JobPosting":
                    return item
    return None


def parse_glints_job(html: str, url: str, ref: Optional[date] = None) -> RawJob:
    """Parse halaman detail Glints (HTML apa adanya) -> RawJob.

    Prioritas field: JSON-LD JobPosting dulu, lalu teks halaman.
    Fungsi ini PURE — tidak ada HTTP — jadi bisa diuji dari fixture.
    """
    parser = _GlintsPageParser()
    parser.feed(html)
    teks = parser.text
    teks_rendah = teks.lower()

    is_active = not any(m in teks_rendah for m in CLOSED_MARKERS)

    job = _jobposting_from_ld_json(parser.json_ld)
    title = ""
    company = ""
    location = ""
    salary_min = salary_max = None
    salary_text = ""
    posted_at = None
    posted_certain = True
    posted_raw = ""
    description = ""

    if job:
        title = str(job.get("title") or "")
        org = job.get("hiringOrganization") or {}
        if isinstance(org, dict):
            company = str(org.get("name") or "")
        loc = job.get("jobLocation") or {}
        if isinstance(loc, dict):
            addr = loc.get("address") or {}
            if isinstance(addr, dict):
                location = str(
                    addr.get("addressLocality") or addr.get("addressRegion") or ""
                )
        gaji = job.get("baseSalary") or {}
        if isinstance(gaji, dict):
            nilai = gaji.get("value") or {}
            if isinstance(nilai, dict):
                try:
                    salary_min = int(float(nilai.get("minValue"))) \
                        if nilai.get("minValue") is not None else None
                    salary_max = int(float(nilai.get("maxValue"))) \
                        if nilai.get("maxValue") is not None else None
                except (TypeError, ValueError):
                    salary_min = salary_max = None
        date_posted = str(job.get("datePosted") or "")
        if date_posted:
            posted_raw = date_posted
            posted_at, posted_certain = parse_posted_at(date_posted, ref)
        description = str(job.get("description") or "")

    if not title:
        # Fallback: <h1>, lalu <title> ("Judul Jobs at Perusahaan | Glints")
        title = parser.h1.strip() or parser.title.split(" Jobs at ")[0].strip()
    if not company:
        m = re.search(r"Jobs at\s+(.+?)\s*(?:,|\||$)", parser.title)
        if m:
            company = m.group(1).strip()
    if not salary_text:
        m = re.search(
            r"(?:IDR|Rp)\s?[\d\.,]+\s*(?:-|–|—|sampai|to)\s*"
            r"(?:IDR|Rp)?\s?[\d\.,]+(?:\s*/\s*(?:Month|Bulan))?"
            r"|(?:IDR|Rp)\s?[\d\.,]+(?:\s*(?:jt|juta))?",
            teks, re.IGNORECASE,
        )
        if m:
            salary_text = m.group(0)
            salary_min, salary_max, _ = parse_salary(salary_text)
    if not posted_at:
        m = re.search(
            r"Posted\s+([^.]{1,40}?ago)|"
            r"Diposting\s+([^.]{1,40})",
            teks, re.IGNORECASE,
        )
        if m:
            posted_raw = (m.group(1) or m.group(2) or "").strip()
            posted_at, posted_certain = parse_posted_at(posted_raw, ref)
    if not description:
        description = teks[:2000]

    if not title or not company:
        raise SourceFetchError(
            f"Halaman Glints {url} tidak bisa diparse (judul/perusahaan "
            "tidak ditemukan — kemungkinan layout berubah atau halaman "
            "bukan halaman lowongan)."
        )

    return RawJob(
        source_id="glints",
        source_url=url,
        title=title.strip(),
        company_raw=company.strip(),
        company_norm=normalize_company(company),
        location=normalize_location(location),
        salary_min=salary_min,
        salary_max=salary_max,
        salary_currency="IDR",
        salary_text=salary_text,
        posted_at=posted_at,
        posted_at_certain=posted_certain,
        posted_raw=posted_raw,
        description_text=description.strip(),
        is_active=is_active,
    )


# ---------------------------------------------------------------------------
# Adapter
# ---------------------------------------------------------------------------


class GlintsAdapter(JobSourceAdapter):
    source_id = "glints"
    base_url = "https://glints.com"
    enabled = True
    polite_delay_s = 3.0
    robots_disallows = (
        "*/opportunities/jobs/recommended$",
        "*/opportunities/jobs/bookmarked$",
        "*/opportunities/jobs/explore?*",
        "*/settings", "*/oauth2", "*/user/",
    )

    def discover(self, keywords: str = "", location: str = "",
                 max_pages: int = 1) -> list[str]:
        """Daftar URL lowongan via sitemap index.

        Keterbatasan jujur (ASUMSI, perlu uji live): isi
        `sitemap_index.xml` belum diverifikasi berisi sitemap lowongan
        (robots.txt hanya mendeklarasikan keberadaannya). `keywords` /
        `location` di v1 HANYA dipakai untuk menyaring hasil sitemap
        berdasarkan slug URL — bukan query ke server. Kalau sitemap
        ternyata tidak memuat lowongan, discover harus diganti ke
        halaman list publik (bukan explore ber-query).
        """
        status, xml = self._get(SITEMAP_INDEX)
        if status != 200:
            raise SourceFetchError(f"Sitemap Glints gagal (HTTP {status})")
        urls = parse_sitemap(xml)
        if keywords:
            kata = keywords.lower().replace(" ", "-")
            urls = [u for u in urls if kata in u.lower()]
        return urls

    def fetch_job(self, url: str) -> RawJob:
        status, html = self._get(url)
        if status == 404:
            raise SourceFetchError(f"Halaman Glints 404 (tutup/hilang): {url}")
        if status != 200:
            raise SourceFetchError(f"Halaman Glints gagal (HTTP {status}): {url}")
        return parse_glints_job(html, url)

    def check_active(self, url: str) -> bool:
        status, html = self._get(url)
        if status == 404:
            return False
        if status != 200:
            raise SourceFetchError(
                f"check_active Glints gagal teknis (HTTP {status}): {url} "
                "— status lama dipertahankan (unknown), bukan closed."
            )
        return "this job was closed" not in html.lower() \
            and "lowongan ini sudah ditutup" not in html.lower()
