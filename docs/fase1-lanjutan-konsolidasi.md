# Laporan Konsolidasi Akhir — Fase 1-lanjutan CekLoker

**Status: SELESAI (lokal saja). Tanggal: 15 Nov 2026. Bahasa: Indonesia.**
**Tidak ada push / PR / merge ke GitHub.** Semua hasil lokal di
`~/workspace/cekloker/`. Repo remote `Gigajn/cekloker` tetap di main @
`fb65039d` (D6–D12); parent yang memverifikasi lalu push hasil ini.

Metode: 4 tim paralel (Normalisasi + Flag-Engine, Uji Live, API + Database,
Web) → tiap tim di-grill ala Matt Pocock (grill-with-docs) + verifikasi ke
sumber primer → koordinator membaca keempat laporan, menjalankan ulang
semua test sendiri di VM ini, menyatukan konflik, memperbaiki 6 masalah
integrasi, lalu menulis laporan ini. Konflik antar tim diberi nomor
global **K1–K9** (§3). Keputusan baru yang butuh Giga diberi nomor
**D13–D19** (§7) — lanjutan D1–D12, penomoran usulan tiap tim sudah
disatukan ulang di sini (usulan D13–D16 tim Uji Live dan D13–D14 tim
Normalisasi bertabrakan nomornya; yang berlaku adalah penomoran §7 ini).

Keputusan D6–D12 yang sudah dikunci Giga dan dipegang semua tim: D6
scraper langsung tanpa API resmi (JobStreet/Indeed/LinkedIn TETAP stub);
D7 normalisasi skor; D8 alat pribadi dulu, tidak publish/komersial
sampai alur legal; D9 non-komersial pribadi; D10 $0, tanpa API berbayar
apa pun; D11 IG tanpa yang berbayar, lead manual saja; D12 JobSpy
REFERENSI saja.

---

## 1. Ringkasan per tim (hasil + verifikasi koordinator)

Semua angka test di bawah **dijalankan ulang oleh koordinator di VM ini**,
bukan sekadar mengutip laporan tim.

| Tim | Yang diserahkan | Test (dijalankan ulang koordinator) |
|---|---|---|
| **Normalisasi + Flag-Engine** | D7 diberlakukan (total `None` bila 0 kategori terukur), fingerprint disamakan (K8), K4 ditegakkan (google_places + evidence_text → ValueError), amandemen ADR-0005/ADR-0006 + ARCH §5 + glossary | flag-engine **66 test, OK** (baseline 45 + 21 baru); scraper-core ikut naik karena perbaikan fingerprint |
| **Uji Live** | Uji live §8 konsolidasi Fase 1, 2 bug adapter diperbaiki (Glints false-positive tutup, Kalibrr tanpa `__NEXT_DATA__`), laporan uji live + ADR-0008 | scraper-core bagian dari **101 passed** total (lihat bawah) |
| **API + Database** | FastAPI `/api/v1` lengkap + skema Postgres + migrasi SQL + worker recheck + seed (9 lowongan, 3 perusahaan, 8 sinyal) + ADR-0009 | **36 passed** (3 warning deprecation Starlette, bukan gagal) |
| **Web** | Next.js 15 (4 halaman + mock berlabel + ADR-0010) | `npm run build` **sukses** (type-check lolos, 5 route) — dijalankan ulang koordinator setelah perbaikan penyatuan |

**Total Python: 203 test lolos, 0 gagal** — flag-engine 66 + scraper-core
101 + API 36. Baseline Fase 1 adalah 129 (84 + 45); kenaikan +74 test
(25 normalisasi, 9 uji live, 4 koordinator, 36 API baru). Web tidak
dihitung dalam angka Python (verifikasi via build + curl tim Web, dan
build ulang koordinator).

**Smoke test end-to-end API (oleh koordinator, di luar test suite):**
seed SQLite `/tmp/cekloker-smoke.db` → uvicorn (startup ~18 detik di VM
ini) → `GET /health` 200 `{"status":"ok","version":"0.1.0","db":"ok"}`;
`GET /api/v1/jobs?salary_min=5000000` total 4 (sama persis dengan
`?gaji_min=5000000`); `?score_min=50` total 1 (sama dengan `?skor_min=50`);
`GET /api/v1/companies/pt-contoh-maju-bersama` → score 56, Mixed,
measured `['reputasi','stabilitas']`, decisive 3, red_override false;
`GET /api/v1/companies` → contoh-corp 0 Red, pt-contoh-maju-bersama
56 Mixed, pt-fiktif-teknologi-nusantara null "Belum cukup data".
Server dimatikan setelah smoke test; DB smoke di `/tmp` (bukan di repo).

---

## 2. Hasil uji live per sumber (Tim Uji Live, ±43 request, delay 2–5 dtk)

| Cek | Hasil | Bukti kunci |
|---|---|---|
| Glints sitemap | **LOLOS** | `sitemap_index.xml` = 4.898 child sitemap; `sitemap_job_id_1.xml` 200/200 URL lowongan |
| Glints detail | **LOLOS + 1 BUG (diperbaiki)** | JSON-LD `JobPosting` ada (`datePosted` 2026-08-27 ISO, `validThrough` 2026-12-16, gaji Rp5–5,5 jt) — tapi adapter lama menandai lowongan AKTIF ini tutup (false positive, lihat §4) |
| Kalibrr `?query=` | **GAGAL** | HTTP 200 tapi shell SPA ~2,3 KB, tanpa `__NEXT_DATA__`, 0 URL — `?query=` tidak terverifikasi; klaim robots.txt Fase 1 juga tidak terverifikasi (robots.txt .id/.com mengembalikan shell SPA yang sama) |
| Greenhouse `discord` | **LOLOS** | 26 lowongan; `first_published` ada di daftar **26/26** (K-D1 terjawab sebagian — dokumen resmi tidak lengkap) |
| Lever `spotify` | **LOLOS** | 87 lowongan; `createdAt` ada **87/87** (K-D2 terjawab) |
| Ashby `ashby` | **LOLOS** | 76 lowongan; lowongan pertama `publishedAt` **2024-03-04** — bukti langsung K-D3 (publishedAt = terakhir dipublikasikan, bukan tanggal buka) |
| Workable `huggingface` | **LOLOS** | 6 lowongan; `published_on` tanggal saja |
| 9 perusahaan Direct | **0/9 beri lowongan contoh** | GoTo/BCA/Blibli terjangkau tapi tanpa data terstruktur (JS, 0 JSON-LD); Tokopedia timeout; Bukalapak 406; Xendit/Ruangguru/Telkom/DANA koneksi ditutup server. **GoTo BUKAN di Lever** (`api.lever.co/v0/postings/goto` → 404, K-D5 terbantah) |
| Instagram | **TIDAK DIUJI** | Sesuai D11 — tanpa token, lead manual saja |

**Caveat (dari tim, disetujui koordinator):** semua temuan negatif
(Kalibrr, 6 perusahaan) berasal dari VM/egress datacenter dan **bisa
spesifik-egress** — ditandai "perlu uji ulang dari jaringan Indonesia"
sebelum disimpulkan permanen (lihat D15/D16). Catatan log per-request di
`/tmp` sempat hilang saat tmpfs dibersihkan di tengah pekerjaan; bukti di
laporan uji live berasal dari output pengamatan langsung yang tercatat
di laporan itu sendiri.

---

## 3. Konflik verifikasi global (K1–K9) — semua diselesaikan koordinator

| ID | Konflik | Keputusan / perbaikan koordinator |
|---|---|---|
| **K1** | Tiga tim sama-sama membuat ADR-0008 (uji live, desain web, API) | **Diselesaikan.** Uji live tetap ADR-0008, API sudah rename sendiri jadi ADR-0009, desain web di-rename koordinator jadi **ADR-0010** (+ semua referensi di `apps/web/` diperbarui). Penomoran kini 0001–0010 tanpa tabrakan |
| **K2** | Web mengirim `salary_min`/`score_min`, API menunggu `gaji_min`/`skor_min` — filter gaji/skor web diam-diam tidak jalan (FastAPI mengabaikan query param tak dikenal). **Bug integrasi nyata.** | **Diselesaikan.** API menerima kedua nama (kanonik tetap `gaji_min`/`skor_min`). Diverifikasi smoke test: alias dan kanonik memberi total sama (4 dan 1). Dicatat di ADR-0009 Amandemen |
| **K3** | Company response tanpa `measured_categories`/flag decisive (K-W1) — web tidak bisa memverifikasi syarat "≥2 kategori penentu", hanya percaya `score: null` | **Diselesaikan.** `CompanyOut` kini mengembalikan `measured_categories`, `decisive_signals`, `red_override`; router mengisinya dari hasil flag-engine; web memakainya. Diverifikasi smoke test |
| **K4** | Tanpa field `red_override` (K-W4) — web memakai heuristik rapuh pencocokan kata fee/biaya | **Diselesaikan.** Web memakai `warnings` + `red_override` dari API. Heuristik dihapus |
| **K5** | `CareerPageAdapter.check_active` mengembalikan `False` saat board tidak bisa dibaca / halaman tidak bisa diparse — setelah 2x kunjungan, lowongan aktif jadi `closed` (melanggar ADR-0002 "gagal teknis ≠ tutup") | **Diselesaikan koordinator.** Kegagalan teknis kini melempar `SourceFetchError` (worker → `unknown`); hanya HTTP 404 / lowongan benar-benar tidak ada di board yang berarti `False`. 4 test baru, scraper-core 101 lolos. Amandemen ADR-0002 |
| **K6** | Jalur fallback skor API mengembalikan total `0` bila 0 kategori terukur, sementara flag-engine mengembalikan `None` (D7) | **Diselesaikan.** Fallback kini `None` bila `measured_cap == 0`, sama dengan flag-engine. Test kesetaraan jalur tetap hijau |
| **K7** | `.env.example` masih menulis `ENABLED_SOURCES=glints,jobstreet` padahal JobStreet `enabled=false` di migrasi+seed | **Diselesaikan.** Diubah jadi `glints,kalibrr` + ditambah placeholder `CEKLOKER_CONTACT` dan `CEKLOKER_ADMIN_EMAIL/PASSWORD` (kosong, tanpa nilai asli) |
| **K8** | Service `web` masih dikomentari di `infra/docker-compose.yml` — `docker compose up` tidak menjalankan web | **Diselesaikan.** Ditambah `apps/web/Dockerfile` + `.dockerignore` + service `web` di compose (port 3000, `NEXT_PUBLIC_API_URL=http://localhost:8000`). **Belum terverifikasi jalan** karena docker tidak ada di VM ini (lihat §8) |
| **K9** | `docs/SCORING.md` + ARCH §5 prinsip 2 menulis "Belum cukup data" bila sinyal < 3, sementara ADR-0005 mensyaratkan ≥3 sinyal penentu **dari ≥2 kategori** | **TERBUKA — jadi D13.** Koordinator tidak mengubahnya diam-diam (di luar area tim + butuh keputusan Giga) |

Konflik yang sudah terselesaikan di dalam tim (dicatat saja): definisi
"cap terukur" + total `None` bila 0 kategori (Tim Normalisasi, ADR-0005);
Kalibrr `__NEXT_DATA__` tidak ada di live → parser kini melempar
`SourceFetchError`, bukan `[]` diam-diam; `normalize_company` idempotent
(verifikasi awal tim yang salah, bukan kode); `measured_cap` dihitung
hanya dari kategori penentu.

---

## 4. Hasil grill — keputusan yang BERUBAH karena di-grill

| # | Keputusan awal | Setelah grill |
|---|---|---|
| G-A | Total skor = angka walau 0 kategori terukur (0 = vonis) | Total = **None** bila 0 kategori terukur ("kami belum tahu", bukan 0) |
| G-B | Dua definisi fingerprint (Tim Normalisasi + Direct) | **Satu definisi**: `job_fingerprint` (company_norm, SHA-256 32 hex, URL tidak masuk) |
| G-C | `evidence_text` google_places diam-diam dikosongkan | **Ditolak keras** (`ValueError`) — gagal keras lebih jujur daripada diam-diam mengubah data (K4) |
| G-D | Frasa penanda tutup dicari di seluruh HTML Glints | Penanda hanya di teks tampil (tanpa script/style) + `validThrough` sebagai sinyal kedua + dedup UUID sitemap (varian locale) — memperbaiki false positive "semua lowongan tutup" |
| G-E | Kalibrr `__NEXT_DATA__` diasumsikan ada di live | Terbukti tidak ada → parser melempar `SourceFetchError` (worker → `unknown`), adapter tidak dimatikan diam-diam |
| G-F | `check_active` gagal teknis = False (K5) | Gagal teknis = `SourceFetchError` → `unknown` |
| G-G | Tiga ADR-0008 (K1) | Penomoran dirapikan 0008/0009/0010 |
| G-H | Web percaya `score`/`label` API tanpa verifikasi (K-W1) + heuristik fee (K-W4) | API mengembalikan `measured_categories`/`decisive_signals`/`red_override`/`warnings`; web memakai itu |
| G-I | Filter web `salary_min`/`score_min` diasumsikan sama dengan API (K2) | API menerima kedua nama parameter; smoke test membuktikan alias = kanonik |
| G-J | Service web tidak ada di compose (K8) | Dockerfile + service web ditambahkan |
| G-K | Skor ternormalisasi dari cap berbeda dianggap setara | UI wajib menampilkan "dari N kategori terukur" (ADR-0005 Amandemen D7) — angka 72 dari 2 kategori ≠ 72 dari 5 kategori |

---

## 5. ADR + glossary

- **ADR baru:** 0008 Hasil uji live Fase 1-lanjutan; 0009 API + Database; 0010 Desain Web ( semula 0008, di-rename — lihat K1).
- **Amandemen:** ADR-0005 (D7: rumus + 5 contoh hitung A–E), ADR-0006 (K4: penegakan google_places), ADR-0002 (check_active — K5), ADR-0009 (kontrak API–Web — K2/K3/K4/K6), ARCHITECTURE.md §5 (rumus mentah → ternormalisasi).
- **Glossary** (`docs/glossary.md`): "total ternormalisasi" diperbarui (D7 disetujui), istilah baru "cap terukur", "kategori penentu", "shell SPA", "validThrough", "false positive", "data contoh (mock)", "skor ternormalisasi (tampilan web)", + 8 istilah API/database/worker.

---

## 6. Daftar file yang dibuat / diubah (lokal, belum di-push)

**Baru di Fase 1-lanjutan (tidak ada di push `a8e3db8b` / `fb65039d`):**
- `docs/fase1-lanjutan-konsolidasi.md` (dokumen ini),
  `docs/fase1-lanjutan-uji-live.md`,
  `docs/adr/ADR-0008-hasil-uji-live-fase1-lanjutan.md`,
  `docs/adr/ADR-0009-api-database.md`,
  `docs/adr/ADR-0010-desain-web.md`
- `apps/api/` — `app/` lengkap (main, routers jobs/companies/signals/admin,
  models, schemas, services, auth, errors, config, database, worker),
  `migrations/001_init.sql`, `scripts/seed.py`, `tests/` (4 file),
  `pyproject.toml`, `Dockerfile`, `README.md`
- `apps/web/` — `src/app/` (4 halaman + layout + not-found),
  `src/lib/` (types, api, mock, format), `src/components/`,
  `package.json`, `package-lock.json`, `next.config.ts`,
  `postcss.config.mjs`, `tsconfig.json`, `Dockerfile`, `.dockerignore`,
  `.env.example`, `README.md`
- `packages/scraper-core/tests/fixtures/` — 7 fixture live baru
  (3 HTML + 4 JSON, potongan struktur saja)

**Diubah:** `packages/flag-engine/social_signals.py` + testnya,
`packages/scraper-core/scraper_core/base.py` + `__init__.py` +
`adapters/career_page.py` + `adapters/glints.py` + `adapters/kalibrr.py`
+ testnya, `apps/api/app/routers/jobs.py` + `schemas.py` +
`routers/companies.py` + `services/scoring.py` (amandemen koordinator),
`apps/web/src/lib/types.ts` + `src/app/companies/[slug]/page.tsx`
(amandemen koordinator), `ARCHITECTURE.md` (§5 saja),
`docs/glossary.md`, `docs/adr/ADR-0002/0005/0006/0009`,
`infra/docker-compose.yml` (service api, worker, web),
`.env.example` (K7).

**Sengaja TIDAK diubah:** `docs/decisions-d6-d12.md` (keputusan Giga —
hanya ditambah D13–D19 di §7 laporan ini, bukan di file itu),
`docs/SCORING.md` (butuh D13), JobStreet/Indeed/LinkedIn tetap stub,
tidak ada credential/data pribadi di file mana pun.

---

## 7. Keputusan baru yang masih butuh Giga (D13–D19)

| ID | Pertanyaan | Usulan / rekomendasi |
|---|---|---|
| **D13** | Samakan rumusan "Belum cukup data" di ARCH §5 + `docs/SCORING.md` ("<3 sinyal") dengan ADR-0005 (≥3 sinyal penentu **dari ≥2 kategori**)? (K9) | Ya, samakan — ADR-0005 yang berlaku; ARCH + SCORING diamandemen |
| **D14** | `normalize_company` mengubah merek camelCase jadi aneh ("GoTo" → "Goto", "Bukalapak.com" → "Bukalapak.Com") — perbaiki title-casing untuk merek, atau biarkan? (dedup tetap konsisten karena kedua sisi memakai fungsi yang sama) | Perbaiki di Fase 2 (daftar pengecualian merek) — bukan blocker |
| **D15** | Kalibrr: uji ulang dari jaringan Indonesia (Fedora Giga) dulu, atau Playwright, atau cari endpoint XHR (tidak direkomendasikan), atau jeda? | Uji ulang dari jaringan rumah dulu (paling murah, membedakan blokir egress vs blokir sungguhan) |
| **D16** | 6 perusahaan gagal/blokir dari VM: uji ulang dari jaringan Giga sebelum disimpulkan BLOKIR permanen? | Ya — uji ulang dulu; pola penolakan identik di 4 domain mencurigakan sebagai filter egress |
| **D17** | GoTo tanpa Lever: lacak via Glints saja untuk sekarang, atau adapter khusus? | Via Glints saja untuk sekarang |
| **D18** | BCA/Blibli/GoTo butuh JS: batasi direct ke ATS + JSON-LD, atau setujui Playwright? | Batasi ke ATS + JSON-LD dulu; Playwright ditunda sampai D15/D16 dijawab |
| **D19** | Alamat kontak / form koreksi resmi (K-W7) — `/cara-menilai` menulis proses + batas 7 hari tanpa mengarang alamat email. Alamat apa, atas nama siapa? | Tentukan sebelum publik; sementara proses koreksi via email Giga (perlu alamat yang diputuskan Giga) |

Catatan soal D6 yang belum diputuskan ulang: jawaban Giga D6 ("scraper
langsung, jangan khawatirkan API resmi") TIDAK dipakai koordinator
untuk mengaktifkan kembali JobStreet/Indeed/LinkedIn — ketiganya tetap
stub sampai Giga bilang eksplisit per sumber (lihat
`docs/decisions-d6-d12.md` D6).

---

## 8. Yang BELUM selesai / masih berisiko — jujur

- **Docker TIDAK tersedia di VM ini** (`docker: command not found`),
  jadi **`docker compose up` end-to-end BELUM terverifikasi** dan
  **`migrations/001_init.sql` belum pernah dieksekusi di Postgres 16
  asli** — hanya diverifikasi statis; test API memakai SQLite
  in-memory. Wajib dijalankan di mesin Giga (Fedora) sebelum klaim
  "jalan dengan docker compose up".
- **Web `npm run dev` belum terverifikasi** — verifikasi memakai
  `npm run build` + `next start` produksi (tim Web) dan build ulang
  koordinator. Mode dev sempat start tapi compile pertama >12 detik
  dan sesi uji tim terpotong.
- **Uji live Kalibrr GAGAL** dan **0/9 perusahaan uji memberi lowongan
  contoh** — keduanya mungkin spesifik-egress VM (D15/D16); jangan
  disimpulkan permanen sebelum uji ulang dari jaringan Indonesia.
- **ToS Glints/Kalibrr belum dibaca penuh** (gate rilis, D8) — adapter
  aktif berjalan atas asumsi pemakaian sopan.
- **Situs bisa berubah layout / memblokir kapan saja** — arsitektur
  sudah menahan (adapter mati lewat `enabled=False`, job lama jadi
  `unknown`, worker berhenti saat 403/429, dilarang memutar proxy).
- **Ambang rubrik adalah heuristik** — wajib kalibrasi di Fase 2 pada
  50 perusahaan pertama (K-S8 Fase 1).
- **Deteksi ulasan palsu diakui tidak bisa** — risiko terbuka.
- **Harga X / Reddit / Google Places dari sumber sekunder** — jangan
  pakai untuk anggaran final; D10 melarang API berbayar apa pun.
- **Seed data adalah FIKTIF** (Maju, Contoh Corp, Fiktif) — bukan data
  live; lowongan nyata pertama baru ada setelah worker jalan + uji live
  lolos.
- **API test lambat** (29–76 detik untuk 36 test — kemungkinan sleep
  worker) + 3 warning deprecation Starlette
  (`HTTP_422_UNPROCESSABLE_ENTITY`) — bukan gagal, tapi perlu
  dibersihkan di Fase 2.
- **Skor ternormalisasi dari cap berbeda tidak setara** — UI sudah
  menampilkan "dari N kategori terukur" (G-K); jangan bandingkan
  angka mentah antar perusahaan tanpa melihat kategorinya.
- **Fingerprint ganda kecil (K8 Fase 1) SELESAI** — satu definisi kini
  berlaku; sisa observasi D14 (title-casing merek) bukan blocker.

---

## 9. Cara menjalankan end-to-end (untuk Giga, di Fedora)

> Peringatan: langkah Docker di bawah ini **belum terverifikasi di VM**
> (docker tidak ada di sana). Langkah SQLite + uvicorn + `next start`
> sudah terverifikasi koordinator/tim di VM ini.

**Opsi A — Docker (yang dimaksud ARCHITECTURE.md):**
```bash
cd ~/cekloker   # atau clone https://github.com/Gigajn/cekloker
cp .env.example .env   # isi CEKLOKER_CONTACT + CEKLOKER_ADMIN_EMAIL/PASSWORD
docker compose -f infra/docker-compose.yml up --build
# web:    http://localhost:3000
# api:    http://localhost:8000/health  (+ /docs untuk OpenAPI)
# worker: profile "worker" — jalan manual:
#   docker compose -f infra/docker-compose.yml run --rm worker \
#     python -m app.worker --once --limit 20
```

**Opsi B — lokal tanpa Docker (terverifikasi sebagian di VM):**
```bash
# API + seed SQLite
cd apps/api && python3 -m venv .venv && .venv/bin/python -m pip install -e ".[test]"
DATABASE_URL="sqlite:///./data/cekloker.db" \
CEKLOKER_ADMIN_EMAIL="giga@contoh.invalid" \
CEKLOKER_ADMIN_PASSWORD="<rahasia>" .venv/bin/python scripts/seed.py
# -> 9 lowongan, 3 perusahaan, 8 sinyal (FIKTIF)
DATABASE_URL="sqlite:///./data/cekloker.db" \
  .venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
# Web (terminal lain)
cd apps/web && npm install && npm run build && npm start
# -> http://localhost:3000 (mode mock berlabel bila API belum jalan;
#    mock mati otomatis begitu API menjawab)
```

**Akun seed:** admin dari env `CEKLOKER_ADMIN_EMAIL` /
`CEKLOKER_ADMIN_PASSWORD` saat seed — tidak ada akun default di repo.
**Yang sudah bisa dipakai Giga sendiri:** daftar + detail lowongan
(seed fiktif), profil perusahaan + skor ternormalisasi + bukti, halaman
"cara kami menilai", cek ulang lowongan via `POST /api/v1/admin/refresh`
(butuh login admin). **Yang belum bisa:** lowongan NYATA (butuh worker
jalan + uji live lolos + D15/D16), dan `docker compose up` (belum
terverifikasi di VM ini).

---

*Koordinator Fase 1-lanjutan, 15 Nov 2026. Semua angka test di §1
dijalankan ulang koordinator sendiri di VM ini setelah penyatuan:
flag-engine 66 OK, scraper-core 101 passed, API 36 passed, web build
sukses. Tidak ada klaim "teruji live" tanpa bukti — yang belum diuji
live tercantum di §8.*
