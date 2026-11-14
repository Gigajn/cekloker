# ADR-0005 — Rubrik Skor Rule-Based (Sinyal Sosial & Reputasi)

- **Status:** Diterima (tim sosial) — **butuh persetujuan Giga untuk satu
  penyimpangan dari ARCHITECTURE.md §5** (lihat "Keputusan" butir 3).
- **Tanggal:** 15 November 2026
- **Penulis:** Tim Sosial & Reputasi (Fase 1 CekLoker)
- **Terkait:** `docs/SCORING.md`, `ARCHITECTURE.md §5`,
  `packages/flag-engine/social_signals.py`,
  `docs/fase1-riset-sosial.md` (§3, §6), ADR-0006.

## Konteks

CekLoker menilai perusahaan dengan skor 0–100 dalam 5 kategori
(Transparansi 25, Reputasi 25, Stabilitas 20, Praktik rekrutmen 15,
Gaji & benefit 15). Draf ARCHITECTURE.md §5 menetapkan contoh ambang —
"rating ≥ 4,0 dari ≥ 20 ulasan = +15", "keluhan sama ≥ 5x = −15",
"lowongan tayang > 90 hari = −10" — dan penjumlahan mentah per kategori
menjadi total. Modul sosial mengisi Reputasi (penuh), Stabilitas
(berita), Praktik rekrutmen (ghost job), dan Transparansi (biaya).
Masalah: contoh ambang itu disajikan seolah-olah rubrik final, padahal
tidak ada satu pun yang punya dasar eksternal; dan penjumlahan mentah
punya cacat yang ditemukan grill (lihat bawah).

## Keputusan

1. **Rule-based dulu, tanpa sentimen ML sampai Fase 4.** Hanya angka
   agregat (rating, jumlah ulasan, %) dan kata kunci eksplisit yang
   memberi poin. Alasan: skor harus bisa dibuktikan kalimat per kalimat
   (prinsip "skor tanpa bukti tidak tampil"), dan tidak ada benchmark
   sentimen Bahasa Indonesia untuk ulasan tempat kerja yang terverifikasi.
   Gerbang ML Fase 4: 200 contoh berlabel + precision/recall dilaporkan.
2. **Ambang dipertahankan dari ARCH §5 sebagai HEURISTIK, dengan
   justifikasi yang ditulis jujur.** Yang bisa dipertahankan statistik
   hanya `n ≥ 20` (galat baku rata-rata rating ~0,22 pada simpangan baku
   ~1,0 — cukup membedakan 4,0 dari 3,5; pada n=5 galat bakunya ~0,45).
   Angka 4,0 / 3,5 / 2,5 / 80% / 50% adalah pembagian skala yang mudah
   dijelaskan, **bukan standar industri** — tidak ada standar yang
   ditemukan. Wajib kalibrasi ulang di Fase 2 (50 perusahaan) dan revisi
   lewat ADR baru bila tidak memisahkan perusahaan bermasalah dari yang
   sehat.
3. **Total DINORMALISASI terhadap kategori yang terukur — ini menyimpang
   dari ARCH §5 dan BUTUH PERSETUJUAN GIGA.**
   `total = 100 × perolehan / cap kategori terukur`, dijepit 0–100.
   Kategori tanpa sinyal penentu tidak masuk penyebut. Alasan: penjumlahan
   mentah menghukum data yang BELUM diukur seolah-olah data BURUK —
   perusahaan bagus yang baru terukur reputasi + stabilitas (25 poin)
   akan berlabel Red (25/100). Contoh: rating 4,4 (n=155) + rekomendasi
   97% + berita ekspansi → total ternormalisasi 56 (Mixed), bukan 25
   (Red). Label baru diberikan bila ada ≥ 3 sinyal penentu dari ≥ 2
   kategori berbeda; di bawah itu "Belum cukup data".
4. **Tiering jumlah ulasan (n).** Rating: n ≥ 20 poin penuh; n 5–19
   setengah poin; n < 5 nol poin (konteks saja). Rekomendasi: n ≥ 20,
   di bawah itu nol. Tujuannya: perusahaan bagus tapi baru tidak dihukum
   (dan tidak dipuji berlebihan) dari segelintir ulasan.
5. **Keluhan berulang memakai dua ambang.** ≥ 3 ulasan berbeda → −5;
   ≥ 5 ulasan DAN pangsa ≥ 10% dari sampel → −15. Satu ulasan dihitung
   sekali per cluster (tidak peduli berapa kali ia mengulang kata yang
   sama). Pelindung negasi: "tidak pernah telat" bukan keluhan.
6. **Biaya = override, bukan poin.** Permintaan biaya yang terbukti di
   teks lowongan membuat label langsung Red + peringatan (`red_override`),
   poin sinyal 0 — supaya tidak bisa "ditebus" poin positif. Pola "adm"/
   "administrasi" hanya dihitung bila berdampingan dengan biaya/bayar/
   uang (supaya "staff administrasi" tidak memicu).
7. **Ghost job memakai ambang ganda + pengecualian evergreen.** > 90 hari
   + ≥ 3 lowongan basi + jabatan bukan evergreen (sales/driver/kurir/dsb.)
   → −10. Selain itu konteks saja.
8. **Berita memakai ambang ganda.** PHK/tutup → −15 hanya bila ≥ 2 media
   independen DAN ≤ 12 bulan. Satu media atau > 12 bulan → konteks saja.
   Ekspansi/pendanaan → +5 dengan syarat yang sama.
9. **Sinyal penentu (`decisive`).** Hanya sinyal yang memenuhi ambang
   minimum yang dihitung dalam penentuan label "Belum cukup data".
   Konteks tanpa poin tidak dihitung penentu.
10. **Perubahan ambang wajib lewat ADR baru + kalibrasi ulang.** Angka di
    `social_signals.py` bukan konstanta yang boleh diubah diam-diam.

## Alternatif yang ditolak + alasan

| Alternatif | Alasan ditolak |
|---|---|
| Penjumlahan mentah seperti ARCH §5 (total = jumlah kategori) | Menghukum data yang belum diukur sebagai data buruk; perusahaan bagus yang baru terukur 2 kategori berlabel Red. Ditemukan grill G-2; diganti normalisasi (butir 3). |
| Sentimen ML langsung di Fase 1/2 | Tidak ada akurasi yang bisa diklaim; skor tidak bisa dibuktikan per kalimat; Reddit + JobStreet melarang latih model dari data mereka tanpa izin tertulis; tidak bisa dijawab dalam proses koreksi perusahaan. |
| Satu ambang keluhan (mis. "≥ 5x" tanpa pangsa) | 5 keluhan dari 500 ulasan ≠ 5 dari 25 ulasan; tanpa pangsa, perusahaan besar selalu terlihat lebih buruk. |
| Rating tanpa tiering n (semua n diperlakukan sama) | Rating 5,0 dari 2 ulasan disamakan dengan 4,4 dari 155 ulasan — menyesatkan dan rawan manipulasi. |
| Biaya sebagai pengurangan poin (−25, mis.) | Poin negatif bisa "ditebus" poin positif lain; permintaan biaya adalah peringatan keselamatan, bukan sekadar skor jelek — harus override. |
| Ghost job dari `posted_at` saja | Tanggal yang ditulis sumber bisa direpost/diperbarui; sinyal ini butuh `fingerprint` + `first_seen_at`/`last_seen_at` dari tim scraper. Tanpa itu, ghost job = konteks saja. |
| Skor rata-rata tertimbang per sinyal (bukan per kategori) | Kategori dengan banyak sinyal murah (mis. 3 sinyal reputasi) akan mendominasi total; cap kategori menjaga keseimbangan rubrik 100 poin. |

## Konsekuensi

- **Positif:** skor tidak mengarang reputasi dari ketiadaan data
  ("Belum cukup data" adalah jawaban yang sah); perusahaan baru tidak
  langsung Red; setiap poin bisa ditelusuri ke kalimat/bukti tertentu;
  proses koreksi perusahaan punya bahan yang konkret.
- **Negatif / risiko:** perusahaan dengan data sebagian terlihat "Mixed"
  padahal mungkin bagus — label Green menjadi sulit (butuh ≥ 2 kategori
  + total ≥ 70), sehingga di awal banyak perusahaan akan berlabel
  "Belum cukup data"/Mixed; normalisasi membuat total bergantung pada
  *kategori mana* yang terukur (kurang intuitif dibanding penjumlahan);
  ambang tetap heuristik sampai kalibrasi Fase 2 membuktikan/membantahnya.
- **Dependensi:** sinyal ghost job butuh fingerprint stabil dari tim
  scraper; sinyal gaji/transparansi butuh modul tim job-board; UI wajib
  menampilkan rincian per kategori + "dari berapa kategori terukur",
  bukan hanya angka total.

## Hasil grill yang mengubah keputusan

- **G-2 (angka ambang):** memaksa pengakuan bahwa 4,0/20 adalah
  heuristik, bukan standar — dan menemukan cacat penjumlahan mentah.
  **Berubah:** total ternormalisasi + label butuh ≥ 2 kategori penentu.
  Ini penyimpangan dari ARCH §5 → butuh persetujuan Giga.
- **G-1 (adil untuk perusahaan baru vs manipulasi ulasan):**
  **Berubah:** tiering n + setengah poin + `decisive`; keluhan dihitung
  dari teks secara independen dari rating. **Tidak berubah:** deteksi
  ulasan palsu — diakui tidak bisa, dicatat sebagai risiko terbuka.
- **G-3 (1–2 ulasan ekstrem/palsu):** **Berubah:** satu ulasan dihitung
  sekali per cluster; ambang ganda jumlah + pangsa; tuduhan berat dari
  satu sumber tidak pernah jadi fakta di tampilan.
- **G-4 (negasi):** **Berubah:** pelindung negasi (batas kata, jendela
  25 karakter) + pola keluhan mensyaratkan kata kerja negatifnya.
- **G-5 ("staff administrasi"):** **Berubah:** pola fee mensyaratkan
  konteks pembayaran; negasi juga diperiksa pada pola fee ("tidak ada
  biaya pendaftaran" tidak memicu).
- **G-6 (ghost job vs evergreen):** **Berubah:** pengecualian jabatan
  evergreen + ambang ≥ 3 lowongan basi.
- **G-7 (satu artikel = rumor):** **Berubah:** berita butuh ≥ 2 media
  + ≤ 12 bulan untuk poin.
- **G-8 (kenapa ML ditunda):** **Tidak berubah** — penundaan
  dipertahankan, tetapi gerbang masuk Fase 4 ditulis eksplisit (200
  contoh berlabel + precision/recall) supaya penundaan ini berbatas,
  bukan alasan permanen.
