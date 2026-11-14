# Riset Sinyal Sosial & Reputasi — Fase 1 CekLoker

> **Status:** Riset + kode rule-based selesai (Fase 1). **Bahasa:** Indonesia.
> **Tanggal cek:** 15 November 2026. **Penulis:** Tim Sosial & Reputasi.
> **Kode:** `packages/flag-engine/social_signals.py` (+ unit test
> `packages/flag-engine/tests/test_social_signals.py`, 41 test lolos).
> **Keputusan yang mengikat:** `docs/adr/ADR-0005-rubrik-skor-rule-based.md`
> dan `docs/adr/ADR-0006-sumber-reputasi-dan-anti-fitnah.md`.

## Cara membaca dokumen ini (VERIFIKASI vs ASUMSI)

- **VERIFIKASI PRIMER** — klaim yang dicek langsung ke halaman ketentuan
  resmi sumber itu (dibuka dan dibaca teksnya pada 15 Nov 2026):
  Glassdoor Terms of Use (revisi 1 Juli 2026), JobStreet Website Terms
  and Conditions, Google Places API Policies, Reddit Responsible Builder
  Policy, Kaskus Syarat dan Ketentuan. Dikutip pasal/bagiannya.
- **VERIFIKASI SEKUNDER** — klaim dari ringkasan/berita/panduan pihak kedua
  yang **saling menguatkan dari ≥ 2 sumber independen** (mis. harga X API
  pay-per-use, harga Reddit $0,24/1.000 panggilan). Ditandai sebagai
  sekunder; angka uang **wajib dicek ulang di konsol resmi** sebelum dipakai
  menganggarkan.
- **DATA KETERSEDIAAN** — jumlah ulasan perusahaan Indonesia (Telkomsel,
  BFI Finance, dsb.) berasal dari **cuplikan hasil pencarian**, bukan dari
  pembukaan langsung halaman perusahaan atau panggilan API. Ini bukti
  ketersediaan yang cukup ("perusahaan X memang punya N ulasan di sana"),
  **bukan** hitungan live yang terverifikasi.
- **ASUMSI** — diberi label eksplisit (mis. ambang rubrik). Tidak ada klaim
  "sudah teruji live": **tidak ada** API key yang dibuat, **tidak ada**
  akun yang didaftarkan, **tidak ada** panggilan API atau scraping yang
  dijalankan dalam riset ini.
- **Konflik** diberi nomor `K-S1` … `K-S10` di §7. Bila klaim bertentangan
  atau tidak terverifikasi, ditulis penyelesaiannya atau ditandai
  "butuh jawaban Giga".

---

## 1. Tabel per sumber

| Sumber | Akses resmi | Yang bisa diambil secara legal | Batasan + ToS | Kecukupan untuk Indonesia | Peran di CekLoker |
|---|---|---|---|---|---|
| **Glassdoor** (ulasan + rating perusahaan) | **Tidak ada API publik.** API publik ditutup 2021; tersisa API mitra (partner-only, harga tidak dipublikasikan, tanpa pendaftaran mandiri). | Halaman profil perusahaan publik (rating 1–5, jumlah ulasan, % rekomendasi, ringkasan pro/kontra) — **hanya dilihat manual** oleh Giga, dicatat angkanya + tautannya. Bukan diambil otomatis. | **Terms of Use revisi 1 Juli 2026, §4.3(16) — VERIFIKASI PRIMER:** dilarang "memperkenalkan perangkat lunak atau agen otomatis … untuk scrape, strip, atau mine data … tanpa izin tertulis expressly". Juga §3.2: konten hanya untuk pemakaian pribadi, non-komersial, kecuali ada perjanjian terpisah. Login wall + Cloudflare di sebagian halaman ulasan. **Scraping otomatis = DILARANG tanpa izin tertulis.** | **Sedang-rendah, dan timpang.** Perusahaan besar/multinasional berisi: Telkomsel 155 ulasan (4,4), Huawei Indonesia 125 (3,8), Ipsos Indonesia 25 (4,0). Perusahaan menengah/kecil Indonesia umumnya **tidak ada atau < 10 ulasan** → tidak bisa memberi poin (lihat ambang n ≥ 5/20). Glassdoor **bukan** sumber utama untuk Indonesia; hanya pelengkap untuk perusahaan besar. | **Fase 2, manual saja.** Entri manual Giga (baca halaman publik, catat rating + n + tautan). Adapter otomatis **DILARANG** sampai ada izin tertulis Glassdoor (lihat K-S1). |
| **JobStreet Company Review** (`id.jobstreet.com/companies/...`) | **Tidak ada API publik untuk ulasan.** SEEK API (induk JobStreet) adalah API mitra; dokumennya menyebut JobStreet by SEEK "terbatas untuk Filipina" sampai pemberitahuan lebih lanjut — **tidak ada jalur API Indonesia yang terverifikasi.** | Halaman profil perusahaan publik: rating 1–5, jumlah rating, distribusi bintang 1–5, % "gaji tinggi/rata-rata", % "merekomendasikan", ringkasan AI atas ulasan terbaru, dan isi ulasan terbaru (sebagian). **Hanya dibaca manual** oleh Giga. | **Website Terms and Conditions (dibaca langsung, 15 Nov 2026) — VERIFIKASI PRIMER:** butir (d) melarang "aggregate, copy or duplicate" konten apa pun dari situs/aplikasi mereka "other than as permitted"; butir (u) melarang scrape/harvest/export Profil atau detail kontak kecuali lewat API yang terdokumentasi. JobStreet sendiri menulis di halaman ulasan: "Jobstreet does not verify the truth or accuracy of any reviews". **Pengambilan otomatis = melanggar ToS; manual (membaca + mencatat angka + tautan) adalah penggunaan biasa.** | **TERBAIK untuk Indonesia.** Contoh nyata (cuplikan pencarian, Nov 2026): BFI Finance 393 ulasan (4,2), Charoen Pokphand 150 (4,0), Lotte Shopping 117 (4,1), NBC Indonesia 51 (4,6), Protelindo 27 (4,7), Wowrack 8 (4,3), Brinks 9 (4,8). Perusahaan yang memasang lowongan di JobStreet hampir selalu punya halaman profil + ulasan. **Ini sumber reputasi #1 untuk Indonesia.** | **Fase 2, manual saja.** Sama seperti Glassdoor: entri manual + tautan. Adapter otomatis **DILARANG** (lihat K-S2). Temuan ini juga wajib diteruskan ke tim job-board: ToS yang sama berlaku untuk lowongan. |
| **Google Review / Google Maps** (Places API New) | **API resmi tersedia** (Google Maps Platform): Place Details mengembalikan `rating`, `userRatingCount`, dan **maksimal 5 ulasan** per tempat. Butuh proyek Google Cloud + billing. | Rating agregat + jumlah ulasan (field `rating`, `userRatingCount`) — **boleh ditampilkan live**. Teks ulasan: maksimal 5, wajib atribusi penulis + tautan `googleMapsUri`, dan **tidak boleh disimpan**. | **Places API Policies (dibaca langsung, 15 Nov 2026) — VERIFIKASI PRIMER:** "You must not pre-fetch, cache, or store Places API content" kecuali `place_id` (bebas disimpan) dan lat/lng (maks. 30 hari). "Don't … copy and save business names, addresses, or user reviews." Atribusi wajib (logo/nama Google Maps + nama penulis ulasan). **Konsekuensi: `evidence_text` untuk sumber Google HARUS kosong** — yang disimpan hanya rating, jumlah, `place_id`, dan tautan. Tampilan teks ulasan harus live dari API saat halaman dibuka, bukan dari database. | **Sedang, dan bias.** Hanya perusahaan dengan listing Google Maps (kantor fisik yang terdaftar) yang punya ulasan — bias ke ritel, cabang, dan perusahaan besar. Startup remote / PT tanpa listing = tidak ada data (ketiadaan data ≠ nilai negatif). Jumlah ulasan di Maps untuk kantor perusahaan biasanya kecil (puluhan, bukan ratusan). | **Fase 2, API resmi, rating saja.** Simpan `place_id` + rating + jumlah + tautan; jangan simpan teks ulasan. Biaya: field ulasan masuk tier termahal (sekunder: US$25/1.000 request; rating-only lebih murah — cek konsol, K-S9). Karena mahal + data tipis, prioritas **di bawah JobStreet**. |
| **X / Twitter** | **API resmi v2, bayar per pemakaian (pay-per-use).** Sejak 6 Feb 2026 tidak ada lagi tier Free/Basic/Pro untuk pendaftar baru (hanya Public Utility Apps yang dikecualikan). Sekunder (≥ 3 panduan independen, Sep–Okt 2026): baca post US$0,005/post, tulis US$0,015 (US$0,20 bila ada URL), cap 3 juta bacaan/siklus. | Pencarian publik `GET /2/tweets/search/recent` (jendela 7 hari terakhir) — sebutan nama perusahaan, keluhan, dan tautan post. Arsip penuh butuh Enterprise. | Developer Terms X melarang penggunaan di luar ketentuan; data post adalah milik penulis, kutipan harus dengan atribusi + tautan. **Tidak ada** scraping (login wall + ToS). Biaya kecil pada skala Fase 2 (contoh: 50 perusahaan × 10 post = 500 bacaan ≈ US$2,50/bulan — hitungan sekunder, cek konsol). | **Rendah untuk sinyal terstruktur.** Keluhan karyawan Indonesia di X ada, tapi tersebar, berbahasa campuran, dan sulit dikaitkan ke perusahaan tertentu tanpa model bahasa. Nilai utamanya: deteksi kasus viral (PHK, penipuan lowongan) — itu pun jarang. | **Fase 2: konteks saja, tanpa poin.** Pencarian manual/terjadwal atas nama perusahaan + kata kunci penipuan ("[nama] penipu", "[nama] biaya pendaftaran"). **Tidak masuk rumus skor** sampai ada validasi (Fase 4). |
| **Reddit** | **Data API resmi, gratis non-komersial 100 query/menit per OAuth client ID** — **tetapi sejak Nov 2025 akses mandiri (self-service) DITUTUP: semua aplikasi baru wajib minta persetujuan (approval) dulu**, termasuk proyek pribadi. Komersial butuh persetujuan tertulis terpisah. Sekunder: tarif komersial US$0,24/1.000 panggilan (angka 2023, masih dikutip 2026). | Pencarian post/komentar publik di subreddit (mis. r/indonesia, r/jobs) lewat Data API setelah approval. | **Responsible Builder Policy (dibaca langsung, 15 Nov 2026) — VERIFIKASI PRIMER:** "You must request access and get explicit approval before accessing any Reddit data through our API"; dilarang mengkomersialkan data / melatih model ML/AI tanpa izin tertulis; dilarang menyimpulkan atribut sensitif pengguna; konten yang dihapus penulis **wajib ikut dihapus** dari simpanan kita; dilarang menyamarkan identitas akses. **Pelanggaran → token dicabut / akun ditangguhkan.** | **Sangat rendah untuk Indonesia.** Komunitas karier Indonesia di Reddit kecil; hampir tidak ada ulasan perusahaan Indonesia yang sistematis. Nilai nyaris nol untuk Fase 2. | **DITUNDA ke Fase 4, dan butuh jawaban Giga (K-S5).** Alasan: (1) approval wajib — belum diajukan; (2) status CekLoker (nantinya open source / berbayar murah) kemungkinan tergolong komersial → butuh persetujuan tertulis; (3) isi Indonesia minim. Jangan bangun apa pun di atas Reddit sebelum (a) dan (b) jelas. |
| **Kaskus** (forum) | **Tidak ada API publik yang ditemukan** (15 Nov 2026). Tidak ada program developer. | Thread publik yang bisa dibaca manual (tanpa login) — laporan penipuan lowongan, pengalaman interview, nama PT bermasalah. Contoh nyata (cuplikan): thread "hati-hati penipuan modus lowongan kerja online" (PT Mitra Utama Global, diminta uang Rp500–700 ribu untuk training), "Penipuan Lowongan Kerja PT SAI" (jobdesc tidak sesuai posisi). | **Syarat dan Ketentuan KASKUS (dibaca langsung, 15 Nov 2026) — VERIFIKASI PRIMER:** pengguna non-pemilik konten "tidak boleh, tanpa persetujuan tertulis dari kami: memberikan lisensi, menjual, mentransfer, … atau mengeksploitasi LAYANAN atau KONTEN untuk tujuan komersial; … mengakses dan mengcopy LAYANAN atau KONTEN untuk membuat situs web, produk, atau layanan yang serupa atau kompetitif". Konten dilarang mengandung fitnah, penipuan, SARA, dan **"informasi pribadi suatu pihak ketiga"** (foto, alamat, telepon, email). **Artinya: pengumpulan otomatis = dilarang; penyalinan isi thread ke produk komersial = butuh izin tertulis.** | **Tinggi untuk sinyal PENIPUAN, rendah untuk reputasi umum.** Kaskus adalah tempat laporan penipuan lowongan berbahasa Indonesia paling kaya — justru untuk modus yang tidak muncul di Glassdoor/JobStreet (PT fiktif, pungutan liar, jobdesc palsu). Tapi: anonim, tidak terstruktur, tidak bisa diverifikasi kebenarannya per thread. | **Fase 2: konteks saja, tanpa poin, tautan manual saja.** Satu thread Kaskus tidak pernah memberi/mengurangi poin. Gunanya: (a) peringatan dini penipuan (ditampilkan sebagai "laporan komunitas — belum terverifikasi" + tautan), (b) daftar nama PT yang patut diperiksa manual. Jangan simpan isi thread, jangan simpan username. |
| **Berita** (PHK / ekspansi / pendanaan / kasus) | **Google News RSS — gratis, tanpa API key** (`news.google.com/rss/search?q=…&hl=id-ID&gl=ID&ceid=ID:id`). Bukan API resmi yang didokumentasikan Google (News Search API resmi dimatikan 2016); RSS adalah feed publik yang sudah bertahun-tahun tersedia. Maks. ~100 item per feed; tautan berupa redirect Google News, bukan URL penerbit langsung. | Judul + media + tanggal terbit per artikel. Cukup untuk sinyal peristiwa (PHK massal, tutup, ekspansi, pendanaan). **Bukan isi penuh artikel** (hak cipta penerbit; tautkan saja). | Hormati hak cipta: simpan judul + tautan, bukan isi artikel. RSS boleh dibaca berkala dengan sopan (jangan polling agresif). Bila butuh isi/arsip terstruktur, gunakan API berita berbayar (mis. NewsAPI, Webz.io) — di luar anggaran Fase 2. | **Baik untuk perusahaan besar; buruk untuk UKM.** PHK/pendanaan perusahaan besar diliput media nasional (Kompas, Detik, Kontan, dsb.); UKM hampir tidak pernah masuk berita. Ketiadaan berita ≠ stabil. | **Fase 2, RSS + pencocokan kata kunci judul.** Sinyal `news_*` memberi poin hanya bila ≥ 2 media independen + ≤ 12 bulan (lihat §3). |
| **Indeed** (pembanding; bukan sumber Fase 2) | **Tidak ada API publik untuk ulasan/lowongan.** Publisher API lama sudah pensiun; API mitra hanya untuk ATS/perusahaan yang memposting lowongan sendiri. | — (tidak ada rute pengambilan yang sah untuk CekLoker) | ToS Indeed (versi 29 Sep 2026, dikutip ≥ 2 panduan independen): melarang bot/scraper/agen AI mengakses atau menambang data tanpa izin tertulis; crawling hanya sebatas yang diizinkan `robots.txt` (yang memblokir halaman lowongan dan halaman perusahaan `/cmp/`). | Indeed Indonesia berisi, tapi **tidak bisa dipakai** tanpa melanggar ToS. | **DITUNDA / tidak dipakai.** Jangan jadikan sumber Fase 2. Bila suatu hari Indeed membuka API atau memberi izin tertulis, tinjau ulang (K-S10). |

### Ringkasan: apa yang sebenarnya bisa dipakai Fase 2

1. **JobStreet Company Review — sumber #1 Indonesia (manual).** Paling berisi, paling relevan.
2. **Glassdoor — pelengkap perusahaan besar (manual).**
3. **Google Places API — rating + jumlah saja (API resmi, tanpa teks ulasan).**
4. **Google News RSS — sinyal peristiwa (otomatis, judul + tautan saja).**
5. **X, Kaskus — konteks manual, tanpa poin.**
6. **Reddit, Indeed — ditunda.**

Konsekuensi terbesar dari verifikasi primer: **tidak ada satu pun sumber
ulasan yang boleh diambil otomatis tanpa izin.** Karena itu Fase 2
dirancang sebagai **entri manual Giga + RSS berita + Places API** — bukan
sebagai "scraper ulasan". Ini perubahan dari bayangan awal di
ARCHITECTURE.md §5 ("sumber resmi/terstruktur" seolah-olah bisa diambil
langsung); lihat K-S1/K-S2 dan ADR-0006.

---

## 2. Kecukupan data untuk Indonesia (bukti nyata)

Data di bawah ini dari cuplikan hasil pencarian (15 Nov 2026) — cukup
untuk menjawab "apakah sumber ini berisi untuk perusahaan Indonesia?",
bukan hitungan live:

| Perusahaan | Glassdoor (Indonesia) | JobStreet Review |
|---|---|---|
| Telkomsel | 155 ulasan, 4,4 | — |
| Huawei Technologies (ID) | 125 ulasan, 3,8 | — |
| Ipsos Indonesia | 25 ulasan, 4,0 | — |
| BFI Finance | — | 393 ulasan, 4,2 |
| Charoen Pokphand | — | 150 ulasan, 4,0 |
| Lotte Shopping | — | 117 ulasan, 4,1 |
| NBC Indonesia | — | 51 ulasan, 4,6 |
| Protelindo | — | 27 ulasan, 4,7 |
| Wowrack Indonesia | — | 8 ulasan, 4,3 |
| Brinks Solutions Indonesia | — | 9 ulasan, 4,8 |

**Kesimpulan:**

- **JobStreet adalah satu-satunya sumber yang berisi untuk perusahaan
  Indonesia lintas ukuran** — dari 393 ulasan (BFI) sampai 8–9 ulasan
  (Wowrack, Brinks). Tapi perhatikan: perusahaan dengan **< 20 ulasan
  tidak bisa memberi poin penuh** (ambang §3) — Wowrack (8) dan Brinks (9)
  hanya mendapat setengah poin. Ini disengaja (grill G-1).
- **Glassdoor hanya berisi untuk perusahaan besar/multinasional.**
  Perusahaan Indonesia menengah/kecil umumnya tidak ada di sana.
- **Kesenjangan struktural:** mayoritas perusahaan yang memasang lowongan
  di Glints/JobStreet adalah UKM dengan sedikit atau tanpa ulasan di mana
  pun. Untuk mereka, skor reputasi akan sering berbunyi **"Belum cukup
  data"** — dan itu jawaban yang benar, bukan kegagalan. Skor tidak boleh
  mengarang reputasi dari ketiadaan data.
- **Google Maps** menutupi sebagian celah untuk perusahaan dengan kantor
  fisik, tetapi datanya tipis dan bias ke ritel/cabang.
- **Kaskus** menutupi celah yang berlawanan: justru PT kecil/fiktif yang
  menipu yang paling banyak dibicarakan di sana — tetapi sebagai konteks,
  bukan poin.

---

## 3. Pemetaan sinyal ke rubrik SCORING.md

Rubrik: total 100 poin — Transparansi 25, Reputasi 25, Stabilitas 20,
Praktik rekrutmen 15, Gaji & benefit 15 (lihat `docs/SCORING.md`).
**Modul sosial ini mengisi: Reputasi (penuh), Stabilitas (berita),
Praktik rekrutmen (ghost job), Transparansi (biaya).** Sinyal Gaji &
benefit dan Transparansi-gaji berasal dari modul lain (tim job-board);
modul ini hanya menyediakan fungsi agregasi bersama (`aggregate_signals`).

### 3.1 Tabel sinyal final (Fase 2)

| Key | Kategori (cap) | Rumus / ambang poin | Confidence | Evidence wajib | Contoh |
|---|---|---|---|---|---|
| `rating_overall` | Reputasi (25) | Rating 1–5 + n ulasan. **n ≥ 20:** ≥ 4,0 → +15; 3,5–3,99 → +8; 2,5–3,49 → 0; < 2,5 → −10. **n 5–19:** setengah poin (±8/±4/0/−5 — pembulatan `round`, mis. 15×0,5 = 8). **n < 5:** 0 poin, konteks saja. | high bila n ≥ 50; medium bila n ≥ 20; low bila n < 20 | `evidence_url` (tautan halaman profil), `evidence_date` (tanggal data dicatat), `source` (`glassdoor` / `jobstreet_review` / `google_places`), `evidence_text` (ringkasan angka, mis. "4,4 dari 155 ulasan"; untuk Google: teks ulasan dikosongkan — hanya angka + `place_id`) | Telkomsel: 4,4 dari 155 → +15, high. Brinks: 4,8 dari 9 → +8, low. |
| `recommend_rate` | Reputasi (25) | % "merekomendasikan ke teman", **n ≥ 20:** ≥ 80% → +5; 50–79% → 0; < 50% → −5. n < 20 → 0 poin, konteks saja. | medium (n ≥ 20); low (n < 20) | sama seperti di atas | Telkomsel 97% (n=155) → +5. |
| `complaint_repeated` | Reputasi (25) | Hitung **ulasan berbeda** yang mengandung ≥ 1 cluster keluhan (lembur tidak dibayar; gaji telat/ditahan; PHK sepihak/tanpa pesangon; jam kerja berlebihan) — satu ulasan dihitung sekali per cluster, negasi dikecualikan ("gaji tidak pernah telat" bukan keluhan). **≥ 3 ulasan → −5; ≥ 5 ulasan DAN pangsa ≥ 10% dari sampel → −15.** Di bawah itu 0 poin, konteks saja. | medium bila poin ≠ 0 dan n ≥ 20; low bila tidak | `evidence_url`, `evidence_date`, `source`, `evidence_text` = kutipan pertama yang cocok (≤ 280 karakter, **tanpa nama reviewer**) | 5 dari 25 ulasan (20%) menyebut "gaji telat" → −15. 5 dari 100 ulasan (5%) → −5 (pangsa kecil). 1 ulasan marah → 0. |
| `fee_request` | Transparansi (25) | Teks lowongan mengandung pola permintaan biaya ("biaya pendaftaran", "bayar biaya training", "transfer biaya administrasi", … — "adm"/"administrasi" hanya dihitung bila berdampingan dengan biaya/bayar/uang). **Bila cocok: `red_override` — label langsung Red + peringatan, apa pun skor lain. Poin 0** (sanksinya berupa override, bukan pengurangan poin, supaya tidak bisa "ditebus" poin positif). | high (bukti kutipan langsung dari teks lowongan) | `evidence_url` (tautan lowongan), `evidence_date`, `source`, `evidence_text` = kutipan kalimat yang meminta biaya (≤ 280 karakter) | "Transfer biaya pendaftaran Rp300.000 sebelum interview" → Red + peringatan. "Dibutuhkan staff administrasi" → tidak memicu. |
| `news_layoff_massal` / `news_tutup` | Stabilitas (20) | Berita PHK massal / tutup dalam **≤ 12 bulan** terakhir DAN **≥ 2 media independen** (atau pernyataan resmi perusahaan) → **−15**. Satu media saja, atau > 12 bulan → 0 poin, konteks saja. | medium bila poin ≠ 0; low bila tidak | `evidence_url` (tautan artikel), `evidence_date` (tanggal terbit), `source` (`google_news_rss`), `evidence_text` = judul artikel | PHK diliput 2 media, 3 bulan lalu → −15. Satu blog 18 bulan lalu → 0. |
| `news_ekspansi` / `news_pendanaan` | Stabilitas (20) | Sama syaratnya (≥ 2 media, ≤ 12 bulan) → **+5**. | medium / low | sama seperti di atas | Ekspansi + pendanaan, 2 media → +5. |
| `ghost_job` | Praktik rekrutmen (15) | Lowongan yang sama tayang **> 90 hari** tanpa perubahan DAN perusahaan punya **≥ 3 lowongan basi** sekaligus DAN jabatan **bukan evergreen** (sales/driver/kurir/dsb. memang rekrutmen bergulir) → **−10**. Satu lowongan basi, atau jabatan evergreen → 0 poin, konteks saja. | medium bila poin ≠ 0; low bila tidak | `evidence_url` (tautan lowongan), `evidence_date`, `source` | "Backend Engineer" tayang 120 hari, 4 lowongan basi → −10. "Sales Executive" tayang 200 hari → 0 (evergreen). |
| `social_buzz` (X / Reddit / Kaskus) | — (konteks) | **Tanpa poin, selamanya di Fase 2.** Ditampilkan sebagai "konteks" dengan tautan + tanggal + label "belum terverifikasi" bila sumbernya forum/anonim. | low | `evidence_url`, `evidence_date`, `source`, `evidence_text` ≤ 280 karakter, tanpa nama pengguna | Thread Kaskus tentang PT X → tampil sebagai konteks, skor tidak berubah. |

### 3.2 Contoh perhitungan lengkap

**Contoh A — perusahaan besar, reputasi kuat (angka nyata Glassdoor):**

- `rating_overall`: 4,4 dari 155 ulasan (Glassdoor) → **+15**, high.
- `recommend_rate`: 97% (n=155) → **+5**, medium.
- `news_ekspansi`: 2 media, 2 bulan lalu → **+5**, medium.
- Kategori terukur: reputasi 20/25 + stabilitas 5/20 → cap terukur 45,
  perolehan 25 → **total = 100 × 25/45 = 56 → Mixed**.
- Catatan: **bukan Green** — baru 2 dari 5 kategori terukur (grill G-2).
  Total mentah lama (25/100) akan salah menyebutnya Red.

**Contoh B — perusahaan bermasalah:**

- `rating_overall`: 1,5 dari 100 ulasan → **−10**.
- `complaint_repeated`: 10 dari 30 ulasan menyebut "gaji telat" (33%) → **−15**.
- `news_tutup`: 2 media, 1 bulan lalu → **−15**.
- Kategori terukur: reputasi −25/25 + stabilitas −15/20 → cap 45,
  perolehan −40 → **total = 0 → Red**. 3 sinyal penentu, 2 kategori.

**Contoh C — perusahaan bagus tapi baru (grill G-1):**

- `rating_overall`: 4,8 dari 9 ulasan (Brinks, data nyata JobStreet) → **+8** (setengah poin), low.
- Hanya 1 sinyal penentu → **label: Belum cukup data**.
- Bukan Red, bukan Green. Skor tidak mengarang dari 9 ulasan.

**Contoh D — fee (override):**

- Perusahaan dengan rating 4,4 + rekomendasi 97% + ekspansi (total 56,
  Mixed seperti Contoh A), tetapi satu lowongannya menulis "bayar biaya
  pendaftaran Rp500rb" → **`red_override` → label Red + peringatan**,
  dengan kutipan + tautan sebagai bukti. Poin positif tidak menghapus
  peringatan ini.

### 3.3 Aturan agregasi (`aggregate_signals`)

- Tiap kategori dijepit ke [−cap, +cap].
- **Total ternormalisasi** terhadap kategori yang terukur (punya ≥ 1 sinyal
  penentu): `total = 100 × perolehan / cap_terukur`, dijepit 0–100.
  Ini **perubahan dari draf ARCHITECTURE.md §5** (penjumlahan mentah) —
  alasannya di §6 (G-2) dan ADR-0005. **Butuh persetujuan Giga** karena
  mengubah rubrik.
- Label: fee → Red; sinyal penentu < 3 **atau** kategori penentu < 2 →
  "Belum cukup data"; ≥ 70 Green; 40–69 Mixed; < 40 Red.
- Sinyal penentu (`decisive=True`): rating n ≥ 5; recommend n ≥ 20;
  keluhan/ghost/berita yang benar-benar memberi poin; fee yang terbukti.
  Konteks tanpa poin tidak dihitung penentu.

---

## 4. Aturan anti-fitnah + privasi

### 4.1 Mana yang BOLEH memengaruhi skor, mana yang hanya konteks

| Jenis bukti | Pengaruh skor | Syarat |
|---|---|---|
| Rating agregat + jumlah ulasan | Poin (lihat §3.1) | n ≥ 5; sumber: Glassdoor/JobStreet/Google (manual/API resmi) |
| % rekomendasi | Poin | n ≥ 20 |
| Keluhan berulang (kata kunci eksplisit) | Poin | ≥ 3 ulasan berbeda (≥ 5 + pangsa ≥ 10% untuk −15) |
| Permintaan biaya di teks lowongan | Override Red | Kutipan langsung dari lowongan |
| Berita PHK/tutup/ekspansi | Poin | ≥ 2 media independen, ≤ 12 bulan |
| Ghost job | Poin | > 90 hari + ≥ 3 lowongan basi + bukan evergreen |
| Satu-dua ulasan ekstrem | **Konteks saja** | Tampil dengan label "1 ulasan — belum cukup untuk poin" |
| Thread Kaskus / post X / Reddit | **Konteks saja** | Tampil sebagai "laporan komunitas — belum terverifikasi" + tautan |
| Satu artikel berita | **Konteks saja** | Bisa jadi rumor; butuh media kedua untuk poin |
| Rating n < 5 | **Konteks saja** | Angka ditampilkan, poin 0 |
| Ulasan anonim (tanpa identitas terverifikasi) | **Boleh dihitung agregatnya** (rating/jumlah/keluhan), **tanpa nama** | Nama reviewer **tidak pernah** disimpan atau ditampilkan |

### 4.2 Menangani 1–2 ulasan negatif ekstrem

1. **Tidak pernah memberi poin.** Ambang minimum 3 ulasan berbeda untuk
   −5; satu ulasan marah, sepedas apa pun, bernilai 0.
2. **Tampil sebagai konteks** dengan jumlah yang jujur ("1 dari 30 ulasan
   menyebut …"), bukan sebagai vonis.
3. **Tuduhan berat** (penipuan, pencurian, pelecehan, pelanggaran hukum)
   dalam satu ulasan **tidak pernah dikutip sebagai fakta** — paling jauh
   ditampilkan sebagai "ada laporan [topik] di [sumber], tautan" dengan
   label belum terverifikasi. Kami tidak pernah menulis "perusahaan ini
   penipu" atau "perusahaan ini melanggar UU" — itu penilaian hukum, bukan
   tugas kami (ARCHITECTURE.md §1: "bukan penilai hukum").
4. **Pola ledakan (burst):** banyak ulasan 1-bintang dalam waktu singkat
   dari sumber yang sama → ditandai sebagai konteks "lonjakan ulasan
   negatif pada [periode]" dan **tidak** dihitung sebagai keluhan berulang
   bila berasal dari < 3 tanggal berbeda. (Deteksi burst otomatis belum
   diimplementasikan — Fase 2 manual; lihat §8.)

### 4.3 Ulasan anonim

- Glassdoor/JobStreet memang anonim secara desain — itu **bukan** alasan
  menolak datanya, tapi alasan membatasi bobotnya (ambang n, confidence).
- Nama pengguna forum (Kaskus/X/Reddit) **tidak disimpan dan tidak
  ditampilkan**. Kutipan ≤ 280 karakter, tautan ke sumber asli.
- Bila suatu kutipan masih bisa mengidentifikasi seseorang (nama orang,
  jabatan spesifik + kota kecil), kutipan **tidak ditampilkan** — hanya
  angka agregat + tautan.

### 4.4 Permintaan koreksi perusahaan (alur)

1. Perusahaan mengajukan koreksi lewat form (nama perusahaan, sinyal yang
   disengketakan, bukti tandingan, kontak) — lihat ARCHITECTURE.md §5.4.
2. **Sinyal yang disengketakan langsung dibekukan:** poinnya ditangguhkan
   (dihitung 0 sementara) dan ditampilkan sebagai "disengketakan —
   sedang ditinjau" sampai ada keputusan. Ini mencegah skor yang
   disengketakan terus merugikan selama proses.
3. Tanggapan ≤ 7 hari (ARCHITECTURE.md §8). Keputusan: (a) sinyal
   dipertahankan + alasan tertulis, (b) sinyal dikoreksi, (c) sinyal
   dihapus bila bukti tidak cukup. Tanggapan perusahaan (bila sopan dan
   faktual) **diterbitkan berdampingan** dengan sinyal.
4. Perusahaan **tidak bisa** meminta penghapusan sinyal hanya karena
   tidak suka — hanya bila bukti salah / kedaluwarsa / melanggar aturan
   (data pribadi, fitnah, duplikat). Penolakan disertai alasan tertulis.
5. Sinyal kedaluwarsa: rating dihitung ulang bila data > 12 bulan;
   keluhan > 24 bulan keluar dari poin (konteks saja); berita > 12 bulan
   tidak memberi poin (sudah di rumus §3.1).

### 4.5 Privasi — yang TIDAK PERNAH disimpan

- Nama pelamar, email, telepon, CV, atau isi lamaran.
- Nama reviewer / nama pengguna forum / foto profil / handle X/Reddit.
- Isi DM, grup tertutup (WhatsApp/Telegram/Discord), atau konten di balik
  login.
- Gaji individu, NIK, alamat rumah, atau data pribadi lain dari ulasan.
- Yang disimpan: **angka agregat + kutipan singkat (≤ 280 karakter) +
  tautan + tanggal + sumber.** Untuk Google: bahkan kutipan pun tidak
  disimpan (larangan ToS — K-S3).

Dasar hukum (ringkasan umum, **bukan nasihat hukum**; cek teks resmi):
UU PDP No. 27/2022 (data pribadi hanya diproses dengan dasar sah,
tujuan jelas, minimasi; subjek data berhak minta hapus — Pasal 8, 43);
KUHP baru (UU 1/2023, berlaku 2 Jan 2026) Pasal 433–441 tentang
pencemaran/fitnah; **Putusan MK No. 105/PUU-XXII/2024 (29 Apr 2025)**:
korporasi/lembaga pemerintah **tidak dapat** menjadi pengadu pasal
pencemaran nama baik — tetapi **gugatan perdata** (perbuatan melawan
hukum) dan pengaduan oleh **individu** (mis. HR yang namanya disebut)
tetap terbuka. Jadi risiko hukum **tidak hilang** hanya karena putusan MK
— lihat K-S7. Bila ragu, minta pendapat penasihat hukum sebelum
publikasi luas (Fase 5).

---

## 5. Kenapa sentimen ML ditunda sampai Fase 4

**Yang hilang karena penundaan ini (jujur):**

- Nuansa: sarkasme, ulasan campuran ("gaji oke tapi lembur parah"),
  bahasa gaul Indonesia ("PHP", "zonk", "gas") tidak tertangkap kata
  kunci.
- Cakupan: teks bebas di X/Reddit/Kaskus tidak bisa dihitung — hanya
  bisa tampil sebagai konteks manual.
- Kecepatan: volume teks besar harus dibaca manusia.

**Kenapa tetap ditunda (keputusan ADR-0005):**

1. **Tidak ada akurasi yang bisa diklaim.** Tidak ditemukan benchmark
   sentimen Bahasa Indonesia untuk ulasan tempat kerja yang terverifikasi
   — akurasi "90%" dari model umum tidak berlaku untuk domain ini.
   Mengklaim skor ML tanpa pengujian melanggar prinsip "skor tanpa bukti
   tidak tampil": skor ML tidak bisa ditunjukkan buktinya per poin.
2. **ToS melarang latih model dari data sumber.** Reddit (Responsible
   Builder Policy, primer): dilarang memakai data untuk melatih model
   ML/AI tanpa izin tertulis. JobStreet Terms butir (t): dilarang memakai
   Profil untuk membangun/melatih model ML/AI. Melatih sentimen dari data
   ini = pelanggaran ketentuan sumber.
3. **Tidak bisa dikoreksi perusahaan.** Skor ML yang tidak bisa dijelaskan
   ("model berkata negatif") tidak bisa dijawab dalam proses koreksi §4.4
   — perusahaan berhak tahu *kalimat mana* yang mengurangi skornya.
4. **Biaya dan kredibilitas.** Rule-based sudah menangkap sinyal
   bernilai tertinggi (biaya, keluhan berulang, rating) dengan biaya nol
   dan hasil yang bisa diaudit baris per baris.
5. **Bahasa Indonesia adalah kasus sulit.** Negasi, sarkasme, dan campur
   kode (Indonesia–Inggris–daerah) membuat model umum sering salah pada
   teks pendek seperti ulasan — tanpa dataset berlabel lokal, ML adalah
   tebakan berbaju angka.

**Gerbang masuk Fase 4 (tidak boleh dilompati):** 200 contoh ulasan
Berbahasa Indonesia berlabel (positif/negatif/netral + cluster keluhan)
yang dinilai manusia; precision/recall per cluster dilaporkan; contoh
yang diperselisihkan manusia vs model ditinjau manual; model hanya
dipakai sebagai **sinyal pendukung** (menambah konteks / menandai ulasan
untuk ditinjau manusia), bukan penentu poin langsung, sampai akurasinya
terbukti di atas ambang yang disepakati Giga.

---

## 6. Hasil Grill (skill Matt Pocock grill-with-docs)

Setiap keputusan besar di-grill kejam sebelum diterima. Yang di bawah ini
bukan tempelan — **grill inilah yang mengubah desain** (perubahan dicatat
di tiap butir dan di ADR-0005/ADR-0006).

### G-1 — "Perusahaan bagus tapi baru vs perusahaan bermasalah tapi rajin minta ulasan positif — rubrikmu adil?"

**Pertanyaan grill:** Perusahaan baru yang bagus hanya punya 4 ulasan
5-bintang. Perusahaan bermasalah yang rajin meminta ulasan positif dari
karyawan yang masih bekerja punya 60 ulasan 5-bintang. Rubrik awal
(ARCH §5: "rating ≥ 4,0 dari ≥ 20 ulasan = +15") memberi yang pertama
0 dan yang kedua +15. Apa rubrikmu melindungi keduanya?

**Jawaban:** Tidak — rubrik awal gagal di kedua arah. Perbaikannya:
(1) **tiering n**: n 5–19 hanya setengah poin, n < 5 nol poin — perusahaan
baru tidak dihukum (label "Belum cukup data", bukan Red) dan tidak
dipuji berlebihan dari segelintir ulasan; (2) **rating bukan satu-satunya
penentu reputasi**: keluhan berulang (`complaint_repeated`) dihitung
dari teks, independen dari rating — perusahaan bermasalah yang
ulasan-ulasannya tetap berisi "lembur tidak dibayar" akan terkena −5/−15
meski ratingnya 4,5; (3) **pangsa + jumlah absolut** dipakai bersamaan,
supaya 5 keluhan dari 500 ulasan tidak disamakan dengan 5 dari 25.

**Yang BERUBAH:** tiering n + setengah poin + `decisive` (sinyal n kecil
tidak dihitung penentu) + `complaint_repeated` memakai dua ambang
(jumlah DAN pangsa). **Yang BELUM berubah (jujur):** manipulasi ulasan
positif (review solicitation) tidak bisa dideteksi rule-based —
perusahaan yang "meminta" ulasan positif tidak tertangkap. Mitigasi yang
diputuskan: (a) tidak pernah memberi label Green dari rating saja (butuh
≥ 2 kategori penentu); (b) distribusi bintang (mis. 95% bintang 5 +
hampir tanpa bintang 1–3) dicatat sebagai **sinyal yang dipertimbangkan
untuk Fase 2** — belum masuk kode karena ambangnya butuh data kalibrasi
(50 perusahaan). Tidak ada klaim "anti-palsu" di mana pun.

### G-2 — "Dari mana angka 'rating ≥ 4,0 dari ≥ 20 ulasan' — apa buktinya bukan asal tebak?"

**Pertanyaan grill:** 4,0 — kenapa bukan 3,8 atau 4,2? 20 — kenapa bukan
10 atau 50? Tunjukkan sumbernya. Kalau tidak ada, akui itu tebakan.

**Jawaban:** Jujur: angka 4,0 dan ambang +15/+8/−10 **diwarisi dari
contoh di ARCHITECTURE.md §5, bukan dari standar industri** — tidak ada
standar eksternal yang ditemukan (K-S8). Yang bisa dipertahankan secara
statistik hanya **n ≥ 20**: dengan simpangan baku rating ~1,0 (asumsi —
bukan fakta terukur), galat baku rata-rata pada n=20 adalah ~0,22,
sehingga beda 4,0 vs 3,5 adalah ~2 galat baku (cukup berarti); pada n=5
galat bakunya ~0,45 (terlalu berisik untuk poin penuh). Angka 4,0/3,5/2,5
sendiri tetap heuristik — dipilih karena membagi skala 1–5 menjadi
"jelas bagus / menengah-atas / menengah-bawah / jelas buruk" yang mudah
dijelaskan ke pengguna dan perusahaan.

**Yang BERUBAH (terbesar dalam riset ini):** agregasi total. Grill
menemukan penjumlahan mentah ARCH §5 **menghukum data yang belum diukur
seolah-olah data buruk** — perusahaan bagus yang baru terukur 2 kategori
(25 poin dari 100) langsung berlabel Red. Total kini **dinormalisasi
terhadap kategori yang terukur** (`100 × perolehan / cap_terukur`) dan
label baru diberikan bila ada ≥ 3 sinyal penentu dari ≥ 2 kategori.
Perubahan ini **menyimpang dari ARCH §5 dan butuh persetujuan Giga**
(lihat ADR-0005). Ambang 4,0/20 sendiri **dipertahankan sebagai
heuristik** dengan kewajiban kalibrasi ulang di Fase 2 (50 perusahaan:
uji apakah ambang ini memisahkan perusahaan bermasalah dari yang sehat,
lalu revisi lewat ADR).

### G-3 — "Bagaimana 1–2 ulasan ekstrem atau palsu dicegah mengubah skor?"

**Pertanyaan grill:** Satu mantan karyawan yang marah menulis ulasan
1-bintang sepanjang 3 paragraf dengan kata "penipu" di judul. Satu
pesaing menulis 2 ulasan palsu. Apa yang terjadi pada skor?

**Jawaban:** Pada rubrik awal: tidak ada yang mencegah — keluhan "≥ 5x"
di ARCH §5 sebenarnya sudah mensyaratkan 5, tetapi definisi "muncul"
tidak jelas (5x kata yang sama dalam 1 ulasan? 5 ulasan?). Perbaikan:
(1) **satu ulasan dihitung sekali per cluster** — ulasan 3 paragraf yang
mengulang "gaji telat" 5x tetap dihitung 1; (2) **ambang 3 ulasan berbeda**
untuk −5, **5 ulasan + pangsa ≥ 10%** untuk −15 — 1–2 ulasan = 0 poin;
(3) **tuduhan berat dari satu sumber tidak pernah jadi fakta** di
tampilan (hanya "laporan — belum terverifikasi" + tautan); (4) ulasan
palsu **tidak diklaim bisa dideteksi** — yang diklaim hanya: dampaknya
dibatasi oleh ambang jumlah + pangsa + keharusan multi-kategori untuk
label. Palsu yang terkoordinasi (> 5 akun) tetap bisa lolos — dicatat
sebagai risiko terbuka di ADR-0006, dengan mitigasi manual (tinjau pola
tanggal/bahasa bila ada lonjakan).

### G-4 — "Kata kuncimu — apa jadinya kalimat pujian yang mengandung kata keluhan?"

**Pertanyaan grill:** "Gaji **tidak pernah** telat, lembur **selalu
dibayar**" mengandung "gaji telat" dan "lembur dibayar". Mesin kata
kuncimu akan menghukum perusahaan terbaik. Dan "lembur" saja tanpa
"tidak dibayar" — lembur itu sendiri bukan pelanggaran.

**Jawaban:** Benar — pencocokan naif gagal. Perbaikan: (1) **pelindung
negasi** — bila kata negasi (tidak/tak/nggak/bukan/never/not, dsb.)
muncul ≤ 25 karakter sebelum kecocokan, kecocokan dibatalkan; (2) pola
keluhan **mensyaratkan kata kerja negatifnya** ("lembur *tidak dibayar*",
bukan "lembur" saja); (3) unit tes khusus: "gaji tidak pernah telat,
lembur selalu dibayar" → 0 keluhan (diuji). Sisa risiko: negasi jauh
("gajinya sih oke, cuma kadang telat" — "kadang" tidak tertangkap),
sarkasme, dan kalimat terbalik ("telat? tidak pernah!"). Dicatat sebagai
keterbatasan rule-based; inilah salah satu alasan ML ditunda, bukan
diatasi setengah-setengah (§5).

### G-5 — "Pola 'biaya adm' — apa jadinya lowongan 'staff administrasi'?"

**Pertanyaan grill:** Pola fee-mu mengandung "adm". Setiap lowongan
"staff administrasi" — jabatan yang sah dan umum — akan memicu Red +
peringatan penipuan. Berapa banyak lowongan sah yang akan kau fitnah?

**Jawaban:** Pada draf pertama, benar — "adm" sebagai kata bebas akan
memicu. Perbaikan: **"adm"/"administrasi" hanya dihitung bila
berdampingan dengan "biaya"/"bayar"/"uang"/"transfer"/"Rp"** (pola
regex menuntut konteks pembayaran). Unit tes: "Dibutuhkan staff
administrasi" → tidak memicu; "Bagian ADM akan menghubungi kandidat" →
tidak memicu; "transfer biaya pendaftaran Rp300.000" → memicu. Sisa
risiko: lowongan sah yang menulis "tidak ada biaya administrasi" —
kata "tidak ada" **tidak** berada dalam jendela negasi pola fee (negasi
dicek sebelum pola, bukan di tengahnya). Ini cacat yang diketahui:
pola `biaya\s+(pendaftaran|administrasi|…)` akan cocok pada "tidak ada
biaya pendaftaran". **Perbaikan yang diputuskan sesudah grill:** fungsi
`detect_fee_request` juga memeriksa negasi di depan kecocokan (sama
seperti keluhan) — "tidak ada biaya pendaftaran" kini tidak memicu.
Tetap ada sisa risiko kalimat lain ("biaya ditanggung perusahaan" —
"biaya" + "ditanggung" tidak ada di pola, aman; "biaya hidup
ditanggung" — aman). Pola fee wajib ditinjau ulang tiap kalibrasi Fase 2
dengan contoh lowongan nyata.

### G-6 — "Ghost job — apa jadinya lowongan sales yang memang selalu buka?"

**Pertanyaan grill:** Perusahaan sales membuka lowongan "Sales
Executive" 365 hari setahun karena turnover tinggi. Rubrik awal
("> 90 hari = −10") menghukum praktik rekrutmen yang sah. Dan
lowongan yang direpost tiap bulan dengan tanggal baru — apakah itu
ghost job atau rekrutmen aktif?

**Jawaban:** Rubrik awal salah untuk jabatan bergulir. Perbaikan:
(1) **pengecualian evergreen** — jabatan sales/driver/kurir/telemarketing
dan sejenis tidak pernah mendapat poin ghost job (konteks saja);
(2) **ambang ganda** — satu lowongan basi tidak cukup; butuh ≥ 3
lowongan basi sekaligus di perusahaan yang sama (pola, bukan satu
kecelakaan); (3) pengakuan batas: repost dengan tanggal baru **tidak
bisa dibedakan** dari rekrutmen aktif hanya dari tanggal — sinyal ini
bergantung pada `first_seen_at`/`last_seen_at` dari tim scraper (fingerprint
lowongan yang sama), bukan pada `posted_at` yang ditulis sumber. Bila tim
scraper belum menyediakan fingerprint stabil, sinyal ghost job **tidak
boleh memberi poin** (konteks saja). Dicatat sebagai dependensi di §10.

### G-7 — "Satu artikel berita — apa jadinya rumor, atau berita 3 tahun lalu?"

**Pertanyaan grill:** Satu blog menulis "PT X PHK massal" — belum tentu
benar, belum tentu massal. Artikel 2023 tentang PHK — perusahaannya
sudah pulih. Rubrik awal ("berita PHK −15") tidak membedakan.

**Jawaban:** Benar. Perbaikan: **−15 hanya bila ≥ 2 media independen
atau pernyataan resmi perusahaan, DAN ≤ 12 bulan terakhir.** Satu media
→ konteks saja; > 12 bulan → konteks saja. Tambahan: judul saja yang
dipakai (bukan isi penuh — hak cipta), dan media yang dikutip harus
media yang punya redaksi (bukan blog anonim) — definisi "media
independen" ini masih perlu daftar yang disepakati di Fase 2 (masuk
§10). Berita positif (ekspansi/pendanaan) diberi syarat yang sama
supaya tidak ada standar ganda.

### G-8 — "Kenapa sentimen ML ditunda — apa yang hilang, dan kapan kau mengaku kalah?"

**Pertanyaan grill:** Kau menunda ML dengan alasan "belum teruji". Tapi
tanpa ML, kau tidak bisa membaca X/Reddit/Kaskus sama sekali — dan itu
justru sumber yang kau sebut "paling kaya untuk penipuan". Bukankah
penundaan ini membuat CekLoker buta di sumber terpentingnya? Apa
kriteriamu untuk berkata "sekarang ML layak"?

**Jawaban:** Kehilangan itu nyata dan diakui di §5 — tapi "membaca"
bukan sama dengan "menilai". Yang ditunda adalah **ML sebagai penentu
poin**, bukan ML sebagai alat bantu baca. Yang tetap jalan Fase 2:
pencarian kata kunci eksplisit (biaya, penipuan, nama PT) + tautan
manual — itu sudah menangkap modus penipuan yang paling berbahaya
(pungutan biaya), tanpa perlu memahami sarkasme. Kriteria "ML layak"
ditulis sebagai gerbang di §5 (200 contoh berlabel, precision/recall
dilaporkan, ML hanya pendukung sampai terbukti). Alasan paling keras
menunda bukan teknis, melainkan **hukum**: Reddit dan JobStreet
**melarang** memakai data mereka untuk melatih model ML/AI tanpa izin
tertulis — jadi "latih saja dulu" bukan opsi yang tersedia.

---

## 7. Konflik verifikasi (K-S1 … K-S10)

| ID | Klaim yang bertentangan / tidak terverifikasi | Status |
|---|---|---|
| **K-S1** | ARCHITECTURE.md §5 menempatkan Glassdoor sebagai sumber reputasi prioritas #1 ("sumber resmi/terstruktur") — tetapi Glassdoor Terms of Use §4.3(16) (primer, revisi 1 Jul 2026) **melarang scraping/mining otomatis tanpa izin tertulis**, dan tidak ada API publik sejak 2021. | **DISELESAIKAN dengan perubahan desain:** Glassdoor Fase 2 = entri manual saja; adapter otomatis dilarang sampai izin tertulis. Dicatat di ADR-0006. |
| **K-S2** | JobStreet adalah sumber Fase 1 (lowongan) sekaligus sumber ulasan #1 — tetapi JobStreet Terms butir (d) melarang agregasi/penyalinan konten dan butir (u) melarang scraping Profil kecuali via API terdokumentasi; tidak ada API ulasan Indonesia yang terverifikasi. | **DISELESAIKAN sebagian (untuk tim ini):** ulasan JobStreet = entri manual saja. **DITERUSKAN ke koordinator/tim job-board:** ToS yang sama berlaku untuk adapter lowongan Glints/JobStreet — tim itu harus menjawab apakah pengambilan lowongan mereka melanggar butir (d) atau ada dasar lain. Bukan wewenang tim sosial memutuskan. |
| **K-S3** | Model data ARCH §4 (`signals.evidence_text`) mengasumsikan kutipan bisa disimpan untuk semua sumber — tetapi Google Places API Policies (primer) **melarang menyimpan teks ulasan** ("copy and save … user reviews"). | **DISELESAIKAN:** untuk sumber `google_places`, `evidence_text` wajib kosong; yang disimpan hanya rating, jumlah, `place_id`, tautan. Dicatat di ADR-0006 + docstring kode. Jika tim API/DB menganggap `evidence_text` wajib terisi untuk semua sinyal, skema harus diubah (kolom boleh null). |
| **K-S4** | Asumsi umum "API X gratis untuk memantau sebutan perusahaan" — **salah untuk pendaftar baru sejak 6 Feb 2026**: pay-per-use US$0,005/bacaan, tanpa free tier (kecuali Public Utility Apps). | **DISELESAIKAN:** X tidak masuk perhitungan biaya gratis; anggaran pay-per-use dihitung (murah pada skala Fase 2) dan X hanya konteks. **Harga dari sumber sekunder** — wajib cek konsol `developer.x.com` sebelum menganggarkan. |
| **K-S5** | Reddit Data API "gratis 100 QPM" — **benar, tetapi tidak bisa langsung dipakai**: Responsible Builder Policy (primer, Nov 2025) mewajibkan approval untuk SEMUA aplikasi, dan penggunaan komersial butuh persetujuan tertulis. Status CekLoker (nantinya open source / berbayar murah) belum diputuskan → belum jelas apakah masuk "komersial". | **BUTUH JAWABAN GIGA:** (a) apakah CekLoker akan mengajukan approval Reddit sebagai proyek non-komersial pribadi (Giga sendiri) sekarang, atau (b) menunda Reddit sampai status komersial jelas (Fase 4)? Sampai dijawab: Reddit tidak dipakai. |
| **K-S6** | Kaskus adalah sumber laporan penipuan terkaya — tetapi ToS Kaskus melarang penyalinan/eksploitasi konten untuk tujuan komersial tanpa izin tertulis, dan tidak ada API publik. | **DISELESAIKAN:** Kaskus = konteks manual + tautan saja, tanpa poin, tanpa menyimpan isi thread/username. Bila suatu hari butuh agregasi otomatis: minta izin tertulis PT Darta Media Indonesia dulu. |
| **K-S7** | Anggapan "Putusan MK 105/PUU-XXII/2024 membuat perusahaan tidak bisa menuntut, jadi risiko fitnah kecil" — **salah sebagian**: putusan itu hanya menutup pasal pencemaran nama baik UU ITE/KUHP bagi korporasi sebagai pengadu; gugatan **perdata** dan pengaduan oleh **individu** tetap terbuka; KUHP baru berlaku sejak 2 Jan 2026. | **DISELESAIKAN:** aturan anti-fitnah tetap ketat (ambang bukti, pembekuan sinyal yang disengketakan, larangan kata "penipu"/"melanggar UU"). Ringkasan hukum di dokumen ini **bukan nasihat hukum**. |
| **K-S8** | Ambang "rating ≥ 4,0 dari ≥ 20 ulasan" disajikan di ARCH §5 seolah-olah rubrik final — **tidak ada standar eksternal yang ditemukan**; angka ini heuristik warisan dari contoh ARCH. | **DISELESAIKAN sebagian:** dipertahankan sebagai heuristik dengan justifikasi statistik parsial (n ≥ 20) + kewajiban kalibrasi Fase 2 (50 perusahaan) + revisi via ADR. Lihat G-2. |
| **K-S9** | Harga Google Places API (US$25/1.000 request untuk tier Enterprise + Atmosphere; rating-only lebih murah) — hanya dari **sumber sekunder** (panduan pihak kedua, 1–9 Nov 2026). | **TIDAK TERVERIFIKASI PRIMER.** Jangan pakai untuk anggaran final; cek halaman harga Google Maps Platform / konsol sebelum Fase 2 memakai Places API. |
| **K-S10** | Indeed sering disebut sebagai sumber lowongan/reputasi — tetapi tidak ada API publik untuk ulasan dan ToS Indeed (29 Sep 2026) melarang scraping/agen AI tanpa izin tertulis; `robots.txt` memblokir halaman perusahaan. | **DISELESAIKAN:** Indeed tidak dipakai sebagai sumber reputasi Fase 2. Tinjau ulang hanya bila ada API/izin resmi. |

---

## 8. Sinyal final Fase 2 vs yang ditunda ke Fase 4

### 8.1 Direkomendasikan untuk Fase 2 (dengan ambangnya — lihat §3.1)

| # | Sinyal | Ambang | Status kode |
|---|---|---|---|
| 1 | `rating_overall` (Glassdoor/JobStreet/Google, manual/API resmi) | n ≥ 20 poin penuh; n 5–19 setengah; n < 5 nol | ✅ `score_rating` |
| 2 | `recommend_rate` | n ≥ 20; ≥ 80% +5; < 50% −5 | ✅ `score_recommend_rate` |
| 3 | `complaint_repeated` | ≥ 3 ulasan −5; ≥ 5 + pangsa ≥ 10% −15 | ✅ `detect_complaints` |
| 4 | `fee_request` | terbukti di teks lowongan → Red override | ✅ `detect_fee_request` |
| 5 | `news_layoff_massal` / `news_tutup` | ≥ 2 media, ≤ 12 bln → −15 | ✅ `score_news_event` |
| 6 | `news_ekspansi` / `news_pendanaan` | ≥ 2 media, ≤ 12 bln → +5 | ✅ `score_news_event` |
| 7 | `ghost_job` | > 90 hari + ≥ 3 basi + bukan evergreen → −10 | ✅ `score_ghost_job` |
| 8 | `social_buzz` (X/Kaskus, manual) | konteks saja, tanpa poin | ⏳ tampil di UI saja (bukan modul ini) |

### 8.2 DITUNDA ke Fase 4 + alasannya

| Sinyal / kemampuan | Alasan penundaan |
|---|---|
| Sentimen ML atas teks ulasan/post | Tidak ada benchmark Bahasa Indonesia terverifikasi; skor ML tidak bisa dibuktikan per poin; Reddit + JobStreet melarang latih model dari data mereka tanpa izin (§5). Gerbang: 200 contoh berlabel + precision/recall. |
| Agregasi otomatis Glassdoor / JobStreet Review | ToS melarang tanpa izin tertulis (K-S1/K-S2). Butuh izin tertulis atau tetap manual. |
| Reddit Data API (otomatis) | Approval wajib + status komersial belum jelas (K-S5 — butuh jawaban Giga). Isi Indonesia juga minim. |
| Indeed (ulasan) | Tidak ada rute legal (K-S10). |
| Deteksi ulasan palsu / review bombing otomatis | Tidak ada metode rule-based yang andal; klaim deteksi = klaim palsu. Mitigasi manual + ambang jumlah (G-3). |
| Distribusi bintang sebagai sinyal (mis. 95% bintang 5 = mencurigakan) | Ambang butuh kalibrasi data 50 perusahaan dulu (G-1). |
| Deteksi burst (lonjakan ulasan negatif singkat) | Butuh data tanggal per ulasan yang konsisten lintas sumber; manual dulu di Fase 2. |
| Sinyal dari TikTok/Instagram | Di luar tim ini (tim direct/company career page + IG); belum diteliti ToS-nya di sini. |
| Skor stabilitas dari umur perusahaan / legalitas PT (cek nama PT) | Milik tim lain (data perusahaan), bukan modul sosial. Modul ini hanya menyediakan `score_news_event` untuk Stabilitas. |

---

## 9. Istilah

*(Bagian ini adalah glosarium tim sosial; koordinator menggabungkan ke
`docs/glossary.md` — JANGAN edit glossary.md langsung dari tim ini.)*

- **Sinyal** — satu fakta terukur tentang perusahaan beserta buktinya
  (mis. "rating 4,4 dari 155 ulasan"). Sinyal adalah unit terkecil skor:
  tidak ada poin tanpa sinyal, tidak ada sinyal tanpa bukti.
- **Bukti (evidence)** — tautan + tanggal + sumber + (bila diizinkan)
  kutipan singkat yang menopang satu sinyal. Bukti yang kedaluwarsa
  (> 12–24 bulan, tergantung jenisnya) kehilangan hak memberi poin.
- **Confidence** — tingkat kepercayaan pada satu sinyal: `high`
  (bukti langsung + n besar), `medium` (memenuhi ambang minimum),
  `low` (konteks saja / n kecil / satu sumber). Confidence bukan poin —
  ia menjelaskan seberapa serius pembaca boleh menganggap sinyal itu.
- **Sinyal penentu (decisive)** — sinyal yang cukup kuat untuk dihitung
  dalam penentuan label "Belum cukup data": rating n ≥ 5, rekomendasi
  n ≥ 20, keluhan/berita/ghost job yang benar-benar memberi poin, dan
  fee yang terbukti. Konteks tanpa poin bukan penentu.
- **Green / Mixed / Red flag** — label ringkas dari skor total
  ternormalisasi: Green 70–100, Mixed 40–69, Red 0–39. Label adalah
  **ringkasan sinyal publik, bukan vonis** — selalu disertai rincian
  per sinyal + tautan bukti, dan disclaimer bahwa ini bukan penilaian
  hukum.
- **Belum cukup data** — label bila sinyal penentu < 3 atau kategori
  penentu < 2. Artinya "kami belum tahu", bukan "perusahaan ini buruk".
  Perusahaan baru yang bagus akan sering mendapat label ini — dan itu
  benar.
- **Ghost job (lowongan hantu)** — lowongan yang sama tayang > 90 hari
  tanpa perubahan, padahal perusahaan tampaknya tidak benar-benar
  merekrut (pola: ≥ 3 lowongan basi sekaligus, jabatan bukan evergreen).
  Satu lowongan lama saja belum tentu hantu — bisa saja rekrutmen
  bergulir.
- **Evergreen (jabatan bergulir)** — jabatan yang lowongannya wajar
  selalu buka karena turnover tinggi (sales, driver, kurir,
  telemarketing, dsb.). Tidak pernah dihitung sebagai ghost job.
- **Red override** — pemicu yang langsung membuat label jadi Red +
  peringatan, apa pun skor lainnya. Saat ini hanya satu: terbuktinya
  permintaan biaya dalam teks lowongan. Override tidak bisa "ditebus"
  oleh poin positif.
- **Keluhan berulang** — keluhan dengan isi yang sama (satu cluster kata
  kunci) yang muncul di ≥ 3 ulasan berbeda. Satu ulasan marah bukan
  keluhan berulang, sepedas apa pun isinya.
- **Cluster keluhan** — satu jenis keluhan (mis. `gaji_telat_atau_ditahan`)
  yang mencakup beberapa pola kata kunci Indonesia + Inggris. Satu
  ulasan dihitung sekali per cluster.
- **Konteks (tanpa poin)** — informasi yang ditampilkan ke pengguna
  tanpa memengaruhi skor: thread forum, post media sosial, satu ulasan
  ekstrem, satu artikel berita. Konteks membantu pengguna menilai
  sendiri; ia tidak boleh menyamar sebagai penilaian sistem.
- **Total ternormalisasi** — skor 0–100 yang dihitung hanya dari kategori
  yang sudah terukur (`100 × perolehan / cap kategori terukur`), supaya
  "data belum diukur" tidak disamakan dengan "data buruk". Perubahan
  dari penjumlahan mentah ARCH §5 — lihat G-2 dan ADR-0005.
- **Cap kategori** — batas poin per kategori (Reputasi 25, Transparansi
  25, Stabilitas 20, Praktik rekrutmen 15, Gaji & benefit 15). Satu
  kategori tidak boleh mendominasi total tanpa batas.
- **Entri manual** — pencatatan data oleh manusia (Giga) dari halaman
  publik yang dibaca biasa — cara pengambilan data ulasan yang diizinkan
  Fase 2, karena pengambilan otomatis dilarang ToS sumber (K-S1/K-S2).
- **Izin tertulis (express written permission)** — persetujuan eksplisit
  dari pemilik platform untuk pengambilan data otomatis. Syarat yang
  ditulis Glassdoor/Indeed/Reddit/Kaskus. Visibilitas publik **bukan**
  izin.

---

## 10. Yang belum terverifikasi / butuh jawaban Giga

1. **(K-S5) Reddit:** ajukan approval sebagai proyek non-komersial
   pribadi sekarang, atau tunda ke Fase 4? Jawaban ini menentukan apakah
   Reddit pernah masuk peta jalan.
2. **Perubahan rubrik (G-2 / ADR-0005):** total ternormalisasi +
   label butuh ≥ 2 kategori penentu — menyimpang dari ARCH §5
   (penjumlahan mentah + "< 3 sinyal"). **Minta persetujuan Giga**
   sebelum dipakai di produk.
3. **Daftar "media independen"** untuk sinyal berita: media apa saja
   yang dihitung (Kompas/Detik/Kontan/dsb.) dan apakah blog/portal
   tanpa redaksi jelas dikecualikan? Perlu daftar yang disepakati.
4. **Dependensi ghost job:** sinyal ini butuh `fingerprint` lowongan
   yang stabil + `first_seen_at`/`last_seen_at` dari tim scraper. Bila
   belum tersedia, ghost job = konteks saja.
5. **Harga yang belum dicek primer:** Google Places API (K-S9) dan X
   API (K-S4) — cek konsol resmi sebelum menganggarkan.
6. **Kalibrasi Fase 2:** ambang 4,0/20/≥3/≥5/90 hari wajib diuji pada
   50 perusahaan pertama; bila ambang tidak memisahkan perusahaan
   bermasalah dari yang sehat, revisi lewat ADR baru.

---

## Sumber (diakses 15 November 2026)

**Primer (dibuka dan dibaca teksnya):**

- Glassdoor Terms of Use, revisi 1 Juli 2026, §4.3(16) —
  `glassdoor.com.au/about/terms/`
- JobStreet Website Terms and Conditions, butir (d), (t), (u) —
  `sg.jobstreet.com/terms`
- Google Places API (New) — Policies and attributions —
  `developers.google.cn/maps/documentation/places/web-service/policies`
- Reddit Responsible Builder Policy —
  `support.reddithelp.com/hc/en-us/articles/42728983564564-Responsible-Builder-Policy`
- Kaskus Syarat dan Ketentuan —
  `bantuan.kaskus.co.id/hc/id/articles/226392548-Syarat-dan-Ketentuan`

**Sekunder (ringkasan/panduan pihak kedua, saling menguatkan ≥ 2 sumber):**

- Glassdoor API publik ditutup (2021, mitra saja) — Dev.to (Apr–Jun 2026),
  CopyProgramming, ScrapeOps (Nov 2026).
- JobStreet Company Review, data ulasan perusahaan Indonesia —
  cuplikan `id.jobstreet.com/companies/…` (BFI Finance, Charoen Pokphand,
  Lotte, NBC, Protelindo, Wowrack, Brinks).
- Glassdoor Indonesia, data ulasan — cuplikan `glassdoor.com/Reviews/…`
  (Telkomsel, Huawei, Ipsos).
- Google Places API: maks. 5 ulasan, tier Enterprise + Atmosphere
  US$25/1.000 request — RepU (1 Nov 2026), EveryInfra (9 Nov 2026).
- X API pay-per-use sejak 6 Feb 2026 (US$0,005/bacaan, tanpa free tier
  untuk pendaftar baru) — Outstand, PostProxy, Social-SDK, Superframeworks
  (Sep–Okt 2026).
- Reddit API: 100 QPM gratis non-komersial, approval wajib sejak Nov 2025,
  komersial US$0,24/1.000 panggilan — Captapi, GetAnyAPI, Monocrawl,
  RedReplier, Snitchfeed (Okt 2026).
- Indeed: tanpa API publik; ToS melarang scraping (29 Sep 2026) —
  100Hires, UnknownProxies, ScrapeOps (Okt 2026).
- Kaskus thread penipuan lowongan — `kaskus.co.id` (cuplikan pencarian).
- Hukum Indonesia: UU PDP No. 27/2022; KUHP baru (UU 1/2023, berlaku
  2 Jan 2026) Pasal 433–441; Putusan MK No. 105/PUU-XXII/2024
  (29 Apr 2025) — InfoHukum (Okt 2026). **Ringkasan umum, bukan nasihat
  hukum.**

**Yang TIDAK dilakukan dalam riset ini (batas yang ditegakkan):** tidak ada
API key yang dibuat; tidak ada akun yang didaftarkan; tidak ada panggilan
API, scraping, bypass login/paywall/CAPTCHA, atau akun palsu; tidak ada
data pribadi (nama/email/telepon) yang dikumpulkan atau disimpan.
