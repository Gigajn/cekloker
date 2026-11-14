"""Adapter JobStreet (id.jobstreet.com) — status: TUNDA (STUB).

Alasan penundaan — diverifikasi ke sumber primer 15 Nov 2026:
1. **ToS SEEK/JobStreet melarang agregasi**: Website Terms and
   Conditions (sg.jobstreet.com/terms, dibaca 15 Nov 2026) klausul (d):
   "aggregate, copy or duplicate in any matter any of the Content or
   information available from any of our websites and apps or Services,
   including expired job postings, other than as permitted by these
   Terms or another agreement we have with you".
   Advertising Terms SEEK klausul 27: "You may not use data mining,
   robots, screen scraping, or similar automated data gathering,
   extraction or publication tools on our websites or apps ... without
   our prior written approval."
2. **robots.txt melarang bot umum mengambil halaman detail**:
   `https://id.jobstreet.com/robots.txt` (dibaca langsung 15 Nov 2026),
   grup `User-agent: *`: `Disallow: */job/` dan `Disallow: *?` serta
   `Disallow: /api/jobsearch/` dan `Disallow: /graphql`.
   Halaman list bersih (`/<kata>-jobs/in-<Kota>`) memang tidak dilarang,
   TETAPI tanpa halaman detail tidak ada `posted_at`/deskripsi — dan
   ToS tetap melarang agregasi kontennya.
3. **API internal bukan API resmi**: endpoint Chalice Search v4
   (`id.jobstreet.com/api/chalice-search/v4/search`) muncul di repo
   open-source (ceroberoz/id-jobs) dan PR career-ops #1086 sebagai
   "public, no-auth". Itu FAKTA TEKNIS (endpoint merespons tanpa
   kunci), BUKAN izin legal: "no-auth" ≠ "diizinkan". robots.txt
   melarang `/api/jobsearch/`, ToS melarang agregasi. Lihat K-JB3.

Keputusan (ADR-0001, hasil grill): adapter ini STUB yang raise
`SourceNotPermittedError` di semua metode. Kode parser TIDAK ditulis
di sini supaya tidak ada yang "tidak sengaja" mengaktifkannya — yang
ada hanya dokumentasi endpoint + bentuk respons (ASUMSI, dari sumber
sekunder) untuk dipakai BILA izin tertulis sudah ada.

Alternatif legal:
- **SEEK API** (developer.seek.com): API resmi, tapi butuh pengajuan
  + persetujuan, dan ditujukan untuk integrasi ATS/perekrut — bukan
  pencarian lowongan publik. Untuk Indonesia, kontraknya dengan
  PT JobStreet Indonesia.
- Minta **izin tertulis** ke JobStreet Indonesia, lalu aktifkan
  adapter ini (butuh ADR baru + implementasi parser Chalice).
- Sementara: andalkan Glints + Kalibrr + halaman karier perusahaan
  (tim direct/ATS).

Mengaktifkan stub ini tanpa izin = melanggar ToS. Jangan diakali.
"""

from __future__ import annotations

from ..base import JobSourceAdapter, RawJob, SourceNotPermittedError

# Dokumentasi (BUKAN kode aktif) — bentuk endpoint internal Chalice v4
# menurut sumber sekunder, ASUMSI sampai ada uji live + izin:
#   GET https://id.jobstreet.com/api/chalice-search/v4/search
#   Params (dari DeepWiki ceroberoz/id-jobs, dibaca 15 Nov 2026):
#     siteKey=ID-Main, locale=id-ID, seek-request-country=ID,
#     referer=https://id.jobstreet.com/id/jobs?sortmode=ListedDate
#   Respons JSON: daftar job (title, company, "Listed seven days ago",
#   "Rp 22.000.000 – Rp 32.000.000 per month"), 30 job/halaman.
#   URL detail: https://id.jobstreet.com/job/<job_id>
CHALICE_SEARCH_V4 = "https://id.jobstreet.com/api/chalice-search/v4/search"


class JobStreetAdapter(JobSourceAdapter):
    source_id = "jobstreet"
    base_url = "https://id.jobstreet.com"
    enabled = False
    polite_delay_s = 5.0
    robots_disallows = ("*/job/", "*?", "/api/jobsearch/", "/graphql")

    disabled_reason = (
        "ToS SEEK/JobStreet melarang agregasi & screen scraping tanpa "
        "izin tertulis (klausul d & 27); robots.txt id.jobstreet.com "
        "melarang User-agent * mengambil */job/ dan URL ber-query. "
        "Endpoint Chalice v4 bersifat internal/tidak terdokumentasi. "
        "Lihat docs/fase1-riset-jobboard.md (K-JB1, K-JB3) & ADR-0001."
    )
    alternative = (
        "Ajukan akses SEEK API (developer.seek.com) atau minta izin "
        "tertulis ke PT JobStreet Indonesia. Sementara pakai Glints + "
        "Kalibrr + halaman karier perusahaan."
    )

    def discover(self, keywords: str = "", location: str = "",
                 max_pages: int = 1) -> list[str]:
        self.require_enabled()
        raise SourceNotPermittedError("unreachable")  # pragma: no cover

    def fetch_job(self, url: str) -> RawJob:
        self.require_enabled()
        raise SourceNotPermittedError("unreachable")  # pragma: no cover

    def check_active(self, url: str) -> bool:
        self.require_enabled()
        raise SourceNotPermittedError("unreachable")  # pragma: no cover
