# Laporan Konsolidasi Akhir — Fase 1 CekLoker

**Status: SELESAI (riset + adapter + flag engine rule-based, lokal saja).**
**Tanggal:** 15 Nov 2026. **Bahasa:** Indonesia.
**Tidak ada push / PR / merge ke GitHub.** Semua hasil lokal di `~/workspace/cekloker/`.
Repo remote `Gigajn/cekloker` tetap di main @ `8ec8d4dd` (Fase 0); parent yang
memverifikasi lalu push hasil Fase 1 ini.

Metode: 4 tim paralel (Job-Board, Direct, Sosial & Reputasi, Referensi GitHub)
→ tiap tim di-grill ala Matt Pocock (grill-with-docs) + verifikasi ke sumber
primer → koordinator membaca keempat laporan, memeriksa sendiri file + test
di VM ini, menyatukan duplikasi kode, lalu menulis laporan ini.
Konflik antar tim diberi nomor global **K1–K12** (bukan nomor tim K-JB/K-D/K-S/K-G
— pemetaannya ada di §3).

---

## 1. Ringkasan per tim (hasil + verifikasi koordinator)

Semua angka test di bawah **dijalankan ulang oleh koordinator di VM ini**,
bukan sekadar mengutip laporan tim.

| Tim | Yang diserahkan | Test (dijalankan ulang koordinator) |
|---|---|---|
| **Job-Board** | Riset Glints/JobStreet/Kalibrr/Indeed + adapter `glints`, `kalibrr` (aktif), `jobstreet`, `indeed` (stub `SourceNotPermittedError`) + `base.py` + `parsers.py` + ADR-0001, ADR-0002 | `cd packages/scraper-core && .venv/bin/python -m pytest -q` → **84 passed** (32 milik tim ini + 52 tim Direct), Python 3.12.3, pytest 9.2.0 |
| **Direct** | Adapter `career_page` (Greenhouse/Lever/Ashby/Workable/dll + JSON-LD) + `social_company` (IG lead, tanpa fetcher LinkedIn) + 10 perusahaan uji + ADR-0003, ADR-0004 | Termasuk dalam 84 test di atas (52 test tim ini, 0 gagal — dijalankan 2x oleh tim, 1x lagi oleh koordinator setelah penyatuan, tetap 84 lolos) |
| **Sosial & Reputasi** | `social_signals.py` (6 fungsi rule-based) + pemetaan sinyal ke SCORING.md + ADR-0005, ADR-0006 | `python3 -m unittest discover -s packages/flag-engine/tests` → **45 test, 45 lolos, 0 gagal** (unittest stdlib; pytest tidak tersedia untuk paket ini) |
| **Referensi GitHub** | 10 repo kandidat + rekomendasi adopsi + ADR-0007 (kebijakan adopsi vs tulis ulang) | Riset saja, tanpa kode — diverifikasi dari halaman GitHub masing-masing (15 Nov 2026) |

**Total: 129 test lolos, 0 gagal** (84 scraper-core + 45 flag-engine).
Tidak ada satu pun test live (sengaja — tidak ada request massal ke situs
sumber; semua test memakai fixture buatan).

---

## 2. Kesepakatan antar tim (yang disetujui semua pihak)

1. **LinkedIn DITUNDA penuh — suara bulat 4/4 tim.** Job-Board (§2.5),
   Direct (ADR-0004, ToS §8.2 berlaku 3 Nov 2025), Sosial (bukan sumber
   reputasi), GitHub (JobSpy LinkedIn dimatikan). LinkedIn hanya boleh
   jadi info perusahaan publik yang dibaca manual — bukan adapter.
2. **JobStreet dilarang ToS — suara bulat 2/2 tim yang menyentuhnya.**
   Job-Board (K-JB1) dan Sosial (K-S2) sama-sama menemukan klausul (d)
   SEEK melarang agregasi. JobStreet TUNDA untuk lowongan DAN ulasan.
3. **Ulasan tidak boleh di-scrape otomatis.** Sosial membuktikan tidak
   satu pun sumber ulasan mengizinkan pengambilan otomatis (Glassdoor,
   JobStreet, Google, Reddit, Kaskus). Fase 2 memakai entri manual +
   RSS berita + Places API (rating + jumlah saja).
4. **Instagram = lead, bukan lowongan.** Direct dan Sosial sepakat: IG
   hanya menghasilkan lead yang diverifikasi manual; `job_posted_at`
   dari IG selalu `None`.
5. **Sentimen ML ditunda ke Fase 4.** Sosial mempertahankannya dengan
   gerbang eksplisit (200 contoh berlabel + precision/recall); alasan
   hukum ikut menguatkan (Reddit & JobStreet melarang latih model dari
   data mereka).
6. **Stdlib-only untuk scraper-core v1.** Semua data v1 adalah JSON
   tersemat (JSON-LD / `__NEXT_DATA__` / feed ATS), jadi `json` + `re` +
   `urllib` cukup — nol dependensi runtime, Docker image kecil.

---

## 3. Konflik verifikasi global (K1–K12)

| ID | Konflik (tim asal) | Keputusan koordinator |
|---|---|---|
| **K1** | Tim GitHub merekomendasikan JobSpy sebagai library live untuk **Indeed/Glassdoor** — padahal Job-Board (K-JB5) dan Sosial (K-S1, K-S10) membuktikan scraping Indeed & Glassdoor dilarang ToS tanpa izin tertulis. Memakai library tidak mengubah ToS. | **DISELESAIKAN: JobSpy turun jadi REFERENSI** (pola multi-sumber + parser gaji/tanggal). Dilarang dipakai live untuk Indeed/Glassdoor/LinkedIn di v1. Nilai sisanya: contoh struktur adapter + parsing; bila nanti ada sumber yang mengizinkan, potongan kodenya boleh dipakai ulang dengan atribusi (MIT). Lihat D12. |
| **K2** | JobStreet ToS (K-JB1 + K-S2): apakah larangan agregasi juga melarang adapter lowongan? Sosial meneruskan ke koordinator. | **DISELESAIKAN: ya, berlaku.** JobStreet TUNDA untuk lowongan dan ulasan. Alternatif: SEEK API / izin tertulis PT JobStreet Indonesia (D6). |
| **K3** | Total skor: penjumlahan mentah (ARCH §5) vs **total ternormalisasi** (Sosial G-2, ADR-0005). Penjumlahan mentah membuat perusahaan bagus yang baru terukur 2 kategori langsung Red (25/100). | **DISELESAIKAN di pihak desain, BUTUH PERSETUJUAN GIGA (D7).** Koordinator menyetujui usulan normalisasi (`100 × perolehan / cap terukur`, label butuh ≥2 kategori penentu) sebagai usulan resmi — tapi ini menyimpang dari ARCH §5, jadi tidak diberlakukan diam-diam sebelum Giga setuju. |
| **K4** | Model data ARCH §4 mengasumsikan `signals.evidence_text` selalu terisi — Google Places API Policies **melarang menyimpan teks ulasan** (K-S3). | **DISELESAIKAN:** `evidence_text` boleh null; untuk sumber `google_places` wajib kosong (hanya rating, jumlah, `place_id`, tautan). Dicatat di ADR-0006. Skema DB Fase 2 wajib mengikuti ini. |
| **K5** | Tim Job-Board melaporkan "tabrakan penomoran ADR" karena ADR-0007 sudah ada saat mereka membuat ADR-0001/0002. | **BUKAN tabrakan — DISELESAIKAN tanpa renumber.** Nomor 0001–0007 semuanya unik; hanya urutan pembuatannya yang tidak berurutan (tim GitHub selesai duluan). Tidak ada file yang ditimpa. |
| **K6** | Dua definisi `RawJob` + dua pohon adapter: `scraper_core/` (Job-Board) vs `adapters/` di root paket (Direct) — duplikat yang akan bercabang. | **DISELESAIKAN oleh koordinator (lihat §5).** Satu `RawJob` bersama di `scraper_core/base.py`; `career_page.py` + `social_company.py` dipindah ke `scraper_core/adapters/`; direktori `adapters/` lama dihapus; test tetap 84 lolos. |
| **K7** | ADR-0002 memutuskan `posted_at` punya flag kepastian — tapi adapter Glints/Kalibrr membuangnya (`posted_at, _ = parse_posted_at(...)`) dan `RawJob` tidak punya field-nya. | **DISELESAIKAN oleh koordinator (lihat §5).** Field `posted_at_certain` ditambahkan ke `RawJob` dan diteruskan dari kedua adapter. |
| **K8** | Definisi fingerprint berbeda antar tim: Job-Board 32 karakter (judul + `company_norm` + lokasi) vs Direct 16 karakter vs GitHub "hash URL + judul + perusahaan". | **DISELESAIKAN sebagian.** `job_fingerprint` Direct disamakan panjangnya (32) dengan `RawJob.fingerprint`. URL sengaja TIDAK masuk fingerprint (supaya repost terdeteksi) — definisi GitHub ditolak untuk bagian URL-nya. Sisa kecil: `job_fingerprint` memakai nama perusahaan mentah, `RawJob.fingerprint` memakai `company_norm` — normalizer Fase 1-lanjutan wajib memilih satu (dicatat di §8). |
| **K9** | Tiga asumsi Glints/Kalibrr belum diuji live (Job-Board G6): sitemap Glints berisi URL lowongan? JSON-LD `JobPosting` ada di halaman detail? Parameter pencarian Kalibrr `?query=` bekerja? | **TERBUKA — uji live wajib sebelum klaim "jalan".** Daftar uji di §8. Kalibrr dipastikan pagination-nya tidak jalan (±15 hasil/query, uji 2026-07-11) — jadi v1 hanya pencarian kata kunci. |
| **K10** | Makna tanggal tiap ATS belum pasti (K-D1 Greenhouse `first_published` hanya di endpoint satu job; K-D2 Lever `createdAt` tidak ada di README resmi; K-D3 Ashby `publishedAt` = "last published"). | **DISELESAIKAN sebagian di kode** (adapter memanggil endpoint satu job bila perlu; membaca field bila ada, `None` bila tidak). Perlu uji live (§8). |
| **K11** | K-D4 (board kosong ambigu), K-D5 (GoTo ID "via Lever" vs GoTo AS = Workday — dua perusahaan berbeda), K-D6 (dokumen resmi Meta menolak dibaca, HTTP 403). | **TERBUKA.** Jangan simpulkan apa pun dari board kosong; jangan campur GoTo ID dengan GoTo AS; IG butuh token aplikasi sendiri untuk uji live (D11). |
| **K12** | Harga/aturan akses dari sumber sekunder, belum terverifikasi primer: X pay-per-use US$0,005/bacaan (K-S4), Reddit butuh approval + status komersial belum jelas (K-S5), harga Google Places (K-S9), biaya Adzuna/JSearch (K-G6). | **TERBUKA — jangan pakai untuk anggaran final.** X hanya konteks; Reddit tidak dipakai sampai D9 dijawab; harga Places dicek di konsol sebelum Fase 2; Adzuna/JSearch butuh D10. |

Konflik tim yang sudah terselesaikan di dalam tim dan TIDAK perlu dibawa ke
sini (dicatat saja): K-JB2 (GraphQL Glints ditolak), K-JB3 ("no-auth" ≠ izin,
endpoint Chalice tidak dipakai), K-JB4 (Kalibrr full crawl ditunda), K-S6
(Kaskus = konteks manual tanpa poin), K-S7 (Putusan MK tidak melemahkan
aturan anti-fitnah), K-S8 (ambang 4,0/20 = heuristik, wajib kalibrasi Fase 2),
K-G1 (klaim 28 vs 33 vs 21 sumber jobdrop tidak dipercaya), K-G2 ("unlimited
free" glassdoor-scraper tidak dikutip), K-G3 (bintang dossier upstream tak
terverifikasi), K-G4 (5 repo tanpa tanggal update pasti → tak bisa naik ke
ADOPSI), K-G5 (PyPI JobSpy tertinggal ~15 bulan dari GitHub — pin ke GitHub).

---

## 4. Hasil grill — keputusan yang BERUBAH karena di-grill

| # | Keputusan awal | Setelah grill | Pemicu |
|---|---|---|---|
| G-A | JobStreet sumber utama Fase 1 (ARCH D2) | **JobStreet TUNDA, diganti Kalibrr** | ToS SEEK + robots.txt primer (K-JB1) |
| G-B | `check_active` mengembalikan False bila gagal ambil | Gagal teknis → `unknown`, bukan `closed`; hanya 404/penanda tutup = False | Grill G2/G3 Job-Board — salah label = lowongan aktif hilang dari daftar |
| G-C | `posted_at` satu angka tanggal | `posted_at` + flag `posted_at_certain`; "1 bulan lalu" = perkiraan ±30 hari | Grill G3 — tanggal relatif tidak boleh tampil sebagai tanggal pasti |
| G-D | GraphQL Glints / endpoint Chalice JobStreet sebagai jalur | **Dua-duanya ditolak** ("no-auth" ≠ izin; skema tak terdokumentasi) | Grill K-JB2/K-JB3 |
| G-E | IG = sumber lowongan | **IG = lead saja**, `job_posted_at: None` | Grill G3 Direct — tanggal posting IG ≠ tanggal buka |
| G-F | LinkedIn "scraper hati-hati" | **LinkedIn dibatalkan total** | Grill G4 Direct + ToS §8.2 |
| G-G | Skor = penjumlahan mentah (ARCH §5) | **Total ternormalisasi** + label butuh ≥2 kategori penentu | Grill G-2 Sosial — perusahaan baru yang bagus tidak boleh langsung Red |
| G-H | JobSpy ADOPSI penuh; jobdrop ADOPSI (calon #1); Riley ADOPSI | JobSpy → REFERENSI (K1); jobdrop → REFERENSI (bus factor 1, TLS impersonation); Riley → REFERENSI (commit otomatis + CC BY-NC) | Grill G1–G5 GitHub |
| G-I | jobradar & dossier REFERENSI kode | **TOLAK adopsi kode (AGPL-3.0)** — referensi ide saja | Grill G6 GitHub — AGPL menular ke rencana MIT |
| G-J | Ulasan = "scraper ulasan" | **Ulasan = entri manual + RSS + Places API** | Grill Sosial — tidak satu pun sumber ulasan mengizinkan otomasi |
| G-K | 1 ulasan ekstrem bisa mengubah skor | 1 ulasan dihitung sekali per cluster; keluhan butuh ≥3 ulasan; ghost job butuh ≥3 lowongan basi + bukan evergreen; berita butuh ≥2 media + ≤12 bulan | Grill G-3/G-6/G-7 Sosial |
| G-L | "Staff administrasi" / "tidak ada biaya" bisa memicu red override | Pola fee mensyaratkan konteks bayar + pelindung negasi (jendela 25 karakter) | Grill G-5 Sosial + regresi test |

---

## 5. Pekerjaan penyatuan koordinator (dilakukan sendiri, bukan klaim tim)

1. **Satu `RawJob` bersama.** `scraper_core/base.py` diperluas dengan field
   ATS (`platform`, `platform_job_id`, `job_key`, `department`,
   `repost_hint`, `raw`) + `posted_at_certain`. Definisi lokal `RawJob` /
   `JobSourceAdapter` di `career_page.py` dihapus; file itu kini impor
   dari `..base`.
2. **Satu pohon adapter.** `career_page.py` + `social_company.py` dipindah
   dari `packages/scraper-core/adapters/` ke
   `packages/scraper-core/scraper_core/adapters/`; direktori lama dihapus;
   registry diperluas (`DIRECT_ADAPTERS = (CareerPageAdapter,)`).
   `discover()` CareerPageAdapter disamakan signature-nya dengan kontrak
   base (parameter opsional).
3. **Flag kepastian tanggal diteruskan.** Glints + Kalibrr kini mengisi
   `posted_at_certain` dari `parse_posted_at` (sebelumnya dibuang).
   Ini menutup K7 — ADR-0002 kini benar-benar diimplementasikan.
4. **Fingerprint disamakan.** `job_fingerprint` kini 32 karakter, sama
   dengan `RawJob.fingerprint` (K8, sebagian).
5. **User-Agent jujur.** `career_page.py` sempat memakai kontak email
   palsu (`admin@cekloker.id`) — diganti memakai helper `user_agent()`
   dari base (kontak lewat env `CEKLOKER_CONTACT`).
6. **Kebersihan repo.** `.pytest_cache/` ditambahkan ke `.gitignore`
   (muncul dari test run); `.venv/` sudah ter-ignore.
7. **Test dijalankan ulang setelah penyatuan:** scraper-core **84 passed**,
   flag-engine **45 passed** — sama seperti sebelum penyatuan, tidak ada
   regresi. (Perintah persis di §1.)

---

## 6. Tabel keputusan akhir per sumber

| Sumber | Keputusan | Alasan singkat |
|---|---|---|
| Glints | **BANGUN** | Sitemap + halaman publik JSON-LD; robots tidak melarang halaman detail. Asumsi sitemap/JSON-LD belum uji live; ToS penuh belum dibaca (gate rilis, D8). |
| Kalibrr | **BANGUN (terbatas)** | `__NEXT_DATA__` + `activationDate` ISO terverifikasi; pagination tidak jalan (±15 hasil/query) → v1 hanya pencarian kata kunci. ToS penuh belum dibaca (D8). |
| JobStreet | **TUNDA (stub)** | ToS SEEK (d) + (27) dan robots.txt melarang. Alternatif: SEEK API / izin tertulis (D6). |
| Indeed | **TUNDA (stub)** | ToS §D.21 + robots melarang halaman detail; Publisher API mati ~2023. Alternatif: Adzuna API, ATS langsung (D10). |
| LinkedIn | **TUNDA penuh** | ToS §8.2 melarang scraping/bot; penegakan meningkat 2026 (Proxycurl tutup). Hanya info perusahaan publik manual. |
| Greenhouse | **BANGUN** | Feed JSON publik tanpa auth, dokumen resmi; `first_published` hanya di endpoint satu job (K10). |
| Lever | **BANGUN** | Feed publik tanpa auth; satu-satunya vendor yang eksplisit menulis "may be scraped by third parties". `createdAt` perlu uji live (K10). |
| Ashby | **BANGUN** | API publik tanpa auth; `publishedAt` = "last published", bukan pertama dibuka (K-D3 — sudah ditangani). |
| Workable | **BANGUN** | Endpoint publik di Help resmi; robots.txt mengizinkan semua. |
| SmartRecruiters / Recruitee / Personio / Bamboohr | **BANGUN (dengan catatan)** | Dari sumber sekunder — perlu uji live sebelum produksi. |
| Workday | **TUNDA (stub)** | Tidak ada pola slug yang bisa ditebak; adapter raise `NotImplementedError`. |
| Halaman karier custom (JSON-LD) | **BANGUN** | JSON-LD `JobPosting` schema.org; Traveloka sudah dibaca langsung. |
| Instagram perusahaan | **BANGUN (lead saja)** | Business Discovery API resmi; butuh token aplikasi Meta sendiri (D11); tanpa token tak bisa uji live. |
| Glassdoor (ulasan) | **TUNDA otomatis → entri manual** | ToS §4.3(16) melarang scraping; tidak ada API publik sejak 2021. |
| JobStreet (ulasan) | **TUNDA otomatis → entri manual** | ToS butir (d)/(u) melarang agregasi/scraping. |
| Google Review | **BANGUN (rating + jumlah saja)** | Places API; teks ulasan dilarang disimpan → `evidence_text` wajib kosong (K4). Harga belum terverifikasi primer (K12). |
| Google News RSS | **BANGUN (Fase 2)** | Judul + tautan saja; sinyal berita butuh ≥2 media + ≤12 bulan. |
| X / Twitter | **Konteks manual saja** | Pay-per-use sejak 6 Feb 2026 (US$0,005/bacaan, tanpa free tier baru) — harga sekunder, belum cek konsol. |
| Reddit | **TUNDA** | Wajib approval + status komersial belum jelas (D9). |
| Kaskus | **Konteks manual saja** | ToS melarang eksploitasi komersial; tanpa poin, tanpa simpan isi/username. |
| JobSpy (speedyapply) | **REFERENSI** | MIT, terawat (commit 27 Okt 2026). Live untuk Indeed/Glassdoor/LinkedIn dilarang (K1). Dipakai sebagai pola + parser. |
| job-board-aggregator (Riley-Dorrington) | **REFERENSI** | Pola klien ATS + pruning basi + deteksi anomali. Dataset CC BY-NC 4.0; "commit harian" sebagian snapshot otomatis. |
| jobdrop (kbwhodat) | **REFERENSI** | Ide flag layoff + staleness filter. Klaim sumber bertentangan (28 vs 33 vs 21); bus factor 1; teknik bypass anti-bot. |
| glassdoor-scraper (omkarcloud) | **REFERENSI** | Klaim "unlimited free" bertentangan dengan RapidAPI berbayar; repo baru 6 minggu, 2★. |
| job-scraper (Ameya) / ai-job-tracker / gitjobs | **REFERENSI** | Pola yang relevan; tanggal update terakhir 3 dari antaranya tidak terverifikasi hari ini (K-G4). |
| JobFunnel (PaulMcInnis) | **TOLAK** | Diarsipkan 10 Des 2025 oleh maintainernya sendiri. |
| jobradar / dossier | **TOLAK adopsi kode** | AGPL-3.0 menular ke rencana MIT — referensi ide saja. |

---

## 7. Keputusan yang masih butuh Giga (D6–D12)

Melanjutkan D1–D5 di ARCHITECTURE.md — jangan ulangi nomor lama.

| ID | Pertanyaan | Opsi yang diajukan koordinator |
|---|---|---|
| **D6** | JobStreet keluar dari sumber utama (diganti Kalibrr). Ajukan izin tertulis / SEEK API ke JobStreet, atau lanjut tanpa JobStreet? | (a) Lanjut tanpa JobStreet dulu, ajukan SEEK API belakangan; (b) ajukan izin sekarang sebelum Fase 1-lanjutan. Koordinator merekomendasikan (a) — Glints + Kalibrr + ATS sudah cukup untuk uji 500 lowongan. |
| **D7** | Setujui total skor **ternormalisasi** (ADR-0005) yang menyimpang dari ARCH §5? | (a) Ya, berlakukan normalisasi + label butuh ≥2 kategori penentu; (b) Tidak, tetap penjumlahan mentah. Koordinator merekomendasikan (a) — penjumlahan mentah terbukti membuat perusahaan baru yang bagus langsung Red. |
| **D8** | ToS Glints + Kalibrr belum dibaca penuh (K-JB6, K-JB8) — siapa yang baca sebelum rilis publik? | Gate rilis: ToS dibaca langsung sebelum publik; sampai dibaca, adapter jalan atas asumsi pemakaian sopan + risiko sedang. |
| **D9** | Reddit: ajukan approval sebagai proyek non-komersial pribadi sekarang, atau tunda ke Fase 4? (K-S5) | (a) Ajukan sekarang atas nama Giga pribadi; (b) tunda ke Fase 4. Koordinator merekomendasikan (b) — Reddit bukan penentu Fase 2. |
| **D10** | API berbayar resmi (Adzuna/JSearch) boleh jadi rencana cadangan bila Glints/JobStreet diblokir? (K-G6) | (a) Ya, cek biayanya dulu; (b) Tidak, tetap scraping sopan saja. Biaya belum dicek — jangan putuskan sebelum ada angka. |
| **D11** | Akun/aplikasi Meta untuk token Instagram Graph API — atas nama siapa (Giga pribadi / badan usaha nanti)? Tanpa ini modul IG tak bisa diuji live. | Tentukan identitas aplikasi sebelum uji live IG. |
| **D12** | JobSpy diturunkan jadi REFERENSI saja (tanpa live Indeed/Glassdoor/LinkedIn) — setuju, atau tetap mau coba library live dengan risiko ToS? (K1) | Koordinator merekomendasikan setuju (REFERENSI saja). |

---

## 8. Yang BELUM selesai / masih berisiko

**Uji live yang wajib dilakukan sebelum klaim apa pun "jalan"** (belum satu pun
dilakukan — sengaja, bukan kelalaian; tidak ada request live massal di Fase 1):
1. Glints: ambil `sitemap_index.xml` — apakah berisi URL lowongan?
2. Glints: ambil 1 halaman detail — apakah JSON-LD `JobPosting` ada?
3. Kalibrr: 1 pencarian `?query=` — apakah parameter bekerja + berapa hasil?
4. ATS: 1 board live per platform (Greenhouse, Lever, Ashby, Workable) —
   cek `first_published` / `createdAt` / `publishedAt` di data nyata.
5. 10 perusahaan uji Direct (Tokopedia, GoTo, Bukalapak, Xendit, Ruangguru,
   BCA, Telkom, Blibli, DANA, Traveloka) — hanya Traveloka yang halamannya
   dibaca langsung; 9 lainnya perlu uji live. Perhatian K-D5: jangan campur
   GoTo Indonesia dengan GoTo AS (Workday).
6. Instagram: uji Business Discovery dengan token aplikasi sendiri (butuh D11).

**Risiko yang masih terbuka:**
- **ToS Glints/Kalibrr belum dibaca penuh** (K-JB6/K-JB8) — adapter aktif
  berjalan atas asumsi; gate sebelum rilis publik (D8).
- **Situs bisa berubah layout / memblokir kapan saja.** Arsitektur sudah
  menahan ini (adapter mati lewat `enabled=False`, job lama jadi `unknown`,
  worker berhenti saat 403/429, dilarang memutar proxy) — tapi tetap risiko
  nyata, bukan teori.
- **Ambang rubrik adalah heuristik** (K-S8: rating ≥4,0 dari ≥20 ulasan
  tidak punya standar eksternal) — wajib dikalibrasi di Fase 2 pada
  50 perusahaan pertama, lalu direvisi via ADR.
- **Deteksi ulasan palsu diakui tidak bisa** (Sosial G-1) — dicatat sebagai
  risiko terbuka, bukan diklaim.
- **Harga X / Reddit / Google Places dari sumber sekunder** (K12) — jangan
  pakai untuk anggaran final.
- **Fingerprint ganda kecil** (K8): `job_fingerprint` memakai nama
  perusahaan mentah, `RawJob.fingerprint` memakai `company_norm` —
  normalizer Fase 1-lanjutan wajib memilih satu.
- **Belum ada API, web, atau database.** Fase 1 ini hanya scraper-core +
  flag-engine + riset. FastAPI + Next.js + Postgres (ARCH §3, §6) belum
  dibangun — itu Fase 1-lanjutan.
- **Skor ternormalisasi belum berlaku** sampai D7 dijawab Giga.
- **JobSpy di PyPI tertinggal ~15 bulan dari GitHub** (K-G5) — bila suatu
  hari dipakai sebagai library, pin ke versi GitHub yang teruji, bukan
  `pip install` buta.

---

## 9. Daftar file yang dibuat / diubah (lokal, belum di-push)

**Dokumen riset + konsolidasi:**
- `docs/fase1-riset-jobboard.md`, `docs/fase1-riset-direct.md`,
  `docs/fase1-riset-sosial.md`, `docs/github-references.md`
- `docs/fase1-konsolidasi.md` (dokumen ini)
- `docs/glossary.md` (gabungan koordinator dari 4 kontribusi tim)
- `docs/adr/ADR-0001-sumber-job-board.md`
- `docs/adr/ADR-0002-kontrak-adapter-deteksi-aktif.md`
- `docs/adr/ADR-0003-halaman-karier-dan-ats.md`
- `docs/adr/ADR-0004-sosial-perusahaan-ig-linkedin.md`
- `docs/adr/ADR-0005-rubrik-skor-rule-based.md`
- `docs/adr/ADR-0006-sumber-reputasi-dan-anti-fitnah.md`
- `docs/adr/ADR-0007-adopsi-vs-tulis-ulang.md`

**Kode scraper-core (`packages/scraper-core/`):**
- `scraper_core/base.py` (kontrak + `RawJob` + robots + kesopanan;
  **diubah koordinator:** field ATS + `posted_at_certain`)
- `scraper_core/parsers.py` (gaji IDR, tanggal relatif, normalisasi)
- `scraper_core/adapters/glints.py`, `kalibrr.py` (aktif;
  **diubah koordinator:** `posted_at_certain` diteruskan)
- `scraper_core/adapters/jobstreet.py`, `indeed.py` (stub
  `SourceNotPermittedError`)
- `scraper_core/adapters/career_page.py`, `social_company.py`
  (**dipindah + disatukan koordinator** dari `adapters/` lama)
- `scraper_core/adapters/__init__.py` (registry + `DIRECT_ADAPTERS`)
- `scraper_core/__init__.py`, `pyproject.toml`, `README.md`
  (**diubah koordinator:** catatan penyatuan)
- `tests/test_jobboard_adapters.py` (32 test) + 9 fixture
- `tests/test_direct_adapters.py` (52 test;
  **diubah koordinator:** import + `company_raw`) + 7 fixture
- `.venv/` (venv lokal pytest — ter-ignore di `.gitignore`)

**Kode flag-engine (`packages/flag-engine/`):**
- `social_signals.py` (6 fungsi rule-based + `aggregate_signals`)
- `tests/test_social_signals.py` (45 test, unittest stdlib) +
  `tests/__init__.py`

**Lainnya:**
- `.gitignore` (**diubah koordinator:** tambah `.pytest_cache/`)

**Yang sengaja TIDAK dibuat:** tidak ada perubahan ke `ARCHITECTURE.md`
(D2/D5 diusulkan berubah lewat D6/D7 di §7, bukan diubah diam-diam),
tidak ada kode API/web/DB, tidak ada credential/data pribadi di file mana pun.

---

*Koordinator Fase 1, 15 Nov 2026. Verifikasi test oleh koordinator sendiri di
VM ini: scraper-core 84 passed, flag-engine 45 passed, setelah penyatuan.
Tidak ada klaim "teruji live" di laporan ini — semua yang belum diuji live
tercantum di §8.*
