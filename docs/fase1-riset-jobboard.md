# Riset Job Board — Fase 1 CekLoker

> **Tanggal riset: 15 November 2026.** Semua klaim "TERVERIFIKASI" di
> bawah ini dibaca langsung dari dokumen primer (robots.txt situs itu
> sendiri, halaman ToS, halaman lowongan, atau repo open-source yang
> dikutip) pada 15 Nov 2026 (halaman di-crawl 14 Nov 2026, 17:30–17:32 UTC).
> Klaim yang TIDAK bisa diverifikasi dilabeli **ASUMSI, perlu uji live**
> dan TIDAK dipakai sebagai dasar keputusan. Tidak ada scraping massal
> live, tidak ada bypass login/paywall/CAPTCHA, tidak ada akun palsu.
>
> Pendekatan verifikasi mengikuti arahan grill-with-docs (Matt Pocock):
> tiap keputusan besar di-grill dulu, tiap klaim penting dicek ke sumber
> primer, kontradiksi diberi nomor konflik (K-JB1 dst). Lihat §"Hasil Grill".
>
> Konteks arsitektur: `ARCHITECTURE.md` (§4 model data, §5 flag engine,
> §6 kontrak adapter, §8 legal) dan `docs/SCORING.md`. Keputusan formal:
> `docs/adr/ADR-0001-sumber-job-board.md` dan
> `docs/adr/ADR-0002-kontrak-adapter-deteksi-aktif.md`.
> Referensi GitHub (JobSpy dkk) adalah tugas tim lain — lihat
> `docs/github-references.md` + `docs/adr/ADR-0007-adopsi-vs-tulis-ulang.md`.

---

## 1. Ringkasan keputusan (baca ini dulu)

| Sumber | Putusan | Jalur utama | Alasan satu kalimat |
|---|---|---|---|
| **Glints** | **BANGUN** | Sitemap + halaman detail publik (JSON-LD) | robots.txt paling permisif untuk halaman lowongan; sitemap dideklarasikan resmi; penanda tutup terverifikasi. |
| **Kalibrr** | **BANGUN** (terbatas) | Halaman publik `__NEXT_DATA__` | robots.txt hanya melarang 2 path internal; data tersemat sebagai JSON; tapi pagination TIDAK jalan (±15 hasil/query). |
| **JobStreet** | **TUNDA** — stub | — (butuh izin tertulis / SEEK API) | ToS SEEK **melarang agregasi & screen scraping** tanpa izin tertulis + robots.txt melarang halaman detail `*/job/`. |
| **Indeed** | **TUNDA** — stub | — (butuh izin tertulis / partner) | ToS **melarang bot/scraper tanpa izin tertulis** + robots.txt melarang `/viewjob`, `/job/`, `/jobs/ID/`; Publisher API sudah ditutup ~2023. |

**Konsekuensi terbesar dari grill (berubah dari rencana awal):**
rencana awal ARCHITECTURE.md (D2 + §5) menempatkan **Glints + JobStreet**
sebagai sumber utama Fase 1. Setelah membaca ToS + robots.txt primer,
**JobStreet DICORET dari sumber utama** dan diganti **Kalibrr**.
JobStreet tetap ada sebagai stub berdokumentasi — bukan dihapus diam-diam,
bukan diakali. Lihat K-JB1 dan §"Hasil Grill".

---

## 2. Tabel per sumber

### 2.1 Glints (glints.com / glints.id) — BANGUN

| Aspek | Temuan |
|---|---|
| Akses legal (urut paling resmi) | 1. **Sitemap**: `https://glints.com/sitemap_index.xml` — dideklarasikan di robots.txt (TERVERIFIKASI). 2. **Halaman detail publik** `/id/en/opportunities/jobs/<slug>/<uuid>` — TIDAK ada di daftar Disallow (TERVERIFIKASI). 3. **JSON-LD** `JobPosting` di halaman detail — pola standar, **ASUMSI, perlu uji live** (fetch teks 15 Nov 2026 tidak menampilkan blok JSON-LD-nya). 4. GraphQL `/api/graphql` — **DITOLAK** (tidak terdokumentasi, reverse-engineered; lihat K-JB2). |
| Field yang bisa diambil | Judul, perusahaan, lokasi, gaji ("IDR1,500,000 - 2,500,000/Month", "Rp5–8 jt"), tipe kerja (Contract · On-site), "Posted 1 month ago" / "Updated 1 month ago", URL detail, status tutup ("This job was closed" — TERVERIFIKASI dari halaman contoh). |
| robots.txt | `https://glints.com/robots.txt` dibaca langsung 15 Nov 2026. `User-agent: *` melarang: `*/opportunities/jobs/recommended$`, `*/opportunities/jobs/bookmarked$`, `*/settings`, `*/oauth2`, `*/onboarding-guided`, `*/preview/`, `*/talenthunt`, `*/user/`, `*/redirect$`, `*/403$`, `*/500$`, `*/opportunities/jobs/explore?*`, `*/en/opportunities/jobs/explore?*`, `*/blog/?s*`, `/api/glintsTracking/*`, `/api/gt/*`. **Halaman detail lowongan & sitemap TIDAK dilarang.** |
| ToS | **TIDAK TERVERIFIKASI** (K-JB6): pencarian 15 Nov 2026 tidak mengembalikan teks ToS glints.com (hasil yang muncul adalah perusahaan lain bernama mirip "Glin*"). Risiko sedang. |
| Risiko blokir | Sedang. Halaman explore ber-query dilarang robots — jangan dipakai. Rate-limit tidak dipublikasikan; delay 3 dtk disarankan. Layout bisa berubah sewaktu-waktu (JSON-LD adalah jangkar paling stabil). |
| Delay sopan | **3 detik/request** per domain (ARCHITECTURE.md §8: 2–5 dtk). |
| Status verifikasi | **TERVERIFIKASI** (robots, pola URL, penanda tutup, format gaji/tanggal). **ASUMSI**: isi sitemap berisi URL lowongan; JSON-LD `JobPosting` ada di halaman detail. Keduanya perlu uji live sekali. |

### 2.2 JobStreet (id.jobstreet.com) — TUNDA (stub)

| Aspek | Temuan |
|---|---|
| Akses legal | **Tidak ada jalur legal tanpa izin tertulis.** (1) ToS SEEK/JobStreet klausul (d): melarang "aggregate, copy or duplicate … any of the Content … including expired job postings, other than as permitted by these Terms or another agreement" (TERVERIFIKASI dari sg.jobstreet.com/terms, dibaca 15 Nov 2026). (2) Advertising Terms SEEK klausul 27: "You may not use data mining, robots, screen scraping, or similar automated data gathering … without our prior written approval." (3) robots.txt `User-agent: *`: `Disallow: */job/`, `Disallow: *?`, `Disallow: /api/jobsearch/`, `Disallow: /graphql` (TERVERIFIKASI, dibaca langsung 15 Nov 2026). (4) **SEEK API** (developer.seek.com) adalah API resmi, tapi butuh pengajuan + persetujuan dan ditujukan untuk integrasi ATS/perekrut, bukan pencarian publik; kontrak Indonesia dengan PT JobStreet Indonesia (TERVERIFIKASI dari au.seek.com API Terms, efektif 15 Okt 2023). |
| Field yang bisa diambil | *Andaikan* diizinkan: judul, perusahaan, lokasi, gaji ("Rp 22.000.000 – Rp 32.000.000 per month"), "Listed seven days ago" (TERVERIFIKASI dari cuplikan halaman pencarian). Endpoint internal Chalice Search v4 (`/api/chalice-search/v4/search`, 30 job/halaman, `siteKey=ID-Main`) — **teknisnya merespons tanpa kunci, tetapi BUKAN izin** (K-JB3). |
| robots.txt | Lihat di atas. Halaman list bersih (`/<kata>-jobs/in-<Kota>`) tidak dilarang robots — tetapi ToS tetap melarang agregasi kontennya. Jadi "boleh di-crawl" ≠ "boleh diambil dan ditampilkan". |
| ToS | **TERVERIFIKASI melarang** (lihat di atas). |
| Risiko blokir | **Tinggi + risiko hukum/ToS.** Anti-scraping countermeasure dicatat di repo open-source (random UA, IP rotation, fingerprinting) — itu justru bukti sumber ini aktif melawan scraper; meniru teknik itu = bypass, dilarang aturan proyek. |
| Delay sopan | Tidak relevan (adapter mati). Bila izin didapat nanti: 5 dtk. |
| Status verifikasi | **TERVERIFIKASI DILARANG.** Adapter = stub `SourceNotPermittedError` + alternatif legal. |

### 2.3 Kalibrr (kalibrr.id / kalibrr.com) — BANGUN (terbatas)

| Aspek | Temuan |
|---|---|
| Akses legal (urut paling resmi) | 1. **Halaman pencarian & detail publik** tanpa login/API key — data tersemat sebagai JSON di `<script id="__NEXT_DATA__">` (TERVERIFIKASI lewat skill `kalibrr-search`, fachrinoor/ai-job-search, diuji live penulisnya 2026-07-11: "Each page embeds its full data as JSON in a `__NEXT_DATA__` script tag, which the CLI parses directly"). 2. **robots.txt** hanya melarang `/root` dan `/candidate/profile` (TERVERIFIKASI, dibaca langsung 15 Nov 2026). 3. Pola URL detail `/c/<company-code>/jobs/<id>/<slug>` (TERVERIFIKASI dari hasil pencarian). |
| Field yang bisa diambil | Judul, perusahaan, lokasi, tipe kerja, `activationDate` (ISO, mis. `2026-09-28T06:44:24.594079+00:00`), deadline aplikasi ("Apply before 30 Dec"), "Posted a month ago", "Recruiter was hiring X ago", jumlah lowongan, website perusahaan. **Gaji: tidak selalu tampil** (banyak lowongan Kalibrr tanpa gaji — parser mengembalikan None, jangan ditebak). |
| robots.txt | `https://www.kalibrr.com/robots.txt`: `User-agent: *`, `Disallow: /root`, `Disallow: /candidate/profile`. Itu saja. |
| ToS | Cuplikan ToS (kalibrr.id/terms) dibaca 15 Nov 2026: pemakaian "for professional and legitimate purposes", melarang aktivitas ilegal; **tidak ditemukan klausul eksplisit anti-scraping dalam cuplikan** (K-JB8: teks penuh belum dibaca — butuh baca penuh sebelum rilis publik). |
| Risiko blokir | Sedang. Ada retry 429/5xx dengan backoff di skill referensi — artinya 429 memang terjadi. **Pagination tidak jalan** (K-JB4): selalu ±15 hasil pertama per query, tidak ada cara mengambil batch berikutnya lewat jalur ini (diuji live 2026-07-11, 3 bentuk parameter). Filter `?location=` tidak berpengaruh — kota harus dilipat ke kata kunci. |
| Delay sopan | **3 detik/request**; backoff eksponensial bila 429/5xx. |
| Status verifikasi | **TERVERIFIKASI** (robots, `__NEXT_DATA__`, pola URL, `activationDate`, penanda tutup "Ditutup."). **ASUMSI**: bentuk persis kunci JSON di `__NEXT_DATA__` (parser defensif, mencari kunci `job`/`jobs` di mana saja) + parameter query pencarian `?query=` — keduanya perlu uji live sekali. |

### 2.4 Indeed (indeed.com / id.indeed.com) — TUNDA (stub)

| Aspek | Temuan |
|---|---|
| Akses legal | **Tidak ada jalur legal tanpa izin tertulis.** (1) ToS Indeed versi 29 Sep 2026, §D.21 Site Rules (dikutip dari sumber sekunder yang membaca teks ToS langsung, Okt 2026): melarang "any automated system (bots, scrapers, spiders, AI or Agentic AI) to access, data-mine, or submit content to the Site … without Indeed's express written permission (we conditionally grant permission to crawl the Site solely as outlined in our robots.txt file)". (2) robots.txt (dibaca langsung 15 Nov 2026), `User-agent: *`: `Allow: /` TETAPI `Disallow: /viewjob`, `/job/`, `/jobs/ID/` (+ semua kode negara), `/graphql`, `/api/getrecjobs`, `/company/*`, `/rss`; pencarian hanya diizinkan sampai `&start=90` (±10 halaman). (3) **Publisher API (API pencarian publik ber-key) sudah ditutup** untuk developer baru dan berhenti mengembalikan data sejak ~2023; API tersisa (Job Sync, Disposition Sync, Job Update) untuk ATS/perekrut yang MENGIRIM lowongan — bukan membaca indeks publik — dan butuh review/partner. |
| Field yang bisa diambil | *Andaikan* diizinkan: judul, perusahaan, lokasi, gaji, deskripsi — semuanya di halaman detail `/viewjob` yang DILARANG robots. Hasil pencarian saja tidak cukup (tanpa deskripsi/posted_at andal). |
| robots.txt | Lihat di atas. Bahkan bot AI/training (`GPTBot`, `CCBot`, `anthropic-ai`, `ClaudeBot`, `Bytespider`, dll) diberi aturan sendiri yang juga melarang `/viewjob` & `/job/`. |
| ToS | **TERVERIFIKASI melarang** (lewat kutipan sekunder atas teks ToS primer — K-JB7: teks ToS belum dibuka langsung oleh tim ini; kutipan dari 2 sumber sekunder independen konsisten kata-per-kata). |
| Risiko blokir | **Sangat tinggi.** Anti-bot aktif (interstitial/blokir untuk request non-browser). Mengakali dengan proxy residensial/TLS impersonation = bypass, dilarang aturan proyek. |
| Delay sopan | Tidak relevan (adapter mati). |
| Status verifikasi | **TERVERIFIKASI DILARANG.** Adapter = stub `SourceNotPermittedError` + alternatif legal (Adzuna API, ATS langsung, program partner Indeed). |

### 2.5 LinkedIn — BUKAN sumber (dicatat karena ditanya di grill)

LinkedIn tidak masuk tugas, tetapi grill menanyakannya: ToS LinkedIn
melarang scraping dengan akun palsu/bot dan robots.txt-nya `Disallow: /`
untuk crawler yang tidak disebutkan namanya. Sesuai ARCHITECTURE.md §5:
LinkedIn di v1 HANYA sebagai info perusahaan publik + link keluar,
bukan sumber lowongan. Tidak ada adapter LinkedIn di paket ini.

---

## 3. Konflik verifikasi (K-JB)

| ID | Klaim yang bertentangan / tak terverifikasi | Status |
|---|---|---|
| **K-JB1** | ARCHITECTURE.md D2 + §5 menempatkan JobStreet sebagai sumber utama Fase 1. ToS SEEK (klausul d & 27) + robots.txt (`Disallow: */job/`, `*?`) melarang agregasi/scraping tanpa izin tertulis. | **DISELESAIKAN dengan mengubah keputusan**: JobStreet TUNDA, diganti Kalibrr sebagai sumber kedua. Butuh jawaban Giga: ajukan izin tertulis / SEEK API, atau lanjut tanpa JobStreet? |
| **K-JB2** | PR career-ops-hq/career-ops #1086 menyebut Glints GraphQL `/api/graphql` sebagai "public, no-auth API". Skema tidak terdokumentasi ("configurable query … since the schema is undocumented", "reverse-engineered"). | **DISELESAIKAN**: GraphQL DITOLAK sebagai jalur. Adapter Glints memakai sitemap + halaman publik. |
| **K-JB3** | Endpoint JobStreet Chalice v4 disebut "public, no-auth" di PR career-ops & DeepWiki ceroberoz/id-jobs. Di sisi lain robots.txt melarang `/api/jobsearch/` & ToS melarang agregasi. | **DISELESAIKAN**: "no-auth" ≠ "diizinkan". Endpoint didokumentasikan sebagai ASUMSI di stub, tidak dipakai. |
| **K-JB4** | Harapan umum: Kalibrr bisa di-crawl penuh seperti job board lain. Skill kalibrr-search (uji live 2026-07-11): pagination tidak jalan, selalu ±15 hasil pertama. | **DISELESAIKAN**: Kalibrr = pencarian kata kunci saja di v1; full crawl ditunda sampai ada jalur pagination. |
| **K-JB5** | robots.txt Indeed `Allow: /` untuk `User-agent: *` tampak permisif. ToS melarang bot tanpa izin tertulis; robots melarang `/viewjob`, `/job/`, `/jobs/ID/`. | **DISELESAIKAN**: izin robots ≠ izin ToS. Indeed TUNDA. |
| **K-JB6** | ToS Glints tidak ditemukan teksnya (pencarian 15 Nov 2026 hanya mengembalikan perusahaan lain bernama mirip). | **TERBUKA — butuh jawaban Giga**: baca ToS glints.com langsung sebelum rilis publik. Adapter jalan dengan asumsi pemakaian sopan; risiko sedang. |
| **K-JB7** | Kutipan ToS Indeed (§D.21, 29 Sep 2026) berasal dari 2 sumber sekunder (urltotext.com, unknownproxies.com, Okt 2026), bukan pembacaan langsung tim ini atas indeed.com/legal. | **TERBUKA (risiko kecil)**: 2 sumber independen mengutip kata-per-kata sama; robots.txt primer sudah menguatkan (melarang halaman detail). Verifikasi langsung ToS disarankan sebelum mengambil keputusan berbeda. |
| **K-JB8** | ToS Kalibrr: cuplikan tidak menunjukkan larangan scraping eksplisit, tetapi teks penuh belum dibaca. | **TERBUKA — butuh jawaban Giga**: baca penuh kalibrr.id/terms sebelum rilis publik. |

---

## 4. Hasil Grill

Skill grill-with-docs (Matt Pocock) diterapkan sebagai interogasi
terhadap setiap keputusan besar SEBELUM diterima. Pertanyaan tersulit,
jawaban, dan apa yang berubah:

### G1 — "Kenapa Glints utama, Kalibrr kedua, JobStreet ditunda, Indeed ditunda — bukan sebaliknya?"

**Jawaban:** Satu-satunya pembeda yang sah adalah **izin tertulis +
robots.txt primer**, bukan "yang paling banyak lowongannya" atau
"yang paling gampang di-scrape". JobStreet punya lowongan Indonesia
terbanyak setelah Glints, dan endpoint internalnya paling mudah
dipakai (JSON rapi, 30/halaman) — tetapi ToS-nya secara eksplisit
melarang agregasi & screen scraping, dan robots-nya melarang halaman
detail. Kemudahan teknis tidak menghapus larangan. Indeed sama:
paling besar global, tetapi ToS + robots + anti-bot ketiganya menolak.
Glints dan Kalibrr lolos karena robots-nya tidak melarang halaman
lowongan dan tidak ditemukan larangan ToS eksplisit (dengan catatan
K-JB6/K-JB8).
**Yang berubah:** urutan sumber di ARCHITECTURE.md D2 dibalik —
JobStreet keluar dari sumber utama, Kalibrr naik jadi sumber kedua.

### G2 — "Kenapa kontrak adapter ini (discover/fetch_job/check_active) bukan yang lain?"

Alternatif yang dipertimbangkan: (a) satu fungsi `scrape()` yang
melakukan segalanya; (b) adapter mengembalikan dict bebas; (c) kontrak
tanpa `check_active` (status aktif disimpulkan dari "masih ada di
halaman list").
**Jawaban:** (a) ditolak — satu fungsi raksasa tidak bisa diuji
per-bagian dan tidak bisa dipakai ulang untuk re-check aktif saja
(ARCHITECTURE.md §3 butuh kunjungan ulang murah: cek aktif ≠ ambil
detail penuh). (b) ditolak — dict bebas membuat normalizer menebak
field; `RawJob` dataclass memaksa semua adapter mengisi field yang
sama, dan `posted_at=None` eksplisit lebih jujur daripada tanggal
tebakan. (c) ditolak — "masih ada di list" tidak sama dengan "masih
buka": lowongan tutup tetap muncul di hasil pencarian yang di-cache.
**Yang berubah:** `check_active()` dibuat mengembalikan `bool` HANYA
untuk hasil pasti (200 + tanpa penanda tutup / 404); gagal teknis
(timeout/5xx) melempar error agar status lama jadi `unknown`, bukan
keliru `closed` — ini aturan baru yang TIDAK ada di ARCHITECTURE.md
awal (lihat ADR-0002).

### G3 — "Bagaimana kamu yakin deteksi aktif + posted_at itu benar? Apa celahnya?"

Celah yang ditemukan grill (semuanya dicatat, tidak disembunyikan):
1. **Repost**: perusahaan mem-posting ulang lowongan yang sama → URL/ID baru, `posted_at` baru, terlihat seperti lowongan baru. Deteksi naif ("tanggal baru = lowongan baru") akan menampilkan ghost job sebagai lowongan segar. **Mitigasi**: `fingerprint(title + company_norm + location)` — repost dengan isi sama mendapat fingerprint sama, normalizer menyimpan `first_seen_at` paling awal dan menandai "kemungkinan repost". Tidak sempurna (judul diubah sedikit lolos), tetapi lebih jujur daripada tidak ada.
2. **Tanggal relatif**: "1 bulan lalu" tidak bisa dipastikan ke tanggal kalender (±30 hari). **Mitigasi**: `parse_posted_at` mengembalikan `(tanggal, pasti)` — hanya tanggal absolut/ISO yang `pasti=True`; UI WAJIB menampilkan `first_seen_at` ("Pertama terlihat oleh kami: …") berdampingan dan menulis "tanggal sumber tidak tersedia" bila `posted_at` None (ARCHITECTURE.md §4).
3. **Zona waktu**: sumber menampilkan tanggal relatif terhadap zona servernya (belum tentu WIB). **Mitigasi**: `posted_at` disimpan sebagai `date` (bukan datetime), dan tanggal relatif dihitung terhadap tanggal fetch dalam Asia/Jakarta. Selisih ±1 hari diterima sebagai batas ketelitian — dan inilah alasan `posted_at` tidak pernah ditampilkan sendirian.
4. **Halaman di-cache / CDN**: halaman list yang di-cache bisa menampilkan lowongan yang sudah tutup, dan halaman detail yang di-cache bisa menyembunyikan penanda tutup. **Mitigasi**: `check_active` hanya mengandalkan halaman detail (bukan list), dan aturan 2x kunjungan berturut-turut hilang → `closed` (ARCHITECTURE.md §3) menahan satu kali cache basi. Tidak ada jaminan 100%.
5. **Penanda tutup tidak universal**: Glints memakai "This job was closed", Kalibrr "Ditutup." — situs lain bisa memakai teks lain (atau tanpa teks, hanya 404/redirect). **Mitigasi**: `check_active` memakai 3 sinyal (HTTP 404 → tutup; penanda teks → tutup; redirect ke list → tutup) dan adapter baru WAJIB mendokumentasikan penanda tutupnya di docstring.
**Yang berubah:** `posted_at` tidak lagi dianggap "tanggal buka yang pasti" — kontrak baru membedakan `posted_at` (klaim sumber, bisa perkiraan) vs `first_seen_at` (fakta pengamatan kami). Lihat ADR-0002.

### G4 — "Apa yang terjadi kalau satu sumber memblokir besok?"

**Jawaban:** (1) Adapter mati lewat `enabled=False` (1 baris + ADR),
bukan dengan menghapus kode — riwayat & alasan tetap terdokumentasi.
(2) Job yang sudah terindeks dari sumber itu TIDAK dihapus; statusnya
menjadi `unknown` (bukan `closed`) karena "tidak bisa dicek" ≠ "tutup".
(3) Sumber lain tetap jalan — inilah gunanya kontrak adapter yang sama.
(4) Worker WAJIB berhenti saat 403/429 (`SourceBlockedError`), bukan
memutar proxy/memalsukan UA — perilaku "melawan" itulah yang mengubah
pelanggaran ToS ringan menjadi bypass yang disengaja.
**Yang berubah:** `SourceBlockedError` dan `SourceNotPermittedError`
ditambahkan sebagai tipe error berbeda (blokir teknis vs larangan
legal), dengan perilaku worker yang berbeda untuk masing-masing.
Sebelumnya keduanya hanya "error".

### G5 — "Kenapa parser stdlib saja, tanpa BeautifulSoup/httpx?"

**Jawaban:** Data yang dipakai v1 tersemat sebagai JSON (JSON-LD
Glints, `__NEXT_DATA__` Kalibrr) — `json` + `re` + `html.parser`
sudah cukup. bs4/httpx menambah dependensi + permukaan serangan
rantai pasok tanpa manfaat yang terukur di v1. Kalau nanti ada sumber
yang butuh DOM berat (mis. halaman karier perusahaan dengan JS),
adapter itu boleh memakai Playwright/bs4 — tetapi sebagai dependensi
opsional adapter itu sendiri, bukan beban paket inti.
**Yang berubah:** tidak ada — keputusan ini justru dikuatkan grill.
Dicatat di ADR-0002 sebagai alternatif yang ditolak + kondisi
kapan boleh dipakai.

### G6 — "Kamu yakin sitemap Glints berisi URL lowongan dan JSON-LD ada? Kamu belum uji live!"

**Jawaban:** Tidak yakin — dan itu dicatat sebagai ASUMSI, bukan
klaim. robots.txt hanya membuktikan sitemap_index.xml
DIDEKLARASIKAN; isinya belum dibaca. Fetch teks halaman Glints tidak
menampilkan blok JSON-LD (kemungkinan dihapus oleh perender teks).
Karena itu `discover()` Glints diberi fallback yang jujur (menyaring
berdasarkan slug, gagal dengan error yang jelas bila sitemap kosong)
dan `parse_glints_job` punya fallback parsing HTML bila JSON-LD tak
ada. Satu uji live (1x ambil sitemap + 1x halaman detail) adalah
pekerjaan rumah pertama sebelum Fase 1 dinyatakan selesai — bukan
"nanti saja".
**Yang berubah:** dokumentasi menandai kedua asumsi itu secara
eksplisit + test tidak mengklaim "teruji live".

---

## 5. Rekomendasi adopsi / bangun / tunda

| Sumber | Putusan | Langkah berikut |
|---|---|---|
| Glints | **BANGUN** | Uji live 1x (sitemap + 1 halaman detail, cek JSON-LD ada/tidak). Lalu aktifkan discover terjadwal (1x/hari dulu). |
| Kalibrr | **BANGUN** | Uji live 1x (cek `__NEXT_DATA__` + parameter `?query=`). Batasi ke daftar kata kunci kurasi (tiap query ±15 hasil). |
| JobStreet | **TUNDA** | Giga: putuskan ajukan izin tertulis / SEEK API, atau lanjut tanpa JobStreet. Stub tetap ada + terdokumentasi. |
| Indeed | **TUNDA** | Global ditunda; alternatif global = Adzuna API + ATS langsung (tugas tim direct). |
| LinkedIn | **BUKAN sumber** | Hanya info perusahaan publik + link keluar (sesuai ARCHITECTURE.md §5). |

**Pekerjaan rumah sebelum Fase 1 selesai (uji live, bukan klaim):**
1. Ambil `https://glints.com/sitemap_index.xml` 1x — apakah ada sitemap lowongan + URL-nya cocok pola?
2. Ambil 1 halaman detail Glints — apakah JSON-LD `JobPosting` ada?
3. Ambil 1 halaman pencarian Kalibrr `?query=...` — apakah parameter bekerja + `__NEXT_DATA__` berisi job?
4. Baca penuh ToS Glints (K-JB6) + ToS Kalibrr (K-JB8) — Giga.
5. Putuskan nasib JobStreet (K-JB1) — Giga.

---

## 6. Istilah

> Bagian ini adalah kontribusi tim job-board untuk glossary proyek.
> **JANGAN edit `docs/glossary.md` langsung** — koordinator yang
> menggabungkan nanti. Definisi di bawah memakai bahasa Indonesia
> yang tajam dan konsisten dengan kode.

| Istilah | Definisi |
|---|---|
| **adapter** | Satu file Python yang tahu cara mengambil lowongan dari SATU sumber (situs job board / ATS) dan mematuhi kontrak `JobSourceAdapter` (`discover` / `fetch_job` / `check_active`). Adapter baru = 1 file + 1 test + 1 baris registry. |
| **discover** | Langkah adapter yang mengembalikan daftar URL halaman detail lowongan (dari sitemap / RSS / API resmi / halaman list publik). Tidak mengambil isi detail. |
| **fetch_job** | Langkah adapter yang mengambil SATU halaman detail lowongan dan mengembalikannya sebagai `RawJob` (termasuk penanda masih buka / sudah tutup). |
| **check_active** | Langkah adapter yang menjawab "lowongan ini masih buka?" dengan YA/TIDAK yang pasti. Gagal teknis (timeout/5xx) BUKAN jawaban "tidak" — status lama dipertahankan sebagai `unknown`. |
| **RawJob** | Struktur data mentah satu lowongan hasil adapter, sebelum normalisasi ke database: judul, perusahaan (mentah + ternormalisasi), lokasi, gaji, `posted_at`, URL sumber, dan `is_active`. |
| **posted_at** | Tanggal lowongan dibuka **menurut klaim sumber** (tertulis di halaman sumber). Bisa berupa tanggal pasti (ISO/"12 Nov 2026") atau perkiraan dari tanggal relatif ("2 hari lalu"). Bila sumber tidak menulis tanggal, nilainya kosong — JANGAN ditebak. |
| **first_seen_at** | Waktu (tanggal + jam) **scraper kami pertama kali melihat** lowongan itu masih buka. Ini fakta pengamatan kami, bukan klaim sumber — dan tidak sama dengan `posted_at`. |
| **last_seen_at** | Waktu terakhir scraper kami melihat lowongan itu masih buka. Dipakai bersama `first_seen_at` untuk membuktikan lowongan "masih aktif" dari waktu ke waktu. |
| **ghost job** | Lowongan yang tayang berbulan-bulan (atau di-repost berulang) padahal perusahaan tidak benar-benar merekrut — dipakai untuk memancing lamaran / membangun database CV. Sinyal red flag di flag engine (tayang >90 hari tanpa perubahan: −10). |
| **repost** | Lowongan yang sama diposting ulang dengan URL/ID baru sehingga tanggalnya terlihat baru. Dideteksi lewat `fingerprint` (judul + perusahaan + lokasi sama). |
| **fingerprint** | Hash (SHA-256, 32 karakter) dari judul + nama perusahaan ternormalisasi + lokasi. Dipakai normalizer untuk dedup: lowongan yang sama di dua sumber, atau repost dengan URL baru, punya fingerprint sama. |
| **company_norm** | Nama perusahaan yang sudah dibersihkan untuk dedup: imbuhan badan hukum ("PT", "CV", "Tbk", "Ltd") dibuang, spasi dirapikan, kapital diseragamkan. Nama asli tetap disimpan di `company_raw` dan tidak pernah dibuang. |
| **sitemap** | File XML yang dideklarasikan situs di robots.txt, berisi daftar URL halaman situs itu (beserta `lastmod`). Jalur discover paling resmi kedua setelah API resmi — karena disediakan situs itu sendiri untuk crawler. |
| **JSON-LD** | Blok JSON (`application/ld+json`) yang disematkan di halaman web untuk mesin pencari, berisi data terstruktur halaman itu. Di Glints diharapkan berisi `JobPosting` (judul, gaji, tanggal posting). |
| **`__NEXT_DATA__`** | Blok JSON (`<script id="__NEXT_DATA__">`) yang disematkan framework Next.js di tiap halaman, berisi seluruh data yang dipakai halaman itu. Di Kalibrr berisi data lowongan lengkap — lebih andal daripada parsing HTML. |
| **robots.txt** | File aturan di root sebuah situs (`/robots.txt`) yang menyatakan path mana yang BOLEH dan TIDAK BOLEH diambil crawler. Dipatuhi CekLoker; tetapi izin robots.txt BUKAN izin ToS — ToS bisa tetap melarang. |
| **ToS** (Terms of Service) | Syarat Layanan situs — perjanjian yang mengikat pengguna situs itu. Beberapa ToS (JobStreet/SEEK, Indeed) secara eksplisit melarang scraping/agregasi tanpa izin tertulis. Melanggar ToS bukan sekadar "diblokir" — ada risiko hukum. |
| **Chalice Search API v4** | Endpoint pencarian internal JobStreet (`/api/chalice-search/v4/search`) yang dipakai situsnya sendiri; tidak terdokumentasi publik. Merespons tanpa kunci ("no-auth") — tetapi itu BUKAN izin legal untuk memakainya. |
| **SEEK API** | API resmi grup SEEK (induk JobStreet) di developer.seek.com — butuh pengajuan + persetujuan, ditujukan untuk integrasi ATS/perekrut. Satu-satunya jalur legal memakai data JobStreet bila izin scraping tidak diberikan. |
| **Publisher API (Indeed)** | API pencarian lowongan publik Indeed yang lama (ber-key, untuk afiliasi). Sudah ditutup untuk developer baru dan berhenti mengembalikan data sejak ~2023. Tidak bisa dipakai lagi. |
| **polite delay** | Jeda antar-request ke satu domain (v1: 3 detik Glints/Kalibrr, 5 detik bila JobStreet/Indeed diizinkan nanti) supaya scraper tidak membanjiri server sumber. |
| **SourceNotPermittedError** | Error yang dilempar adapter yang DINONAKTIFKAN karena larangan legal (ToS/robots/login). Bukan bug — keputusan sadar yang terdokumentasi, beserta alternatif legalnya. |
| **SourceBlockedError** | Error saat sumber menolak request (HTTP 403/429/CAPTCHA). Worker harus berhenti sementara (backoff) — dilarang memutar proxy / memalsukan identitas untuk lolos. |

---

## 7. Artefak tim ini

| Artefak | Path |
|---|---|
| Kode adapter + parser + kontrak | `packages/scraper-core/scraper_core/` (`base.py`, `parsers.py`, `adapters/{glints,jobstreet,kalibrr,indeed}.py`) |
| Unit test (84 test) | `packages/scraper-core/tests/test_jobboard_adapters.py` |
| Fixture contoh buatan | `packages/scraper-core/tests/fixtures/` (8 file; data fiktif, bukan salinan halaman asli) |
| ADR sumber job board | `docs/adr/ADR-0001-sumber-job-board.md` |
| ADR kontrak adapter + deteksi aktif | `docs/adr/ADR-0002-kontrak-adapter-deteksi-aktif.md` |
| Riset ini | `docs/fase1-riset-jobboard.md` |

**Hasil test:** `python -m pytest` di `packages/scraper-core/` (venv `.venv`,
pytest 9.2.0, Python 3.12.3): **84 lolos, 0 gagal.** Tidak ada test
live (sengaja — lihat kepala file test).

**Catatan penomoran ADR:** tugas ini memerintahkan penomoran ADR khusus
CekLoker mulai 0001. Namun `docs/adr/` sudah berisi `ADR-0007-adopsi-vs-tulis-ulang.md`
(dari tim referensi GitHub, 15 Nov 2026) — ada tabrakan skema penomoran.
Dokumen 0001/0002 ini dibuat sesuai perintah tugas; koordinator perlu
memutuskan: renumber seri ini, atau terima dua seri (0001–0002 job-board
vs 0007 adopsi). Jangan diam-diam menimpa ADR-0007.
