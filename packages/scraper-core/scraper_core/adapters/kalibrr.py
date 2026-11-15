"""Adapter Kalibrr (kalibrr.com / kalibrr.id) — status: BANGUN.

Jalur akses (diverifikasi 15 Nov 2026):
1. **Halaman pencarian & detail publik** — tanpa login, tanpa API key.
   Sumber primer: skill `kalibrr-search` (fachrinoor/ai-job-search,
   dibaca 15 Nov 2026) yang diuji live 2026-07-11: "Each page embeds
   its full data as JSON in a `__NEXT_DATA__` script tag, which the
   CLI parses directly (more reliable than HTML scraping)."
   Adapter ini memakai jalur yang SAMA: parse `__NEXT_DATA__`.
2. **robots.txt** — `https://www.kalibrr.com/robots.txt` (dibaca langsung
   15 Nov 2026) hanya melarang `/root` dan `/candidate/profile`.
   Halaman lowongan & pencarian TIDAK dilarang.
3. **Pola URL detail** (terverifikasi dari hasil pencarian 15 Nov 2026):
   `https://www.kalibrr.id/c/<company-code>/jobs/<id>/<slug>`
   (mis. `.../c/pt-bumi-amartha-teknologi-mandiri/jobs/274906/...`).
   Domain Indonesia: `www.kalibrr.id` (locale `id-ID`).
4. **Field yang tersedia** (terverifikasi dari cuplikan halaman):
   `activationDate` (ISO, mis. `2026-09-28T06:44:24.594079+00:00`),
   deadline aplikasi, tipe kerja, lokasi, jumlah lowongan.
   "Posted a month ago" + "Apply before 30 Dec" tampil di halaman.

Keterbatasan yang SUDAH diketahui (dari skill yang sama):
- **Pagination TIDAK jalan** — "Every search call returns the same
  top ~15 results ... There is currently no known way to retrieve
  more than the first batch" (diuji live 2026-07-11). Konsekuensi:
  Kalibrr di v1 hanya untuk pencarian kata kunci (~15 hasil/query),
  BUKAN full crawl. Lihat K-JB4.
- Filter `?location=` diterima tapi tidak mengubah hasil — kota
  harus dilipat ke dalam kata kunci.
- Bentuk persis JSON `__NEXT_DATA__` tidak terdokumentasi publik;
  parser di sini defensif (mencari kunci `job`/`jobs` di mana saja
  dalam JSON) dan field yang tak ditemukan = None, bukan tebakan.

HASIL UJI LIVE 15 Nov 2026 (lihat docs/fase1-lanjutan-uji-live.md)
— ASUMSI `__NEXT_DATA__` GAGAL dari VM ini:
- `GET www.kalibrr.id/jobs?query=software+engineer` -> HTTP 200
  TAPI isinya hanya shell SPA ~2,3 KB (tanpa `__NEXT_DATA__`, tanpa
  URL lowongan, query tidak ter-echo). Data lowongan baru muncul
  setelah JS jalan — jadi adapter stdlib ini TIDAK BISA menemukan
  lowongan apa pun dari halaman itu.
- `robots.txt` (kalibrr.id MAUPUN kalibrr.com) juga mengembalikan
  shell SPA yang sama — bukan robots.txt sungguhan. Klaim Fase 1
  ("robots hanya melarang /root dan /candidate/profile") TIDAK
  TERVERIFIKASI live; `robots_disallows` di bawah dipertahankan
  sebagai catatan klaim lama, bukan fakta terverifikasi.
- Respons shell .com memuat penanda `<meta kb="__KB_THIS_IS_A_503__"/>`
  — kemungkinan Kalibrr menyajikan halaman error ke egress ini.
  BELUM BISA disimpulkan Kalibrr mati permanen: perlu uji ulang dari
  jaringan Indonesia (Fedora Giga) sebelum diputuskan (lihat D13).
- Perilaku adapter sejak perbaikan ini: bila halaman yang diterima
  TIDAK memuat `__NEXT_DATA__` sama sekali, parser melempar
  `SourceFetchError` (gagal teknis -> worker menandai `unknown`),
  BUKAN mengembalikan [] seolah "0 lowongan". Diam-diam kosong
  adalah data yang salah; gagal jujur adalah data yang benar.

ToS Kalibrr: teks ToS (kalibrr.id/terms) dibaca cuplikannya 15 Nov
2026 — pemakaian "for professional and legitimate purposes",
melarang aktivitas ilegal; **tidak ditemukan klausul eksplisit
anti-scraping dalam cuplikan** (K-JB8: teks penuh belum dibaca —
Giga perlu baca penuh sebelum rilis publik).

Penanda tutup (terverifikasi dari hasil pencarian 15 Nov 2026):
halaman lowongan tutup menampilkan teks "Ditutup."
"""

from __future__ import annotations

import json
import re
from datetime import date
from html.parser import HTMLParser
from typing import Any, Optional

from ..base import JobSourceAdapter, RawJob, SourceFetchError
from ..parsers import normalize_company, normalize_location, parse_posted_at

SEARCH_BASE = "https://www.kalibrr.id/jobs"
CLOSED_MARKERS = ("ditutup.", "this job is closed", "lowongan ditutup")


class _NextDataParser(HTMLParser):
    """Ambil isi <script id="__NEXT_DATA__" type="application/json">."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._capture = False
        self._buf: list[str] = []
        self.next_data: Optional[dict] = None
        self.text_parts: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag == "script" and dict(attrs).get("id") == "__NEXT_DATA__":
            self._capture = True
            self._buf = []

    def handle_endtag(self, tag):
        if tag == "script" and self._capture:
            self._capture = False
            try:
                self.next_data = json.loads("".join(self._buf))
            except (json.JSONDecodeError, ValueError):
                self.next_data = None

    def handle_data(self, data):
        if self._capture:
            self._buf.append(data)
        self.text_parts.append(data)

    @property
    def text(self) -> str:
        return " ".join(p for p in self.text_parts if p.strip())


def _walk(obj: Any, key: str) -> list[Any]:
    """Cari semua nilai dengan kunci `key` di struktur JSON bertingkat."""
    found: list[Any] = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == key:
                found.append(v)
            found.extend(_walk(v, key))
    elif isinstance(obj, list):
        for item in obj:
            found.extend(_walk(item, key))
    return found


def _first_str(data: dict, keys: tuple[str, ...]) -> str:
    for k in keys:
        v = data.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip()
    return ""


def parse_kalibrr_job(html: str, url: str,
                      ref: Optional[date] = None) -> RawJob:
    """Parse halaman detail Kalibrr -> RawJob (PURE, tanpa HTTP).

    Prioritas: `__NEXT_DATA__` dulu; fallback: penanda teks halaman.
    `posted_at` diisi dari `activationDate` (ISO, pasti) bila ada.
    """
    parser = _NextDataParser()
    parser.feed(html)
    teks = parser.text
    teks_rendah = teks.lower()
    is_active = not any(m in teks_rendah for m in CLOSED_MARKERS)

    # Gagal jujur (uji live 15 Nov 2026): tanpa __NEXT_DATA__ halaman
    # Kalibrr hanyalah shell SPA tanpa data lowongan. Melempar di sini
    # supaya worker menandai sumber `unknown`, bukan "0 lowongan".
    if parser.next_data is None:
        raise SourceFetchError(
            "Halaman detail Kalibrr tanpa __NEXT_DATA__ "
            f"(shell SPA, data tidak tersedia tanpa JS): {url}"
        )

    job: dict = {}
    if parser.next_data:
        # Cari objek job: kunci yang umum di __NEXT_DATA__ Kalibrr.
        # Bentuk persis tidak terdokumentasi -> defensif.
        for kandidat in _walk(parser.next_data, "job"):
            if isinstance(kandidat, dict) and (
                kandidat.get("title") or kandidat.get("name")
            ):
                job = kandidat
                break
        if not job:
            for kandidat in _walk(parser.next_data, "jobPosting"):
                if isinstance(kandidat, dict):
                    job = kandidat
                    break

    title = _first_str(job, ("title", "name", "jobTitle"))
    company = _first_str(job, ("companyName", "company", "employerName"))
    if not company:
        comp = job.get("company")
        if isinstance(comp, dict):
            company = _first_str(comp, ("name", "companyName"))
    location = _first_str(
        job, ("location", "jobLocation", "city", "address"))
    if not location:
        loc = job.get("location")
        if isinstance(loc, dict):
            location = _first_str(loc, ("name", "city", "address"))
    salary_text = _first_str(job, ("salary", "salaryRange", "salaryText"))
    work_type = _first_str(
        job, ("employmentType", "jobType", "workType")).lower()

    posted_at = None
    posted_certain = True
    posted_raw = ""
    activation = _first_str(job, ("activationDate", "postedAt", "datePosted",
                                   "createdAt"))
    if activation:
        posted_raw = activation
        posted_at, posted_certain = parse_posted_at(activation, ref)

    if not posted_at:
        m = re.search(
            r"Posted\s+([^•\n]{1,40}?ago)|Diposting\s+([^•\n]{1,40})",
            teks, re.IGNORECASE,
        )
        if m:
            posted_raw = (m.group(1) or m.group(2) or "").strip()
            posted_at, posted_certain = parse_posted_at(posted_raw, ref)

    if not title:
        # Fallback: judul halaman dari teks ("<Judul> Job Openings at <Prsh>")
        m = re.search(r"(.+?)\s+Job Openings at\s+(.+)", teks)
        if m:
            title, company = m.group(1).strip(), m.group(2).strip()
    if not title or not company:
        raise SourceFetchError(
            f"Halaman Kalibrr {url} tidak bisa diparse (judul/perusahaan "
            "tidak ditemukan di __NEXT_DATA__ maupun teks — kemungkinan "
            "layout berubah atau halaman bukan detail lowongan)."
        )

    description = _first_str(
        job, ("description", "jobDescription", "about"))
    if not description:
        description = teks[:2000]

    work_type_norm = ""
    if "remote" in work_type or "telecommute" in work_type:
        work_type_norm = "remote"
    elif "hybrid" in work_type:
        work_type_norm = "hybrid"
    elif "onsite" in work_type or "on-site" in work_type \
            or "on site" in work_type:
        work_type_norm = "onsite"

    return RawJob(
        source_id="kalibrr",
        source_url=url,
        title=title.strip(),
        company_raw=company.strip(),
        company_norm=normalize_company(company),
        location=normalize_location(location),
        work_type=work_type_norm,
        salary_text=salary_text,
        posted_at=posted_at,
        posted_at_certain=posted_certain,
        posted_raw=posted_raw,
        description_text=description.strip(),
        is_active=is_active,
    )


def parse_kalibrr_search(html: str) -> list[str]:
    """Ambil URL detail lowongan dari halaman pencarian Kalibrr.

    Mencari pola `/c/<company>/jobs/<id>/<slug>` di `__NEXT_DATA__`
    maupun di HTML mentah. Deduplikasi menjaga urutan.

    Melempar SourceFetchError bila halaman TIDAK memuat `__NEXT_DATA__`
    sama sekali dan tidak ada URL ditemukan — itu shell SPA tanpa data
    (uji live 15 Nov 2026), bukan "0 lowongan". Halaman pencarian yang
    sah tapi memang 0 hasil tetap mengembalikan [] (karena
    `__NEXT_DATA__`-nya ada, hanya daftarnya kosong).
    """
    parser = _NextDataParser()
    parser.feed(html)
    urls: list[str] = []
    pola = re.compile(
        r"https://www\.kalibrr\.(?:id|com|ph|vn)"
        r"/c/[a-z0-9-]+/jobs/\d+/[a-z0-9-]+", re.IGNORECASE
    )
    for sumber in (html, json.dumps(parser.next_data or {})):
        for m in pola.finditer(sumber):
            if m.group(0) not in urls:
                urls.append(m.group(0))
    if parser.next_data is None and not urls:
        raise SourceFetchError(
            "Halaman pencarian Kalibrr tanpa __NEXT_DATA__ (shell SPA, "
            "data tidak tersedia tanpa JS) — bukan berarti 0 lowongan."
        )
    return urls


class KalibrrAdapter(JobSourceAdapter):
    source_id = "kalibrr"
    base_url = "https://www.kalibrr.id"
    enabled = True
    polite_delay_s = 3.0
    robots_disallows = ("/root", "/candidate/profile")

    def discover(self, keywords: str = "", location: str = "",
                 max_pages: int = 1) -> list[str]:
        """Cari lowongan lewat halaman pencarian publik.

        ASUMSI (perlu uji live): parameter query halaman pencarian
        Kalibrr adalah `?query=<kata kunci>` — bentuk persis tidak
        terdokumentasi publik. `location` dilipat ke kata kunci
        (filter `?location=` terbukti tidak bekerja, skill 2026-07-11).
        `max_pages` diabaikan dengan sengaja: pagination Kalibrr
        terbukti tidak jalan (selalu ~15 hasil pertama). Jangan
        memanggil discover berulang dengan harapan halaman berbeda.

        UJI LIVE 15 Nov 2026: dari VM ini pencarian mengembalikan shell
        SPA tanpa `__NEXT_DATA__` — `?query=` TIDAK TERVERIFIKASI
        bekerja, dan discover() melempar SourceFetchError pada kondisi
        itu (lihat parse_kalibrr_search). Perlu uji ulang dari jaringan
        Indonesia sebelum disimpulkan (D13).
        """
        query = " ".join(p for p in (keywords, location) if p).strip()
        if not query:
            raise ValueError(
                "Kalibrr discover butuh kata kunci (tidak ada mode "
                "'semua lowongan' yang terdokumentasi)."
            )
        from urllib.parse import quote_plus
        url = f"{SEARCH_BASE}?query={quote_plus(query)}"
        status, html = self._get(url)
        if status != 200:
            raise SourceFetchError(
                f"Pencarian Kalibrr gagal (HTTP {status}): {url}")
        return parse_kalibrr_search(html)

    def fetch_job(self, url: str) -> RawJob:
        status, html = self._get(url)
        if status == 404:
            raise SourceFetchError(f"Halaman Kalibrr 404 (tutup/hilang): {url}")
        if status != 200:
            raise SourceFetchError(f"Halaman Kalibrr gagal (HTTP {status}): {url}")
        return parse_kalibrr_job(html, url)

    def check_active(self, url: str) -> bool:
        status, html = self._get(url)
        if status == 404:
            return False
        if status != 200:
            raise SourceFetchError(
                f"check_active Kalibrr gagal teknis (HTTP {status}): {url} "
                "— status lama dipertahankan (unknown), bukan closed."
            )
        rendah = html.lower()
        return "ditutup." not in rendah \
            and "this job is closed" not in rendah
