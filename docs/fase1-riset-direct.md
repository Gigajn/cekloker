# Fase 1 — Riset Jalur Direct: Halaman Karier Perusahaan + Sosial Perusahaan

> Tim: **Direct / Perusahaan Langsung** — Fase 1 CekLoker
> Tanggal cek: **15 November 2026**
> Bahasa: Indonesia. Semua klaim penting punya sumber + tanggal cek.
> Aturan baca: **VERIFIKASI** = dicek ke dokumen resmi vendor / halaman
> publik yang dibaca langsung pada 15 Nov 2026. **ASUMSI** = dari ringkasan
> sekunder / pengetahuan umum, belum diuji live — jangan dipakai sebagai
> fakta sebelum uji live.

## 1. Ringkasan eksekutif

Perusahaan yang tidak posting di job board tetap bisa dilacak — tapi
**bukan dengan scraping HTML halaman kariernya**. Jalur yang benar:

1. **Feed JSON publik ATS** (Greenhouse, Lever, Ashby, Workable): ini
   endpoint yang sama dengan yang dipakai widget karier perusahaan itu
   sendiri. Tanpa login, tanpa kunci, didokumentasikan resmi oleh vendor.
   Inilah sumber direct utama CekLoker.
2. **Halaman karier custom**: baca JSON-LD `JobPosting` (schema.org)
   yang ditanam untuk SEO — 1 request, data terstruktur. Bila tidak
   ada JSON-LD, jangan tebak selector CSS: catat sebagai "butuh adapter
   khusus" dan kerjakan manual dulu.
3. **Instagram perusahaan**: hanya lewat Graph API resmi (Business
   Discovery). Hasilnya LEAD, bukan lowongan — tanggal posting IG
   bukan tanggal buka lowongan.
4. **LinkedIn perusahaan**: **TIDAK ADA pengambilan otomatis.**
   Hanya pencatatan manual oleh operator dari halaman publik.
   User Agreement LinkedIn §8.2 melarang scraping & bot secara eksplisit.

| Jalur | Rekomendasi | Alasan singkat |
|---|---|---|
| Greenhouse Job Board API | **ADOPSI** | Resmi, tanpa auth, `first_published` tersedia (endpoint satu job) |
| Lever Postings API | **ADOPSI** | Resmi, tanpa auth, Lever menulis eksplisit "may be scraped by third parties" |
| Ashby Job Postings API | **ADOPSI** | Resmi, tanpa auth, gaji terstruktur bila dipublikasikan |
| Workable widget API | **ADOPSI** | Didokumentasikan di Help resmi Workable, robots.txt mengizinkan |
| SmartRecruiters API | **BANGUN** | Endpoint publik, tapi butuh uji live + deskripsi butuh request per job |
| Workday | **TUNDA** | Slug tidak bisa ditebak; tanggal hanya relatif ("Posted 20 Days Ago") |
| Recruitee / Personio / BambooHR | **BANGUN (cadangan)** | Endpoint publik, tapi belum terverifikasi dari sumber primer |
| Halaman karier custom (JSON-LD) | **BANGUN** | Sopan & terstruktur; cakupan tergantung tiap perusahaan |
| Instagram (Graph API resmi) | **BANGUN (sebagai lead)** | Hanya Business Discovery; bukan sumber lowongan |
| LinkedIn otomatis | **TUNDA / JANGAN** | Dilarang §8.2; API resmi tidak memberi akses baca perusahaan lain |

## 2. Jalur ATS — tabel per platform

### 2.1 Yang terverifikasi dari dokumen resmi

| Platform | Endpoint publik (tanpa login) | Field tanggal buka | Gaji | Deteksi baru | Deteksi tutup |
|---|---|---|---|---|---|
| **Greenhouse** | `GET boards-api.greenhouse.io/v1/boards/{token}/jobs?content=true` | `first_published` — HANYA di endpoint satu job (`GET .../jobs/{id}`); list tidak menjamin (K-D1) | `pay_input_ranges` via `?pay_transparency=true` (per job) | id angka baru di list | hilang dari list / 404 |
| **Lever** | `GET api.lever.co/v0/postings/{slug}?mode=json` (EU: `api.eu.lever.co`) | `createdAt` epoch ms (tidak ada di tabel field README resmi — K-D2) | `salaryRange` bila diisi perusahaan | id UUID baru | hilang dari list (array kosong ambigu — K-D4) |
| **Ashby** | `GET api.ashbyhq.com/posting-api/job-board/{slug}?includeCompensation=true` | `publishedAt` = **TERAKHIR** dipublikasikan (K-D3) | `compensation` (Salary tier) bila dipublikasikan | id UUID baru | hilang dari list |
| **Workable** | `GET www.workable.com/api/accounts/{slug}?details=true` → 302 ke `apply.workable.com/api/v1/widget/accounts/{slug}` | `published_on` (YYYY-MM-DD) | tidak ada field gaji terstruktur | shortcode baru | hilang dari list |

Sumber resmi (dibaca langsung 15 Nov 2026):
- Greenhouse Job Board API: `developers.greenhouse.io/job-board.html` —
  "Only the application submission endpoint requires Basic Auth."
  List mengembalikan `jobs[]` + `meta.total`; `content=true` menambah
  deskripsi + departemen + kantor. `content` ter-encode ganda.
- Lever Postings API: `github.com/lever/postings-api` (README resmi) —
  "Note that all job postings in the `published` state are publicly
  viewable. **These jobs may be scraped by third parties.**"
  Satu-satunya vendor yang menulis izin itu secara eksplisit.
- Ashby Job Postings API: `developers.ashbyhq.com/docs/public-job-posting-api`
  (diperbarui 23 Okt 2026) — `publishedAt`: "ISO DateTime when the job
  was **last published**".
- Workable: `help.workable.com` artikel "Using the Workable API to
  create a careers page" — endpoint publik `www.workable.com/api/accounts/{subdomain}?details=true`
  ("try in your terminal ... public endpoints"); `robots.txt`
  `apply.workable.com`: `User-agent: *`, `Disallow:` (kosong).

### 2.2 Yang baru dari sumber sekunder (perlu uji live)

| Platform | Endpoint publik | Catatan |
|---|---|---|
| **SmartRecruiters** | `GET api.smartrecruiters.com/v1/companies/{id}/postings?limit=&offset=` | `releasedDate` ISO; list tanpa deskripsi (1 request/job); kosong ambigu (200 + `totalFound: 0`) |
| **Workday** | `POST {tenant}.{shard}.myworkdayjobs.com/wday/cxs/{tenant}/{site}/jobs` body `{"limit":20,"offset":0,"searchText":""}` | Tenant/site/shard TIDAK bisa ditebak dari nama perusahaan — butuh URL board asli. `postedOn` hanya relatif ("Posted Yesterday"). Multi-lokasi jadi placeholder "2 Locations". |
| **Recruitee** | `GET https://{slug}.recruitee.com/api/offers/` (trailing slash penting) | `published_at` ISO; percaya array `locations`, bukan field `city` datar |
| **Personio** | `GET https://{slug}.jobs.personio.de/xml` | XML (bukan JSON); slug palsu = 307 redirect ke personio.com, bukan 404 |
| **BambooHR** | `GET https://{slug}.bamboohr.com/careers/list` | Tanpa deskripsi & tanpa tanggal di list; slug palsu = 302 redirect |

Sumber sekunder: referensi ATS `conorscode.github.io/ats-api-reference`
(verifikasi live oleh penulisnya, diakses 15 Nov 2026) + beberapa
artikel dev.to Oktober–November 2026. Bukan dokumen resmi vendor —
karena itu statusnya ASUMSI sampai uji live CekLoker sendiri.

### 2.3 Cara deteksi lowongan BARU vs TUTUP (semua ATS)

- **Baru**: id platform (`job_key` = `platform:slug:id`) belum pernah
  terlihat di kunjungan sebelumnya. `posted_at` klaim sumber dipakai
  untuk tampilan; `first_seen_at` (kapan CekLoker pertama melihat)
  dicatat terpisah dan TIDAK PERNAH ditampilkan sebagai `posted_at`.
- **Tutup**: lowongan hilang dari respons board pada kunjungan ulang,
  atau endpoint satu job mengembalikan 404. Aturan ARCHITECTURE §3:
  2 kunjungan berturut-turut tidak ditemukan → `closed`.
- **Repost** (jebakan utama — lihat Hasil Grill §6): id ATS baru +
  fingerprint (judul + perusahaan + lokasi) sama dengan lowongan lama
  = kemungkinan repost, bukan lowongan baru. Adapter memberi `job_key`
  + fingerprint; keputusan "baru vs repost" ada di normalizer/scheduler,
  bukan di adapter.
- **Ambiguitas board kosong**: Lever/Ashby/SmartRecruiters mengembalikan
  respons kosong yang sama untuk "bukan pelanggan platform ini" dan
  "pelanggan tapi 0 lowongan". Jangan simpulkan perusahaan tutup dari
  board kosong — cek apakah halaman kariernya masih menautkan board itu.

### 2.4 Risiko per jalur ATS

- **Rate limit tidak didokumentasikan** di semua vendor. Tidak ada
  header `Retry-After` yang teramati. Karena itu: 1 request per 2 detik
  per host, User-Agent pengenal, cache agresif, jangan retry ketat
  saat 429/5xx.
- **Perusahaan bisa menonaktifkan board publik** atau pindah ATS
  (Lever: banyak pelanggan menonaktifkan endpoint publik). Adapter
  harus gagal dengan eksplisit (404 → board kosong), bukan diam-diam.
- **Greenhouse `content` double-encoded**: harus `unescape` 2x.
  **Ashby**: judul sering berawalan spasi — trim.
  **Lever**: respons array telanjang (bukan object `{"jobs": [...]}`).
- **Tidak ada webhook** perubahan lowongan di API publik mana pun
  (Lever: permintaan webhook terbuka sejak 2019). Deteksi baru/tutup
  hanya lewat polling berkala.

## 3. Halaman karier custom (bukan ATS)

| Cara | Bisa diambil | Tidak boleh / tidak bisa |
|---|---|---|
| JSON-LD `JobPosting` (schema.org) di HTML | judul, `datePosted`, lokasi, `hiringOrganization`, `baseSalary`, `validThrough`, deskripsi | `validThrough` bukan bukti masih buka — status aktif tetap dari kunjungan ulang |
| Sitemap (`/sitemap.xml`) + RSS/Atom | daftar URL halaman lowongan (bila perusahaan menyediakannya) | Sitemap tidak memberi tanggal buka yang andal; banyak perusahaan tidak punya sitemap karier |
| HTML mentah (selector CSS) | hanya sebagai fallback terakhir, per perusahaan | rapuh (layout berubah), mahal dirawat; jangan jadikan jalur utama |
| Halaman yang butuh login / CAPTCHA / paywall | — | **JANGAN diakali.** Cari sumber lain. |

Keputusan: custom = **BANGUN** dengan JSON-LD dulu. Adapter
`CareerPageAdapter(platform="custom")` sudah membaca JSON-LD + `check_active`
(halaman masih 200 + masih berisi JobPosting). Perusahaan custom tanpa
JSON-LD masuk antrean adapter khusus manual, bukan ditebak-tebak.

## 4. Instagram & LinkedIn perusahaan

### 4.1 Instagram — apa yang BISA dan TIDAK BOLEH

| Hal | Status |
|---|---|
| Graph API resmi — Business Discovery: field publik akun Bisnis/Kreator lain (username, bio, follower count, media + caption + timestamp + permalink) | **BOLEH** — butuh aplikasi Meta sendiri + token + App Review untuk fitur Public Content Access; hanya akun Bisnis/Kreator, bukan akun personal |
| Graph API — Hashtag Search / recent media | **BOLEH (terbatas)** — 30 hashtag unik / 7 hari, media 24 jam terakhir, maks 50/halaman; butuh App Review |
| Membaca postingan akun sendiri (akun CekLoker) | **BOLEH** — bila CekLoker punya akun Bisnis sendiri |
| instaloader / instagrapi / login dengan password (otomatisasi tak resmi) | **DILARANG** — Terms of Use Instagram melarang pengumpulan otomatis tanpa izin; akun bisa ditangguhkan; `challenge_required` sering muncul |
| Scraping massal profil publik tanpa login (skala besar / produk komersial) | **RISIKO TINGGI** — Meta v. Bright Data (Jan 2024) memang memenangkan logged-out scraping data publik di pengadilan AS, tapi Terms tetap melarang dan Meta aktif memblokir IP + menggugat (kasus Octopus, 2022). Untuk produk komersial: jangan jadikan jalur utama |
| DM, grup tertutup, akun privat, daftar follower massal | **DILARANG** |
| Menyimpan foto/caption utuh untuk dipublikasikan ulang | **JANGAN** — hak cipta; simpan kutipan singkat + link saja |

Batas Graph API (sekunder, Nov 2026): 200 request/jam per token pengguna.
Login wall muncul cepat pada endpoint web publik; Graph API stabil
hanya untuk akun yang memberi izin.

### 4.2 LinkedIn — apa yang BISA dan TIDAK BOLEH

| Hal | Status |
|---|---|
| Membaca postingan / lowongan perusahaan lain lewat API publik | **TIDAK ADA** — tidak ada Job Search API publik; Talent Solutions API hanya untuk partner yang disetujui; Community Management API (`r_organization_social`) hanya untuk halaman yang kita kelola |
| Scraping halaman LinkedIn (otomatis / browser otomatis / ekstensi) | **DILARANG** — User Agreement §8.2 (berlaku 3 Nov 2025): "Develop, support or use software, devices, scripts, robots or any other means or processes (such as crawlers, browser plugins and add-ons or any other technology) to scrape or copy the Services" + larangan "bots or other unauthorized automated methods". Akun berisiko dibatasi/ditutup. Penegakan meningkat 2026 (gugatan terhadap Proxycurl/Nubela; Proxycurl tutup 2026) |
| Membaca halaman publik perusahaan secara manual (manusia membuka browser) | **BOLEH** — dan itulah satu-satunya jalur LinkedIn v1: `ManualSocialLead` |
| Menyimpan data pribadi (nama karyawan, profil, koneksi) | **DILARANG** — GDPR/CCPA + §8.2; retensi data LinkedIn dibatasi (24 jam profil / 48 jam data sosial menurut ketentuan API) |

Keputusan: LinkedIn = **TUNDA otomatisasi, JALAN manual**. Tidak ada
satu baris pun kode pengambilan otomatis LinkedIn di paket ini — dengan
sengaja. Bila suatu hari LinkedIn membuka akses baca perusahaan,
barulah dibuat adapter API.

### 4.3 Kenapa sosial hanya menghasilkan LEAD, bukan lowongan

1. **Tanggal posting ≠ tanggal buka.** Postingan IG "We're hiring"
   bisa merujuk ke lowongan yang dibuka berminggu-minggu sebelumnya,
   atau lowongan yang sudah tutup.
2. **Caption bisa diedit** setelah diposting — tanggal posting tidak
   berubah, isinya berubah. Tidak ada jejak edit yang bisa dibaca.
3. **Satu postingan ≠ satu lowongan.** "We're hiring 5 roles" tidak
   memberi judul/lokasi/tanggal per role.
4. **Klasifikasi kata kunci rapuh** ("lowongan" bisa muncul di caption
   "Bukan lowongan" — sudah ditangani negasi di kode, tapi tetap
   heuristik).

Karena itu `to_job_lead()` **sengaja tidak mengisi `job_posted_at`**
(dibuat None secara eksplisit). Lead hanya memicu verifikasi ke halaman
karier / board ATS. Tanpa verifikasi itu, lead tidak pernah tampil
sebagai lowongan.

## 5. Konflik verifikasi (K-D1 … K-D6)

| ID | Klaim yang bertentangan / belum terverifikasi | Status |
|---|---|---|
| **K-D1** | Ringkasan sekunder menyebut list Greenhouse memuat `first_published`. Dokumen resmi (`developers.greenhouse.io/job-board.html`, contoh respons LIST) TIDAK memuat `first_published`; field itu hanya ada di contoh endpoint SATU job. | **DISELESAIKAN sebagian**: adapter memanggil endpoint satu job bila `posted_at` kosong. Perlu uji live: apakah list nyata memuat `first_published`? |
| **K-D2** | Tabel field README resmi Lever (`github.com/lever/postings-api`) TIDAK mencantumkan `createdAt`. Respons live (referensi sekunder + contoh) memuat `createdAt` epoch ms. | **DISELESAIKAN sebagian**: adapter membaca `createdAt` bila ada, `posted_at=None` bila tidak ada. Perlu uji live. |
| **K-D3** | Banyak ringkasan menyebut Ashby `publishedAt` sebagai "tanggal publikasi". Dokumen resmi: "**last published**" — berubah saat re-publish. Jadi `publishedAt` ≠ tanggal pertama dibuka. | **DISELESAIKAN**: `posted_at` = publishedAt + `first_seen_at` sendiri + deteksi repost via fingerprint. Butuh jawaban Giga? Tidak — keputusan sudah diambil (lihat ADR-0003). |
| **K-D4** | Board kosong (Lever/Ashby/SmartRecruiters) — apakah artinya perusahaan tutup / bukan pelanggan? | **TIDAK TERSELESAIKAN**: respons kosong ambigu. Keputusan: jangan simpulkan apa pun dari board kosong; cek tautan karier perusahaan. |
| **K-D5** | GoTo Indonesia disebut "via Lever" oleh MulaJob (sekunder). GoTo (AS) memakai Workday — hasil fetch `goto.com/careers` 15 Nov 2026 menautkan `goto.wd5.myworkdayjobs.com`. Dua "GoTo" berbeda! | **TIDAK TERSELESAIKAN**: perlu uji live `gotocompany.com/careers` + `jobs.lever.co/goto`. Jangan campur GoTo ID dengan GoTo AS. |
| **K-D6** | Bentuk respons Instagram Business Discovery: dokumen resmi Meta (`developers.facebook.com`) menolak dibaca langsung pada 15 Nov 2026 (HTTP 403 dari sisi Meta). Bentuk parser mengikuti ringkasan sekunder yang konsisten. | **TIDAK TERSELESAIKAN**: perlu uji live dengan token aplikasi sendiri sebelum produksi. |

## 6. Hasil Grill (skill Matt Pocock — grill-with-docs)

Grill dilakukan terhadap keputusan-keputusan besar di bawah. Setiap
pertanyaan ditulis sebelum dijawab; jawaban yang mengubah keputusan
ditandai **BERUBAH**.

### G1. Kenapa jalur karier langsung layak dikejar — bukankah cukup lewat job board (Glints/JobStreet)?

**Grill:** Job board sudah mengindeks ribuan lowongan. Jalur direct
menambah biaya perawatan adapter per ATS + per perusahaan custom.
Apa yang TIDAK didapat dari job board?

**Jawaban:** Tiga hal. (1) **Lowongan yang hanya ada di halaman
perusahaan** — banyak perusahaan (terutama startup & BUMN) tidak
posting ke agregator. (2) **Tanggal buka yang andal** — job board
sering menampilkan tanggal repost/sindikasi, sementara ATS memberi
`first_published`/`createdAt`/`publishedAt` dari sumber pertama.
(3) **Status tutup yang jujur** — lowongan hilang dari board ATS =
tutup; di job board, lowongan kadaluarsa sering tetap tampil.
Tetapi grill ini benar soal biaya: **BERUBAH** — direct TIDAK
dikejar untuk semua perusahaan. Cakupan v1 dibatasi: 4 ATS terverifikasi
+ JSON-LD custom + daftar 10 perusahaan uji (§7). Perusahaan custom
tanpa JSON-LD tidak dikerjakan di Fase 1.

### G2. Bagaimana kamu yakin bisa bedakan lowongan BARU vs lowongan LAMA yang di-repost?

**Grill:** ATS memberi id baru saat repost. `publishedAt` Ashby
berubah saat re-publish (K-D3). Kalau adapter hanya membandingkan id,
setiap repost akan tampil sebagai "lowongan baru" — persis kebohongan
yang produk ini janji tidak lakukan ("masih buka beneran, sejak kapan?").

**Jawaban:** Tidak yakin — dan itu alasan arsitekturnya berubah.
**BERUBAH** — keputusan "baru" dipindah dari adapter ke
normalizer/scheduler dengan 3 sinyal: (a) `job_key` (id ATS),
(b) `posted_at` klaim sumber, (c) fingerprint judul+perusahaan+lokasi.
Aturan: id baru + fingerprint lama = **kemungkinan repost** (tampil
dengan label, bukan sebagai baru); id baru + fingerprint baru = baru.
`first_seen_at` dicatat scheduler dan tidak pernah ditampilkan sebagai
`posted_at`. Fungsi `job_fingerprint()` + test repost sudah ada di kode.

### G3. Apa celah deteksi tanggal buka dari postingan IG?

**Grill:** Caption bisa diedit. Tanggal posting ≠ tanggal buka.
Postingan bisa merujuk ke 5 lowongan sekaligus. Hashtag #loker bisa
dipakai perusahaan untuk konten edukasi, bukan pengumuman.

**Jawaban:** Semua celah itu nyata dan tidak bisa ditutup dari sisi
IG. **BERUBAH** — IG diturunkan dari "sumber lowongan" menjadi
"sumber lead". `to_job_lead()` sengaja mengembalikan
`job_posted_at: None`. Tanpa verifikasi ke board ATS / halaman karier,
lead IG tidak pernah menjadi lowongan tampil. Klasifikasi caption
ditambah penanganan negasi ("bukan lowongan") setelah test menemukan
false positive.

### G4. Apa risiko terbesar jalur IG/LinkedIn — kenapa tidak langsung ditunda saja?

**Grill:** IG: akun ditangguhkan, IP diblokir, App Review ditolak,
Graph API berubah. LinkedIn: gugatan, akun ditutup, §8.2 eksplisit.
Nilai tambah nyata jalur ini kecil (lead, bukan lowongan). Kenapa
tidak TUNDA semua sosial ke Fase 4 seperti rencana awal?

**Jawaban:** Untuk LinkedIn otomatis — grill benar. **BERUBAH** —
LinkedIn otomatis **DITUNDA penuh** (tidak ada kode fetcher sama
sekali; hanya `ManualSocialLead`). Untuk IG — dipertahankan dengan
alasan sempit: (a) Business Discovery adalah API resmi, bukan
scraping; risikonya administratif (App Review, kuota), bukan hukum;
(b) lead IG berguna untuk sinyal flag Fase 2 (perusahaan aktif
merekrut vs diam) walau bukan sumber lowongan; (c) biaya implementasi
kecil karena parser-nya murni. Syarat: tanpa token aplikasi sendiri,
modul IG tidak jalan — dan itu disengaja.

### G5. Bagaimana kalau perusahaan menonaktifkan board publiknya besok?

**Grill:** Semua endpoint ATS di atas tidak dijamin kontrak. Vendor
bisa menutup, perusahaan bisa mematikan. Kalau 4 ATS mati bersamaan,
apakah CekLoker ikut mati?

**Jawaban:** Tidak — karena direct BUKAN satu-satunya sumber
(job board tetap jalan paralel, tim lain). Adapter dirancang gagal
eksplisit: 404 → board kosong, bukan error diam-diam; `discover()`
mengembalikan list kosong dan scheduler menandai sumber "tidak
terjangkau" (bukan "perusahaan tutup"). **BERUBAH**: `check_active()`
untuk Workday sengaja `raise NotImplementedError` — gagal keras dan
jelas, bukan pura-pura jalan.

### G6. Asumsi apa yang paling mungkin salah di riset ini?

**Grill:** Sebutkan tiga asumsi yang kalau salah, meruntuhkan
keputusanmu.

**Jawaban:** (1) "Endpoint ATS publik akan tetap publik" — kalau
Greenhouse/Lever menutup akses anonim, seluruh jalur direct runtuh;
mitigasi: job board + JSON-LD tetap ada. (2) "`publishedAt` Ashby
berubah saat re-publish" — ini dari kata "last published" di dokumen
resmi; kalau ternyata tidak berubah, deteksi repost melemah tapi tidak
runtuh (fingerprint tetap jalan). (3) "Perusahaan Indonesia memakai
ATS global" — mayoritas perusahaan Indonesia (BUMN, swasta besar)
pakai portal custom, bukan ATS global; karena itu daftar uji §7
didominasi custom — dan JSON-LD menjadi penentu, bukan ATS.

## 7. Daftar 10 perusahaan Indonesia untuk uji coba Fase 1

Tanggal cek daftar ini: 15 Nov 2026. **Hanya Traveloka yang halaman
kariernya dibaca langsung pada tanggal ini** (terverifikasi ada,
custom). Sembilan lainnya: URL dari pengetahuan umum + klaim sekunder —
**ATS "belum terverifikasi", perlu uji live** sebelum dipakai produksi
(lihat K-D5 untuk jebakan nama kembar).

| # | Perusahaan | Jenis | Halaman karier | Platform ATS (status) |
|---|---|---|---|---|
| 1 | Traveloka | Startup besar | https://careers.traveloka.com | Custom — **TERVERIFIKASI dibaca 15 Nov 2026**, halaman terbuka publik, ATS tidak terdeteksi dari teks halaman |
| 2 | Tokopedia | Startup besar | https://www.tokopedia.com/careers | Custom (diduga) — belum terverifikasi |
| 3 | GoTo (Gojek + Tokopedia) | Startup besar | https://www.gotocompany.com/careers | Diduga Lever (klaim MulaJob, sekunder) — belum terverifikasi; JANGAN samakan dengan GoTo AS (Workday) |
| 4 | Bukalapak | Startup besar | https://careers.bukalapak.com | Custom (diduga) — belum terverifikasi |
| 5 | Xendit | Startup fintech | https://careers.xendit.co | Belum terverifikasi |
| 6 | Ruangguru | Startup edtech | https://careers.ruangguru.com | Belum terverifikasi |
| 7 | BCA (Bank Central Asia) | Swasta besar | https://karir.bca.co.id | Portal custom (diduga) — belum terverifikasi |
| 8 | Telkom Indonesia | BUMN | https://rekrutmen.telkom.co.id | Portal custom (diduga) — belum terverifikasi |
| 9 | Blibli | Swasta besar / e-commerce | https://careers.blibli.com | Belum terverifikasi |
| 10 | DANA | Startup fintech | https://careers.dana.id | Belum terverifikasi |

Kriteria pilih: halaman karier terbuka publik (tanpa login), campur
startup / BUMN / swasta besar / menengah, ada kemungkinan ATS global
atau JSON-LD. Uji live Fase 1 untuk tiap baris: (a) buka halaman karier,
(b) deteksi platform via `detect_platform`, (c) bila ATS → panggil feed
JSON, catat jumlah lowongan + 1 contoh `posted_at`, (d) bila custom →
cek ada/tidaknya JSON-LD JobPosting.

## 8. Rencana uji live (yang belum dilakukan)

1. Panggil 4 feed ATS terverifikasi dengan slug contoh nyata
   (bukan fixture) — catat status HTTP + jumlah job + contoh tanggal.
2. Untuk 10 perusahaan §7: deteksi platform + uji feed / JSON-LD.
3. Uji Business Discovery IG dengan token aplikasi sendiri (K-D6).
4. Uji repost: amati 1 board selama 2 minggu, catat id yang hilang /
   muncul kembali dengan fingerprint sama.
5. Uji `robots.txt` tiap host ATS sebelum volume naik.

## 9. Istilah

- **ATS (Applicant Tracking System)** — perangkat lunak yang dipakai
  perusahaan untuk mengelola lowongan dan lamaran (menerima, menyaring,
  melacak kandidat). Contoh: Greenhouse, Lever, Ashby, Workable.
  Perusahaan membeli ATS; ATS menyediakan halaman karier + feed lowongan.
- **Halaman karier (career page / careers page)** — halaman di situs
  perusahaan sendiri yang menampilkan lowongan terbukanya. Bisa di-host
  ATS (mis. `boards.greenhouse.io/acme`) atau custom (mis.
  `careers.perusahaan.id`).
- **Board (job board ATS)** — daftar lowongan satu perusahaan di dalam
  satu ATS, dikenali dari **slug/board token** (mis. `acme` pada
  `boards.greenhouse.io/acme`).
- **Slug / board token** — pengenal singkat perusahaan di dalam ATS,
  biasanya nama perusahaan tanpa spasi. Bukan nama resmi perusahaan.
- **Feed JSON publik** — endpoint HTTP yang mengembalikan daftar
  lowongan sebagai JSON tanpa login, dipakai widget karier perusahaan
  itu sendiri. Inilah yang dibaca CekLoker.
- **posted_at** — tanggal buka lowongan *menurut klaim sumber*
  (`first_published` / `createdAt` / `publishedAt` / `published_on` /
  `datePosted`). Bisa kosong; bisa berarti "terakhir dipublikasikan",
  bukan pertama dibuka.
- **first_seen_at** — kapan scraper CekLoker PERTAMA KALI melihat
  lowongan itu. Selalu dicatat terpisah; tidak pernah ditampilkan
  sebagai `posted_at`.
- **Ghost job (lowongan hantu)** — lowongan yang tayang berbulan-bulan
  tanpa proses hiring nyata (tayang >90 hari tanpa perubahan, ARCHITECTURE §5).
- **Repost** — lowongan lama yang diterbitkan ulang sehingga tampak
  baru: id ATS baru dan/atau tanggal publikasi baru, tapi judul +
  perusahaan + lokasi sama. Dideteksi lewat fingerprint, bukan id.
- **Fingerprint lowongan** — hash dari judul + perusahaan + lokasi
  (normalisasi huruf kecil), dipakai untuk mengenali lowongan yang sama
  di berbagai sumber / waktu.
- **JSON-LD JobPosting** — blok data terstruktur schema.org yang
  ditanam di HTML halaman karier untuk SEO; berisi judul, `datePosted`,
  lokasi, organisasi perekrut, gaji. Jalur utama membaca halaman
  karier custom.
- **Business Discovery** — endpoint Instagram Graph API resmi untuk
  membaca field publik akun Bisnis/Kreator *lain*. Butuh token aplikasi
  sendiri; tidak bisa membaca akun personal.
- **Lead sosial (social lead)** — petunjuk dari media sosial bahwa
  perusahaan mungkin membuka lowongan. Bukan lowongan; wajib
  diverifikasi ke halaman karier / board ATS sebelum ditampilkan.
- **Check active** — pengecekan ulang apakah lowongan masih terlihat
  buka di sumbernya. Dua kali berturut-turut tidak ditemukan → `closed`.
