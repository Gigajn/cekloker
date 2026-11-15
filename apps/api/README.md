# CekLoker API — FastAPI + Worker + PostgreSQL

**Status:** Fase 1-lanjutan, jalan lokal. Bahasa: Indonesia.
**JANGAN push / PR / merge ke GitHub dari sini** — parent yang memverifikasi lalu push.
**$0, tanpa API berbayar, tanpa credential di file mana pun.**

API ini menyajikan 2 janji produk (ARCHITECTURE.md §1):
1. Daftar lowongan yang **status aktifnya terverifikasi** (`posted_at` klaim
   sumber + `first_seen_at`/`last_seen_at` pengamatan kami).
2. Skor **Green / Mixed / Red Flag** perusahaan yang transparan (skor
   ternormalisasi dari flag-engine + rincian sinyal + tautan bukti).

## Cara jalanin (lokal, dari `apps/api/`)

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e ".[test]"

# 1. Skema database — pilih SATU:
#    a) Postgres (produksi / docker-compose, lihat infra/docker-compose.yml):
#       psql "$DATABASE_URL" -f migrations/001_init.sql
#    b) Dev cepat SQLite (file lokal, tanpa Postgres):
#       DATABASE_URL="sqlite:///./data/cekloker.db" .venv/bin/python -c \
#         "from app.models import Base; from app.database import engine; Base.metadata.create_all(engine)"

# 2. Seed dari fixture Fase 1 (BUKAN data live, perusahaan FIKTIF):
DATABASE_URL="sqlite:///./data/cekloker.db" \
CEKLOKER_ADMIN_EMAIL="giga@contoh.invalid" \
CEKLOKER_ADMIN_PASSWORD="ganti-dengan-yang-kuat" \
  .venv/bin/python scripts/seed.py
# Hasil: 9 lowongan, 3 perusahaan, 8 sinyal, 1 akun admin.
# Seed idempotent (upsert per source_url); tambah --reset untuk hapus dulu.

# 3. Jalankan API:
DATABASE_URL="sqlite:///./data/cekloker.db" .venv/bin/python -m uvicorn app.main:app --port 8000
#    Buka http://127.0.0.1:8000/health  (dan /docs untuk OpenAPI)
```

Catatan PYTHONPATH: API mengimpor `scraper_core` (packages/scraper-core)
dan `social_signals` (packages/flag-engine) dari repo. Saat dijalankan
dari repo, path itu ditemukan otomatis. Di Docker, image sudah mengatur
`PYTHONPATH` (lihat Dockerfile). Bila dijalankan dari luar repo, set:
`PYTHONPATH=<repo>/packages/scraper-core:<repo>/packages/flag-engine`.

## Endpoint (`/api/v1`)

| Endpoint | Keterangan |
|---|---|
| `GET /health` (juga `/api/v1/health`) | `{status, version, db}` |
| `GET /jobs?status=active&q=&location=&gaji_min=&skor_min=&posted_from=&posted_to=&page=&per_page=` | Daftar lowongan. Default `status=active`. `gaji_min` = gaji minimum yang ditawarkan perusahaan harus >= nilai ini. `skor_min` = skor ternormalisasi perusahaan >= nilai ini. |
| `GET /jobs/{id}` | Detail 1 lowongan |
| `GET /companies?skor_min=&skor_max=&label=` | Daftar perusahaan + skor |
| `GET /companies/{slug}` | Skor ternormalisasi + rincian sinyal + bukti |
| `GET /signals?company_id=&category=` | Daftar sinyal (bukti) 1 perusahaan |
| `POST /admin/login` `{email, password}` | -> `{token, expires_at}` (token 7 hari) |
| `POST /admin/refresh` `{job_id?, limit?}` | Cek ulang lowongan (butuh `Authorization: Bearer <token>`). Default limit 20, maks 100. |
| `POST /admin/logout` | Cabut semua sesi admin ini |

**Bentuk respons** mengikuti kontrak bersama Tim Web (lihat `app/schemas.py`):
- job = `{id, title, company{name,slug}, location, work_type, salary_min,
  salary_max, salary_currency, posted_at, posted_at_certain, first_seen_at,
  last_seen_at, status, source, source_url}`.
- company = `{id, slug, name, score (null bila "Belum cukup data"), label,
  signals:[{category, key, points, evidence_url, evidence_text,
  evidence_date, source, confidence}]}` + `warnings` (peringatan keselamatan,
  mis. permintaan biaya — tambahan yang boleh diabaikan web, lihat ADR-0009).

**Error** selalu berbentuk `{"error": {"code", "message", "details"?}}`
— tanpa stack trace (`internal_error` = pesan generik saja).

## Auth (1 akun Giga dulu, D8)

- Password di-hash **PBKDF2-HMAC-SHA256** (stdlib, 600.000 iterasi) —
  tanpa bcrypt/passlib, tanpa OAuth Google, tanpa layanan auth berbayar.
- Login menghasilkan token acak; yang disimpan di DB hanya SHA-256 token
  itu (bukan tokennya). Token berlaku 7 hari (`ADMIN_SESSION_DAYS`).
- Akun admin dibuat **hanya lewat seed dari env**
  `CEKLOKER_ADMIN_EMAIL` / `CEKLOKER_ADMIN_PASSWORD` — jangan tulis
  password di file, jangan commit `.env`.

## Worker — cek ulang lowongan aktif

```bash
# Cek ulang sekali (manual — JANGAN jalan otomatis massal saat dev):
DATABASE_URL=... .venv/bin/python -m app.worker --once [--limit 20] [--source glints] [--job-id <uuid>]
# Loop sopan tiap 1 jam:
DATABASE_URL=... .venv/bin/python -m app.worker --interval 3600 --limit 50
```

Aturan recheck (ADR-0002 + ARCH §3):
- Masih buka -> `last_seen_at` diperbarui, `missed_checks` = 0.
- 1x hilang -> `missed_checks` + 1, status tetap `active`,
  `last_seen_at` TIDAK diubah. 2x hilang berturut-turut -> `closed`.
- Gagal teknis (timeout/5xx/403/429) -> `unknown`, TIDAK PERNAH `closed`.
- Adapter dimatikan (JobStreet/Indeed) / tanpa board_url -> `skipped`.
- Tiap kunjungan dicatat sebagai `job_snapshots` (append-only).

## Skor perusahaan (D7 — normalisasi)

Skor **dibaca dari flag-engine** (`packages/flag-engine/social_signals.py`,
`aggregate_signals`), bukan dihitung ulang di API:
`total = 100 × perolehan / cap kategori terukur`, label butuh
≥ 3 sinyal penentu dari ≥ 2 kategori; "Belum cukup data" -> `score: null`;
permintaan biaya -> label Red + peringatan (red override).
Bila flag-engine tidak bisa diimpor, API memakai rumus lokal yang SAMA
dan menandai `engine="fallback"` (lihat `app/services/scoring.py`).
Perubahan ambang tetap lewat ADR (ADR-0005).

## Migrasi — kenapa SQL, bukan Alembic?

`migrations/001_init.sql` (PostgreSQL) dipilih atas Alembic:
satu file SQL yang bisa dibaca/direview langsung, cerminan ARCH §4,
tanpa dependensi + rantai migrasi baru untuk proyek 1 orang.
Bila skema sudah berubah > 2-3x, pindah ke Alembic lewat ADR baru.
File SQL idempotent (aman dijalankan 2x).

## Test

```bash
.venv/bin/python -m pytest -q        # 36 test (TestClient + SQLite in-memory)
```

Batas yang dicatat jujur: **docker TIDAK tersedia di VM ini**, jadi test
memakai SQLite in-memory, bukan Postgres. CHECK constraint (termasuk K4:
`google_places` -> `evidence_text` NULL) tetap diuji karena SQLite
menegakkan CHECK; tipe Postgres-spesifik (`jsonb`, `gen_random_uuid`)
hanya diverifikasi statis di `tests/test_migration.py`. Eksekusi
`001_init.sql` di Postgres asli masih menunggu docker-compose di
mesin Giga (lihat ADR-0009).

## Struktur

```
apps/api/
  app/
    main.py            # FastAPI app + /health
    config.py          # semua dari env
    database.py        # engine + session per-request
    models.py          # SQLAlchemy (cermin ARCH §4 + ADR-0009)
    schemas.py         # Pydantic (kontrak Tim Web)
    errors.py          # format error JSON, tanpa stack trace
    auth.py            # PBKDF2 + token sesi admin
    routers/           # jobs, companies, signals, admin
    services/
      scoring.py       # skor dari flag-engine (+ fallback berumus sama)
      jobs.py          # upsert RawJob -> Company + Job
      scraper_import.py# cari scraper-core di repo / PYTHONPATH
    worker.py          # recheck_job + CLI --once / --interval
  migrations/001_init.sql
  scripts/seed.py      # seed dari fixture Fase 1
  tests/               # pytest (TestClient + SQLite in-memory)
  Dockerfile           # image yang sama untuk api + worker
```

## Yang TIDAK ada di sini (sengaja)

- JobStreet / Indeed / LinkedIn tetap **stub / dimatikan** (D6, ADR-0001).
- Tanpa Redis/RQ di v1: refresh admin sinkron + berbatas (maks 100).
  Antrean masuk bila refresh sudah menangani ribuan lowongan.
- Tanpa Playwright/bs4/httpx di runtime API (scraper-core stdlib-only).
- Tanpa data live massal: seed hanya fixture; data live masuk lewat
  worker setelah uji live (K9/K10 di fase1-konsolidasi.md §8).
