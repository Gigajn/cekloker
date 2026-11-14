# ADR-0003 — Pendekatan Halaman Karier Perusahaan + ATS

> Penomoran KHUSUS CekLoker. ADR-0001 dan ADR-0002 milik Tim Job-Board.
> Tanggal: 15 November 2026. Tim: Direct / Perusahaan Langsung.
> Status: **Diterima** (Fase 1).

## Status

Diterima.

## Konteks

CekLoker menjawab "lowongan ini masih buka beneran, sejak kapan?".
Job board (Glints/JobStreet/Kalibrr, tim lain) mengindeks lowongan
yang diposting ke agregator — tapi banyak perusahaan Indonesia hanya
membuka lowongan di halaman kariernya sendiri. Untuk menjangkau
mereka, ada tiga pendekatan: (a) baca feed JSON publik ATS yang
dipakai perusahaan, (b) scraping HTML halaman karier custom,
(c) tidak melacak jalur direct sama sekali dan mengandalkan job board.

Riset 15 Nov 2026 (lihat `docs/fase1-riset-direct.md`) menemukan:
Greenhouse, Lever, Ashby, dan Workable masing-masing menyediakan
endpoint JSON publik tanpa login yang dipakai widget karier perusahaan
itu sendiri — didokumentasikan resmi oleh vendor. Lever bahkan menulis
eksplisit bahwa posting yang dipublikasikan "may be scraped by third
parties". Sementara itu tanggal buka tidak seragam: Greenhouse
`first_published` hanya dijamin di endpoint satu job, Lever `createdAt`
tidak ada di tabel field README resmi, Ashby `publishedAt` berarti
"terakhir dipublikasikan".

## Keputusan

1. **Jalur utama direct = feed JSON publik ATS**, dengan prioritas:
   Greenhouse, Lever, Ashby, Workable (terverifikasi dokumen resmi).
   SmartRecruiters, Recruitee, Personio, BambooHR sebagai cadangan
   (baru sumber sekunder — wajib uji live dulu). Workday DITUNDA
   (slug tidak bisa ditebak, tanggal hanya relatif).
2. **Halaman karier custom dibaca lewat JSON-LD `JobPosting`**
   (schema.org) — 1 request, data terstruktur. Tanpa JSON-LD, perusahaan
   masuk antrean adapter khusus manual; selector CSS bukan jalur utama.
3. **Arsitektur deteksi baru/tutup/repost**: adapter hanya memberi
   `job_key` (platform:slug:id ATS), `posted_at` klaim sumber, dan
   fingerprint (judul+perusahaan+lokasi). Keputusan "baru vs repost"
   ada di normalizer/scheduler: id baru + fingerprint lama = kemungkinan
   repost; id baru + fingerprint baru = baru. `first_seen_at` dicatat
   scheduler, tidak pernah ditampilkan sebagai `posted_at`.
4. **Gagal eksplisit, bukan diam-diam**: board 404 → list kosong;
   platform tanpa feed JSON / tanpa implementasi (Workday) →
   `NotImplementedError` / `ValueError`, bukan hasil kosong palsu.
5. **Kesopanan**: hanya endpoint publik tanpa login; User-Agent
   pengenal; jeda ≥2 detik per host; hormati `robots.txt`; tidak ada
   bypass login/paywall/CAPTCHA; tidak ada kunci akun perusahaan
   (Lever Data API v1, Greenhouse Harvest, Workable SPI v3 tidak dipakai).
6. **Cakupan Fase 1 dibatasi**: 4 ATS terverifikasi + JSON-LD custom +
   10 perusahaan uji (lihat riset §7). Bukan semua perusahaan.

## Alternatif yang ditolak + alasan

| Alternatif | Alasan ditolak |
|---|---|
| Hanya andalkan job board, tanpa jalur direct | Kehilangan lowongan yang hanya ada di halaman perusahaan; tanggal buka & status tutup dari sindikasi job board kurang andal |
| Scraping HTML halaman karier custom sebagai jalur utama | Rapuh (layout berubah tiap saat), mahal dirawat per perusahaan, dan tidak memberi tanggal buka yang terstruktur |
| Memakai API resmi ber-auth (Harvest, Lever Data API v1, Workable SPI v3) | Butuh kunci dari tiap perusahaan — tidak mungkin untuk agregator pihak ketiga; jalur ini untuk pemilik akun ATS, bukan CekLoker |
| Menganggap `posted_at` dari ATS sebagai kebenaran mutlak | Ashby `publishedAt` = terakhir dipublikasikan (K-D3); Greenhouse list tidak menjamin `first_published` (K-D1). Harus dipasangkan `first_seen_at` + deteksi repost |
| Menebak slug ATS perusahaan dari namanya | Slug ≠ nama perusahaan; board kosong ambigu (K-D4). Slug harus berasal dari URL board / tautan halaman karier yang ditemukan |

## Konsekuensi

- **Positif**: lowongan direct bisa ditambahkan per perusahaan tanpa
  menyentuh inti aplikasi (1 adapter = 1 perusahaan + platform);
  tanggal buka berasal dari sumber pertama, bukan sindikasi; status
  tutup terdeteksi dari hilangnya lowongan di board.
- **Negatif**: tiap ATS punya bentuk tanggal/gaji berbeda → normalizer
  harus menangani 4+ varian; perusahaan bisa menonaktifkan board
  publik kapan saja → adapter harus tahan gagal; cakupan Indonesia
  terbatas karena banyak perusahaan pakai portal custom, bukan ATS global.
- **Risiko**: tidak ada rate limit terdokumentasi di vendor mana pun —
  volume naik tanpa sopan santun bisa berujung blokir IP. Mitigasi di
  keputusan poin 5.
- **Butuh jawaban Giga**: tidak ada untuk ADR ini. Yang tersisa adalah
  uji live (K-D1, K-D2, K-D4, K-D5), bukan keputusan.

## Hasil grill yang mengubah keputusan

(Grill penuh: `docs/fase1-riset-direct.md` §6.)

- **G1** (kenapa tidak cukup job board?) → cakupan direct dipersempit:
  4 ATS + JSON-LD + 10 perusahaan uji, bukan "semua perusahaan".
- **G2** (baru vs repost?) → keputusan "baru" dipindah dari adapter ke
  normalizer/scheduler dengan 3 sinyal (`job_key`, `posted_at`,
  fingerprint). Adapter yang awalnya direncanakan memutuskan sendiri
  diubah total.
- **G5** (board dimatikan besok?) → aturan gagal eksplisit ditambahkan
  (404 → kosong; Workday → `NotImplementedError`), dan direct
  ditegaskan sebagai pelengkap job board, bukan pengganti.
- **G6** (asumsi paling rapuh?) → didokumentasikan bahwa mayoritas
  perusahaan Indonesia memakai portal custom — JSON-LD, bukan ATS,
  menjadi penentu cakupan direct di Indonesia.
