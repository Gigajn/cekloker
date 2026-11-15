# ADR-0005 — Rubrik Skor Rule-Based (Sinyal Sosial & Reputasi)

- **Status:** Diterima — D7 **disetujui Giga 2026-11-15 00:51 WIB**;
  normalisasi (butir 3) kini berlaku, lihat "Amandemen D7 — 2026-11-15".
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
3. **Total DINORMALISASI terhadap kategori yang terukur — DISETUJUI
   Giga (D7, 15 Nov 2026 00:51 WIB); lihat "Amandemen D7" di bawah.**
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

## Amandemen D7 — 2026-11-15 (Fase 1-lanjutan, tim Normalisasi + Flag-Engine)

**Keputusan Giga (D7, dijawab 00:51 WIB): "Ya, lakukan normalisasi."**
Dengan ini penyimpangan dari ARCHITECTURE.md §5 berakhir: rumus total
mentah di §5 diganti rumus ternormalisasi (ARCH §5 diamandemen bersamaan),
dan implementasi di `packages/flag-engine/social_signals.py`
(`aggregate_signals` + `normalized_total`) kini menjadi aturan yang
berlaku, bukan lagi usulan.

### Rumus yang berlaku

```
total = 100 × perolehan / cap terukur        (dijepit 0–100)
label: Green ≥ 70 | Mixed ≥ 40 | Red < 40
       "Belum cukup data" bila < 3 sinyal penentu atau < 2 kategori penentu
```

- **Cap terukur** = jumlah cap kategori yang punya ≥ 1 sinyal penentu
  (`decisive=True`). Contoh: hanya reputasi (25) + stabilitas (20)
  terukur → cap terukur 45, bukan 100.
- **Kategori penentu** = kategori yang punya ≥ 1 sinyal penentu.
  Sinyal konteks (0 poin, tidak penentu — mis. rating dari 2 ulasan)
  TIDAK membuat kategorinya terukur.
- **0 kategori terukur → total = None, bukan 0.** Jangan bagi nol, dan
  jangan kembalikan 0: 0/100 dibaca sebagai "perusahaan paling buruk",
  padahal artinya "kami belum tahu apa-apa". API/UI wajib menampilkan
  label "Belum cukup data", bukan angka 0. Total tetap dihitung (angka)
  walau labelnya "Belum cukup data" — angka itu hanya untuk debug/
  internal; yang tampil ke pengguna adalah labelnya.
- **Pembulatan** memakai `round()` Python (half-even, ke genap terdekat);
  selisih dari nilai eksak ≤ 1 poin. Diverifikasi brute-force 15 Nov 2026:
  dengan cap kategori 15/20/25, nilai tepat 39,5 / 69,5 tidak dapat
  terjadi, jadi pembulatan tidak pernah mengubah label Green/Mixed/Red.
- Poin negatif tetap dihitung (kategori dijepit di −cap, total dijepit
  di 0): perusahaan yang terukur dan buruk mendapat total 0 + label Red
  — beda dengan None saat 0 kategori terukur.

### Contoh hitung

| Perusahaan | Sinyal penentu | Perolehan / cap terukur | Total | Label |
|---|---|---|---|---|
| A (bagus, data lengkap) | rating 4,4 (n=155) +15, rekomendasi 97% +5, ekspansi +5, transparansi gaji +25, gaji vs UMR +15 | 65 / 85 | 76 | Green (4 kategori) |
| B (bagus, data sebagian) | rating +15, rekomendasi +5, ekspansi +5 | 25 / 45 | 56 | Mixed (2 kategori, 3 sinyal) — penjumlahan mentah akan memberi 25/100 = Red |
| C (hanya 1 kategori) | rating 4,4 (n=155) +15 | 15 / 25 | 60 | Belum cukup data (1 kategori) — angka 60 hanya internal |
| D (tanpa data) | — | — / 0 | None | Belum cukup data |
| E (buruk, terukur) | rating 1,5 −10, keluhan berat −15, berita tutup −15, ghost job −10 | −50 / 60 → dijepit 0 | 0 | Red (3 kategori, 4 sinyal) |

### Hasil grill D7 (pertanyaan yang diajukan sebelum amandemen ini ditulis)

- **G-D7-1 — Kenapa penyebut hanya kategori dengan sinyal penentu, bukan
  semua kategori yang punya sinyal apa pun?** Karena konteks tanpa poin
  tidak membuktikan apa-apa. Rating dari 2 ulasan (konteks) yang ikut
  masuk penyebut akan menahan total perusahaan itu di bawah nilai yang
  layak — hukuman yang sama seperti penjumlahan mentah, hanya lebih kecil.
  **Tidak berubah:** definisi cap terukur tetap dari sinyal penentu.
- **G-D7-2 — Kenapa 0 kategori menghasilkan None, bukan 0?** Karena 0
  adalah vonis ("paling buruk"), sedangkan None adalah pengakuan
  ketidaktahuan. UI yang menampilkan "0/100" untuk perusahaan tanpa data
  adalah fitnah dalam bentuk angka. **Berubah:** `aggregate_signals`
  mengembalikan `total=None` bila `measured_cap == 0` (sebelumnya 0).
- **G-D7-3 — Kenapa label tetap butuh ≥ 3 sinyal + ≥ 2 kategori, bukan
  cukup total ≥ 70?** Karena satu kategori sempurna (reputasi 25/25 →
  total 100) bukan bukti perusahaan itu bagus secara keseluruhan — itu
  bukti satu aspeknya bagus. Syarat ganda ini yang mencegah label Green
  dari satu sumber. **Tidak berubah.**
- **G-D7-4 — Apakah normalisasi membuat total sulit dibandingkan antar
  perusahaan?** Ya, sebagian: 76 dari cap 85 (A) tidak setara dengan 76
  dari cap 45. Karena itu UI wajib menampilkan "dari berapa kategori
  terukur" di samping angka (sudah dicatat di Konsekuensi). **Tidak
  berubah**, tapi dicatat eksplisit sebagai biaya desain.
- **G-D7-5 — Apa jadinya bila semua poin negatif?** Total dijepit 0 dan
  label Red — selama syarat label terpenuhi (≥ 3 penentu, ≥ 2 kategori).
  Bila hanya 1 kategori negatif (mis. hanya keluhan −15), label tetap
  "Belum cukup data", bukan Red: satu sisi buruk saja belum cukup untuk
  memberi label. **Tidak berubah**, diuji di `TestNormalisasiD7`.

### Konsekuensi amandemen

- ARCHITECTURE.md §5 kini memakai rumus ternormalisasi; rumus mentah
  tidak lagi berlaku di mana pun.
- `docs/SCORING.md` masih menulis "Belum cukup data (<3 sinyal)" tanpa
  menyebut syarat ≥ 2 kategori — perlu disamakan saat SCORING.md direvisi
  Fase 2 (di luar wewenang amandemen ini).
- API/UI Fase 1-lanjutan harus menangani `total=None` (jangan tampilkan
  0/100) dan menampilkan "dari N kategori terukur".

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
