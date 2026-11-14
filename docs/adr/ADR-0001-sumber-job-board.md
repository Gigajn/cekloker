# ADR-0001 — Keputusan sumber job board Indonesia + global

> **Penomoran:** seri ADR khusus CekLoker mulai 0001 (perintah tugas
> Fase 1). Catatan: `docs/adr/` sudah berisi `ADR-0007-adopsi-vs-tulis-ulang.md`
> (tim referensi GitHub) — ada tabrakan skema penomoran yang harus
> diputuskan koordinator (lihat akhir dokumen ini).

- **Status:** Diterima (tim job-board, 15 Nov 2026). Menunggu jawaban Giga untuk K-JB1 (nasib JobStreet) dan K-JB6/K-JB8 (baca penuh ToS Glints/Kalibrr).
- **Tanggal:** 15 November 2026
- **Konteks terkait:** `ARCHITECTURE.md` §5 (sumber utama v1), D2 (sumber pertama), D3 (scope Indonesia dulu); `docs/fase1-riset-jobboard.md` (riset + konflik K-JB1–K-JB8).

## Status

Diterima.

## Konteks

CekLoker v1 butuh sumber lowongan Indonesia yang (a) punya volume
lowongan besar, (b) bisa diakses secara legal dan sopan, (c) memberi
tanggal buka + status aktif yang bisa diverifikasi. ARCHITECTURE.md
(D2, §5) semula menetapkan **Glints + JobStreet** sebagai sumber utama,
dengan Kalibrr + halaman karier perusahaan sebagai pelengkap dan
Indeed/LinkedIn sebagai sumber global/reputasi. Penetapan itu dibuat
sebelum ada yang membaca ToS + robots.txt tiap sumber ke dokumen
primernya. Tim job-board membaca keempatnya pada 15 Nov 2026.

## Keputusan

1. **Glints — BANGUN (sumber utama 1).** Jalur: sitemap index
   (`glints.com/sitemap_index.xml`, dideklarasikan robots.txt) +
   halaman detail publik (`/opportunities/jobs/<slug>/<uuid>`)
   dengan JSON-LD `JobPosting` + fallback HTML. Delay 3 dtk.
2. **Kalibrr — BANGUN (sumber utama 2, terbatas).** Jalur: halaman
   pencarian & detail publik, parse `__NEXT_DATA__`. Terbatas:
   pagination tidak jalan (±15 hasil/query), jadi hanya untuk daftar
   kata kunci kurasi. Delay 3 dtk + backoff 429/5xx.
3. **JobStreet — TUNDA.** Adapter berupa stub yang raise
   `SourceNotPermittedError`. Tidak ada request ke JobStreet dari
   worker sampai ada (a) izin tertulis dari PT JobStreet Indonesia,
   atau (b) akses SEEK API yang disetujui.
4. **Indeed — TUNDA.** Adapter berupa stub yang raise
   `SourceNotPermittedError`. Tidak ada request ke Indeed dari worker
   sampai ada izin tertulis / kemitraan partner.
5. **LinkedIn — BUKAN sumber lowongan.** Hanya info perusahaan publik
   + link keluar (sesuai ARCHITECTURE.md §5).
6. **Global (di luar ID):** ditunda ke setelah Indonesia mantap.
   Alternatif legal yang dicatat (bukan dibangun): Adzuna API,
   ATS langsung (Greenhouse/Lever/Ashby).

## Alternatif yang ditolak + alasan

| Alternatif | Alasan ditolak |
|---|---|
| JobStreet tetap sumber utama (rencana awal D2) | ToS SEEK klausul (d) melarang agregasi konten termasuk lowongan kedaluwarsa; klausul 27 melarang data mining/screen scraping tanpa izin tertulis; robots.txt `User-agent: *` melarang `*/job/` dan `*?`. Tiga penolakan independen dari sumber primer. |
| Pakai endpoint internal Chalice v4 JobStreet ("no-auth") | "No-auth" ≠ "diizinkan". Endpoint tidak terdokumentasi, robots melarang `/api/jobsearch/`, ToS melarang agregasi. Memakainya = mengandalkan celah teknis melawan aturan tertulis. |
| Pakai GraphQL Glints `/api/graphql` | Skema tidak terdokumentasi (reverse-engineered, PR career-ops #1086). "Bisa diakses" bukan "diizinkan"; skema bisa berubah tanpa pemberitahuan. |
| Pakai scraping Indeed + proxy/anti-bot | ToS 29 Sep 2026 §D.21 melarang bot/scraper tanpa izin tertulis; robots melarang halaman detail; anti-bot aktif. Mengakali = bypass yang disengaja, dilarang aturan proyek. |
| LinkedIn sebagai sumber lowongan | ToS + robots melarang; butuh login/akun (dilarang: jangan akun palsu). |
| "Semua sumber dibangun dulu, legalitas dipikir nanti" | Membalik urutan yang benar: pelanggaran ToS yang sudah diketahui sejak awal tidak bisa diperbaiki belakangan dengan "nanti minta izin". Stub yang jujur lebih murah daripada takedown/Blokir di tengah jalan. |

## Konsekuensi

- **Positif:** Fase 1 bisa jalan HARI INI dengan 2 sumber legal (Glints + Kalibrr) tanpa menunggu izin siapa pun. Risiko hukum/Blokir paling besar (JobStreet, Indeed) dihilangkan dari jalur kritis. Arsitektur terbukti: 1 sumber mati/tunda tidak mematikan produk.
- **Negatif:** Volume awal lebih kecil (tanpa JobStreet, job board Indonesia terbesar kedua; tanpa Indeed untuk global). Kalibrr hanya ±15 hasil/query — butuh kurasi kata kunci yang baik. Perlu uji live 1x untuk 2 asumsi Glints (isi sitemap, JSON-LD) dan 1 asumsi Kalibrr (parameter `?query=`).
- **Netral:** Stub JobStreet/Indeed tetap terdokumentasi (endpoint + alasan + alternatif) sehingga mengaktifkan nanti = 1 ADR + implementasi parser, bukan riset ulang.

## Hasil grill yang mengubah keputusan

Grill G1 ("kenapa urutan ini, bukan sebaliknya?") membalik keputusan
awal: **JobStreet keluar dari sumber utama, Kalibrr naik**. Sebelum
grill, alasan implisitnya adalah "JobStreet paling besar + paling
gampang di-scrape (JSON rapi)". Grill memaksa pembeda yang sah —
izin tertulis + robots.txt primer — dan di bawah pembeda itu JobStreet
gagal di tiga pemeriksaan independen (ToS klausul d, ToS klausul 27,
robots.txt). Kemudahan teknis dinyatakan BUKAN pembenar. Grill juga
menolak argumen "kan cuma dibaca, bukan disalin mentah": ToS SEEK
melarang agregasi kontennya apa pun bentuk penyajiannya.
Lihat `docs/fase1-riset-jobboard.md` §4 (G1) dan konflik K-JB1/K-JB3.
