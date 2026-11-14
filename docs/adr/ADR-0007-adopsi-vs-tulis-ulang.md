# ADR-0007 — Kebijakan Adopsi vs Tulis Ulang Kode Pihak Ketiga

> **Penomoran khusus CekLoker.** ADR ini memakai nomor 0007 karena 0001–0006 sudah
> dipakai tim lain di Fase 1. JANGAN disamakan dengan nomor ADR Archodin — penomoran ini
> hanya berlaku di dalam repo CekLoker.

- **Status:** Diterima (menunggu persetujuan Giga — keputusan ini dibuat Tim Referensi
  GitHub 15 Nov 2026 berdasarkan grill; Giga dapat mengubah statusnya)
- **Tanggal:** 15 November 2026
- **Konteks dokumen:** `docs/github-references.md` (riset repo kandidat, tanggal cek sama),
  `ARCHITECTURE.md` §2 (lisensi rencana MIT), §6 (kontrak adapter), §8 (legal & etika),
  `docs/SCORING.md`.
- **Diputuskan oleh:** Tim Referensi GitHub — Fase 1 CekLoker.

---

## Status

Diterima (draft untuk persetujuan Giga).

## Konteks

CekLoker v1 adalah website scraper lowongan + analisis Green/Red Flag perusahaan
(Python 3.12 + FastAPI, Next.js + TypeScript, PostgreSQL 16, Redis), direncanakan
menjadi open source berlisensi **MIT** pada Fase 5. Untuk mempercepat Fase 1, tim riset
memeriksa 10 repo open-source (job scraper, job board, review scraper) dan 5 library
pendukung pada 15 Nov 2026.

Ada tiga tarikan yang bertentangan:

1. **Kecepatan:** memakai library yang sudah jadi (mis. JobSpy, 4.728★) menghemat
   1–2 minggu kerja per adapter.
2. **Lisensi MIT:** tidak semua "open source" boleh masuk ke proyek MIT. Kode
   AGPL-3.0 (jobradar, dossier) menular: bila dipakai lalu dijalankan sebagai website,
   CekLoker wajib menawarkan source code-nya — dan kewajiban itu merusak rencana MIT.
3. **Risiko ToS sumber:** hampir semua scraper lowongan bekerja di wilayah abu-abu
   ToS situs target (LinkedIn, Glassdoor melarang scraping otomatis). Mengadopsi
   library berarti mewarisi posisi itu — termasuk teknik yang secara eksplisit
   mengelabui deteksi bot (TLS impersonation, Googlebot UA) pada sebagian kandidat.

Tanpa aturan tertulis, setiap kontributor akan memutuskan sendiri di setiap PR —
dan satu keputusan adopsi yang salah (mis. menyalin satu fungsi AGPL) bisa memaksa
seluruh repo berganti lisensi.

## Keputusan

### 1. Tiga tingkat pemakaian — dan hanya tiga

| Tingkat | Arti | Syarat |
|---------|------|--------|
| **ADOPSI** | Kode/library dipakai apa adanya (dependensi atau salinan) dengan atribusi | Lisensi **MIT, Apache-2.0, atau BSD** saja. Repo harus terbukti terawat (commit kode dalam ~3 bulan terakhir, bukan hanya commit otomatis). Tidak memakai teknik bypass anti-bot sebagai perilaku default. |
| **REFERENSI** | Pola/struktur dipelajari, implementasi ditulis ulang sendiri | Berlaku untuk semua repo, termasuk yang berlisensi copyleft. Tidak menyalin kode — termasuk tidak "menerjemahkan" fungsi baris demi baris. |
| **TOLAK** | Tidak dipakai sama sekali, dengan alasan tercatat | Repo diarsipkan, terbengkalai, atau risikonya (lisensi/ToS) melebihi manfaatnya. |

### 2. Aturan lisensi (mengikat)

- **MIT / Apache-2.0 / BSD → boleh diadopsi** dengan atribusi (cantumkan di README
  dan/atau file `NOTICE` / daftar dependensi).
- **GPL / AGPL → HANYA referensi ide, JANGAN salin.** Dilarang menyalin kode,
  menyalin struktur fungsi secara verbatim, atau mem-vendor-kan potongan kode GPL/AGPL
  ke dalam repo CekLoker — walau satu fungsi, walau "sudah diubah sedikit".
  Alasannya: GPL/AGPL adalah copyleft; AGPL-3.0 secara eksplisit menular ke layanan
  yang dijalankan lewat jaringan (website). Satu salinan bisa memaksa seluruh
  CekLoker berganti lisensi dan membatalkan rencana MIT Fase 5.
- **Lisensi ganda dalam satu repo harus dibaca per bagian.** Contoh nyata dari riset:
  Riley-Dorrington/job-board-aggregator — kode MIT, dataset `data/` CC BY-NC 4.0
  (non-komersial). Memakai datasetnya untuk layanan yang nanti berbayar adalah
  pelanggaran lisensi, walau kodenya MIT.
- **Repo tanpa lisensi = TOLAK adopsi.** Kode tanpa file LICENSE bukan "bebas dipakai";
  secara default hak cipta penuh ada pada pembuatnya.
- **Dependensi transitif ikut diperiksa.** Bila library MIT yang diadopsi menarik
  dependensi berlisensi GPL/AGPL, dependensi itu harus diganti atau library tersebut
  turun tingkat menjadi REFERENSI.

### 3. Aturan ToS sumber (mengikat)

- Adapter CekLoker harus patuh pada **ARCHITECTURE.md §8**: patuhi `robots.txt`,
  delay 2–5 detik per domain, User-Agent jelas berisi kontak, jangan bypass login /
  paywall / CAPTCHA.
- **Dilarang mengadopsi teknik yang tujuannya mengelabui deteksi bot** sebagai
  perilaku default: TLS impersonation (mis. `curl_cffi` untuk meniru Chrome),
  User-Agent Googlebot untuk menyamar, dan klaim "bypass Cloudflare WAF".
  Library yang mengandung teknik itu hanya boleh dipakai bila teknik tersebut
  dimatikan / tidak dipakai, dan keputusan itu dicatat di PR.
- Sumber yang ToS-nya melarang scraping (LinkedIn, Glassdoor) dipakai **hanya**
  sebatas yang diizinkan arsitektur: LinkedIn sebagai info perusahaan publik +
  link keluar (bukan sumber lowongan utama); Glassdoor hanya agregat publik
  (rating + jumlah ulasan + link) dengan frekuensi rendah.
- Setiap adapter wajib bisa **dimatikan lewat config** bila sumbernya memblokir
  atau meminta opt-out (ARCHITECTURE.md §2, §8) — bukan dihapus diam-diam.

### 4. Aturan bukti keterawatan (mengikat untuk ADOPSI)

Sebelum sebuah repo naik ke ADOPSI, pemeriksa wajib mencatat (dengan tanggal cek):
lisensi dari halaman repo, bintang, tanggal commit kode terakhir (dibaca dari halaman
`/commits`, bukan dari angka commit total — commit otomatis seperti "trend snapshot"
tidak dihitung), dan stack. Bila tanggal commit terakhir tidak terverifikasi, repo
tidak bisa naik ke ADOPSI.

## Alternatif yang ditolak + alasan

| Alternatif | Alasan ditolak |
|------------|----------------|
| **Adopsi semua yang berlisensi MIT tanpa grill** | Lisensi MIT tidak menjamin kualitas atau legalitas ToS. jobdrop (MIT, 4★) terbukti punya klaim sumber yang bertentangan (28 vs 33 vs 21) dan teknik bypass anti-bot — MIT-nya legal, adopsinya tetap salah. |
| **Adopsi kode AGPL "sedikit saja, tidak ada yang tahu"** | Pelanggaran lisensi yang menular; membatalkan rencana MIT; dan tidak jujur terhadap pengguna open source nanti. Satu fungsi AGPL yang disalin sudah cukup memicu kewajiban. |
| **Tulis ulang SEMUA dari nol (nol dependensi)** | Membuang hemat nyata: JobSpy menghemat ~1–2 minggu kerja untuk adapter Indeed/Glassdoor (pagination, parsing gaji, rate-limit sudah teruji 4.728★ pengguna). Menulis ulang yang sudah terbukti adalah pemborosan, bukan kemandirian. |
| **Pakai API berbayar resmi (Adzuna/JSearch) sebagai pengganti scraping** | Belum ditolak permanen — ditunda sebagai rencana cadangan (K-G6, butuh jawaban Giga). Biaya belum dicek; dan API berbayar tidak menyelesaikan kebutuhan sumber utama (Glints/JobStreet/Kalibrr tidak ada di API tersebut). |
| **Mengandalkan "repo populer = repo bagus"** | Bintang tidak sama dengan terawat: JobFunnel 2.198★ sudah diarsipkan; Riley-Dorrington 485 commit sebagian besar snapshot otomatis. Popularitas adalah sinyal awal, bukan bukti. |

## Konsekuensi

**Positif:**
- Keputusan adopsi menjadi konsisten antar kontributor dan antar PR; tidak perlu
  grill ulang untuk setiap kandidat baru — cukup terapkan aturan ini.
- Rencana MIT Fase 5 terlindungi dari kontaminasi copyleft.
- Risiko ToS tercatat eksplisit per adapter, bukan tersembunyi di dalam dependensi.

**Negatif / biaya:**
- Adapter Glints/JobStreet/Kalibrr tetap harus ditulis sendiri (tidak ada kandidat
  yang menyediakannya) — biaya ini tidak bisa dihindari dengan adopsi.
- Setiap dependensi baru butuh pemeriksaan lisensi + tanggal cek — menambah
  ~30 menit kerja per dependensi. Diterima sebagai biaya yang murah dibanding risiko
  ganti lisensi di Fase 5.
- Sebagian teknik anti-bot yang "berhasil" di repo lain tidak boleh dipakai —
  scraper CekLoker mungkin lebih sering diblokir daripada scraper yang memakai
  teknik bypass. Ini trade-off sadar: sesuai prinsip §8.

**Yang harus dilakukan sebagai tindak lanjut:**
1. Buat file `NOTICE` / bagian atribusi di README saat dependensi pertama (JobSpy)
   diadopsi — cantumkan nama, URL, lisensi.
2. Pin versi dependensi yang teruji (JobSpy: versi GitHub 1.4.1-era, bukan PyPI 1.1.82
   yang tertinggal — lihat K-G5 di `github-references.md`).
3. Jawaban Giga atas K-G6 (API berbayar sebagai cadangan) sebelum Fase 2.

## Hasil grill yang mengubah keputusan

Grill kejam (ala Matt Pocock) dilakukan pada 15 Nov 2026 sebelum ADR ini ditulis;
rinciannya di `docs/github-references.md` § Hasil Grill. Perubahan terpenting:

1. **JobSpy: ADOPSI penuh → ADOPSI TERBATAS** (hanya Indeed/Glassdoor; LinkedIn
   dilarang dipakai sebagai sumber lowongan). Pemicu: pertanyaan "bukankah ini
   memindahkan risiko ToS LinkedIn ke CekLoker?" — jawabannya ya, dan mitigasinya
   adalah membatasi cakupan, bukan menolak library-nya.
2. **jobdrop: ADOPSI → REFERENSI.** Pemicu: kontradiksi jumlah sumber (28 vs 33 vs
   21) + bus factor 1 + teknik bypass anti-bot. Tanpa grill, proyek ini hampir
   menjadi rekomendasi #1 karena "33 sumber dan flag layoff".
3. **Riley-Dorrington: ADOPSI → REFERENSI.** Pemicu: commit harian ternyata snapshot
   otomatis (bukan pengembangan) + jebakan lisensi ganda CC BY-NC 4.0 pada dataset.
4. **jobradar & dossier: REFERENSI (kode) → TOLAK adopsi kode / REFERENSI IDE.**
   Pemicu: pertanyaan "open source ≠ boleh dipakai di MIT" — AGPL menular lewat
   layanan jaringan, sehingga satu salinan pun dilarang.
5. **glassdoor-scraper: ADOPSI (Fase 2) → REFERENSI.** Pemicu: klaim "unlimited free"
   bertentangan dengan distribusi RapidAPI berbayar + repo baru 6 minggu.
6. **Aturan "bukti keterawatan" lahir dari grill G1/G5:** bintang dan jumlah commit
   tidak diterima sebagai bukti; yang diterima hanya tanggal commit kode terakhir
   yang dibaca dari halaman `/commits`.

Tanpa grill, ADR ini akan berisi "adopsi JobSpy + jobdrop + Riley-Dorrington mentah-mentah"
— keputusan yang mewarisi kontradiksi data, risiko ToS, dan jebakan lisensi sekaligus.

---

*ADR-0007, 15 Nov 2026, Tim Referensi GitHub — Fase 1 CekLoker.*
