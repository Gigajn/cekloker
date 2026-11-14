"""Adapter Indeed (indeed.com / id.indeed.com) — status: TUNDA (STUB).

Alasan penundaan — diverifikasi ke sumber primer 15 Nov 2026:
1. **ToS Indeed melarang bot tanpa izin tertulis**: Terms of Service
   (versi "Last Updated: September 29, 2026", Section D.21 Site Rules,
   dikutip dari sumber sekunder yang membaca teks ToS langsung,
   urltotext.com & unknownproxies.com, Okt 2026):
   "Use any automated system (bots, scrapers, spiders, AI or Agentic
   AI) to access, data-mine, or submit content to the Site, in bulk or
   otherwise, without Indeed's express written permission (we
   conditionally grant permission to crawl the Site solely as outlined
   in our robots.txt file)."
2. **robots.txt melarang bot umum mengambil halaman detail**:
   `https://www.indeed.com/robots.txt` (dibaca langsung 15 Nov 2026),
   grup `User-agent: *`: `Allow: /` tetapi `Disallow: /viewjob`,
   `Disallow: /job/`, `Disallow: /jobs/ID/` (juga DE/GB/US/dll),
   `Disallow: /graphql`, `Disallow: /api/getrecjobs`,
   `Disallow: /company/*`, `Disallow: /rss`.
   Halaman pencarian hanya diizinkan sampai `&start=90` (±10 halaman).
   Jadi: hasil pencarian boleh di-crawl, halaman detail TIDAK.
   Tanpa halaman detail, tidak ada deskripsi/gaji/posted_at yang bisa
   diandalkan — dan ToS tetap melarang data-mining. Lihat K-JB5.
3. **Tidak ada API publik untuk pencarian lowongan**: Publisher API
   (API pencarian ber-key untuk afiliasi) sudah ditutup untuk developer
   baru dan berhenti mengembalikan data sejak ~2023 (beberapa sumber
   sekunder, konsisten). API yang tersisa (Job Sync API, Disposition
   Sync API, Job Update API) ditujukan untuk ATS/perekrut yang
   MENGIRIM lowongan ke Indeed — bukan membaca indeks publik — dan
   butuh review/partner. Indeed Indonesia (id.indeed.com) memakai
   aturan yang sama.
4. **Anti-bot aktif**: Indeed menyajikan interstitial/blokir untuk
   request yang tidak terlihat seperti browser sungguhan (fe.tonywang.io,
   2026). Mengakali itu (proxy residensial, TLS impersonation) adalah
   bentuk bypass — dilarang aturan proyek.

Keputusan (ADR-0001, hasil grill): adapter ini STUB yang raise
`SourceNotPermittedError`. TIDAK ADA parser Indeed di repo ini.

Alternatif legal (untuk cakupan global):
- **Adzuna API** — API lowongan berbayar/gratis-terbatas dengan
  pendaftaran terbuka (perlu dicek harga & cakupan ID).
- **ATS langsung**: Greenhouse / Lever / Ashby / Workday — API publik
  tanpa kunci untuk halaman karier perusahaan (lihat tim direct).
- **Indeed Partner / Employer API** — hanya bila CekLoker bermitra
  sebagai ATS/perekrut (bukan untuk fase v1).
- Untuk Indonesia: Glints + Kalibrr sudah mencakup pasar lokal.

Mengaktifkan scraping Indeed tanpa izin tertulis = melanggar ToS
dan berisiko diblokir + tuntutan. Jangan diakali.
"""

from __future__ import annotations

from ..base import JobSourceAdapter, RawJob, SourceNotPermittedError


class IndeedAdapter(JobSourceAdapter):
    source_id = "indeed"
    base_url = "https://id.indeed.com"
    enabled = False
    polite_delay_s = 5.0
    robots_disallows = (
        "/viewjob", "/job/", "/jobs/ID/", "/graphql",
        "/api/getrecjobs", "/company/*", "/rss",
    )

    disabled_reason = (
        "ToS Indeed (29 Sep 2026, §D.21) melarang bot/scraper/AI agent "
        "tanpa izin tertulis; robots.txt indeed.com melarang User-agent * "
        "mengambil /viewjob, /job/, /jobs/ID/; tidak ada API publik "
        "pencarian lowongan (Publisher API ditutup ~2023). "
        "Lihat docs/fase1-riset-jobboard.md (K-JB5) & ADR-0001."
    )
    alternative = (
        "Adzuna API (pendaftaran terbuka), ATS langsung (Greenhouse/Lever), "
        "atau program partner Indeed. Untuk Indonesia: Glints + Kalibrr."
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
