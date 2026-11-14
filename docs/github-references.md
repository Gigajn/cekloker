# Referensi GitHub untuk CekLoker — Fase 1

> **Tanggal cek: 15 November 2026.** Semua angka bintang, lisensi, dan status repo di bawah ini
> dibaca langsung dari halaman repo GitHub-nya pada 15 Nov 2026 (halaman di-crawl 14 Nov 2026, 17:30 UTC),
> BUKAN dari ingatan. Kalau satu fakta tidak tampil di halaman yang dibuka, ditulis
> "tidak terverifikasi hari ini" — jangan dianggap benar.
>
> **Aturan dokumen ini:** tidak ada satu baris kode pun yang disalin dari repo-repo di bawah.
> Yang dicatat hanya URL + analisis + atribusi. Keputusan adopsi mengikuti
> [ADR-0007](adr/ADR-0007-adopsi-vs-tulis-ulang.md).
>
> Konteks arsitektur: lihat `ARCHITECTURE.md` (§2 stack, §6 kontrak adapter, §8 legal)
> dan `docs/SCORING.md`. Stack CekLoker v1: Python 3.12 + FastAPI, Next.js + TypeScript,
> PostgreSQL 16, Redis, Docker Compose, modular monolith, lisensi rencana MIT (Fase 5 open source).

---

## Ringkasan eksekutif — 3 rekomendasi terbaik

| # | Repo | Putusan | Alasan singkat |
|---|------|---------|----------------|
| 1 | [speedyapply/JobSpy](https://github.com/speedyapply/JobSpy) | **ADOPSI** (sebagai library, terbatas) | MIT, 4.728★, commit terakhir 27 Okt 2026 — paling terawat. Satu-satunya kandidat yang mendukung Indonesia (`country_indeed="Indonesia"`). Dipakai **hanya** sebagai dependensi library untuk adapter Indeed/Glassdoor; adapter Glints/JobStreet/Kalibrr tetap tulis sendiri. |
| 2 | [Riley-Dorrington/job-board-aggregator](https://github.com/Riley-Dorrington/job-board-aggregator) | **REFERENSI** (pola, bukan kode) | Kode MIT, commit terakhir 14 Nov 2026. Pola terbaik untuk klien ATS (Greenhouse/Lever/Ashby/Workday), pruning lowongan basi >30 hari, dan deteksi anomali volume — ketiganya langsung menjawab "lowongan masih aktif?" di ARCHITECTURE.md §3. Dataset perusahaannya berlisensi CC BY-NC 4.0 (non-komersial) — **jangan** dipakai. |
| 3 | [kbwhodat/jobdrop](https://github.com/kbwhodat/jobdrop) | **REFERENSI** (pola, bukan kode) | MIT, fork JobSpy yang diperluas (ATS + TrueUp dengan flag layoff/kesehatan perusahaan — ide yang cocok untuk flag engine). Tapi: hanya 4★, 1 maintainer, dan klaim jumlah sumbernya bertentangan di dalam repo sendiri (K-G1). Teknik anti-bot-nya (TLS impersonation, Googlebot UA) adalah risiko ToS — pelajari polanya, jangan adopsi mentah. |

**Yang sengaja TIDAK masuk 3 besar meski menarik:** `omkarcloud/glassdoor-scraper`
(baru 6 minggu, 2★, klaim "unlimited free" tak terverifikasi — REFERENSI pola endpoint
Glassdoor saja) dan `inigo99/jobradar` (pola dedup & sweep lowongan tutupnya bagus,
tapi AGPL-3.0 — TIDAK BOLEH disalin ke proyek MIT; hanya REFERENSI IDE).

---

## Tabel perbandingan semua kandidat

Tanggal cek per repo: **15 Nov 2026** (halaman repo di-crawl 14 Nov 2026, 17:30 UTC).

| Repo | Lisensi | Bintang | Update terakhir (terverifikasi) | Stack | Relevansi dengan CekLoker | Rekomendasi |
|------|---------|---------|--------------------------------|-------|---------------------------|-------------|
| [speedyapply/JobSpy](https://github.com/speedyapply/JobSpy) | MIT | 4.728 | 27 Okt 2026 (halaman commit) | Python 3.10+, pandas | Sangat tinggi — library scraper 8 board, dukung Indonesia, skema JobPost siap pakai | **ADOPSI** (library, terbatas) |
| [Riley-Dorrington/job-board-aggregator](https://github.com/Riley-Dorrington/job-board-aggregator) | MIT (kode) / CC BY-NC 4.0 (data `data/`) | 187 | 14 Nov 2026 (snapshot tren harian; kode terakhir 13 Nov 2026) | Python 3.12, JS vanilla, GitHub Actions | Tinggi — klien ATS, pruning basi, deteksi anomali | **REFERENSI** |
| [kbwhodat/jobdrop](https://github.com/kbwhodat/jobdrop) | MIT | 4 | Tidak terverifikasi tanggal pasti (halaman commit tanpa tanggal saat di-crawl) | Python 3.10+, curl_cffi | Tinggi — 28+ sumber, ATS, TrueUp flag layoff | **REFERENSI** |
| [omkarcloud/glassdoor-scraper](https://github.com/omkarcloud/glassdoor-scraper) | MIT | 2 | 4 Nov 2026 (halaman commit) | Python, FastAPI (25 endpoint) | Sedang — ulasan/gaji Glassdoor untuk skor Fase 2 | **REFERENSI** |
| [Ameya-Deshmukh26/job-scraper](https://github.com/Ameya-Deshmukh26/job-scraper) | MIT | 1 | Tidak terverifikasi tanggal pasti | Python, Flask, SQLite | Sedang — klien ATS + discovery board via YC | **REFERENSI** |
| [ouverz/ai-job-tracker](https://github.com/ouverz/ai-job-tracker) | MIT | 1 | Tidak terverifikasi tanggal pasti | Python 3.11 FastAPI + React, SQLite | Sedang — struktur mirip CekLoker (FastAPI + frontend), skor 0–100 | **REFERENSI** |
| [cncf/gitjobs](https://github.com/cncf/gitjobs) | Apache-2.0 | 126 | 9 Nov 2026 (halaman commit) | Rust, PostgreSQL | Rendah — job board developer, bukan scraper; ide embed berguna | **REFERENSI** |
| [PaulMcInnis/JobFunnel](https://github.com/PaulMcInnis/JobFunnel) | MIT | 2.198 | **Diarsipkan 10 Des 2025** (owner sendiri menyatakan era HTML statis selesai) | Python 3.11, BeautifulSoup | Historis — pola dedup + delay sopan | **TOLAK** (arsip) |
| [inigo99/jobradar](https://github.com/inigo99/jobradar) | **AGPL-3.0** | 1 | Tidak terverifikasi tanggal pasti | Python 3.10, FastAPI, SQLite | Tinggi — dedup fingerprint, sweep lowongan tutup, "filtered out + alasan" | **TOLAK adopsi kode / REFERENSI IDE saja** |
| [nishanthrajkumarr/dossier](https://github.com/nishanthrajkumarr/dossier) (fork dari AienTech/dossier) | **AGPL-3.0** | 0 (fork; upstream ~3.509★ menurut artikel ulasan 31 Okt 2026 — bukan halaman repo) | Tidak terverifikasi tanggal pasti | Next.js 16, PostgreSQL 18, Prisma | Sedang — auth single-user, Docker Compose + Caddy, PRIVACY.md | **TOLAK adopsi kode / REFERENSI IDE saja** |

> Catatan soal "update terakhir": tanggal di atas diambil dari halaman `/commits` repo
> masing-masing yang dibuka 15 Nov 2026. Untuk repo yang halaman commit-nya tidak
> menampilkan tanggal saat di-crawl, ditulis apa adanya — bukan ditebak dari tanggal
> pembuatan repo.

---

## Detail per repo

### 1. speedyapply/JobSpy — ADOPSI (sebagai library, terbatas)

- **URL:** https://github.com/speedyapply/JobSpy
- **Lisensi:** MIT (tertera di halaman repo) — cocok dengan rencana MIT CekLoker.
- **Bintang / fork:** 4.728★ / 938 fork. Dibuat 6 Jul 2023, 393 commit, 64 rilis.
- **Update terakhir:** 27 Okt 2026 (commit "bump certifi…", halaman `/commits/main`).
- **Stack:** Python ≥3.10, pandas, tersedia di PyPI sebagai `python-jobspy`, plus CLI `jobspy` dan MCP server `mcp-jobspy`.
- **Fitur relevan:** satu panggilan `scrape_jobs()` ke LinkedIn, Indeed, Glassdoor, ZipRecruiter, Bayt, Naukri, BDJobs, HelloWork — konkuren, hasil jadi DataFrame. Skema `JobPost` lengkap: `title, company, location, date_posted, min/max_amount, currency, is_remote, job_type, company_rating, company_reviews_count, description, company_url, job_url`. Filter `hours_old` (umur lowongan dalam jam) dan `country_indeed` — **Indonesia ada di daftar negara Indeed** (penting: satu-satunya kandidat yang menyebut Indonesia). Error per-board dilaporkan lewat `jobs.attrs["errors"]` sehingga kode pemanggil tahu board mana yang diblokir vs yang memang kosong.
- **Yang BISA diadopsi mentah-mentah:** pakai sebagai dependensi PyPI `python-jobspy` untuk adapter Indeed (dan Glassdoor bila perlu) di Fase 1. Tidak perlu fork: panggil `scrape_jobs(site_name=["indeed"], country_indeed="Indonesia", ...)`, lalu petakan `JobPost` → model `jobs` CekLoker (`posted_at` ← `date_posted`, `first_seen_at` ← waktu ambil). Atribusi: cantumkan di README + `NOTICE`/daftar dependensi.
- **Yang harus ditulis ulang / diadaptasi:**
  - JobSpy TIDAK punya Glints, JobStreet, atau Kalibrr — tiga sumber utama Fase 1 CekLoker. Adapter itu wajib tulis sendiri mengikuti kontrak `JobSourceAdapter` (ARCHITECTURE.md §6).
  - JobSpy tidak melacak status aktif: tidak ada `first_seen_at`/`last_seen_at`/`check_active`. Lapisan tracking aktif CekLoker (§3 alur 4) tetap ditulis sendiri di atas hasil JobSpy.
  - Output DataFrame → harus dinormalisasi ke skema Postgres CekLoker (dedup fingerprint `hash(url + judul + perusahaan)`).
- **Risiko:**
  - **ToS sumber:** README JobSpy sendiri mengakui LinkedIn me-rate-limit (429) dan Glassdoor membatasi ~2 req/detik; LinkedIn & Glassdoor melarang scraping otomatis di ToS-nya. Mengadopsi library ini memindahkan risiko itu ke CekLoker — mitigasi: pakai hanya Indeed sebagai sumber JobSpy di v1 (README menyebut "Indeed is the best scraper currently with no rate limiting"), LinkedIn HANYA sebagai info perusahaan publik + link keluar sesuai ARCHITECTURE.md §5, dan patuhi delay 2–5 detik/domain.
  - **Kerapuhan:** PyPI tertinggal dari GitHub (rilis terakhir di PyPI 1.1.82, Jul 2025 — menurut ulasan jobspipe.dev 15 Sep 2026); perbaikan board terbaru hanya ada di GitHub. Keputusan: pin ke versi GitHub yang teruji, atau tunggu rilis PyPI baru.
  - **Google Jobs tidak tersedia** saat ini (FAQ resmi repo) — jangan rencanakan fitur di atasnya.
- **Hasil grill:** awalnya "ADOPSI penuh sebagai mesin scraper". Setelah di-grill (lihat [Hasil Grill](#hasil-grill)), turun menjadi **ADOPSI TERBATAS**: library untuk Indeed/Glassdoor saja, bukan mesin inti. Alasannya: 3 sumber utama CekLoker tidak dicakup, dan tracking aktif (janji produk #1) tidak ada di JobSpy.

### 2. Riley-Dorrington/job-board-aggregator — REFERENSI

- **URL:** https://github.com/Riley-Dorrington/job-board-aggregator
- **Lisensi:** MIT untuk kode. **JEBAKAN: dataset kurasi di `data/` berlisensi CC BY-NC 4.0** (non-komersial, tertulis di README). Lisensi ganda ini mudah terlewat — kode boleh dipakai, datanya tidak boleh dipakai untuk layanan komersial.
- **Bintang / fork:** 187★ / 42 fork. Dibuat 5 Jan 2026, 485 commit.
- **Update terakhir:** 14 Nov 2026 — tapi hampir semua commit harian adalah "Trend snapshot" otomatis dari GitHub Actions; perubahan kode terakhir yang terlihat 13 Nov 2026 (sumber Join + Workable). Aktivitasnya nyata, tapi angka commit menipu: jangan baca "485 commit" sebagai 485 perubahan fitur.
- **Stack:** Python 3.12 (`requests`, `concurrent.futures`, `gzip`), frontend JS vanilla + Bootstrap 5, GitHub Actions cron harian, hosting GitHub Pages.
- **Fitur relevan:** scraper paralel 9 platform ATS (Greenhouse, Lever, Ashby, BambooHR, iCIMs, Paylocity, Workday, Join, Workable XML feed) dengan jumlah worker disetel per platform sesuai rate limit masing-masing (contoh: 50 untuk Workday, 5 untuk Ashby/Paylocity); `merge_data.py` menduplikasi + memangkas lowongan >30 hari; `check_anomalies.py` mencatat tren harian dan membuka issue bila volume satu platform anjlok/melonjak; penemuan perusahaan dari Common Crawl (95 ribu slug perusahaan ATS).
- **Yang BISA diadopsi mentah-mentah:** tidak ada yang perlu diadopsi mentah — arsitekturnya (GitHub Pages + chunk gzip) bukan arsitektur CekLoker (FastAPI + Postgres + Next.js).
- **Yang dipelajari / ditulis ulang:** (a) pola "worker count per platform" → jadikan `politeness.py` CekLoker; (b) pola pruning lowongan basi + deteksi anomali → jadikan dasar `check_active` + alert "1 sumber mati" di scheduler; (c) pola discovery perusahaan ATS via sitemap/Common Crawl → adaptasi untuk halaman karier perusahaan Indonesia (Fase 1 tim direct).
- **Risiko:** dataset CC BY-NC 4.0 (lihat di atas); cakupan ATS global, bukan Indonesia — perusahaan Indonesia yang pakai Greenhouse/Lever/Ashby sedikit; frontend vanilla JS tidak relevan dengan Next.js CekLoker.

### 3. kbwhodat/jobdrop — REFERENSI

- **URL:** https://github.com/kbwhodat/jobdrop
- **Lisensi:** MIT.
- **Bintang / fork:** 4★ / 2 fork. Dibuat 6 Mei 2026, 408 commit, versi 2.4.3.
- **Update terakhir:** tidak terverifikasi tanggal pasti hari ini (halaman `/commits/main` yang dibuka tidak menampilkan tanggal commit).
- **Stack:** Python ≥3.10, `curl_cffi`, tersedia di PyPI sebagai `jobdrop`, plus MCP server dan TUI.
- **Fitur relevan:** fork JobSpy yang diperluas ke ATS (Greenhouse, Ashby, Workday, Lever, iCIMS) + API publik (Adzuna, Jooble, USAJobs) + agregator niche. Dua ide yang sangat relevan: (a) **TrueUp** — memberi skor "company-trajectory", valuasi, tahap pendanaan, dan **flag layoff/kesehatan perusahaan** per lowongan; ini pola yang hampir sama dengan yang dibutuhkan flag engine CekLoker (§5, sinyal stabilitas); (b) **Greenhouse staleness filter 3 lapis** — lowongan "live tapi kuno" disaring (default 90 hari), sejalan dengan aturan ghost job CekLoker (>90 hari tanpa perubahan → −10).
- **Yang BISA diadopsi mentah-mentah:** tidak ada — terlalu muda (4★, 1 maintainer + Claude sebagai co-committer di hampir semua commit) untuk dijadikan dependensi inti.
- **Yang dipelajari / ditulis ulang:** pola flag layoff/kesehatan perusahaan dari TrueUp (tulis ulang sebagai sinyal `layoff_news` di flag engine, sumbernya berita — bukan dari TrueUp yang cakupannya startup AS); pola staleness filter Greenhouse; pola discovery ATS via Google-dork (hati-hati: mengandalkan hasil pencarian Google untuk menemukan board).
- **Risiko:**
  - **Kontradiksi internal (K-G1):** judul repo menyebut "28-source", README menyebut "33 sources", tapi riwayat commit menyebut TrueUp sebagai "21st source" (v2.4.0). Tiga angka berbeda untuk hal yang sama — klaim cakupan tidak bisa dipercaya tanpa menghitung sendiri folder scraper-nya. Ini alasan utama turun dari ADOPSI ke REFERENSI.
  - **Risiko ToS paling tinggi di antara kandidat:** README menyebut "Bypasses Cloudflare WAF via Safari iOS TLS fingerprint" (CareerBuilder), "SSR'd HTML scrape via Googlebot UA" (Dice), dan pemakaian `curl_cffi` untuk meniru TLS Chrome. Itu teknik mengelabui deteksi bot — mengadopsinya mentah berarti mewarisi posisi yang secara eksplisit melawan perlindungan situs. CekLoker (ARCHITECTURE.md §8) berprinsip sebaliknya: patuhi robots.txt, jangan bypass. Pelajari polanya, jangan salin tekniknya.
  - Bus factor 1 (satu maintainer manusia).

### 4. omkarcloud/glassdoor-scraper — REFERENSI

- **URL:** https://github.com/omkarcloud/glassdoor-scraper
- **Lisensi:** MIT.
- **Bintang / fork:** 2★ / 0 fork. Dibuat 26 Sep 2026, hanya 6 commit.
- **Update terakhir:** 4 Nov 2026 (commit README, halaman `/commits/master`).
- **Stack:** Python, FastAPI (25 endpoint), Docker + docker-compose.
- **Fitur relevan:** API lokal untuk ulasan perusahaan Glassdoor (pros/cons, rating, sub-rating 5 kategori, CEO approval, rekomendasi), gaji per jabatan, wawancara, benefit, dan pencarian lowongan — persis data yang dibutuhkan kategori "Reputasi & ulasan" (25 poin) di SCORING.md.
- **Yang BISA diadopsi mentah-mentah:** tidak ada. Repo berumur 6 minggu, 2★, 6 commit — belum ada bukti ketahanan terhadap perubahan Cloudflare/login-wall Glassdoor.
- **Yang dipelajari / ditulis ulang:** daftar endpoint + bentuk respons JSON-nya sebagai spesifikasi untuk adapter Glassdoor CekLoker Fase 2 (tulis ulang dengan `httpx` + Playwright bila perlu, sesuai kontrak adapter). Perhatikan: repo ini juga didistribusikan lewat RapidAPI berbayar (1.000 panggilan/bulan gratis) — "unlimited free" di README bertentangan dengan model bisnis yang sama: klaim "unlimited" tidak terverifikasi dan tidak boleh dikutip ke pengguna (K-G2).
- **Risiko:** Glassdoor memakai Cloudflare + login wall untuk ulasan dan ToS-nya melarang akses otomatis (dikonfirmasi panduan independen liveproxies.io). Untuk Fase 2, CekLoker sebaiknya hanya mengambil agregat publik (rating + jumlah ulasan + link) dengan frekuensi rendah, dan selalu menyimpan `evidence_url` — bukan menyalin isi ulasan massal.

### 5. Ameya-Deshmukh26/job-scraper — REFERENSI

- **URL:** https://github.com/Ameya-Deshmukh26/job-scraper
- **Lisensi:** MIT.
- **Bintang / fork:** 1★ / 0 fork. Dibuat 26 Mei 2026, 19 commit.
- **Update terakhir:** tidak terverifikasi tanggal pasti hari ini.
- **Stack:** Python 3.11/3.12, Flask, SQLite, 125 test offline.
- **Fitur relevan:** klien ATS per file (`sources/greenhouse.py`, `lever.py`, `ashby.py`, `workday.py` — Workday memakai CXS JSON API tak terdokumentasi), discovery board otomatis dengan mem-probe API Y Combinator (6.175 perusahaan) ke Greenhouse/Lever/Ashby, skor kecocokan 0–100 per lowongan, dedup title+company, freshness badge (<1 jam, 1–6 jam, 6–24 jam).
- **Yang dipelajari / ditulis ulang:** struktur "satu file per ATS" sangat dekat dengan kontrak adapter CekLoker (§6: 1 file + 1 test + 1 baris config) — jadikan contoh bentuk file adapter; pola discovery board via direktori perusahaan; pola freshness badge (bisa diadaptasi jadi label "baru <24 jam" di UI CekLoker).
- **Risiko:** cakupan AS-sentris (H-1B, Fortune 500, USCIS) — tidak relevan untuk Indonesia; ada fitur **auto-apply** (melamar otomatis semalaman) — JANGAN diadopsi: melamar atas nama pengguna tanpa pengawasan melanggar prinsip CekLoker (bukan konsultan pelamar, bukan agen yang bertindak atas nama pengguna) dan berisiko diblokir board; 1★ + 19 commit = belum teruji komunitas.

### 6. ouverz/ai-job-tracker — REFERENSI

- **URL:** https://github.com/ouverz/ai-job-tracker
- **Lisensi:** MIT.
- **Bintang / fork:** 1★ / 0 fork. Dibuat 19 Mei 2026, 8 commit.
- **Update terakhir:** tidak terverifikasi tanggal pasti hari ini.
- **Stack:** Python 3.11 FastAPI + React 18/Vite/Tailwind + SQLite — **paling mirip stack CekLoker** di antara semua kandidat (beda: SQLite vs Postgres, React vs Next.js).
- **Fitur relevan:** scraper konkuren + dedup 3 strategi (URL, content hash, fuzzy nama perusahaan); skor ATS 0–100 dengan sub-skor + alasan (Claude API); auto-archive lowongan `new` yang berumur >14 hari; endpoint SSE untuk progres scraping; `BaseScraper` + `scrape() -> list[JobPosting]` (mirip kontrak adapter CekLoker).
- **Yang dipelajari / ditulis ulang:** pola skor 0–100 ber-sub-skor + alasan tertulis — sangat dekat dengan kebutuhan tampilan skor CekLoker ("+15 gaji transparan (8/10 lowongan), −15 keluhan lembur (5 ulasan, link)"); pola auto-archive sebagai pelengkap `expired`; pola SSE untuk progres worker (berguna untuk halaman admin).
- **Risiko:** single-user + SQLite + tanpa autentikasi (README sendiri memperingatkan jangan expose port 8000) — arsitektur ini TIDAK boleh ditiru untuk CekLoker yang akan dibuka publik; cakupan DACH (Jerman/Austria/Swiss), tulisan Jerman; 8 commit = proyek pribadi yang baru jalan 6 bulan.

### 7. cncf/gitjobs — REFERENSI

- **URL:** https://github.com/cncf/gitjobs
- **Lisensi:** Apache-2.0 (permisif, cocok dengan MIT).
- **Bintang / fork:** 126★ / 26 fork. Dibuat 13 Jan 2025, 288 commit.
- **Update terakhir:** 9 Nov 2026 (commit "Bump Alpine to 3.24.4", halaman `/commits/main`).
- **Stack:** Rust, PostgreSQL, HTML/JavaScript — **tidak sama** dengan stack CekLoker (Python + Next.js).
- **Fitur relevan:** job board developer-first di bawah CNCF; fitur **embed** (iframe / kartu SVG satu lowongan) yang bisa dipakai situs lain; masih beta menurut README sendiri.
- **Yang dipelajari / ditulis ulang:** pola embed kartu lowongan/perusahaan (berguna bila nanti CekLoker menyediakan widget "skor perusahaan ini" untuk ditempel di blog/komunitas); pola filter lowongan berdasarkan bahasa/teknologi.
- **Risiko:** stack Rust berarti tidak ada kode yang bisa dipakai ulang di CekLoker tanpa menulis ulang total; fokus niche open-source/developer; commit 2026 didominasi upgrade dependensi/base image (aktivitas pemeliharaan, bukan fitur).

### 8. PaulMcInnis/JobFunnel — TOLAK

- **URL:** https://github.com/PaulMcInnis/JobFunnel
- **Lisensi:** MIT.
- **Bintang / fork:** 2.198★ / 265 fork. Dibuat 25 Agu 2017, 418 commit.
- **Update terakhir:** **repo diarsipkan (read-only) 10 Des 2025.** Pernyataan maintainer di README: job board modern sudah memakai anti-automation agresif; membangun ulang di atas Playwright "technically possible, but too slow, fragile, and operationally complex" untuk pengalaman CLI satu tembakan — jadi diarsipkan sebagai artefak historis/educational.
- **Alasan TOLAK:** arsip = tidak ada perbaikan saat board berubah layout atau memblokir. Nilai sisanya hanya historis: pola dedup (master CSV + block-list + duplicates-list), pola delay sopan ("Respectful Delaying" dengan Jupyter notebook), dan pola konfigurasi YAML per locale. Ketiganya bisa dibaca sebagai ide tanpa mengadopsi kode usang (Python 3.8-era, Selenium-based, tidak ada dukungan Indonesia — hanya locale CA/US/UK/FR/DE).
- **Pelajaran dari arsip ini untuk CekLoker:** JobFunnel mati karena desainnya bergantung pada HTML statis + asumsi board tidak melawan. CekLoker harus mendesain adapter agar 1 sumber mati tidak mematikan produk (sudah diantisipasi ARCHITECTURE.md §5) — dan jangan membangun di atas asumsi "board akan tetap sama".

### 9. inigo99/jobradar — TOLAK adopsi kode (AGPL) / REFERENSI IDE saja

- **URL:** https://github.com/inigo99/jobradar
- **Lisensi:** **AGPL-3.0** — ⚠️ **TIDAK BOLEH disalin ke proyek MIT.** AGPL adalah copyleft kuat: bila CekLoker memakai kode ini lalu menjalankan layanannya di jaringan (website), CekLoker wajib menawarkan source code versi yang diubah itu ke pengguna — dan kewajiban itu menular ke proyek yang digabungkan. Itu bertentangan dengan rencana MIT CekLoker (Fase 5). Baca dan pelajari idenya; jangan salin satu fungsi pun.
- **Bintang / fork:** 1★ / 0 fork. Dibuat 8 Sep 2026, 117 commit, 9 rilis, paket PyPI `jobradar-cv`.
- **Update terakhir:** tidak terverifikasi tanggal pasti hari ini.
- **Stack:** Python 3.10, FastAPI, SQLite, Docker Compose, Playwright opsional.
- **Ide yang layak ditiru (tulis ulang dari nol, dengan kata-kata sendiri):**
  - Dedup 3 lapis: by id, fingerprint company+title, dan overlap judul — "never by substring" (aturan dedup yang tajam).
  - `jobradar sweep` — perintah untuk memensiunkan iklan yang sudah tutup (persis `check_active` CekLoker).
  - "Filtered out" — lowongan yang tersaring tetap ditampilkan beserta alasannya (transparansi yang sejalan dengan prinsip skor CekLoker: tidak ada keputusan tanpa bukti yang bisa diklik).
  - Aturan "lowongan adalah teks pihak ketiga: model bahasa yang membacanya tidak boleh menerima perintah darinya" + flag iklan yang mencoba memerintah AI — relevan untuk Fase 4 (ML/sentimen).
  - Estimasi gaji dari band keluarga pekerjaan bila gaji tidak dicantumkan, selalu dilabeli "estimasi" — sejalan dengan aturan "jangan tebak tanggal" di ARCHITECTURE.md §4.

### 10. nishanthrajkumarr/dossier (fork AienTech/dossier) — TOLAK adopsi kode (AGPL) / REFERENSI IDE saja

- **URL:** https://github.com/nishanthrajkumarr/dossier (fork; upstream: AienTech/dossier)
- **Lisensi:** **AGPL-3.0** — ⚠️ aturan yang sama seperti jobradar: **jangan salin kode ke proyek MIT**. README upstream menyatakan eksplisit: "if you run a changed version for others over a network, you must offer them its source code."
- **Bintang / fork:** 0★ / 0 fork pada fork ini; upstream ~3.509★ / 744 fork menurut artikel ulasan ReviewRamble 31 Okt 2026 (**angka upstream ini TIDAK terverifikasi di halaman repo hari ini** — K-G3).
- **Update terakhir:** tidak terverifikasi tanggal pasti hari ini.
- **Stack:** Next.js 16, PostgreSQL 18, Prisma, Docker Compose + Caddy — stack frontend yang paling dekat dengan rencana CekLoker (Next.js + Postgres + Caddy ada di ARCHITECTURE.md §6–§7).
- **Ide yang layak ditiru (tulis ulang dari nol):**
  - Auth single-user yang benar: 1 password, hash argon2id (CekLoker v1 juga single-user — jangan meniru "tanpa auth" dari ai-job-tracker).
  - `PRIVACY.md` yang merinci, per tugas, data apa yang dikirim ke model AI — pola dokumentasi privasi yang wajib ditiru CekLoker saat masuk Fase 4.
  - Job agent harian yang "tidak pernah mengirim/melamar" (hanya menyiapkan draft untuk ditinjau) — batas etis yang sama dengan yang harus dipegang CekLoker.
  - Pencarian lowongan lewat API resmi berbayar (JSearch, Adzuna) sebagai alternatif scraping — opsi yang patut dipertimbangkan bila Glints/JobStreet memblokir (lihat [Jebakan](#jebakan-yang-harus-dihindari)).
- **Risiko:** AGPL (di atas); fork ini 0★ dan isinya salinan upstream — jangan jadikan acuan utama, rujuk upstream bila perlu; antarmuka Inggris saja; desktop-only.

---

## Library pendukung (bukan repo kandidat — dependensi yang wajar dipakai)

Lisensi di bawah ini **terverifikasi lewat artikel perbandingan yang memeriksa file LICENSE
masing-masing proyek (webscrapingapi.com, dicek 6 Nov 2026; dan daftar terverifikasi
BeQuite)** — bukan dari halaman repo langsung hari ini, jadi ditulis sebagai sekunder.
Semuanya permisif dan cocok dengan MIT:

| Library | Lisensi | Peran di CekLoker |
|---------|---------|-------------------|
| [Playwright](https://github.com/microsoft/playwright) (Python) | Apache-2.0 | Browser automation untuk halaman karier JS-heavy (sudah di ARCHITECTURE.md §3). Dipakai HANYA bila `httpx` + HTML statis tidak cukup. |
| [Beautiful Soup 4](https://www.crummy.com/software/BeautifulSoup/) | MIT | Parser HTML — pasangan `httpx` untuk adapter Glints/JobStreet. |
| [Scrapy](https://github.com/scrapy/scrapy) | BSD-3-Clause | Framework crawl bila volume scraping membesar (Fase 2+). TIDAK dipakai di v1: terlalu berat untuk adapter per-sumber yang sederhana; `httpx` + BS4 + Playwright cukup. |
| [httpx](https://github.com/encode/httpx) | BSD-3-Clause | HTTP client async untuk semua adapter (pengganti `requests` di arsitektur baru). |
| [curl_cffi](https://github.com/lexiforest/curl_cffi) | MIT | Meniru TLS fingerprint browser. ⚠️ **Hanya bila terpaksa dan setelah grill ulang**: fungsinya adalah mengelabui deteksi bot — bertentangan dengan prinsip sopan §8 bila dipakai untuk bypass. Jangan jadikan default. |

---

## Konflik verifikasi (K-G)

Nomor konflik dari riset ini. "Terselesaikan" = diputuskan berdasarkan bukti yang ada;
"butuh jawaban Giga" = keputusan ada di tangan Giga.

| ID | Konflik / klaim bertentangan | Bukti primer | Status |
|----|------------------------------|--------------|--------|
| K-G1 | jobdrop: jumlah sumber = 28 (judul repo) vs 33 (README) vs 21 (commit v2.4.0 "TrueUp as 21st source") | Halaman repo + halaman commit jobdrop, 15 Nov 2026 | **Terselesaikan:** klaim cakupan tidak dipercaya; jobdrop turun ADOPSI → REFERENSI. Menghitung sendiri jumlah scraper tidak dilakukan (di luar riset ini — tim adapter bisa menghitung saat implementasi). |
| K-G2 | omkarcloud/glassdoor-scraper: "unlimited free" di README vs distribusi yang sama dijual di RapidAPI (1.000 panggilan/bulan gratis, selebihnya berbayar) | Halaman repo (README §"Exploring Parameters") | **Terselesaikan:** klaim "unlimited" tidak dikutip; repo dinilai dari umur + bintang + commit saja → REFERENSI. |
| K-G3 | dossier: bintang upstream ~3.509 (artikel ReviewRamble, 31 Okt 2026) tidak bisa diverifikasi di halaman repo fork yang dibuka (0★) | Halaman fork nishanthrajkumarr/dossier; artikel sekunder | **Terselesaikan:** angka upstream ditulis sebagai "menurut artikel ulasan, tidak terverifikasi hari ini". Bila butuh angka pasti, buka halaman upstream AienTech/dossier langsung. |
| K-G4 | Tanggal update terakhir 5 repo (jobdrop, job-scraper Ameya, ai-job-tracker, jobradar, dossier) tidak tampil di halaman commit yang dibuka hari ini | Halaman `/commits` masing-masing, 15 Nov 2026 | **Terselesaikan sebagian:** ditulis "tidak terverifikasi tanggal pasti". Dampak: kelimanya tidak bisa naik ke ADOPSI — bukti keterawatan tidak lengkap. |
| K-G5 | JobSpy: PyPI 1.1.82 (Jul 2025) vs GitHub 1.4.1 (Okt 2026) — rilis PyPI tertinggal ~15 bulan dari GitHub | README repo + ulasan jobspipe.dev 15 Sep 2026 (sekunder) | **Terselesaikan:** pin ke versi GitHub yang teruji / tunggu rilis PyPI baru; jangan asumsikan `pip install python-jobspy` memberi kode terbaru. |
| K-G6 | **Butuh jawaban Giga:** apakah memakai API berbayar resmi (Adzuna/JSearch, pola dossier) dapat diterima sebagai rencana cadangan bila Glints/JobStreet memblokir scraping — atau tetap scraping sopan saja? Biaya Adzuna/JSearch belum dicek. | — | **Butuh jawaban Giga.** |

---

## Hasil Grill

Grill ala Matt Pocock: setiap rekomendasi adopsi diinterogasi sebelum diterima.
Pertanyaan tersulit, jawaban, dan apa yang berubah karenanya.

### G1. "JobSpy 4.728★ — tapi apa buktinya masih terawat, bukan sekadar populer dulu?"

**Jawaban:** halaman `/commits/main` menunjukkan commit 27 Okt 2026 (bump dependensi),
23 Okt 2026 (rilis 1.4.1), dan rentetan perbaikan per-board sepanjang Okt 2026
(LinkedIn, Glassdoor, Indeed, ZipRecruiter, Naukri, BDJobs, Bayt). Ini bukan repo yang
ditinggalkan — perbaikannya spesifik ("fix(glassdoor): restore job search") dan merespons
perubahan board. **Lolos grill, dengan syarat** (lihat G2–G3).

### G2. "JobSpy meng-scrape LinkedIn — bukankah itu memindahkan risiko ToS ke CekLoker?"

**Jawaban:** ya, risikonya nyata dan diakui repo itu sendiri (429 LinkedIn, rate limit
Glassdoor). Grill ini mengubah rekomendasi: **JobSpy tidak dipakai untuk LinkedIn sama
sekali** di v1 — LinkedIn tetap hanya info perusahaan publik + link keluar (ARCHITECTURE.md
§5). Yang dipakai hanya Indeed (README JobSpy: "Indeed is the best scraper currently with
no rate limiting") dan Glassdoor secara hati-hati. Aturan delay 2–5 detik/domain + patuh
robots.txt dari §8 tetap berlaku di atas library ini. **Rekomendasi berubah: ADOPSI penuh →
ADOPSI TERBATAS (Indeed/Glassdoor saja).**

### G3. "Kenapa tidak tulis ulang saja semuanya — apa yang benar-benar dihemat?"

**Jawaban:** menulis ulang scraper Indeed + Glassdoor dari nol berarti menulis ulang
penanganan pagination, parsing gaji (termasuk "preserve cents and mixed k salary ranges"),
rate-limit, dan format deskripsi — pekerjaan yang sudah diuji 4.728★ pengguna dan
diperbaiki berkali-kali pada Okt 2026. Hematnya nyata: ~1–2 minggu kerja vs risiko
mewarisi dependensi yang sudah terawat. Sebaliknya, menulis ulang adapter Glints/JobStreet/
Kalibrr adalah WAJIB karena tidak ada satu pun kandidat yang memilikinya — tidak ada yang
dihemat dengan memaksakan JobSpy ke sana. **Keputusan: adopsi di mana hematnya nyata
(Indeed), tulis ulang di mana tidak ada yang bisa diadopsi (Glints/JobStreet/Kalibrr).**

### G4. "jobdrop punya 33 sumber dan flag layoff — kenapa bukan nomor 1?"

**Jawaban:** karena tiga hal yang tidak lolos grill: (a) kontradiksi jumlah sumber
(K-G1) — repo yang tidak konsisten soal isinya sendiri tidak bisa dipercaya soal
kualitas scraper-nya; (b) 4★ dan bus factor 1 — bila maintainer berhenti besok,
CekLoker mewarisi 33 scraper tanpa komunitas; (c) teknik anti-bot eksplisit
(TLS impersonation, Googlebot UA, "bypass Cloudflare WAF") — mengadopsi itu berarti
CekLoker secara sadar melawan perlindungan situs, bertentangan dengan §8.
**Rekomendasi berubah: ADOPSI → REFERENSI.** Yang diambil hanya idenya (flag layoff,
staleness filter), ditulis ulang dengan sumber berita.

### G5. "Riley-Dorrington aktif setiap hari (commit 14 Nov 2026) — kenapa cuma REFERENSI?"

**Jawaban:** karena "aktif" di sini sebagian besar adalah commit snapshot tren otomatis
dari GitHub Actions, bukan pengembangan fitur — angka 485 commit menyesatkan bila dibaca
mentah. Alasan yang lebih menentukan: (a) dataset perusahaan berlisensi CC BY-NC 4.0 —
bila CekLoker nanti komersial (Fase 5 membuka opsi berbayar murah), memakai dataset itu
adalah pelanggaran lisensi; (b) arsitekturnya (GitHub Pages + chunk gzip) tidak cocok
dengan arsitektur CekLoker. Polanya (pruning basi, deteksi anomali, worker per platform)
yang diambil — bukan kodenya. **Tetap REFERENSI; tidak naik ke ADOPSI.**

### G6. "jobradar dan dossier idenya bagus — kenapa tidak adopsi saja, kan open source?"

**Jawaban:** karena "open source" ≠ "boleh dipakai di proyek MIT". Keduanya AGPL-3.0:
bila CekLoker menyalin kode mereka dan menjalankan hasilnya sebagai website untuk orang
lain, CekLoker wajib menawarkan source code versi yang diubah — kewajiban itu menular
dan menghancurkan rencana lisensi MIT (Fase 5). Satu-satunya cara legal memakai kode AGPL
di proyek MIT adalah tidak memakainya sama sekali. **Tetap TOLAK adopsi kode; hanya
REFERENSI IDE (tulis ulang dari nol dengan kata-kata sendiri).** Ini juga alasan ADR-0007
dibuat: supaya keputusan ini tidak perlu di-grill ulang setiap kali ada kandidat AGPL baru.

### G7. "Glassdoor scraper omkarcloud klaim 'unlimited free' — kenapa tidak langsung adopsi untuk Fase 2?"

**Jawaban:** karena klaim itu bertentangan dengan distribusi yang sama di RapidAPI
(K-G2), repo baru 6 minggu dengan 6 commit, dan Glassdoor memakai Cloudflare + login wall.
Mengadopsi sekarang berarti menggantungkan kategori skor "Reputasi & ulasan" (25 poin)
pada scraper yang belum pernah membuktikan ketahanannya. **Tetap REFERENSI** — dipakai
sebagai spesifikasi endpoint saat Fase 2 tiba, lalu diuji sendiri sebelum dipercaya.

### Ringkasan perubahan akibat grill

| Repo | Sebelum grill | Sesudah grill | Pemicu |
|------|---------------|---------------|--------|
| JobSpy | ADOPSI penuh | ADOPSI TERBATAS (Indeed/Glassdoor saja) | G2 (risiko ToS LinkedIn), G3 (tidak ada Glints/JobStreet) |
| jobdrop | ADOPSI (kandidat #1) | REFERENSI | G4 (K-G1, bus factor, teknik bypass) |
| Riley-Dorrington | ADOPSI (kandidat #2) | REFERENSI | G5 (commit otomatis, CC BY-NC 4.0) |
| jobradar | REFERENSI (kode) | TOLAK adopsi kode / REFERENSI IDE | G6 (AGPL menular ke MIT) |
| dossier | REFERENSI (kode) | TOLAK adopsi kode / REFERENSI IDE | G6 (AGPL menular ke MIT) |
| glassdoor-scraper | ADOPSI (Fase 2) | REFERENSI | G7 (K-G2, umur 6 minggu) |

---

## Jebakan yang harus dihindari

1. **Lisensi ganda dalam satu repo.** Riley-Dorrington: kode MIT, data CC BY-NC 4.0.
   Selalu baca README sampai bagian lisensi — lisensi di badge GitHub hanya lisensi kode.
2. **AGPL/GPL menular ke MIT.** jobradar & dossier (AGPL-3.0): jangan salin kode apa pun,
   walau satu fungsi. Aturan lengkap di ADR-0007.
3. **Repo mati yang terlihat hidup.** JobFunnel (2.198★) diarsipkan 10 Des 2025;
   Riley-Dorrington terlihat "commit tiap hari" padahal isinya snapshot otomatis.
   Selalu buka halaman `/commits` dan baca isi commit-nya, bukan angkanya.
4. **Klaim jumlah sumber yang tidak konsisten.** jobdrop: 28 vs 33 vs 21 (K-G1).
   Hitung sendiri sebelum percaya.
5. **Klaim "unlimited free" yang berbayar di tempat lain.** omkarcloud (K-G2).
6. **Teknik bypass anti-bot = risiko ToS.** "Bypass Cloudflare WAF", Googlebot UA,
   TLS impersonation (jobdrop, curl_cffi): legal di lisensi MIT, tapi melanggar ToS
   situs target dan bertentangan dengan ARCHITECTURE.md §8. Jangan jadikan default.
7. **PyPI tertinggal dari GitHub.** JobSpy: PyPI 1.1.82 (Jul 2025) vs GitHub 1.4.1
   (Okt 2026) — K-G5. Selalu cek versi yang terinstal vs versi repo.
8. **Auto-apply / bertindak atas nama pengguna.** Repo Ameya punya mode auto-apply
   semalaman. CekLoker TIDAK melamar atas nama siapa pun — produk ini memberi informasi,
   bukan bertindak.
9. **Scraping review massal tanpa atribusi.** Untuk skor Fase 2: ambil agregat + kutipan
   singkat + link bukti (SCORING.md), jangan salin isi ulasan penuh. Hormati hak cipta
   dan privasi reviewer.
10. **"Tanpa auth" dari proyek pribadi.** ai-job-tracker memperingatkan sendiri jangan
    expose port-nya. CekLoker yang akan dibuka publik wajib auth sejak v1 (single-user,
    argon2id — pola dossier).

---

## Istilah

*(Bagian ini untuk digabungkan koordinator ke `docs/glossary.md` — JANGAN edit glossary
langsung dari tim ini.)*

| Istilah | Definisi |
|---------|----------|
| **Adopsi** | Memakai kode/library orang lain apa adanya (sebagai dependensi atau dengan menyalin) di dalam CekLoker, dengan atribusi sesuai lisensinya. Hanya boleh untuk lisensi permisif (MIT/Apache-2.0/BSD). |
| **Referensi** | Mempelajari pola, struktur, atau ide dari sebuah repo, lalu menulis ulang dengan kata-kata dan kode sendiri. Tidak menyalin kode. Berlaku untuk semua repo, termasuk yang berlisensi copyleft. |
| **Referensi ide** | Bentuk referensi yang paling ketat: hanya idenya yang diambil (mis. "dedup 3 lapis"), implementasinya ditulis dari nol. Dipakai untuk repo AGPL/GPL. |
| **Fork** | Salinan sebuah repo GitHub di bawah akun sendiri, yang riwayat commit-nya tetap terhubung ke repo asal. Fork ≠ adopsi: mem-fork tidak berarti kodenya dipakai di CekLoker. |
| **Lisensi permisif** | Lisensi yang mengizinkan kode dipakai, diubah, dan digabung ke proyek dengan lisensi lain (termasuk MIT) selama atribusi dipertahankan. Contoh: MIT, Apache-2.0, BSD. |
| **Lisensi copyleft** | Lisensi yang mewajibkan karya turunan memakai lisensi yang sama (atau setara). Contoh: GPL, AGPL. AGPL-3.0 paling ketat: kewajiban berbagi source aktif juga bila program dijalankan sebagai layanan jaringan (website). |
| **Lisensi ganda (dual-license)** | Satu repo memakai dua lisensi berbeda untuk bagian berbeda (mis. kode MIT + dataset CC BY-NC 4.0). Masing-masing bagian harus dipatuhi sendiri-sendiri. |
| **ToS (Terms of Service)** | Syarat layanan sebuah situs. Banyak job board melarang akses otomatis/scraping di ToS-nya. Melanggar ToS bukan otomatis melanggar hukum, tapi situs boleh memblokir dan (untuk layanan publik) berisiko reputasi/hukum. |
| **ATS (Applicant Tracking System)** | Sistem yang dipakai perusahaan untuk menampung lowongan di halaman kariernya sendiri, mis. Greenhouse, Lever, Ashby, Workday. ATS biasanya punya API publik/ semi-publik — lebih stabil di-scrape daripada job board. |
| **Staleness / lowongan basi** | Lowongan yang masih tayang tapi sebenarnya sudah terisi/tidak aktif (tayang >30–90 hari tanpa perubahan). CekLoker memangkasnya dari daftar aktif — lihat "ghost job" di SCORING.md. |
| **Dedup (deduplikasi)** | Menghapus lowongan yang sama yang muncul di beberapa sumber, memakai fingerprint (mis. hash dari URL + judul + perusahaan). |
| **Ghost job** | Lowongan yang tayang berbulan-bulan tanpa ada hiring — sinyal Red Flag (−10) di SCORING.md. |
| **TLS impersonation** | Teknik meniru "sidik jari" TLS browser asli (mis. Chrome) agar server mengira request datang dari browser manusia. Tergolong teknik mengelabui deteksi bot. |
| **Bus factor** | Jumlah orang yang harus "tertabrak bus" sebelum proyek berhenti terawat. Bus factor 1 = satu maintainer; bila ia berhenti, proyek mati. |
| **Snapshot tren** | Commit otomatis harian yang hanya mencatat angka (mis. jumlah lowongan per platform). Bukan pengembangan fitur — jangan dibaca sebagai bukti repo aktif dikembangkan. |
| **Atribusi** | Pencantuman nama pembuat + lisensi asal saat memakai kode orang lain, sesuai syarat lisensi (mis. di README / file NOTICE). |
| **Arsip (archived repo)** | Repo yang dikunci pemiliknya menjadi read-only: tidak ada commit, issue, atau PR baru. Kode tetap bisa dibaca, tapi tidak akan diperbaiki lagi. |

---

*Disusun 15 Nov 2026 oleh Tim Referensi GitHub, Fase 1 CekLoker. Tidak ada kode yang
disalin dalam penyusunan dokumen ini. Keputusan kebijakan: ADR-0007.*
