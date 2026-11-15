# CekLoker — Arsitektur v1 (Blueprint)

> Status: **Blueprint dulu, bukan kode.** Dokumen ini jawaban atas pertanyaan Giga 2026-11-15:
> scraper daftar perusahaan yang sedang buka lowongan (masih aktif + jelas tanggal bukanya),
> lalu analisis Green Flag / Red Flag dari media sosial & sumber lain.
> Dipakai dulu oleh Giga sendiri sebagai pengguna pertama, lalu bisa dibuka jadi
> open source / layanan gratis / berbayar murah.

Bahasa dokumen: Indonesia. Semua istilah bisnis dijelaskan dengan bahasa gampang.

---

## 1. Ringkasnya: produk ini apa?

**Satu kalimat:** Website yang menjawab 2 pertanyaan pencari kerja sebelum melamar —
_"Lowongan ini masih buka beneran, sejak kapan?"_ dan _"Perusahaan ini aman atau bermasalah?"_

**3 janji produk (yang membedakan dari JobStreet / LinkedIn biasa):**

1. **Status aktif itu diverifikasi, bukan sekadar tanggal posting.**
   Setiap lowongan disimpan `posted_at` (tanggal yang ditulis sumber),
   `first_seen_at` (kapan pertama kali scraper kami melihatnya),
   `last_seen_at` (kapan terakhir kali masih terlihat buka),
   dan `status`: `active | closed | expired | unknown`.
   Kalau lowongan hilang dari sumber / halaman jadi 404 / tombol lamar hilang,
   status berubah jadi `closed`, bukan terus tampil sebagai "masih buka".

2. **Green / Red Flag itu transparan, bukan label hitam-putih.**
   Setiap perusahaan dapat skor 0–100 + rincian per sinyal + tautan bukti + tanggal bukti.
   Contoh: "Gaji dicantumkan di 8/10 lowongan (+15)" dengan link ke lowongan itu.
   Tidak ada skor tanpa bukti yang bisa diklik.

3. **Murah dijalankan, gampang dibuka jadi open source.**
   Mulai dari 1 VPS / free-tier, modular monolith dulu, bukan microservices.
   Semua adapter sumber dipisah jadi plugin — kontributor bisa nambah 1 situs
   tanpa menyentuh inti aplikasi.

**Yang BUKAN produk ini (v1):** bukan job board untuk posting lowongan,
bukan konsultan HR, bukan penilai hukum ("perusahaan ini melanggar UU" —
kami hanya menampilkan sinyal + bukti, keputusan tetap di pengguna).

---

## 2. Keputusan arsitektur utama

| Keputusan | Pilihan v1 | Alasan |
|---|---|---|
| Bentuk awal | **Modular monolith** (1 repo, 3 modul jelas: `web`, `api`, `scraper-worker`) | 1 orang yang rawat. Microservices di awal = biaya + debugging 3x lipat, tanpa manfaat. Pecah nanti kalau 1 modul sudah berat sendiri. |
| Bahasa backend + scraper | **Python 3.12 + FastAPI** | Ekosistem scraping + NLP Python paling lengkap (Playwright, httpx, BeautifulSoup). Giga sudah pakai pola ini di Panen Tanam (FastAPI). Satu bahasa untuk API + worker + analisis. |
| Bahasa frontend | **TypeScript + Next.js (App Router) + Tailwind** | Standar untuk website open source, gampang dicari kontributor, SEO penting (halaman perusahaan/lowongan harus terindeks Google). |
| Database utama | **PostgreSQL 16** | Butuh relasi + pencarian teks + JSON untuk bukti sinyal. Satu DB untuk semua di v1, jangan tambah Mongo/Elasticsearch dulu. |
| Antrean + scheduler | **Redis + RQ (atau arq) + APScheduler** di worker | Ringan, cukup untuk ribuan lowongan/hari. Celery terlalu berat untuk v1. |
| Cache + rate-limit | **Redis** (yang sama) | Cache halaman perusahaan populer + batasi request scraper per domain. |
| Penyimpanan mentah | **Object storage S3-compatible** (MinIO self-host / R2 / S3) untuk snapshot HTML | Bukti: simpan snapshot halaman lowongan saat pertama dilihat, supaya klaim "dulu buka tanggal X" bisa dibuktikan. Jangan simpan di Postgres. |
| Pencarian | **Postgres Full-Text + pg_trgm dulu**, Meilisearch nanti | v1 belum butuh search engine terpisah. Tambah Meilisearch kalau pencarian sudah lambat / butuh typo-tolerance serius. |
| Auth v1 | **Single-user dulu: 1 akun Giga (email + password + session JWT)** | Sesuai permintaan: awalnya Giga sebagai pengguna. Multi-user, OAuth Google, dan watchlist publik masuk Fase 3. |
| Deployment v1 | **Docker Compose di 1 VPS** | 1 perintah `docker compose up` jalan semua. Alternatif $0 ada di §7. |
| Lisensi (rencana open source) | **MIT** | Paling bebas, sama seperti Godot / library Archodin. Cocok untuk adopsi komunitas. Kode scraper adapter yang melanggar ToS situs tertentu harus bisa dimatikan lewat config, bukan dihapus diam-diam. |

### Kenapa bukan full Rust / full Kotlin di sini?

Bukan karena Rust/Kotlin jelek — Archodin pakai Rust, Panen Tanam pakai Kotlin.
Tapi untuk proyek ini, yang paling menentukan adalah:

- **Scraper:** library Python (Playwright, Scrapy) jauh lebih matang + contohnya banyak.
- **Analisis teks Indonesia:** model + library NLP Python paling siap (lihat §5).
- **Kontributor open source:** Python + Next.js adalah kombinasi yang paling
  gampang direkrut kontributornya dibanding Rust + Kotlin untuk website lowongan.

Aturan praktisnya: pakai alat yang bikin v1 selesai, bukan alat yang paling keren.

---

## 3. Gambaran sistem

```
                         ┌────────────────────┐
                         │  Sumber lowongan   │
                         │ Glints, JobStreet, │
                         │ Kalibrr, LinkedIn* │
                         │ Karier perusahaan, │
                         │ Indeed, Glassdoor* │
                         └────────┬───────────┘
                                  │ (1) Adapter per sumber
                                  ▼
┌──────────────┐      ┌──────────────────────┐      ┌──────────────────┐
│  Scheduler   │─────▶│  Scraper Worker      │─────▶│  Normalizer      │
│  (kapan      │      │  Playwright + httpx  │      │  Bersihkan data, │
│  cek ulang?) │      │  Sopan: 1 req / 2-5  │      │  samakan format, │
└──────────────┘      │  dtk per domain      │      │  dedup perusahaan│
                      └──────────┬───────────┘      └────────┬─────────┘
                                 │                           │
                      ┌──────────▼───────────────────────────▼──────────┐
                      │  PostgreSQL                                      │
                      │  companies, jobs, job_snapshots, signals,       │
                      │  evidences, reviews, sources                    │
                      └──────────┬──────────────────────────────────────┘
                                 │
              ┌──────────────────┼──────────────────┐
              ▼                  ▼                  ▼
   ┌──────────────────┐ ┌───────────────┐ ┌───────────────────┐
   │  Flag Engine     │ │  FastAPI      │ │  Next.js Web      │
   │  (rule-based v1) │ │  REST API     │ │  Daftar, detail,  │
   │  Skor + bukti    │ │  /api/v1/...  │ │  cari, filter,    │
   │  Lihat §5        │ │  + admin      │ │  profil perusahaan│
   └──────────────────┘ └───────────────┘ └───────────────────┘
```

### Alur data lowongan (paling penting)

1. **Discover:** Scheduler minta adapter `Sumber A` daftar lowongan baru
   (halaman list / sitemap / RSS / API resmi kalau ada).
2. **Fetch detail:** Worker ambil halaman detail lowongan, simpan snapshot HTML
   mentah + ekstrak field (lihat §4).
3. **Normalize:** Samakan nama perusahaan ("PT ABC", "ABC Indonesia" → 1 entitas),
   lokasi, gaji, tipe kerja. Buat fingerprint `hash(url + judul + perusahaan)`
   untuk dedup antar sumber.
4. **Track aktif:** Setiap kunjungan ulang update `last_seen_at`.
   Kalau 2x kunjungan berturut-turut lowongan tidak ditemukan → `closed`.
   Kalau `posted_at` > 60 hari dan tidak ada update → `expired` (aturan bisa diubah per sumber).
5. **Flag:** Flag Engine hitung ulang skor perusahaan kalau ada lowongan / ulasan / sinyal baru.
6. **Tampil:** Web tampilkan lowongan aktif saja secara default, dengan filter
   tanggal buka, lokasi, gaji, dan skor flag.

---

## 4. Model data (inti saja)

```sql
-- Perusahaan: 1 baris per perusahaan asli, bukan per nama tulisan lowongan
companies (
  id uuid PK,
  name text,                    -- nama kanonik, mis. "PT Maju Bersama"
  aliases text[],               -- ["Maju Bersama", "PT Maju Bersama Tbk"]
  website text, linkedin_url text, glassdoor_url text,
  industry text, size_range text, location_hq text,
  created_at timestamptz, updated_at timestamptz
)

-- Lowongan: 1 baris per lowongan di 1 sumber (bisa dobel antar sumber, didedup di view)
jobs (
  id uuid PK,
  company_id uuid FK,
  source_id uuid FK,            -- Glints / JobStreet / dst.
  source_url text UNIQUE,       -- URL asli lowongan
  title text, location text, work_type text, -- onsite/hybrid/remote
  salary_min int, salary_max int, salary_currency text, -- IDR, null = tidak dicantumkan
  posted_at date,               -- tanggal yang ditulis sumber (bisa null)
  expires_at date,
  first_seen_at timestamptz,    -- kapan scraper pertama lihat
  last_seen_at timestamptz,     -- kapan terakhir masih buka
  status text,                  -- active | closed | expired | unknown
  description_text text,        -- teks bersih (bukan HTML penuh)
  fingerprint text,             -- hash untuk dedup
  raw_snapshot_key text         -- kunci file snapshot di object storage
)

-- Snapshot: bukti historis, append-only (jangan dihapus/diubah)
job_snapshots (
  id uuid PK, job_id uuid FK,
  seen_at timestamptz, status text,
  snapshot_key text, hash text
)

-- Sinyal flag: 1 baris = 1 bukti yang bisa diklik
signals (
  id uuid PK, company_id uuid FK,
  category text,                -- lihat §5
  key text,                     -- mis. "salary_transparency"
  value numeric, points int,    -- kontribusi ke skor
  evidence_url text, evidence_text text, -- kutipan singkat
  evidence_date date, source text,
  confidence text               -- high | medium | low
)
```

**Aturan tanggal (jawaban untuk "jelas dia membukanya dari tanggal berapa"):**

- Tampilkan **dua tanggal** di UI: `Dibuka (klaim sumber): 12 Nov 2026`
  dan `Pertama terlihat oleh kami: 12 Nov 2026, 09:14 WIB`.
- Kalau `posted_at` dari sumber tidak ada / tidak bisa dipercaya, tulis
  "Tanggal sumber tidak tersedia — pertama terlihat 12 Nov 2026" — jangan ditebak.
- Jangan pernah tampilkan `first_seen_at` sebagai `posted_at`. Itu dua hal berbeda.

---

## 5. Green Flag / Red Flag Engine

### Prinsip (supaya tidak jadi fitnah)

1. **Skor tanpa bukti = tidak tampil.** Setiap poin skor harus punya `evidence_url` + tanggal.
2. **Skor itu ringkasan, bukan vonis.** Labelnya: `Green (70–100)`, `Mixed (40–69)`,
   `Red (0–39)`, `Belum cukup data` (kalau sinyal < 3). Selalu ada tombol "Lihat bukti".
3. **Sumber yang dikutip, bukan disalin mentah.** Simpan kutipan singkat + link,
   bukan seluruh isi ulasan / postingan orang. Hormati hak cipta + privasi.
4. **Perusahaan bisa membantah / minta koreksi.** Sediakan form koreksi + halaman
   "cara kami menilai" yang terbuka. Ini penting kalau nanti dibuka publik.
5. **Jangan tampilkan data pribadi pelamar.** Nama reviewer anonim, jangan
   tampilkan nama orang dari media sosial tanpa izin.

### Skor v1: rule-based dulu (bukan AI dulu)

Total skor DINORMALISASI terhadap kategori yang sudah terukur
(D7, disetujui Giga 15 Nov 2026 — lihat ADR-0005 Amandemen D7; rumus
penjumlahan mentah tidak lagi berlaku):

    total = 100 × perolehan / cap terukur

dengan *cap terukur* = jumlah cap kategori yang punya sinyal penentu
(mis. hanya reputasi 25 + stabilitas 20 yang terukur → cap terukur 45,
bukan 100). Kategori yang belum terukur tidak masuk penyebut — "belum
diukur" tidak disamakan dengan "buruk". Bila 0 kategori terukur, total
tidak ada (None), bukan 0 — labelnya "Belum cukup data". AI / sentimen
ML baru Fase 4, setelah rule-based terbukti berguna.

| Kategori (bobot) | Sinyal contoh (v1) | Green (+) | Red (−) |
|---|---|---|---|
| **Transparansi lowongan (25)** | Gaji dicantumkan; deskripsi tugas jelas; lokasi + tipe kerja jelas; tidak minta biaya / "adm" | Gaji ada di ≥70% lowongan: +15; deskripsi lengkap: +10 | Minta biaya pendaftaran: **langsung Red + cantumkan peringatan**; gaji tidak pernah dicantumkan: −10 |
| **Reputasi & ulasan (25)** | Rating Glassdoor / JobStreet / Google Review; rasio ulasan positif; keluhan berulang | Rating ≥4.0 dari ≥20 ulasan: +15 | Rating <2.5, atau keluhan sama (lembur tak dibayar, PHK sepihak) muncul ≥5x: −15 |
| **Stabilitas & legalitas (20)** | Umur perusahaan; terdaftar resmi (cek nama PT); berita PHK massal / pailit | Berdiri ≥5 thn + terdaftar: +10 | Berita PHK massal / tutup dalam 12 bln terakhir: −15 |
| **Praktik rekrutmen (15)** | Kecepatan respon; lowongan "hantu" (tayang berbulan-bulan tanpa hiring); wawancara berlapis tak wajar | Update status lowongan rutin: +5 | Lowongan sama tayang >90 hari tanpa perubahan / ghost job: −10 |
| **Gaji & benefit (15)** | Gaji vs UMR / pasar; BPJS disebut; benefit jelas | Gaji di atas UMR + BPJS disebut: +10 | Gaji di bawah UMR untuk kerja full-time: −15 + label peringatan |

**Contoh tampilan:** "Skor 72/100 — Mixed. +15 gaji transparan (8/10 lowongan),
−15 keluhan lembur berulang (5 ulasan, link), +10 berdiri 8 tahun. Data terakhir 15 Nov 2026."

### Dari mana sinyal sosialnya?

Urutan prioritas (yang legal & paling bisa diandalkan dulu):

1. **Sumber resmi / terstruktur:** Glassdoor, JobStreet Company Review,
   Google Maps review, LinkedIn company page (info publik).
2. **Berita:** pencarian berita (PHK, ekspansi, pendanaan, kasus hukum).
3. **Media sosial publik:** X/Twitter, Reddit, Kaskus, TikTok/IG publik —
   **hanya lewat API resmi / pencarian publik, jangan login palsu / bypass.**
   Ambil tren + kutipan, bukan scraping massal akun pribadi.
4. **Laporan pengguna (Fase 3):** pengguna terverifikasi bisa lapor pengalaman,
   dimoderasi dulu sebelum memengaruhi skor.

**Yang TIDAK dilakukan:** scraping DM / grup tertutup, scraping LinkedIn
dengan akun palsu, bypass login/paywall, atau menyimpan password orang.
LinkedIn dan sebagian situs melarang scraping di ToS-nya dan aktif memblokir —
jadi LinkedIn di v1 hanya sebagai sumber info perusahaan publik + link keluar,
bukan sumber lowongan utama. Sumber utama v1: **Glints + JobStreet + Kalibrr +
halaman karier perusahaan** (yang strukturnya paling terbuka di Indonesia).

> Risiko jujur: situs bisa berubah layout / memblokir kapan saja.
> Karena itu setiap adapter dibungkus interface yang sama — kalau 1 situs mati,
> yang lain tetap jalan, dan adapter itu tinggal diperbaiki sendiri.

---

## 6. Modul & struktur repo (monorepo)

```
.
├── apps/
│   ├── web/                   # Next.js + Tailwind (halaman publik)
│   │   └── src/app/ (daftar, /jobs/[id], /companies/[slug], /tentang-skor)
│   └── api/                   # FastAPI (REST /api/v1)
│       ├── app/routers/       # jobs, companies, signals, admin
│       ├── app/models/        # SQLAlchemy
│       └── app/services/      # flag_engine, dedup, search
├── packages/
│   ├── scraper-core/          # Python package: interface adapter + scheduler
│   │   ├── adapters/          # glints.py, jobstreet.py, kalibrr.py, career_page.py
│   │   ├── normalizer.py      # bersih + dedup perusahaan/lowongan
│   │   └── politeness.py      # rate-limit, robots.txt, retry, user-agent
│   └── flag-engine/           # Aturan skor (bisa diuji unit test tanpa DB)
├── infra/
│   ├── docker-compose.yml     # web + api + worker + postgres + redis + minio
│   └── caddy/                 # reverse proxy + HTTPS otomatis
├── docs/
│   ├── ARCHITECTURE.md        # dokumen ini
│   ├── SCORING.md             # rubrik skor lengkap + contoh
│   ├── ADAPTER_GUIDE.md       # cara nambah 1 sumber baru (untuk kontributor)
│   └── LEGAL.md               # ToS, robots.txt, opt-out, koreksi data
├── .env.example
├── README.md
└── LICENSE (MIT)
```

**Kontrak adapter (semua sumber wajib ikut):**

```python
class JobSourceAdapter:
    source_id: str          # "glints"
    def discover(self) -> list[str]: ...        # kembalikan URL lowongan
    def fetch_job(self, url: str) -> RawJob: ...# detail + posted_at + snapshot
    def check_active(self, url: str) -> bool: ...  # masih buka?
```

Adapter baru = 1 file + 1 test + 1 baris di config. Tanpa itu, jangan merge.

---

## 7. Biaya & hosting (supaya tetap murah)

**Target: $0 di MVP (free-tier), ≤ ~Rp150 ribu/bulan saat sudah ramai.**

| Kebutuhan | Opsi $0 (MVP) | Opsi murah saat ramai |
|---|---|---|
| Frontend | Vercel Hobby (free) | Tetap Vercel / VPS |
| API + Worker | Railway trial / Fly.io free tier / VPS | 1 VPS Hetzner/Contabo ~€5/bln |
| Postgres | Neon free tier (3 GB) / Supabase free | VPS yang sama (Docker) |
| Redis | Upstash free tier | VPS yang sama (Docker) |
| Snapshot HTML | Cloudflare R2 free tier (10 GB) | MinIO di VPS |
| Domain `.com/.id` | ~Rp150–200 ribu/tahun (satu-satunya biaya wajib) | Sama |

**Jalur yang disarankan untuk Giga (mulai dari yang sudah dimiliki):**
VPS / home server yang sama seperti rencana Archodin (Agora) bisa dipakai juga
di sini — 1 Docker Compose berisi semua service. Kalau mau tanpa urus server,
pakai kolom "$0" di atas. Jangan bayar apa pun sebelum ada pengguna selain Giga.

---

## 8. Keamanan, legal & etika — jangan dilewati

- **Sopan saat scraping:** patuhi `robots.txt`, delay 2–5 detik per domain,
  `User-Agent` jelas berisi kontak, jangan request bersamaan membabi-buta.
- **Jangan bypass login / paywall / CAPTCHA.** Kalau sumber butuh login,
  jangan diakali — cari sumber lain, atau pakai API resmi.
- **Jangan simpan data pribadi pelamar.** Yang disimpan: info perusahaan +
  lowongan publik + kutipan ulasan publik (dengan link).
- **Opt-out perusahaan:** perusahaan bisa minta lowongannya tidak diindeks /
  minta koreksi skor — prosesnya ada di `docs/LEGAL.md`, ditanggapi ≤ 7 hari.
- **Keamanan:** secret hanya di `.env`, tidak pernah di-commit.
  Rate-limit API publik, validasi input, jangan tampilkan stack trace ke publik.
- **Disclaimer skor:** "Skor ini ringkasan sinyal publik, bukan penilaian hukum
  atau jaminan. Selalu cek langsung ke perusahaan sebelum memutuskan."

---

## 9. Fase (jalan bertahap, tiap fase bisa dipakai)

| Fase | Isi | Selesai kalau… |
|---|---|---|
| **Fase 0 — Blueprint** | Dokumen ini + `SCORING.md` + struktur repo kosong | Giga setuju stack + nama + sumber pertama |
| **Fase 1 — MVP Scraper** | Adapter Glints + JobStreet, tracking aktif, web daftar + detail lowongan, 1 akun (Giga) | 500+ lowongan aktif terindeks, status aktif terbukti berubah saat lowongan ditutup |
| **Fase 2 — Flag v1** | Rule-based scoring + ulasan Glassdoor/JobStreet + halaman profil perusahaan | 50 perusahaan punya skor + bukti yang bisa diklik |
| **Fase 3 — Multi-user** | Registrasi, watchlist perusahaan, alert lowongan baru (email), laporan pengguna + moderasi | Giga + 10 pengguna uji bisa pakai tanpa bantuan |
| **Fase 4 — Sosial + ML** | Agregasi sinyal X/Reddit/berita + sentimen (model lokal / API murah), deteksi ghost job & lowongan palsu | Akurasi sentimen diuji di 200 contoh, bukan asal klaim |
| **Fase 5 — Open source** | README + CONTRIBUTING + ADAPTER_GUIDE + CI + rilis MIT | Orang luar bisa `docker compose up` dan nambah adapter tanpa tanya Giga |

**Yang sengaja ditunda:** aplikasi mobile, API publik berbayar, monetisasi.
Monetisasi (kalau nanti ada) yang paling jujur untuk produk ini: donasi /
langganan murah untuk alert lanjutan — **bukan** menjual data pelamar,
**bukan** memprioritaskan perusahaan berbayar di hasil pencarian tanpa label.
Kalau ada "featured" berbayar, wajib label jelas "Iklan".

---

## 10. Keputusan yang masih butuh jawaban Giga (D1–D5)

| ID | Pertanyaan | Usulan default (kalau Giga belum jawab) |
|---|---|---|
| **D1** | Nama proyek + nama repo GitHub? | **DIPUTUSKAN 2026-11-15: `cekloker` (Gigajn/cekloker, private)** |
| **D2** | Sumber pertama (Fase 1)? | **Glints + JobStreet** dulu (paling terbuka, lowongan Indonesia terbanyak) |
| **D3** | Scope wilayah? | **Indonesia dulu** (Jakarta, Bandung, Surabaya, Yogyakarta, remote Indonesia) |
| **D4** | Hosting awal? | **Docker Compose di VPS/home server** (sama seperti rencana server Giga) — atau free-tier Vercel+Neon kalau mau $0 |
| **D5** | Visibilitas repo? | **Private dulu** saat Fase 0–1, dibuka publik (MIT) saat Fase 5. Jangan publik sebelum skor + legal docs siap. |

---

## 11. Soal GitHub: bisakah Muse buatkan repo-nya langsung?

Jawaban jujur, dari pengalaman sebelumnya (Panen Tanam, 2026-11-10)
dan percobaan langsung untuk repo ini (2026-11-15 00:14 WIB):

- GitHub Giga **sudah terhubung** ke Muse (status `connected`, akun `Gigajn`).
- Tapi pembuatan repo baru lewat integrasi GitHub Muse **gagal lagi** dengan
  `403 Resource not accessible by integration` — integrasi ini tidak punya izin
  membuat repository baru, hanya bisa mengisi repo yang sudah ada.
  Dicek dulu: `Gigajn/cekloker` belum ada (search 0 hasil), lalu `create_repository`
  ditolak 403.
- Jadi langkahnya: **Giga buat repo kosong di github.com (1 menit, nama dari D1),
  lalu Muse yang isi semua file awal + push + verifikasi per file** — pola yang
  sama dan sudah berhasil untuk Panen Tanam & Archodin (PR #52–#57).
- Kalau nanti ternyata `create_repository` tiba-tiba bisa, Muse akan coba dulu
  dan laporkan hasilnya — tidak akan diam-diam mengklaim berhasil tanpa verifikasi.

Setelah repo dibuat, yang Muse push pertama: `ARCHITECTURE.md` (dokumen ini),
`README.md`, `docs/SCORING.md`, `.env.example`, `docker-compose.yml` skeleton,
`.gitignore`, `LICENSE` (MIT), dan struktur `apps/` + `packages/` kosong berisi
`README` penanda — supaya repo langsung bisa diklon dan dipahami orang lain.

---

*Disusun 2026-11-15 untuk Giga. Blueprint ini bukan janji "scraper tidak akan
pernah diblokir" — itu risiko nyata semua scraper. Yang dijanjikan di sini:
arsitektur yang membuat 1 sumber mati tidak mematikan seluruh produk.*
