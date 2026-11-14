# CekLoker — scraper-core
"""Paket inti scraper CekLoker (Fase 1).

Isi paket:
- `scraper_core.base`: kontrak adapter (`JobSourceAdapter`) + `RawJob`
  + helper kesopanan (delay, User-Agent, robots.txt).
- `scraper_core.parsers`: parser gaji IDR, tanggal relatif Indonesia,
  dan normalisasi nama perusahaan (stdlib saja).
- `scraper_core.adapters`: satu file per sumber job board (glints,
  jobstreet, kalibrr, indeed) + `career_page.py` (halaman karier / ATS)
  + `social_company.py` (lead sosial perusahaan, bukan adapter lowongan).
  Semua adapter memakai `RawJob` + `JobSourceAdapter` yang sama dari
  `scraper_core.base` — disatukan koordinator Fase 1 (15 Nov 2026);
  sebelumnya tim Direct punya definisi `RawJob` lokal (duplikat).
  `RawJob` juga membawa `posted_at_certain` (ADR-0002: flag kepastian
  tanggal) dan field ATS (`platform`, `platform_job_id`, `job_key`,
  `department`, `repost_hint`, `raw`).

Dependensi runtime: **stdlib Python 3.12 saja** (tidak ada bs4/httpx).
Alasan: halaman sumber yang dipakai v1 menyematkan data sebagai JSON
(JSON-LD di Glints, `__NEXT_DATA__` di Kalibrr), jadi `json` + `re` +
`html.parser` sudah cukup; nol dependensi = Docker image kecil dan
tidak ada rantai pasok pihak ketiga di worker. Lihat
`docs/adr/ADR-0002-kontrak-adapter-deteksi-aktif.md`.

Menjalankan test:

    python -m venv .venv && .venv/bin/pip install pytest
    .venv/bin/python -m pytest -q

Status adapter (15 Nov 2026) — lihat `docs/fase1-riset-jobboard.md`:
- Glints: BANGUN (sitemap + halaman publik JSON-LD).
- Kalibrr: BANGUN (halaman publik `__NEXT_DATA__`, pagination terbatas).
- JobStreet: TUNDA — stub, ToS SEEK + robots.txt melarang scraping
  tanpa izin tertulis. Butuh izin tertulis / akses SEEK API.
- Indeed: TUNDA — stub, ToS + robots.txt melarang akses bot ke halaman
  detail. Alternatif: Adzuna API, ATS langsung (Greenhouse/Lever).
"""
