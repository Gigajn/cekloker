# ADR-0004 — Jalur Sosial Perusahaan: Instagram & LinkedIn

> Penomoran KHUSUS CekLoker. ADR-0001 dan ADR-0002 milik Tim Job-Board.
> Tanggal: 15 November 2026. Tim: Direct / Perusahaan Langsung.
> Status: **Diterima** (Fase 1).

## Status

Diterima.

## Konteks

ARCHITECTURE.md §5 menempatkan media sosial sebagai sumber sinyal
Green/Red Flag (prioritas ke-3, setelah sumber resmi dan berita) dan
menegaskan: "hanya lewat API resmi / pencarian publik, jangan login
palsu / bypass". Tim Direct harus memutuskan: apa yang diambil dari
Instagram dan LinkedIn perusahaan, dan apa yang dilarang.

Riset 15 Nov 2026 (lihat `docs/fase1-riset-direct.md` §4) menemukan
asimetri tajam:

- **Instagram** punya jalan resmi: Graph API — Business Discovery
  (membaca field publik akun Bisnis/Kreator lain) dan Hashtag Search.
  Batasnya: butuh aplikasi + token sendiri + App Review, hanya akun
  Bisnis/Kreator, kuota 200 request/jam/token. Otomatisasi tak resmi
  (instaloader/instagrapi, login dengan password) dilarang Terms of Use
  dan berujung penangguhan akun.
- **LinkedIn** tidak punya jalan baca perusahaan lain: tidak ada Job
  Search API publik; Talent Solutions API hanya untuk partner yang
  disetujui; Community Management API hanya untuk halaman yang kita
  kelola. User Agreement §8.2 (berlaku 3 Nov 2025) melarang scraping
  dan bot secara eksplisit, dan penegakan meningkat pada 2026
  (gugatan terhadap Proxycurl/Nubela; Proxycurl tutup 2026).
- **Tanggal posting sosial ≠ tanggal buka lowongan**, caption bisa
  diedit tanpa jejak, dan satu postingan bisa merujuk ke banyak
  lowongan. Sosial tidak bisa menjadi sumber lowongan.

## Keputusan

1. **Instagram — ADOPSI sebagai sumber LEAD, bukan sumber lowongan.**
   Hanya lewat Instagram Graph API resmi (Business Discovery).
   Modul `social_company.py` mengambil: username, bio, media publik
   (caption, timestamp, permalink, media_type) + link lowongan dari
   caption/bio. Token diberikan caller saat runtime; TIDAK ADA
   kredensial di file mana pun.
2. **Hasil sosial adalah LEAD, bukan lowongan.** `to_job_lead()`
   sengaja mengembalikan `job_posted_at: None`. Lead hanya memicu
   verifikasi ke halaman karier / board ATS. Tanpa verifikasi itu,
   lead tidak pernah tampil sebagai lowongan.
3. **LinkedIn — TIDAK ADA pengambilan otomatis.** Tidak ada satu baris
   pun kode fetcher LinkedIn di paket ini — dengan sengaja. Yang ada
   hanya `ManualSocialLead`: operator manusia membuka halaman publik
   perusahaan di browser dan mencatat URL + tanggal lihat + kutipan
   singkat. Bila LinkedIn suatu hari membuka akses API resmi untuk
   membaca postingan perusahaan, barulah dibuat adapter API.
4. **Yang dilarang keras**: login palsu / akun palsu, instaloader /
   instagrapi / otomatisasi tak resmi, DM dan grup tertutup, akun
   pribadi, scraping massal profil publik untuk produk komersial,
   menyimpan nama/email/telepon siapa pun, menyimpan foto/caption
   utuh untuk dipublikasikan ulang (kutipan maks 500 karakter + link).
5. **Klasifikasi caption bersifat heuristik**: kata kunci lowongan +
   penanganan negasi ("bukan lowongan", "not hiring"). Hasil True =
   lead untuk diverifikasi, bukan fakta.

## Alternatif yang ditolak + alasan

| Alternatif | Alasan ditolak |
|---|---|
| IG dihitung sebagai sumber lowongan (tanggal posting = tanggal buka) | Salah secara faktual: tanggal posting ≠ tanggal buka; caption bisa diedit; satu postingan bisa untuk banyak lowongan (Hasil Grill G3) |
| Scraping LinkedIn dengan akun / browser otomatis / pihak ketiga | Dilarang eksplisit User Agreement §8.2; risiko akun dibatasi/ditutup dan gugatan; penegakan meningkat 2026. Bukan risiko yang sepadan dengan nilai lead |
| Memakai instaloader/instagrapi untuk IG | Otomatisasi tak resmi: melanggar Terms of Use Instagram, rapuh (`challenge_required`, login wall), akun bisa ditangguhkan |
| Membeli data dari broker data LinkedIn/IG | Rantai pasok data tidak jelas (banyak broker memakai scraping yang sama); risiko hukum + privasi berpindah ke CekLoker |
| Menunda semua sosial ke Fase 4 | Ditolak sebagian: IG resmi dipertahankan karena risikonya administratif (App Review/kuota), bukan hukum, dan lead IG berguna untuk sinyal flag Fase 2. LinkedIn otomatis tetap ditunda (poin 3) |

## Konsekuensi

- **Positif**: jalur IG legal dan stabil selama memakai API resmi;
  lead IG memberi sinyal aktivitas rekrutmen perusahaan untuk flag
  engine Fase 2; tidak ada risiko hukum dari LinkedIn karena tidak ada
  otomatisasi sama sekali.
- **Negatif**: LinkedIn v1 praktis tidak berskala (manual) — sinyal
  LinkedIn perusahaan hanya didapat bila operator mencatat manual;
  IG butuh aplikasi Meta + App Review sebelum jalan (K-D6: bentuk
  respons Business Discovery belum terverifikasi dari dokumen primer
  langsung karena Meta menolak akses baca 403 pada 15 Nov 2026 —
  perlu uji live dengan token sendiri).
- **Risiko**: App Review Meta bisa menolak fitur Public Content Access;
  kuota 200 request/jam membatasi jumlah perusahaan yang dipantau
  per jam. Mitigasi: pantau perusahaan prioritas dulu, cache agresif.
- **Butuh jawaban Giga**: apakah CekLoker membuat akun/aplikasi Meta
  sendiri untuk token Graph API (butuh akun Bisnis IG + aplikasi Meta
  atas nama siapa — Giga pribadi atau badan usaha nanti)? Tanpa ini,
  modul IG tidak bisa diuji live.

## Hasil grill yang mengubah keputusan

(Grill penuh: `docs/fase1-riset-direct.md` §6.)

- **G3** (celah tanggal IG?) → IG diturunkan dari "sumber lowongan"
  menjadi "sumber lead"; `job_posted_at` dibuat None secara eksplisit
  di kode, bukan sekadar dicatat di dokumen.
- **G4** (kenapa tidak tunda semua sosial?) → LinkedIn otomatis
  DITUNDA PENUH — rencana awal "scraper LinkedIn hati-hati" dibatalkan
  total; tidak ada kode fetcher LinkedIn. IG dipertahankan hanya pada
  jalur API resmi dengan alasan yang ditulis di atas.
- **G3 lanjutan** (false positive klasifikasi) → penanganan negasi
  ditambahkan ke `classify_caption_as_job_post` setelah test menemukan
  caption "Bukan lowongan." terklasifikasi sebagai pengumuman.
