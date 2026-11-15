# ADR-0006 — Sumber Reputasi & Aturan Anti-Fitnah/Privasi

- **Status:** Diterima (tim sosial) — beberapa butir **butuh jawaban Giga**
  (lihat "Konsekuensi" dan K-S5).
- **Tanggal:** 15 November 2026
- **Penulis:** Tim Sosial & Reputasi (Fase 1 CekLoker)
- **Terkait:** `docs/fase1-riset-sosial.md` (§1, §4, §7),
  `ARCHITECTURE.md §5, §8`, `packages/flag-engine/social_signals.py`,
  ADR-0005.

## Konteks

Sinyal reputasi CekLoker bergantung pada data milik platform lain
(Glassdoor, JobStreet, Google, X, Reddit, Kaskus, media berita). Setiap
platform punya ketentuan sendiri tentang apa yang boleh diambil, dan
hukum Indonesia (UU PDP, KUHP baru, Putusan MK 105/PUU-XXII/2024)
membatasi pemrosesan data pribadi serta memberi ruang gugat bagi pihak
yang dirugikan. Draf ARCHITECTURE.md §5 menempatkan Glassdoor/JobStreet/
Google sebagai "sumber resmi/terstruktur" seolah-olah datanya bisa
diambil langsung. Verifikasi primer 15 Nov 2026 membuktikan anggapan
itu **salah untuk pengambilan otomatis** (lihat K-S1, K-S2, K-S3 di
`docs/fase1-riset-sosial.md` §7). ADR ini memutuskan sumber mana yang
dipakai, dengan cara apa, dan pagar anti-fitnah/privasi apa yang berlaku.

## Keputusan

### A. Sumber dan cara pengambilan (Fase 2)

1. **JobStreet Company Review = sumber reputasi #1 untuk Indonesia —
   ENTRI MANUAL saja.** Giga membaca halaman profil publik dan mencatat
   rating + jumlah ulasan + % rekomendasi + tautan. **Pengambilan otomatis
   dilarang** (JobStreet Terms butir (d) melarang agregasi/penyalinan
   konten; butir (u) melarang scraping Profil kecuali via API
   terdokumentasi — dan tidak ada API ulasan Indonesia yang terverifikasi).
2. **Glassdoor = pelengkap perusahaan besar — ENTRI MANUAL saja.**
   **Pengambilan otomatis dilarang tanpa izin tertulis** (Terms of Use
   revisi 1 Juli 2026 §4.3(16)). Tidak ada API publik sejak 2021.
3. **Google Places API = API resmi, rating + jumlah saja.** Simpan
   `place_id` + rating + `userRatingCount` + tautan. **Teks ulasan TIDAK
   BOLEH disimpan** (Places API Policies: larangan pre-fetch/cache/store
   konten; hanya `place_id` yang dikecualikan). `evidence_text` untuk
   sumber ini **wajib kosong**; bila UI menampilkan teks ulasan, itu
   harus live dari API saat halaman dibuka, lengkap dengan atribusi
   penulis + logo Google Maps.
4. **Google News RSS = satu-satunya pengambilan otomatis di Fase 2.**
   Judul + media + tanggal + tautan saja; bukan isi penuh artikel
   (hak cipta). Sopan (jangan polling agresif).
5. **X / Kaskus = konteks manual, tanpa poin.** Pencarian manual atas
   nama perusahaan + kata kunci penipuan; tampil sebagai konteks dengan
   tautan + label "belum terverifikasi" bila sumbernya forum/anonim.
   Tanpa menyimpan isi thread/post atau username.
6. **Reddit = DITUNDA ke Fase 4** (approval wajib untuk semua aplikasi
   sejak Nov 2025; komersial butuh persetujuan tertulis; isi Indonesia
   minim). **Butuh jawaban Giga** (K-S5): ajukan approval sebagai proyek
   non-komersial pribadi sekarang, atau tunda sampai status komersial
   jelas.
7. **Indeed = TIDAK DIPAKAI** (tidak ada API publik; ToS melarang
   scraping; `robots.txt` memblokir halaman perusahaan). Tinjau ulang
   hanya bila ada API/izin resmi.
8. **Tidak pernah:** bypass login/paywall/CAPTCHA, akun palsu, scraping
   DM/grup tertutup, atau menyimpan credential/API key di file mana pun.

### B. Aturan anti-fitnah

9. **Skor tanpa bukti tidak tampil.** Setiap sinyal wajib
   `evidence_url` + `evidence_date` + `source` + `confidence`.
   Fungsi skor gagal keras (`ValueError`) bila bukti kosong.
10. **Satu-dua ulasan tidak pernah memberi poin** (ambang §ADR-0005).
    Tuduhan berat (penipuan, pencurian, pelanggaran hukum) dari satu
    sumber tidak pernah ditulis sebagai fakta — paling jauh tampil
    sebagai "ada laporan [topik] di [sumber] — belum terverifikasi" +
    tautan.
11. **Tidak ada kata vonis.** Sistem tidak pernah menulis "perusahaan
    ini penipu", "perusahaan ini melanggar UU", atau sejenisnya.
    Yang ditulis: fakta kutipan + label ringkasan + disclaimer
    ("ringkasan sinyal publik, bukan penilaian hukum").
12. **Sinyal yang disengketakan dibekukan.** Sejak perusahaan mengajukan
    koreksi, poin sinyal itu ditangguhkan (dihitung 0 sementara) dan
    ditampilkan "disengketakan — sedang ditinjau" sampai diputuskan
    (≤ 7 hari). Tanggapan perusahaan yang sopan dan faktual diterbitkan
    berdampingan. Penghapusan hanya bila bukti salah / kedaluwarsa /
    melanggar aturan — bukan karena perusahaan tidak suka.
13. **Kedaluarsa sinyal.** Rating dihitung ulang bila data > 12 bulan;
    keluhan > 24 bulan keluar dari poin (konteks saja); berita > 12
    bulan tidak memberi poin.
14. **Putusan MK bukan alasan meremehkan risiko.** Putusan MK
    No. 105/PUU-XXII/2024 menutup pasal pencemaran nama baik bagi
    korporasi sebagai pengadu, tetapi gugatan perdata dan pengaduan oleh
    individu tetap terbuka (K-S7). Aturan di atas tetap berlaku penuh.

### C. Privasi

15. **Tidak pernah disimpan:** nama pelamar, email, telepon, CV; nama
    reviewer / username forum / handle / foto profil; isi DM atau grup
    tertutup; gaji individu, NIK, alamat rumah.
16. **Yang disimpan:** angka agregat + kutipan singkat (≤ 280 karakter)
    + tautan + tanggal + sumber. Kutipan yang masih bisa mengidentifikasi
    seseorang tidak ditampilkan.
17. **Hak hapus (UU PDP Pasal 8, 43):** subjek data boleh meminta
    penghapusan kutipan tentang dirinya; sinyal dihitung ulang tanpa
    kutipan itu. Mekanisme penghapusan wajib tersedia sebelum publikasi
    luas (Fase 5).

## Alternatif yang ditolak + alasan

| Alternatif | Alasan ditolak |
|---|---|
| Scraping otomatis Glassdoor/JobStreet meski ToS melarang ("toh datanya publik") | Visibilitas publik bukan izin. ToS melarang tegas; risikonya pemblokiran IP/akun + tuntutan + rusaknya kredibilitas proyek open source. Jalan yang sah: entri manual + minta izin tertulis. |
| Memakai agregator pihak ketiga berbayar (mis. API scraping Glassdoor) | Agregator tidak mengalihkan izin: ToS sumber tetap dilanggar oleh pengambilan datanya, dan tanggung jawabnya jatuh ke CekLoker. Harga juga tidak masuk anggaran $0 Fase 1/2. |
| Menyimpan teks ulasan Google di database | Dilarang tegas oleh Places API Policies; hanya `place_id` yang dikecualikan. Solusi: simpan angka + tautan, tampilkan teks secara live. |
| Mengutip thread Kaskus/X sebagai bukti poin | Anonim, tidak terverifikasi, tidak terstruktur. Satu thread bisa jadi fitnah, kekeliruan, atau ulah pesaing. Peran yang jujur: konteks + tautan. |
| Mengandalkan Putusan MK 105/PUU-XXII/2024 untuk melonggarkan aturan ("perusahaan tidak bisa menuntut") | Putusan itu hanya menutup satu pasal pidana bagi korporasi; gugatan perdata + pengaduan individu tetap terbuka. Melonggarkan atas dasar itu adalah kesalahan hukum. |
| Menampilkan nama reviewer untuk "transparansi" | Melanggar privasi + UU PDP; Glassdoor/JobStreet memang anonim secara desain; nama tidak menambah kebenaran sinyal — angka agregat + tautan sudah cukup. |
| Menunda aturan koreksi sampai Fase 5 (publik) | Koreksi harus ada sejak Fase 2: Giga sendiri adalah pengguna pertama dan perusahaan pertama yang dinilai bisa protes kapan saja. Menunda = membiarkan skor yang disengketakan merugikan tanpa jalan keluar. |

## Konsekuensi

- **Positif:** Fase 2 bisa jalan tanpa melanggar ToS sumber mana pun
  (manual + RSS + Places API); risiko hukum ditekan ke titik yang bisa
  dipertahankan; perusahaan punya jalan koreksi yang adil; pengguna
  melihat bukti yang bisa diklik, bukan label gelap.
- **Negatif / biaya:** entri manual tidak berskala — Giga harus mencatat
  rating perusahaan satu per satu; cakupan awal terbatas pada perusahaan
  yang sempat dicatat; sinyal X/Kaskus/Reddit tidak memberi poin
  sehingga sebagian "kekayaan" media sosial tidak masuk skor.
- **Butuh jawaban Giga:** (K-S5) Reddit — ajukan approval sekarang atau
  tunda; (D-?) apakah Giga bersedia mengurus izin tertulis ke Glassdoor /
  JobStreet bila skala manual sudah tidak cukup.
- **Diteruskan ke koordinator:** ToS JobStreet butir (d) juga menyangkut
  adapter lowongan (tim job-board) — bukan wewenang tim ini (K-S2);
  skema `signals.evidence_text` harus membolehkan kosong untuk sumber
  Google (K-S3).

## Amandemen K4 — 2026-11-15 (Fase 1-lanjutan, tim Normalisasi + Flag-Engine)

**Keputusan asal (K4, konsolidasi Fase 1):** `evidence_text` boleh null;
untuk sumber `google_places` wajib kosong (hanya rating, jumlah,
`place_id`, tautan). Amandemen ini menetapkan BAGAIMANA aturan itu
ditegakkan di kode, bukan hanya di dokumen.

### Yang diterapkan di `packages/flag-engine/social_signals.py`

1. **`Signal.evidence_text` bertipe `str | None`.** Null berarti "tidak
   ada kutipan" — dipertahankan sebagai None, bukan diubah diam-diam
   jadi `""`, supaya model/skema membedakan "kutipan tidak diberikan"
   dari "kutipan kosong". Skema DB di ARCHITECTURE.md §4 sudah menulis
   `evidence_text text` tanpa NOT NULL, jadi tidak ada perubahan skema —
   yang berubah hanya penegakannya di flag-engine.
2. **Validasi keras di `Signal.__post_init__`:** sinyal dengan
   `source == "google_places"` dan `evidence_text` terisi (setelah
   di-strip) melempar `ValueError` — DITOLAK, bukan diam-diam dikosongkan.
   Alasan grill (G-K4-1): pengosongan diam-diam menyembunyikan bug
   pemanggil dan membuat pelanggaran Places API Policies lolos tanpa
   jejak; penolakan keras memaksa perbaikan di sumber datanya.
   Kosong yang diterima: `None`, `""`, atau hanya spasi.
3. **Semua fungsi pembentuk sinyal** (`score_rating`,
   `score_recommend_rate`, `score_news_event`) menerima
   `evidence_text: str | None` dan meneruskannya apa adanya (None tetap
   None; string dipotong ke 280 karakter).
4. **`detect_complaints` TIDAK BOLEH dipanggil dengan
   `source="google_places"`** — fungsi ini membangun kutipan dari teks
   ulasan, dan bila ada keluhan yang cocok, `Signal` menolak keras.
   Ini benar: teks ulasan Google memang tidak boleh disimpan dalam
   bentuk apa pun, termasuk sebagai kutipan keluhan.

### Hasil grill K4

- **G-K4-1 — Tolak (raise) atau buang (kosongkan)?** Dipilih TOLAK.
  Modul ini sudah menganut filosofi "gagal keras" untuk bukti kosong
  (`_require_evidence`), jadi penolakan konsisten. Risiko: data lama
  yang keliru membawa teks Google akan gagal diproses sampai dibersihkan
  — itu memang tujuannya, bukan efek samping. **Berubah:** validasi di
  `__post_init__`, bukan di pemanggil.
- **G-K4-2 — Kenapa validasi di `Signal`, bukan di tiap fungsi?**
  Supaya tidak ada jalur yang lolos: sinyal yang dibangun langsung
  (mis. dari modul lain di Fase 2) ikut terjaring. Satu titik penegakan,
  bukan empat. **Berubah:** `__post_init__` sebagai satu-satunya pagar.
- **G-K4-3 — Apakah `place_id` ikut disimpan?** Ya — `place_id` adalah
  satu-satunya field yang dikecualikan Places API Policies dari larangan
  simpan. Tapi `Signal` v1 tidak punya field `place_id`; penyimpanan
  `place_id` menjadi urusan lapisan pengumpul data + skema DB Fase 2,
  bukan modul ini. Yang ditegakkan modul ini hanyalah: tidak ada teks
  ulasan yang lolos lewat `evidence_text`.

### Tindak lanjut (di luar modul ini)

- Skema DB Fase 2 wajib mempertahankan `signals.evidence_text` NULLABLE
  dan sebaiknya menambahkan CHECK (`source='google_places'` →
  `evidence_text IS NULL`) sebagai pagar kedua di database.
- UI yang menampilkan teks ulasan Google harus mengambilnya live dari
  API saat halaman dibuka (dengan atribusi + logo), bukan dari database.

## Hasil grill yang mengubah keputusan

- **G-3 (ulasan ekstrem/palsu):** memaksa aturan 9–11 — ambang jumlah +
  larangan kata vonis + tuduhan berat tidak pernah jadi fakta.
- **G-7 (satu artikel = rumor):** memaksa butir B-10 ditekankan untuk
  berita juga (satu media = konteks, bukan poin) — sudah di ADR-0005
  butir 8, ditegaskan lagi di sini sebagai aturan tampilan.
- **Verifikasi primer (bukan grill, tapi pengubah terbesar):** membaca
  langsung ToS Glassdoor/JobStreet/Google/Reddit/Kaskus membalik
  asumsi awal ("sumber resmi = bisa diambil") menjadi desain manual +
  RSS + Places API. Tanpa verifikasi ini, Fase 2 akan dibangun di atas
  pelanggaran ToS. Konflik K-S1–K-S10 dicatat di
  `docs/fase1-riset-sosial.md` §7.
