# Uji Live Fase 1-Lanjutan — Laporan TIM UJI LIVE

**Tanggal uji:** Ahad, 15 November 2026 (WIB).
**Bahasa:** Indonesia. **Status:** SELESAI (uji + perbaikan adapter + test).
**Tidak ada push / PR / merge ke GitHub. Tidak ada API berbayar.
Tidak ada credential / API key yang disimpan.**
Semua hasil lokal di `~/workspace/cekloker/`.

Metode: daftar uji §8 `docs/fase1-konsolidasi.md`, dijalankan SATU-PER-SATU,
sopan, request minimal. Tiap asumsi Fase 1 di-grill dulu ala Matt Pocock
(grill-with-docs) sebelum dipercaya — hasilnya di §3: 2 asumsi TERBUKTI
SALAH dan 1 klaim Fase 1 TIDAK TERVERIFIKASI.

## 0. Cara uji (aturan main yang dipatuhi)

- **robots.txt dibaca dulu** untuk tiap domain sebelum request ke path-nya.
- **Delay 2–5 detik per domain**, 1 request per cek, tanpa crawl massal.
  Total ±43 request HTTP selama seluruh pengujian.
- **User-Agent jujur:** `CekLokerBot/0.1 (+https://github.com/Gigajn/cekloker;
  scraper riset non-komersial, patuh robots.txt)` — dari `scraper_core.base.user_agent()`.
  Env `CEKLOKER_CONTACT` KOSONG di VM ini, jadi UA default yang dipakai
  (tautan repo GitHub, bukan email — tidak ada email palsu yang dipakai).
- **Hanya Python stdlib (urllib)** — tanpa Playwright, tanpa tool berbayar.
- **BERHENTI saat 403/429/blokir/CAPTCHA/login** — tidak ada satu pun kasus
  403/429/CAPTCHA/login dalam uji ini, jadi tidak ada putaran proxy maupun
  bypass apa pun. Yang ada: 406, timeout, dan koneksi ditutup server
  (dicatat apa adanya di §1, tidak dicoba ulang berulang-ulang — tiap
  domain gagal hanya didiagnosa 1x untuk mencatat penyebabnya).
- **Hanya potongan struktur** yang disimpan sebagai fixture (field yang ada,
  bentuk JSON, 1 judul contoh) — bukan isi penuh halaman, bukan data pribadi.
- **Catatan jujur soal keterbatasan:** semua uji ini dari VM (egress
  datacenter). Hasil GAGAL/BLOKIR bisa jadi spesifik-egress, bukan sifat
  situsnya — karena itu tiap temuan negatif di bawah disertai "perlu uji
  ulang dari jaringan Indonesia (Fedora Giga)" sebelum disimpulkan permanen.
  Yang LOLOS tidak butuh kualifikasi itu (bukti positif dari VM justru
  lebih kuat: kalau dari egress datacenter saja bisa, dari jaringan
  normal hampir pasti bisa).

## 1. Tabel hasil per sumber

| # | Sumber / cek | Hasil | Tanggal | URL yang diuji | Bukti struktur (yang berubah dari asumsi Fase 1) |
|---|---|---|---|---|---|
| 1a | Glints — `sitemap_index.xml` | **LOLOS** | 15 Nov 2026 | `https://glints.com/sitemap_index.xml` | HTTP 200. Berisi **4.898 child sitemap** (0 URL lowongan langsung). Child `sitemap_job_id_1.xml`: **200 URL, 200/200 cocok pola lowongan** `/opportunities/jobs/<slug>/<uuid>`. Asumsi Fase 1 ("sitemap berisi URL lowongan") TERKONFIRMASI — dengan koreksi: lowongan ada di child sitemap, bukan di index. robots.txt Glints (200) mendeklarasikan sitemap + TIDAK melarang halaman detail. |
| 1b | Glints — 1 halaman detail | **LOLOS (dengan 1 bug adapter)** | 15 Nov 2026 | `https://glints.com/id/opportunities/jobs/corporate-sales-executive/ef200192-2650-415a-9fee-216e7b2326a0` | **JSON-LD `JobPosting` ADA**: `datePosted` `2026-08-27T03:33:51.59Z` (ISO, pasti), `validThrough` `2026-12-16`, gaji Rp5.000.000–5.500.000, lokasi Jakarta Selatan. **BUG DITEMUKAN:** adapter menandai lowongan AKTIF ini `is_active=False` — penyebabnya penanda tutup `"lowongan ini sudah ditutup"` ternyata ada di bundel terjemahan i18n di dalam `<script>` (`"job.card.job.closed.message":...`), jadi ada di SEMUA halaman. Perbaikan: penanda tutup hanya dicari di teks tampil + `validThrough` jadi sinyal kedua (lihat §2). |
| 2 | Kalibrr — 1 pencarian `?query=` | **GAGAL** | 15 Nov 2026 | `https://www.kalibrr.id/jobs?query=software+engineer` | HTTP 200 TAPI isi hanya **shell SPA ~2,3 KB** (judul generik "Find Jobs & Candidates Faster", 1 script, **TANPA `__NEXT_DATA__`, 0 URL lowongan, query tidak ter-echo**). Parameter `?query=` TIDAK TERVERIFIKASI bekerja — tidak bisa dijawab dari halaman ini, karena halamannya tidak mengembalikan data sama sekali. **BONUS TEMUAN:** `robots.txt` Kalibrr (.id MAUPUN .com) juga mengembalikan shell SPA yang sama — bukan robots.txt sungguhan. Klaim Fase 1 ("robots hanya melarang /root dan /candidate/profile") **TIDAK TERVERIFIKASI live**. Respons shell .com memuat penanda `<meta kb="__KB_THIS_IS_A_503__"/>`. Perbaikan: adapter kini gagal jujur (`SourceFetchError`, worker → `unknown`), bukan diam-diam [] (lihat §2). Detail Kalibrr tidak bisa diuji (tidak ada URL dari pencarian). |
| 3a | ATS — Greenhouse (board `discord`) | **LOLOS** | 15 Nov 2026 | `https://boards-api.greenhouse.io/v1/boards/discord/jobs?content=true` | HTTP 200, **26 lowongan**. `first_published` **ADA di daftar untuk 26/26** (contoh: `"2026-11-13T15:33:44-05:00"` → `posted_at` 2026-11-13) — K-D1 TERJAWAB SEBAGIAN: contoh di dokumen resmi memang tidak memuatnya, tapi data live memuatnya. Fallback endpoint satu job tetap dipertahankan. robots.txt `boards-api.greenhouse.io` (200) hanya melarang `/embed/`. Contoh: "Account Executive, Mobile Gaming", San Francisco Bay Area. |
| 3b | ATS — Lever (board `spotify`; GoTo 404) | **LOLOS** | 15 Nov 2026 | `https://api.lever.co/v0/postings/spotify?mode=json&limit=500` | HTTP 200, **87 lowongan**. `createdAt` (epoch ms) **ADA di 87/87** (contoh: `1792767640768` → `posted_at` 2026-10-23) — K-D2 TERJAWAB: field itu nyata di respons live meski tidak ada di tabel README resmi. robots.txt `api.lever.co` (200): `Allow: /`, `Crawl-delay: 1`. Contoh: "Account Executive - Commercial, Spotify Technology", New York, NY. |
| 3c | ATS — Ashby (board `ashby`) | **LOLOS** | 15 Nov 2026 | `https://api.ashbyhq.com/posting-api/job-board/ashby?includeCompensation=true` | HTTP 200, **76 lowongan**. `publishedAt` ADA. **Bukti langsung K-D3:** lowongan pertama terdaftar punya `publishedAt` **2024-03-04** (>1,5 tahun lalu) tapi masih terdaftar — `publishedAt` = terakhir dipublikasikan, BUKAN tanggal buka; jangan tampilkan sebagai "baru dibuka". Contoh: "Engineering Manager - EU". Catatan: `robots.txt` api.ashbyhq.com mengembalikan 401 (tidak ada file robots; API-nya sendiri publik tanpa auth). |
| 3d | ATS — Workable (board `huggingface`) | **LOLOS** | 15 Nov 2026 | `https://apply.workable.com/api/v1/widget/accounts/huggingface?details=true` | HTTP 200, **6 lowongan**. `published_on` ADA, tanggal saja (contoh: `"2026-05-29"`). robots.txt `apply.workable.com` (200): `User-agent: *`, `Disallow:` kosong (mengizinkan semua) + `Content-Signal: search=yes, ai-input=yes, ai-train=no`. Contoh: "Open-Source Machine Learning Engineer - EMEA Remote", Paris. |
| 4a | Tokopedia — `tokopedia.com/careers` | **GAGAL (teknis)** | 15 Nov 2026 | `https://www.tokopedia.com/careers` | robots.txt `www.tokopedia.com` (200, asli — memuat aturan Allow/Disallow). Halaman karier: **TimeoutError** (read timeout 25 dtk, 1x diagnosa ulang tetap timeout). Platform tidak ketemu. Bukan 403/429 — murni gagal teknis dari VM ini; perlu uji ulang dari jaringan Giga sebelum disimpulkan. |
| 4b | GoTo — `gotocompany.com/careers` + Lever | **GAGAL (platform tidak ketemu) / K-D5 TERBANTAH** | 15 Nov 2026 | `https://www.gotocompany.com/careers` | robots.txt (200): `Allow: /` untuk semua. Halaman karier: HTTP 200, 17 KB, 13 script, judul "Karier \| GoTo", **platform `custom`, 0 JSON-LD JobPosting, 0 tautan ATS** di HTML statis — halaman dirender JS, lowongan tidak terlihat tanpa JS. **GoTo BUKAN di Lever:** `api.lever.co/v0/postings/goto` → **HTTP 404**. Klaim MulaJob ("GoTo via Lever") TERBANTAH. Board Lever milik Lever sendiri (slug `lever`): 200 dengan **0 lowongan** — board kosong ≠ "tidak merekrut" (K-D4 ditegaskan lagi). 1 lowongan contoh tidak bisa diambil dari HTML statis. |
| 4c | Bukalapak — `careers.bukalapak.com` | **BLOKIR** | 15 Nov 2026 | `https://careers.bukalapak.com` | robots.txt MAUPUN halaman: **HTTP 406** (Not Acceptable) — server menolak melayani request dengan UA ini. Tidak dicoba lagi. Platform tidak ketemu. |
| 4d | Xendit — `careers.xendit.co` | **BLOKIR** | 15 Nov 2026 | `https://careers.xendit.co` | robots.txt MAUPUN halaman: **koneksi ditutup server tanpa respons** (`RemoteDisconnected`, 1x diagnosa ulang sama). Platform tidak ketemu. |
| 4e | Ruangguru — `careers.ruangguru.com` | **BLOKIR** | 15 Nov 2026 | `https://careers.ruangguru.com` | Sama seperti Xendit: robots.txt + halaman **koneksi ditutup server tanpa respons** (`RemoteDisconnected`). Platform tidak ketemu. |
| 4f | BCA — `karir.bca.co.id` | **GAGAL (tanpa data terstruktur)** | 15 Nov 2026 | `https://karir.bca.co.id` | robots.txt (200): `User-agent: *`, `Disallow:` kosong. Halaman karier: HTTP 200, 60.755 byte, judul "Temukan Jalan Untuk Mewujudkan Karir Impian \| BCA Karir", **platform `custom`, 0 JSON-LD JobPosting, 0 tautan ATS** — portal custom, lowongan tidak terstruktur di HTML statis. 1 lowongan contoh tidak bisa diambil tanpa adapter khusus/JS. |
| 4g | Telkom — `rekrutmen.telkom.co.id` | **BLOKIR** | 15 Nov 2026 | `https://rekrutmen.telkom.co.id` | Sama seperti Xendit: robots.txt + halaman **koneksi ditutup server tanpa respons** (`RemoteDisconnected`). Platform tidak ketemu. |
| 4h | Blibli — `careers.blibli.com` | **GAGAL (tanpa data terstruktur)** | 15 Nov 2026 | `https://careers.blibli.com` | robots.txt: 404 (tidak ada file robots). Halaman karier: HTTP 200, 4.708 byte, 12 script, tanpa `<title>` — **shell JS**, `custom`, **0 JSON-LD**, 0 tautan ATS. 1 lowongan contoh tidak bisa diambil dari HTML statis. |
| 4i | DANA — `careers.dana.id` | **BLOKIR** | 15 Nov 2026 | `https://careers.dana.id` | Sama seperti Xendit: robots.txt + halaman **koneksi ditutup server tanpa respons** (`RemoteDisconnected`). Platform tidak ketemu. |

**Ringkasan §8 konsolidasi (6 butir):** (1) ✅ LOLOS — sitemap Glints berisi
lowongan (di child sitemap). (2) ✅ LOLOS — JSON-LD JobPosting ada di halaman
detail Glints. (3) ❌ GAGAL — pencarian Kalibrr `?query=` tidak terverifikasi
(shell SPA tanpa data; jumlah hasil tidak bisa dihitung — 0 URL, bukan
"±15 hasil"). (4) ✅ LOLOS — 1 board live per ATS (Greenhouse 26, Lever 87,
Ashby 76, Workable 6 lowongan; semua field tanggal terverifikasi nyata).
(5) ⚠️ SEBAGIAN — 9 perusahaan uji: **0 dari 9 yang memberi 1 lowongan
contoh dari HTML statis** (GoTo/BCA/Blibli terjangkau tapi tanpa data
terstruktur; Tokopedia timeout; Bukalapak 406; Xendit/Ruangguru/Telkom/DANA
koneksi ditutup). Traveloka tetap satu-satunya perusahaan Direct yang
halamannya sudah dibaca langsung (Fase 1, tidak diulang). (6) Instagram —
TIDAK DIUJI, sesuai keputusan (D11: IG tetap lead manual, tanpa token,
tanpa fetcher otomatis; butuh D11 bila mau uji live).

## 2. Yang berubah dari asumsi Fase 1 (hasil grill + uji live)

### G-L1 — Penanda tutup Glints: false positive di SEMUA halaman (BUG, diperbaiki)
Asumsi Fase 1: halaman tutup menampilkan "This job was closed" /
"lowongan ini sudah ditutup" — dicari di seluruh HTML.
Grill: *teks apa di halaman yang BUKAN pesan tutup tapi mengandung frasa itu?*
Jawaban live: bundel i18n di `<script>` memuat SEMUA pesan UI, termasuk
`"job.card.job.closed.message":"lowongan ini sudah ditutup"`. Jadi adapter
versi lama menandai **semua** lowongan Glints sebagai tutup — lowongan aktif
dengan `validThrough` 2026-12-16 pun ditandai `is_active=False`.
**Perbaikan (`adapters/glints.py`):**
- `_GlintsPageParser` kini TIDAK memasukkan isi `<script>`/`<style>` ke teks
  tampil; penanda tutup hanya dicari di teks tampil.
- `validThrough` JSON-LD dipakai sebagai sinyal kedua: bila sudah lewat,
  lowongan dianggap tutup (menangkap lowongan kedaluwarsa diam-diam).
- `check_active()` kini memakai satu sumber kebenaran (`parse_glints_job`),
  bukan pencarian penanda terpisah di HTML mentah.
- Helper baru `visible_text(html)` (buang `<script>`/`<style>`).
- `parse_sitemap()` kini mendedup varian locale (`/id/` vs `/id/en/`,
  UUID sama) — tiap lowongan muncul 2x di sitemap.
- Test regresi: `glints_job_i18n_bundle.html` (lowongan aktif + bundel i18n
  → `is_active True`), `glints_job_validthrough_lewat.html`
  (`validThrough` lewat → `is_active False`), dedup sitemap, `visible_text`.

### G-L2 — Kalibrr: `__NEXT_DATA__` TIDAK ADA di halaman live (asumsi SALAH, diperbaiki)
Asumsi Fase 1 (dari skill `kalibrr-search`, diuji live 2026-07-11):
"Each page embeds its full data as JSON in a `__NEXT_DATA__` script tag."
Grill: *apakah klaim skill Juli 2026 masih berlaku untuk `kalibrr.id` hari
ini, untuk UA bot yang jujur?* Jawaban live: TIDAK. Halaman pencarian
mengembalikan shell SPA ~2,3 KB tanpa data apa pun.
**Perbaikan (`adapters/kalibrr.py`):**
- `parse_kalibrr_search()` melempar `SourceFetchError` bila halaman tidak
  memuat `__NEXT_DATA__` sama sekali dan tidak ada URL ditemukan — worker
  menandai sumber `unknown`, BUKAN "0 lowongan". Halaman pencarian sah yang
  memang 0 hasil (punya `__NEXT_DATA__` kosong) tetap mengembalikan `[]`.
- `parse_kalibrr_job()` melempar `SourceFetchError` yang sama bila tidak
  ada `__NEXT_DATA__`.
- Test regresi: `kalibrr_search_shell.html` (shell live → raise di kedua
  parser) + kasus pembeda (ada `__NEXT_DATA__` kosong → `[]`).
- Klaim `robots_disallows` Kalibrr ditandai TIDAK TERVERIFIKASI di docstring
  (robots.txt ternyata mengembalikan shell SPA, bukan file robots).
- Adapter TIDAK di-stub/dimatikan: temuan ini bisa spesifik-egress VM
  (penanda `__KB_THIS_IS_A_503__` di shell). Keputusan nasib Kalibrr di D13.

### G-L3 — Greenhouse `first_published`: dokumen resmi TIDAK LENGKAP (asumsi dibalik)
Asumsi Fase 1 (K-D1): field `first_published` hanya ada di endpoint satu job.
Live (board `discord`, 26 lowongan): ada di daftar untuk **26/26**.
Tidak ada perubahan kode yang dibutuhkan (fallback satu job hanya jalan
bila `posted_at` kosong — dan kini jarang terpicu). Docstring
`parse_greenhouse_board` diperbarui dengan bukti live.

### G-L4 — Lever `createdAt`: TERKONFIRMASI ADA (K-D2 terjawab)
Asumsi Fase 1: `createdAt` tidak ada di tabel README resmi, tapi respons
live memuatnya. Live (board `spotify`, 87 lowongan): ada di **87/87**.
Tidak ada perubahan kode. Docstring diperbarui.

### G-L5 — Ashby `publishedAt`: BUKTI LANGSUNG BAHWA ITU BUKAN TANGGAL BUKA (K-D3)
Live (board `ashby`, 76 lowongan): lowongan pertama punya `publishedAt`
2024-03-04 — sudah >1,5 tahun tapi masih terdaftar. Ini ciri lowongan
evergreen/stale, dan membuktikan `publishedAt` tidak boleh tampil sebagai
"baru dibuka". Tidak ada perubahan kode (adapter sudah menyimpan
`posted_at` + `first_seen_at` terpisah). Docstring diperbarui.

### G-L6 — GoTo BUKAN di Lever (K-D5 TERBANTAH)
Klaim sekunder MulaJob ("GoTo Indonesia via Lever") dibantah live:
`api.lever.co/v0/postings/goto` → 404. GoTo (AS) memakai Workday adalah
perusahaan BERBEDA — jangan dicampur (K-D5 menegaskan lagi). Platform
karier GoTo Indonesia tidak ketemu dari HTML statis (JS, tanpa JSON-LD,
tanpa tautan ATS). Keputusan di D15.

### G-L7 — Board kosong AMBIGU, ditegaskan 2x (K-D4)
Board Lever milik Lever sendiri: HTTP 200, 0 lowongan. Ini bisa berarti
"perusahaan tidak merekrut" ATAU "bukan pelanggan Lever lagi" — parser
tetap mengembalikan [] dan pemanggil dilarang menyimpulkan. Tidak ada
perubahan kode (aturan sudah ada di ADR-0003 + test).

### G-L8 — Klaim robots.txt Kalibrr TIDAK TERVERIFIKASI (baru)
Fase 1 mencatat robots.txt Kalibrr "dibaca langsung 15 Nov 2026".
Uji live ini: `kalibrr.id/robots.txt` DAN `kalibrr.com/robots.txt`
sama-sama mengembalikan shell SPA (bukan file robots). Jadi klaim itu
tidak bisa berasal dari fetch langsung ke URL tersebut — kemungkinan
berasal dari cache/pencarian. Dicatat sebagai koreksi fakta, bukan
tuduhan: `robots_disallows` Kalibrr dipertahankan sebagai catatan klaim
lama sampai ada robots.txt sungguhan yang terbaca.

## 3. Perubahan kode & test (hanya yang diizinkan tugas)

**Diubah — `packages/scraper-core/scraper_core/adapters/`:**
- `glints.py` — parser teks tampil (tanpa script/style), `visible_text()`,
  `validThrough` sebagai sinyal tutup, `check_active()` satu sumber
  kebenaran, dedup UUID di `parse_sitemap()`, docstring temuan live.
- `kalibrr.py` — gagal jujur (`SourceFetchError`) saat shell SPA tanpa
  `__NEXT_DATA__` di `parse_kalibrr_search()` + `parse_kalibrr_job()`,
  docstring temuan live + status robots.txt.
- `career_page.py` — HANYA docstring (bukti live Greenhouse/Lever/Ashby/
  Workable + K-D5); tidak ada perubahan logika parser ATS (semuanya
  terbukti benar di data live).

**Tidak diubah:** `apps/`, `infra/`, `packages/flag-engine/`, adapter
JobStreet/Indeed/LinkedIn (tetap stub/tunda — tidak diuji live, tidak
diaktifkan), `social_company.py` (IG tetap manual, D11).

**Fixture baru — `packages/scraper-core/tests/fixtures/`** (potongan struktur
saja, dimodelkan dari respons live 15 Nov 2026):
- `glints_job_i18n_bundle.html`, `glints_job_validthrough_lewat.html`
- `kalibrr_search_shell.html`
- `greenhouse_board_live.json`, `lever_board_live.json`,
  `ashby_board_live.json`, `workable_board_live.json`
  (lowongan pertama = data publik live yang diamati; lowongan kedua fiktif,
  diberi label di file)

**Test baru (9):** 5 di `tests/test_jobboard_adapters.py` (i18n Glints,
validThrough lewat, dedup sitemap, shell Kalibrr → raise, `__NEXT_DATA__`
kosong → `[]`) + 4 di `tests/test_direct_adapters.py` (satu per ATS live).

**Hasil test ulang:**
`cd packages/scraper-core && .venv/bin/python -m pytest -q`
→ **97 passed, 0 failed** (jobboard 37 + direct 60 item terkumpul —
angka direct mencakup test terparametrisasi).
Baseline sebelum tim ini: 88 test (37−5 jobboard, 60−4 direct). Angka 84 di
konsolidasi Fase 1 adalah baseline saat itu; selisih 4 test berasal dari
pekerjaan paralel Fase 1-lanjutan lain sebelum tim ini mulai, bukan dari
tim ini. Tidak ada regresi: semua test lama tetap hijau.

**Dokumen baru:** `docs/adr/ADR-0008-hasil-uji-live-fase1-lanjutan.md`
(temuan + perubahan adapter + keputusan D13–D16).
**Glossary:** tambah `shell SPA`, `validThrough`, `false positive`
(lihat `docs/glossary.md`).

## 4. Keputusan yang butuh Giga (D13–D16)

| ID | Pertanyaan | Opsi yang diajukan tim uji live |
|---|---|---|
| **D13** | Kalibrr dari VM ini hanya mengembalikan shell SPA tanpa data. Nasib adapter Kalibrr? | (a) **Uji ulang dulu dari jaringan Indonesia (Fedora Giga)** — 1 pencarian `?query=` dari jaringan rumah; bila di sana ada `__NEXT_DATA__`, adapter jalan apa adanya dan temuan ini dicatat sebagai spesifik-egress VM. (b) Bangun jalur JS (Playwright, dependensi opsional — sudah diizinkan ARCH §6/ADR-0002 untuk halaman berat JS). (c) Cari endpoint XHR internal Kalibrr — TIDAK direkomendasikan tanpa grill: endpoint tidak terdokumentasi, "bisa diakses" ≠ "diizinkan" (alasan yang sama saat menolak GraphQL Glints). (d) Jeda Kalibrr sampai ada jalur resmi. Tim merekomendasikan **(a) dulu** — paling murah dan menentukan apakah masalahnya situs atau egress. |
| **D14** | 4 perusahaan (Xendit, Ruangguru, Telkom, DANA) koneksi ditutup server + Bukalapak 406 + Tokopedia timeout — semuanya dari VM ini. | (a) Uji ulang dari jaringan Giga (Fedora) sebelum disimpulkan BLOKIR permanen. (b) Terima sebagai BLOKIR dan lacak ke-6 perusahaan itu hanya lewat Glints/Kalibrr/ATS (bila lowongannya ada di sana). Tim merekomendasikan **(a)** — pola "4 domain menolak dengan cara yang sama" mencurigakan sebagai filter egress, bukan kebijakan tiap situs. |
| **D15** | GoTo BUKAN di Lever; halaman kariernya JS tanpa JSON-LD/tanpa tautan ATS. | (a) Lacak GoTo hanya lewat Glints (bila lowongannya tayang di sana) — tanpa adapter direct. (b) Bangun adapter khusus GoTo (butuh Playwright/JS atau menebak endpoint data halaman kariernya). (c) Tunda GoTo sampai platformnya teridentifikasi dari browser. Tim merekomendasikan **(a) untuk sekarang** — GoTo besar, lowongannya hampir pasti ada di Glints. |
| **D16** | BCA / Blibli / GoTo: halaman kariernya hidup tapi tanpa data terstruktur di HTML statis (butuh JS). | (a) Batasi jalur direct hanya ke ATS + JSON-LD (status quo) — ketiga perusahaan ini tidak terlacak direct. (b) Setujui jalur Playwright (opsional, per-perusahaan) untuk halaman karier JS — butuh ADR + biaya perawatan per situs. Tim merekomendasikan **(b) ditunda ke setelah D13/D14 dijawab** — jangan tambah dependensi berat sebelum tahu berapa banyak situs yang benar-benar butuh JS. |

## 5. Yang masih TERBUKA setelah uji ini

- **ToS Glints + Kalibrr penuh belum dibaca** (tetap gate D8) — uji live
  ini membuktikan TEKNIS jalan, bukan LEGAL boleh. Jangan rilis publik
  sebelum dibaca.
- **Kalibrr `?query=` + pagination ±15 hasil/query** — keduanya belum
  terverifikasi dari jaringan mana pun (D13). Angka "±15" dari skill
  Juli 2026 jangan dikutip sebagai fakta saat ini.
- **9 perusahaan Direct: 0 lowongan contoh dari HTML statis.** Jalur
  direct Indonesia praktis baru terbukti untuk Traveloka (Fase 1) + ATS
  global. Cakupan direct Indonesia tetap tipis — JSON-LD adalah penentu,
  dan 3 dari 9 perusahaan yang terjangkau tidak memakainya.
- **Workday tidak diuji live** (tetap `NotImplementedError` — butuh URL
  board asli; GoTo AS memakainya tapi itu perusahaan berbeda).
- **SmartRecruiters / Recruitee / Personio / BambooHR** belum diuji live
  (tetap "sumber sekunder" sesuai ADR-0003).
- **Sitemap Glints berisi ~4.898 child sitemap** — discover penuh berarti
  ratusan ribu URL (tiap child 200 URL, tiap lowongan 2 varian locale).
  Worker produksi wajib: dedup UUID (sudah), batasi per sitemap, dan
  JANGAN crawl semua child sekaligus.

## 6. Daftar file yang dibuat / diubah (lokal, belum di-push)

- `docs/fase1-lanjutan-uji-live.md` (dokumen ini)
- `docs/adr/ADR-0008-hasil-uji-live-fase1-lanjutan.md` (baru)
- `docs/glossary.md` (tambah 3 istilah)
- `packages/scraper-core/scraper_core/adapters/glints.py` (diubah)
- `packages/scraper-core/scraper_core/adapters/kalibrr.py` (diubah)
- `packages/scraper-core/scraper_core/adapters/career_page.py` (docstring saja)
- `packages/scraper-core/tests/test_jobboard_adapters.py` (+5 test)
- `packages/scraper-core/tests/test_direct_adapters.py` (+4 test)
- `packages/scraper-core/tests/fixtures/` (+7 fixture: 3 HTML + 4 JSON)

*TIM UJI LIVE, 15 Nov 2026. Semua URL + status + bukti struktur di §1
adalah hasil pengamatan langsung hari itu, bukan kutipan laporan lain.
Klaim "teruji live" hanya berlaku untuk baris bertanda LOLOS.*
