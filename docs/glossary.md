# Glossary CekLoker

> Digabungkan koordinator Fase 1 (15 Nov 2026) dari kontribusi keempat tim
> (Job-Board, Direct, Sosial, Referensi GitHub). Bahasa Indonesia.
> Bila definisi tim bertentangan, koordinator memilih satu definisi dan
> mencatat alasannya di `docs/fase1-konsolidasi.md` (konflik K5, K8).
> Istilah baru ditambahkan di sini, bukan di dokumen riset masing-masing.

## Inti produk

| Istilah | Definisi |
|---|---|
| **posted_at** | Tanggal lowongan dibuka **menurut klaim sumber** (tertulis di halaman sumber). Bisa berupa tanggal pasti (ISO / "12 Nov 2026") atau perkiraan dari tanggal relatif ("2 hari lalu", "1 bulan lalu" — perkiraan ±30 hari, tidak pasti). Bisa berarti "terakhir dipublikasikan" (Ashby `publishedAt`) — bukan selalu pertama dibuka. Bila sumber tidak menulis tanggal, nilainya kosong — JANGAN ditebak. Beda dengan `first_seen_at`. |
| **posted_at_certain** | Flag di `RawJob`: `True` hanya bila `posted_at` berasal dari tanggal absolut/ISO; `False` bila hanya perkiraan dari tanggal relatif (ADR-0002). |
| **first_seen_at** | Waktu (tanggal + jam) **scraper kami pertama kali melihat** lowongan itu masih buka. Ini fakta pengamatan kami, bukan klaim sumber — dan tidak sama dengan `posted_at`. |
| **last_seen_at** | Waktu terakhir scraper kami melihat lowongan itu masih buka. Dipakai bersama `first_seen_at` untuk membuktikan lowongan "masih aktif" dari waktu ke waktu. |
| **ghost job (lowongan hantu)** | Lowongan yang tayang berbulan-bulan padahal perusahaan tampaknya tidak benar-benar merekrut — dipakai memancing lamaran / membangun database CV. Kriteria CekLoker (gabungan): tayang > 90 hari tanpa perubahan, pola ≥ 3 lowongan basi sekaligus, dan jabatan BUKAN evergreen. Sinyal red flag (−10). Satu lowongan lama saja belum tentu hantu — bisa saja rekrutmen bergulir. |
| **repost** | Lowongan yang sama diposting ulang dengan URL/ID baru sehingga tanggalnya terlihat baru. Dideteksi lewat `fingerprint` (judul + perusahaan + lokasi sama), bukan lewat ID/URL. |
| **evergreen (jabatan bergulir)** | Jabatan yang lowongannya wajar selalu buka karena turnover tinggi (sales, driver, kurir, telemarketing, dsb.). Tidak pernah dihitung sebagai ghost job. |
| **lowongan basi (staleness)** | Lowongan yang masih tayang tapi sebenarnya sudah terisi/tidak aktif (tayang > 30–90 hari tanpa perubahan). CekLoker memangkasnya dari daftar aktif. |
| **Green / Mixed / Red flag** | Label ringkas dari skor total ternormalisasi: Green 70–100, Mixed 40–69, Red 0–39. Label adalah **ringkasan sinyal publik, bukan vonis** — selalu disertai rincian per sinyal + tautan bukti, dan disclaimer bahwa ini bukan penilaian hukum. |
| **Belum cukup data** | Label bila sinyal penentu < 3 atau kategori penentu < 2. Artinya "kami belum tahu", bukan "perusahaan ini buruk". Perusahaan baru yang bagus akan sering mendapat label ini — dan itu benar. |

## Adapter & data

| Istilah | Definisi |
|---|---|
| **adapter** | Satu file Python yang tahu cara mengambil lowongan dari SATU sumber (situs job board / ATS) dan mematuhi kontrak `JobSourceAdapter` (`discover` / `fetch_job` / `check_active`). Adapter baru = 1 file + 1 test + 1 baris registry. Semua adapter memakai `RawJob` yang sama dari `scraper_core.base`. |
| **discover** | Langkah adapter yang mengembalikan daftar URL halaman detail lowongan (dari sitemap / RSS / API resmi / halaman list publik). Tidak mengambil isi detail. |
| **fetch_job** | Langkah adapter yang mengambil SATU halaman detail lowongan dan mengembalikannya sebagai `RawJob` (termasuk penanda masih buka / sudah tutup). |
| **check_active** | Langkah adapter yang menjawab "lowongan ini masih buka?" dengan YA/TIDAK yang pasti. Gagal teknis (timeout/5xx) BUKAN jawaban "tidak" — status lama dipertahankan sebagai `unknown`. |
| **RawJob** | Struktur data mentah satu lowongan hasil adapter, sebelum normalisasi ke database: judul, perusahaan (mentah + ternormalisasi), lokasi, gaji, `posted_at` (+ flag `posted_at_certain`), URL sumber, `is_active`, dan field ATS (`platform`, `platform_job_id`, `job_key`, `department`, `repost_hint`, `raw`). |
| **fingerprint** | Hash (SHA-256, 32 karakter) dari judul + nama perusahaan ternormalisasi + lokasi. Dipakai normalizer untuk dedup: lowongan yang sama di dua sumber, atau repost dengan URL baru, punya fingerprint sama. URL sengaja TIDAK masuk fingerprint — justru supaya repost (URL baru, isi sama) terdeteksi. |
| **company_norm** | Nama perusahaan yang sudah dibersihkan untuk dedup: imbuhan badan hukum ("PT", "CV", "Tbk", "Ltd") dibuang, spasi dirapikan, kapital diseragamkan. Nama asli tetap disimpan di `company_raw` dan tidak pernah dibuang. |
| **job_key** | Identitas stabil satu lowongan di satu ATS: `platform:slug:id-ATS` (mis. `greenhouse:contohcorp:101`). Beda dengan fingerprint: job_key berubah bila lowongan di-repost (id baru), fingerprint tidak. |
| **sitemap** | File XML yang dideklarasikan situs di robots.txt, berisi daftar URL halaman situs itu (beserta `lastmod`). Jalur discover paling resmi kedua setelah API resmi — karena disediakan situs itu sendiri untuk crawler. |
| **JSON-LD** | Blok JSON (`application/ld+json`) yang disematkan di halaman web untuk mesin pencari, berisi data terstruktur halaman itu. Di Glints diharapkan berisi `JobPosting` (judul, gaji, tanggal posting); di halaman karier custom juga dipakai. |
| **`__NEXT_DATA__`** | Blok JSON (`<script id="__NEXT_DATA__">`) yang disematkan framework Next.js di tiap halaman, berisi seluruh data yang dipakai halaman itu. Di Kalibrr berisi data lowongan lengkap — lebih andal daripada parsing HTML. |
| **ATS (Applicant Tracking System)** | Perangkat lunak yang dipakai perusahaan untuk mengelola lowongan dan lamaran (menerima, menyaring, melacak kandidat). Contoh: Greenhouse, Lever, Ashby, Workable. Perusahaan membeli ATS; ATS menyediakan halaman karier + feed lowongan. |
| **halaman karier (career page)** | Halaman di situs perusahaan sendiri yang menampilkan lowongan terbukanya. Bisa di-host ATS (mis. `boards.greenhouse.io/acme`) atau custom (mis. `careers.perusahaan.id`). |
| **board (job board ATS)** | Daftar lowongan satu perusahaan di dalam satu ATS, dikenali dari **slug/board token** (mis. `acme` pada `boards.greenhouse.io/acme`). |
| **slug / board token** | Pengenal singkat perusahaan di dalam ATS, biasanya nama perusahaan tanpa spasi. Bukan nama resmi perusahaan. |
| **feed JSON publik** | Endpoint HTTP yang mengembalikan daftar lowongan sebagai JSON tanpa login, dipakai widget karier perusahaan itu sendiri. Inilah yang dibaca CekLoker. |
| **Business Discovery** | Endpoint Instagram Graph API resmi untuk membaca field publik akun Bisnis/Kreator *lain*. Butuh token aplikasi sendiri; tidak bisa membaca akun personal. |
| **polite delay** | Jeda antar-request ke satu domain (v1: 3 detik Glints/Kalibrr, 2 detik ATS) supaya scraper tidak membanjiri server sumber. |
| **SourceNotPermittedError** | Error yang dilempar adapter yang DINONAKTIFKAN karena larangan legal (ToS/robots/login). Bukan bug — keputusan sadar yang terdokumentasi, beserta alternatif legalnya. |
| **SourceBlockedError** | Error saat sumber menolak request (HTTP 403/429/CAPTCHA). Worker harus berhenti sementara (backoff) — dilarang memutar proxy / memalsukan identitas untuk lolos. |

## Skor & sinyal

| Istilah | Definisi |
|---|---|
| **sinyal** | Satu fakta terukur tentang perusahaan beserta buktinya (mis. "rating 4,4 dari 155 ulasan"). Sinyal adalah unit terkecil skor: tidak ada poin tanpa sinyal, tidak ada sinyal tanpa bukti. |
| **bukti (evidence)** | Tautan + tanggal + sumber + (bila diizinkan) kutipan singkat yang menopang satu sinyal. Bukti yang kedaluwarsa (> 12–24 bulan, tergantung jenisnya) kehilangan hak memberi poin. |
| **confidence** | Tingkat kepercayaan pada satu sinyal: `high` (bukti langsung + n besar), `medium` (memenuhi ambang minimum), `low` (konteks saja / n kecil / satu sumber). Confidence bukan poin — ia menjelaskan seberapa serius pembaca boleh menganggap sinyal itu. |
| **sinyal penentu (decisive)** | Sinyal yang cukup kuat untuk dihitung dalam penentuan label "Belum cukup data": rating n ≥ 5, rekomendasi n ≥ 20, keluhan/berita/ghost job yang benar-benar memberi poin, dan fee yang terbukti. Konteks tanpa poin bukan penentu. |
| **total ternormalisasi** | Skor 0–100 yang dihitung hanya dari kategori yang sudah terukur (`100 × perolehan / cap kategori terukur`), supaya "data belum diukur" tidak disamakan dengan "data buruk". Perubahan dari penjumlahan mentah ARCH §5 — lihat ADR-0005; butuh persetujuan Giga (D7). |
| **cap kategori** | Batas poin per kategori (Reputasi 25, Transparansi 25, Stabilitas 20, Praktik rekrutmen 15, Gaji & benefit 15). Satu kategori tidak boleh mendominasi total tanpa batas. |
| **keluhan berulang** | Keluhan dengan isi yang sama (satu cluster kata kunci) yang muncul di ≥ 3 ulasan berbeda. Satu ulasan marah bukan keluhan berulang, sepedas apa pun isinya. |
| **cluster keluhan** | Satu jenis keluhan (mis. `gaji_telat_atau_ditahan`) yang mencakup beberapa pola kata kunci Indonesia + Inggris. Satu ulasan dihitung sekali per cluster. |
| **konteks (tanpa poin)** | Informasi yang ditampilkan ke pengguna tanpa memengaruhi skor: thread forum, post media sosial, satu ulasan ekstrem, satu artikel berita. Konteks membantu pengguna menilai sendiri; ia tidak boleh menyamar sebagai penilaian sistem. |
| **red override** | Pemicu yang langsung membuat label jadi Red + peringatan, apa pun skor lainnya. Saat ini hanya satu: terbuktinya permintaan biaya dalam teks lowongan. Override tidak bisa "ditebus" oleh poin positif. |
| **entri manual** | Pencatatan data oleh manusia (Giga) dari halaman publik yang dibaca biasa — cara pengambilan data ulasan yang diizinkan Fase 2, karena pengambilan otomatis dilarang ToS sumber (K-S1/K-S2). |
| **izin tertulis (express written permission)** | Persetujuan eksplisit dari pemilik platform untuk pengambilan data otomatis. Syarat yang ditulis Glassdoor/Indeed/Reddit/Kaskus. Visibilitas publik **bukan** izin. |

## Lisensi, legal & GitHub

| Istilah | Definisi |
|---|---|
| **ToS (Terms of Service)** | Syarat Layanan situs — perjanjian yang mengikat pengguna situs itu. Beberapa ToS (JobStreet/SEEK, Indeed, Glassdoor) secara eksplisit melarang scraping/agregasi tanpa izin tertulis. Melanggar ToS bukan otomatis melanggar hukum, tapi situs boleh memblokir dan ada risiko reputasi/hukum. Izin robots.txt BUKAN izin ToS — ToS bisa tetap melarang. |
| **robots.txt** | File aturan di root sebuah situs (`/robots.txt`) yang menyatakan path mana yang BOLEH dan TIDAK BOLEH diambil crawler. Dipatuhi CekLoker; tetapi izin robots.txt BUKAN izin ToS. |
| **SEEK API** | API resmi grup SEEK (induk JobStreet) di developer.seek.com — butuh pengajuan + persetujuan, ditujukan untuk integrasi ATS/perekrut. Satu-satunya jalur legal memakai data JobStreet bila izin scraping tidak diberikan. |
| **Publisher API (Indeed)** | API pencarian lowongan publik Indeed yang lama (ber-key, untuk afiliasi). Sudah ditutup untuk developer baru dan berhenti mengembalikan data sejak ~2023. Tidak bisa dipakai lagi. |
| **Chalice Search API v4** | Endpoint pencarian internal JobStreet (`/api/chalice-search/v4/search`) yang dipakai situsnya sendiri; tidak terdokumentasi publik. Merespons tanpa kunci ("no-auth") — tetapi itu BUKAN izin legal untuk memakainya. |
| **adopsi** | Memakai kode/library orang lain apa adanya (sebagai dependensi atau dengan menyalin) di dalam CekLoker, dengan atribusi sesuai lisensinya. Hanya boleh untuk lisensi permisif (MIT/Apache-2.0/BSD). |
| **referensi** | Mempelajari pola, struktur, atau ide dari sebuah repo, lalu menulis ulang dengan kata-kata dan kode sendiri. Tidak menyalin kode. Berlaku untuk semua repo, termasuk yang berlisensi copyleft. |
| **referensi ide** | Bentuk referensi yang paling ketat: hanya idenya yang diambil (mis. "dedup 3 lapis"), implementasinya ditulis dari nol. Dipakai untuk repo AGPL/GPL. |
| **fork** | Salinan sebuah repo GitHub di bawah akun sendiri, yang riwayat commit-nya tetap terhubung ke repo asal. Fork ≠ adopsi: mem-fork tidak berarti kodenya dipakai di CekLoker. |
| **lisensi permisif** | Lisensi yang mengizinkan kode dipakai, diubah, dan digabung ke proyek dengan lisensi lain (termasuk MIT) selama atribusi dipertahankan. Contoh: MIT, Apache-2.0, BSD. |
| **lisensi copyleft** | Lisensi yang mewajibkan karya turunan memakai lisensi yang sama (atau setara). Contoh: GPL, AGPL. AGPL-3.0 paling ketat: kewajiban berbagi source aktif juga bila program dijalankan sebagai layanan jaringan (website). |
| **lisensi ganda (dual-license)** | Satu repo memakai dua lisensi berbeda untuk bagian berbeda (mis. kode MIT + dataset CC BY-NC 4.0). Masing-masing bagian harus dipatuhi sendiri-sendiri. |
| **atribusi** | Pencantuman nama pembuat + lisensi asal saat memakai kode orang lain, sesuai syarat lisensi (mis. di README / file NOTICE). |
| **arsip (archived repo)** | Repo yang dikunci pemiliknya menjadi read-only: tidak ada commit, issue, atau PR baru. Kode tetap bisa dibaca, tapi tidak akan diperbaiki lagi. |
| **bus factor** | Jumlah orang yang harus "tertabrak bus" sebelum proyek berhenti terawat. Bus factor 1 = satu maintainer; bila ia berhenti, proyek mati. |
| **snapshot tren** | Commit otomatis harian yang hanya mencatat angka (mis. jumlah lowongan per platform). Bukan pengembangan fitur — jangan dibaca sebagai bukti repo aktif dikembangkan. |
| **TLS impersonation** | Teknik meniru "sidik jari" TLS browser asli (mis. Chrome) agar server mengira request datang dari browser manusia. Tergolong teknik mengelabui deteksi bot. Dilarang di CekLoker. |
| **dedup (deduplikasi)** | Menghapus lowongan yang sama yang muncul di beberapa sumber, memakai fingerprint. |
