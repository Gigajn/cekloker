# ADR-0009 — API + Database CekLoker (FastAPI, Postgres, Auth 1 Akun)

- **Status:** Diterima (Tim API + Database, Fase 1-lanjutan, 15 Nov 2026).
- **Tanggal:** 15 November 2026
- **Terkait:** `ARCHITECTURE.md` §3, §4, §6, §9; `docs/decisions-d6-d12.md`
  (D7, D8, D10); `docs/fase1-konsolidasi.md` §3 (K4), §8; ADR-0002
  (kontrak adapter + deteksi aktif), ADR-0005 (rubrik + normalisasi),
  ADR-0006 (anti-fitnah + K4); `apps/api/` (implementasi).

## Konteks

Fase 1 selesai tanpa API, web, atau database (`fase1-konsolidasi.md` §8).
Fase 1-lanjutan butuh ketiganya supaya lowongan hasil scraper bisa
disimpan, ditampilkan, dan dicek ulang status aktifnya — dengan aturan:
skor ternormalisasi (D7, Giga setuju), alat pribadi 1 akun dulu (D8),
$0 tanpa API berbayar (D10), JobStreet/Indeed/LinkedIn tetap stub (D6),
dan perbaikan K4 (`signals.evidence_text` boleh null, wajib kosong
untuk `google_places`).

Dokumen ini mencatat hasil grill (ala Matt Pocock) atas tiap keputusan
desain API/DB: pertanyaan grill, jawaban, dan alternatif yang ditolak.

## Keputusan

### 1. FastAPI + SQLAlchemy 2.0 + Pydantic v2, modular monolith

Sesuai ARCH §2/§6. Satu proses API melayani `/api/v1/*`; worker recheck
satu modul yang sama (`app/worker.py`) supaya tidak ada duplikasi model.
Tidak ada microservices, tidak ada framework kedua.

### 2. PostgreSQL 16 produksi; SQLite hanya untuk dev/test

Postgres adalah database utama (ARCH §2). SQLite dipakai file lokal di
dev dan in-memory di test karena docker TIDAK tersedia di VM ini —
bukan karena SQLite "cukup" untuk produksi. Model SQLAlchemy ditulis
supaya SATU model jalan di keduanya (`Uuid` generik, `JSON` generik,
CHECK constraint yang sama). **Batas jujur:** test SQLite tidak menguji
tipe Postgres-spesifik (`jsonb`, `gen_random_uuid`); skema Postgres
penuh diverifikasi statis di `tests/test_migration.py` dan eksekusi
`001_init.sql` di Postgres asli masih menunggu docker-compose di
mesin Giga (lihat "Yang belum terverifikasi").

### 3. Migrasi = satu file SQL, bukan Alembic

**Grill:** "Untuk proyek 1 orang dengan 1 skema awal, apa yang Alembic
beri selain satu dependensi + satu rantai perintah lagi?"
**Jawaban:** `migrations/001_init.sql` — satu file yang bisa dibaca dan
direview langsung, cerminan ARCH §4, idempotent (aman 2x), dijalankan
dengan `psql`. Alembic ditunda; bila skema sudah berubah > 2-3x, pindah
ke Alembic lewat ADR baru. Yang hilang dari pilihan ini: riwayat migrasi
otomatis + downgrade — diterima untuk v1, dicatat di sini supaya tidak
dianggap "lupa".

### 4. Penyimpangan dari ARCH §4 (dicatat, bukan diam-diam)

| Penyimpangan | Alasan |
|---|---|
| `companies.aliases` JSON/`jsonb`, bukan `text[]` | Satu model SQLAlchemy jalan di SQLite (test) dan Postgres. Array Postgres tidak ada di SQLite. |
| `jobs.missed_checks` (int, default 0) | Dibutuhkan aturan "2x kunjungan hilang -> closed" (ARCH §3, ADR-0002 §2). Tanpa kolom ini worker harus menghitung dari `job_snapshots` tiap kali — lebih lambat + lebih rapuh. |
| `jobs.board_url` (nullable) | Worker butuh URL board ATS untuk menghidupkan `CareerPageAdapter` saat recheck. Tanpa ini, lowongan ATS tidak bisa dicek ulang. |
| `jobs.posted_at_certain` (boolean) | Flag kepastian tanggal dari ADR-0002 — sudah ada di `RawJob`, harus tersimpan supaya UI tidak menampilkan perkiraan sebagai tanggal pasti. |
| `signals.value` JSON/`jsonb`, bukan `numeric` | Nilai sinyal flag-engine bisa dict (`complaint_repeated`: jumlah per cluster) atau bool (`fee_request`), bukan hanya angka. |
| `signals.decisive` + `red_override` (boolean) | Dibaca langsung dari flag-engine (ADR-0005) supaya skor bisa dihitung dari DB tanpa memanggil ulang fungsi sosial. |
| Tabel `sources`, `admin_users`, `admin_sessions` | `sources` menampung status enabled adapter (JobStreet/Indeed `enabled=false` di data, bukan cuma di kode); dua tabel admin untuk auth 1 akun (butir 6). |

### 5. Perbaikan K4 — `evidence_text` NULLABLE + CHECK google_places

`signals.evidence_text` NULLABLE; constraint
`(source <> 'google_places' OR evidence_text IS NULL)` ditegakkan DI
DATABASE (bukan cuma di kode aplikasi) — diuji lewat `IntegrityError`
(`tests/test_scoring.py`). Alasan grill: "Bila hanya dicek di kode,
satu jalur tulis baru (import massal, script darurat) bisa melanggar
aturan Places API tanpa ketahuan." Seed membuktikan: sinyal Google
Places disimpan dengan `evidence_text = NULL`.

### 6. Auth: 1 akun Giga, email + password, session token di DB

**Grill:** "Kenapa bukan JWT? Kenapa bukan OAuth Google?"
**Jawaban:** JWT butuh library + manajemen kunci + tidak bisa dicabut
tanpa daftar blokir — untuk 1 pengguna, token acak di DB lebih
sederhana DAN bisa dicabut (hapus baris sesi). OAuth Google ditolak
oleh D8 (alat pribadi dulu, Fase 3) dan D10 ($0 — tanpa layanan auth
berbayar). Password di-hash **PBKDF2-HMAC-SHA256 stdlib** (600.000
iterasi, salt acak 16 byte) — tanpa bcrypt/passlib, tanpa menyimpan
password mentah. Yang disimpan di DB hanya SHA-256 token, bukan tokennya.
Token berlaku 7 hari. Kegagalan login selalu 401 yang sama (jangan
bocorkan apakah emailnya ada). Akun admin HANYA dibuat lewat seed dari
env (`CEKLOKER_ADMIN_EMAIL` / `CEKLOKER_ADMIN_PASSWORD`) — tidak ada
default password di kode, tidak ada credential di file.

### 7. Skor dibaca dari flag-engine, bukan dihitung ulang

**Grill:** "Bila API menghitung skor sendiri, apa yang menjamin angkanya
sama dengan flag-engine bila ambang berubah?"
**Jawaban:** API TIDAK punya rumus sendiri sebagai sumber kebenaran.
`services/scoring.py` memetakan baris `signals` -> dataclass
`social_signals.Signal` -> `aggregate_signals` (ADR-0005, D7):
total ternormalisasi, label butuh >= 3 sinyal penentu dari >= 2 kategori,
"Belum cukup data" -> `score: null`, fee -> Red + peringatan.
**Jalur darurat:** bila `social_signals` tidak bisa diimpor, dipakai
rumus lokal yang SAMA dan hasilnya ditandai `engine="fallback"`.
Test membuktikan kedua jalur memberi angka yang sama untuk data yang
sama — bila suatu hari berbeda, itu bug, bukan "dua versi skor".
Perubahan ambang tetap lewat ADR (ADR-0005 butir 10).

### 8. `skor_min` dan filter skor dihitung di Python, bukan di SQL

**Grill:** "Kenapa tidak kolom skor terdenormalisasi di `companies`?"
**Jawaban:** Skor adalah fungsi dari sinyal yang berubah (sinyal baru
masuk -> skor berubah). Kolom terdenormalisasi butuh pemicu update di
setiap jalur tulis — v1 belum punya semua jalur tulis itu. Untuk skala
v1 (ribuan lowongan), hitung per perusahaan per request + cache per
request sudah cukup. **Batas yang dicatat:** bila daftar sudah puluhan
ribu lowongan, pindahkan ke kolom `companies.score_cached` + update saat
sinyal berubah — lewat ADR baru, bukan diam-diam.

### 9. Refresh admin sinkron + berbatas, bukan antrean

**Grill:** "Refresh 100 lowongan x jeda sopan 3 detik = 5 menit request
HTTP. Kenapa tidak antrean?"
**Jawaban:** Karena ini alat pribadi 1 pengguna (D8/D9). Antrean
(Redis + RQ, ARCH §2) adalah infrastruktur yang benar untuk produksi,
tapi menambah 1 service + 1 pola failure untuk kebutuhan yang sekarang
20 lowongan per klik. Refresh dibatasi (default 20, maks 100) dan
terdokumentasi sebagai batas — bila suatu hari menangani ribuan
lowongan, pindah ke antrean lewat ADR, jangan naikkan limit diam-diam.

### 10. Worker: aturan 2x hilang + `unknown` untuk gagal teknis

Sesuai ADR-0002 §2 dan ARCH §3. `check_active` False SEKALI hanya
menaikkan `missed_checks`; status baru `closed` di kunjungan hilang
ke-2. Gagal teknis -> `unknown` (jangan pernah `closed` dari timeout).
Setiap kunjungan dicatat `job_snapshots` (append-only, bukti).
Worker JANGAN jalan otomatis massal saat dev: `--once` manual, atau
`--interval` eksplisit. Jeda antar request mengikuti
`WORKER_DELAY_S` (default 3 detik, sopan).
**Batas:** `CareerPageAdapter.check_active` untuk board ATS mengembalikan
False juga bila board gagal dibaca (bukan hanya bila lowongan hilang)
— aturan 2x di atas yang menahan kerusakan dari satu kegagalan baca,
tapi tetap dicatat: deteksi "board gagal dibaca" vs "lowongan hilang"
di adapter adalah perbaikan yang masih terbuka untuk Tim Scraper
(bukan wewenang tim ini).

### 11. API tetap start walau scraper-core / flag-engine tidak ter-mount

**Grill:** "Bila paket scraper tidak ada, haruskah seluruh API mati?"
**Jawaban:** Tidak. Endpoint baca (janji produk ke web) tidak boleh mati
karena paket scraper belum ter-mount. `scraper_import.py` memakai
fallback: skor memakai rumus lokal bertanda `fallback`, worker recheck
mengembalikan `skipped` untuk semua job. Di Docker, `PYTHONPATH` sudah
diatur di image sehingga jalur utama yang dipakai; fallback hanya
pengaman saat mount lupa.

### 12. Error JSON konsisten, tanpa stack trace

Semua error berbentuk `{"error": {"code", "message", "details"?}}`,
termasuk 401 auth dan 422 validasi. 500 memakai pesan generik;
traceback hanya ke log server (ARCH §8). Test membuktikan respons
tidak mengandung kata "Traceback"/"stack".

## Kontrak bersama Tim Web (JANGAN diubah sepihak)

- job = `{id, title, company{name,slug}, location, work_type,
  salary_min, salary_max, salary_currency, posted_at,
  posted_at_certain, first_seen_at, last_seen_at, status, source,
  source_url}`.
- company = `{id, slug, name, score (null bila belum cukup data), label,
  signals:[{category, key, points, evidence_url, evidence_text,
  evidence_date, source, confidence}]}`.
- **Satu tambahan di luar kontrak inti:** `company` juga mengembalikan
  `warnings: []` — dipakai untuk peringatan keselamatan (mis.
  permintaan biaya / red override). Web boleh mengabaikannya, tapi
  bila web menampilkannya, tampilkan sebagai peringatan, bukan sebagai
  bagian skor. Bila Tim Web tidak setuju, hapus field ini (bukan ubah
  diam-diam) — dicatat di sini sebagai **konflik terbuka untuk
  koordinator**, bukan sebagai perubahan kontrak.
- **Ambiguitas yang diputuskan di sini (bukan di kontrak):** `gaji_min`
  berarti `salary_min >= gaji_min` (lowongan tanpa gaji tidak tampil
  bila filter ini dipakai). `posted_from`/`posted_to` memakai
  `posted_at` (klaim sumber), bukan `first_seen_at`.

## Alternatif yang ditolak + alasan

| Alternatif | Alasan ditolak |
|---|---|
| Alembic dari awal | Dependensi + rantai baru untuk 1 skema awal; SQL langsung lebih mudah direview (butir 3). |
| JWT untuk auth | Tidak bisa dicabut tanpa daftar blokir; butuh manajemen kunci; berlebihan untuk 1 pengguna (butir 6). |
| OAuth Google / layanan auth | D8 (Fase 3) + D10 ($0) (butir 6). |
| Skor dihitung ulang di API | Dua sumber kebenaran akan bercabang saat ambang berubah (butir 7). |
| Kolom skor terdenormalisasi dari awal | Butuh pemicu update di semua jalur tulis yang belum ada (butir 8). |
| Refresh non-sinkron via RQ dari awal | Infrastruktur antrean untuk 20 lowongan/klik adalah over-engineering di alat pribadi (butir 9). |
| `check_active` False sekali = langsung `closed` | Satu gangguan baca bisa menutup ratusan lowongan yang masih aktif (ADR-0002 G2/G3). |
| Sembunyikan `score` mentah (0) saat "Belum cukup data" dengan angka | 0 dibaca sebagai "perusahaan buruk" — `null` adalah jawaban yang benar ("kami belum tahu"). |
| Simpan `evidence_text` Google Places sebagai string kosong | String kosong lolos CHECK "IS NULL" hanya bila ditulis begitu; NULL adalah penanda yang ditegakkan DB (K4). |

## Konsekuensi

- **Positif:** API jalan lokal end-to-end (seed -> API -> skor -> worker
  recheck); skor konsisten dengan flag-engine; aturan K4 ditegakkan DB;
  auth sederhana tanpa dependensi baru; worker tidak bisa menutup
  lowongan dari satu kegagalan teknis.
- **Negatif / risiko:** filter `skor_min` per-request akan berat bila
  data sudah puluhan ribu (butir 8); refresh sinkron lambat untuk
  ratusan lowongan (butir 9); `001_init.sql` belum dieksekusi di
  Postgres asli; fingerprint ganda kecil (K8) belum dipilih satu oleh
  Tim Normalisasi — worker/API memakai `RawJob.fingerprint()`
  (company_norm) apa adanya.
- **Butuh jawaban koordinator:** (a) tambahan field `warnings` di
  respons company — setuju atau hapus; (b) `.env.example` di root masih
  menulis `ENABLED_SOURCES=glints,jobstreet` padahal JobStreet
  `enabled=false` di migrasi+seed — perlu diperbarui (di luar wewenang
  edit tim ini, dilaporkan saja).

## Yang belum terverifikasi

1. `migrations/001_init.sql` dieksekusi di PostgreSQL 16 asli
   (docker-compose di mesin Giga) — test di VM ini hanya statis +
   SQLite.
2. `docker compose up` end-to-end (api + worker + postgres + redis)
   — service `api`/`worker` sudah ditambahkan ke
   `infra/docker-compose.yml`, tapi tidak bisa dijalankan di VM ini
   (tidak ada docker).
3. Uji live adapter (K9/K10 konsolidasi): Glints sitemap/JSON-LD,
   Kalibrr `?query=`, board ATS — tetap menjadi prasyarat sebelum klaim
   "jalan" untuk data live.
4. `androidTest`/UI tidak relevan di sini; gate §7.4 (login ke server
   asli) adalah urusan Tim Web + server Giga, bukan API ini.

## Hasil grill yang mengubah keputusan

- **G-1 (Alembic vs SQL):** grill menanyakan nilai tambah Alembic untuk
  1 skema awal -> lahir keputusan migrasi SQL + janji pindah bila skema
  berubah > 2-3x.
- **G-2 (JWT vs token DB):** grill menanyakan pencabutan token -> lahir
  token acak di DB (bisa dicabut) + hash password PBKDF2 stdlib.
- **G-3 (dua rumus skor):** grill menanyakan jaminan angka sama ->
  lahir pemetaan ke flag-engine + test kesetaraan jalur fallback.
- **G-4 (False sekali = closed?):** grill mengulang aturan ADR-0002 ->
  lahir kolom `missed_checks` + snapshot `missed`.
- **G-5 (API mati tanpa scraper-core?):** grill menanyakan kerapuhan
  impor -> lahir mode fallback `skipped`/`fallback` supaya endpoint
  baca tetap jalan.
- **G-6 (401 dua bentuk):** ditemukan saat smoke test — `HTTPException`
  FastAPI mengembalikan `{"detail": ...}` di luar format konsisten ->
  lahir handler `StarletteHTTPException` yang menyamakan bentuknya
  (`unauthorized`).

## Amandemen koordinator Fase 1-lanjutan (15 Nov 2026) — kontrak API–Web

Ditemukan saat penyatuan bahwa kontrak di tugas tidak cukup:
- **K-W3 (bug nyata):** web mengirim `salary_min`/`score_min`, API menunggu
  `gaji_min`/`skor_min` — filter gaji/skor web diam-diam tidak jalan
  (FastAPI mengabaikan query param tak dikenal). Perbaikan: API menerima
  kedua nama (kanonik tetap `gaji_min`/`skor_min`, alias Inggris diterima).
- **K-W1:** `CompanyOut` kini juga mengembalikan `measured_categories`,
  `decisive_signals`, `red_override` supaya web bisa memverifikasi syarat
  label tanpa menghitung ulang skor.
- **K-W4:** web memakai `warnings` + `red_override` dari API untuk
  peringatan biaya, bukan heuristik pencocokan kata.
- **Konsistensi D7:** jalur fallback `_aggregate_fallback` kini
  mengembalikan `total=None` bila 0 kategori terukur (sebelumnya 0),
  sama dengan flag-engine.
