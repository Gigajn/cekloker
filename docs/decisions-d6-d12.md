# Keputusan D6–D12 — dijawab Giga 2026-11-15 00:51 WIB

Lanjutan D1–D5 di ARCHITECTURE.md. Dicatat apa adanya dari jawaban Giga,
termasuk penafsiran yang masih perlu dikonfirmasi (ditandai).

## D6 — API resmi vs scraper langsung
**Jawaban Giga:** Sifatnya scraper dan tidak melakukan tindak kejahatan,
jadi tidak apa-apa memakai scraper langsung tanpa API resmi. Jangan
khawatirkan API resmi.

**Dicatat sebagai:** Jangan kejar API resmi untuk sumber yang sudah jalan
(Glints, Kalibrr, ATS). Lanjut tanpa JobStreet dulu (opsi a dari laporan).
**BELUM diputuskan ulang:** apakah jawaban ini juga berarti mengaktifkan
kembali adapter JobStreet / Indeed / LinkedIn yang di-stub karena ToS?
Sampai Giga bilang eksplisit, ketiganya TETAP stub / ditunda — karena D8
(tidak publish/komersial sampai alur legal) dan risiko blokir.
Kalau Giga mau ketiganya diaktifkan juga, itu keputusan terpisah yang
harus disebut satu per satu.

## D7 — Skor ternormalisasi
**Jawaban Giga:** Ya, lakukan normalisasi.
**Dicatat sebagai:** Berlakukan ADR-0005 — total skor = `100 × perolehan /
cap terukur`, label butuh ≥2 kategori penentu. Implementasi di
Fase 1-lanjutan (flag-engine), bukan diam-diam di ARCHITECTURE.md §5 —
ARCH perlu diamandemen saat implementasi.

## D8 — Siapa pengguna pertama, dan soal legal
**Jawaban Giga:** Pemakaian pertama adalah Giga sendiri — tools untuk
membantu dirinya dulu. Kalau orang lain terbantu, itu urusan lain.
Jujur, ini "sedikit ilegal", jadi TIDAK akan dipublish dan
dikomersialkan sampai benar-benar alurnya legal, baru berani
mengkomersialkan.

**Dicatat sebagai:** Status proyek = alat pribadi dulu. Gate publik/
komersial = alur harus legal dulu (izin/API/sumber yang mengizinkan,
ToS Glints/Kalibrr dibaca penuh, koreksi perusahaan siap).

**KONFLIK YANG HARUS DISELESAIKAN:** Repo `Gigajn/cekloker` saat ini
PUBLIC (dibuat public sementara 00:17 WIB "sampai project selesai").
Public di GitHub = sudah dipublish, bertentangan dengan D8.
Tindakan yang disarankan: balik ke Private sekarang
(Settings → General → Danger Zone → Change visibility → Make private),
baru dibuka lagi saat gate legal lolos. Keputusan ada di Giga.

**Catatan risiko (bukan nasihat hukum):** Melanggar ToS situs bukan
otomatis tindak pidana, tapi situs berhak memblokir, dan memakai data
hasil scraping untuk publik/komersial risikonya jauh lebih besar
daripada pemakaian pribadi yang sopan. Itulah kenapa D8 membedakan
keduanya.

## D9 — Status proyek
**Jawaban Giga:** Ya, ini proyek non-komersial pribadi.
**Dicatat sebagai:** Proyek non-komersial pribadi. Status ini yang
dipakai bila suatu hari mengajukan approval (mis. Reddit) — tapi
pengajuan Reddit tetap DITUNDA ke Fase 4 (bukan penentu Fase 2),
kecuali Giga minta diajukan sekarang.

## D10 — Biaya / API berbayar
**Jawaban Giga:** Semua tanpa biaya, jangan gunakan API berbayar apa pun.
**Dicatat sebagai aturan keras:** $0. Dilarang: Adzuna, JSearch,
Google Places API berbayar, X berbayar, dan API berbayar lain.
Konsekuensi: sinyal Google Review (rating + jumlah) yang tadinya
direncanakan lewat Places API TIDAK bisa jalan otomatis — ganti
entri manual / sumber gratis (RSS berita) sampai ada jalur gratis
yang sah.

## D11 — Instagram / Meta
**Jawaban Giga:** Jangan gunakan yang berbayar, lakukan scraping sopan saja.
**Dicatat sebagai:** Tidak ada aplikasi Meta berbayar, tidak ada token
berbayar. IG tetap lead manual saja (tanpa token, tanpa fetcher
otomatis yang butuh login). Scraping IG web yang butuh login tetap
TIDAK dilakukan — "sopan" di sini berarti: hanya info publik, delay,
tanpa bypass login.

## D12 — JobSpy itu apa (Giga: kurang paham)
**Penjelasan gampang:** JobSpy itu library Python orang lain (MIT)
yang sudah jadi — fungsinya mengambil lowongan dari Indeed,
Glassdoor, LinkedIn, dll secara otomatis. Dua cara pakai:
- (a) **REFERENSI saja (rekomendasi tim):** kita hanya BACA kodenya
  sebagai contoh cara parsing gaji/tanggal, lalu tulis adapter
  sendiri. JobSpy tidak di-install, tidak dijalankan.
- (b) **Pakai live:** kita install JobSpy lalu jalankan untuk
  mengambil lowongan Indeed/Glassdoor/LinkedIn. Lebih cepat, tapi
  risikonya sama seperti scraping situs-situs itu langsung
  (ToS melarang, bisa diblokir).
**DIPUTUSKAN Giga 2026-11-15 10:26 WIB: (a) REFERENSI saja.**
JobSpy tidak di-install dan tidak dijalankan live. Hanya dipakai
sebagai contoh pola parsing (gaji/tanggal) dengan atribusi MIT bila
potongan kodenya dipakai ulang. D6–D12 kini lengkap — tidak ada lagi
keputusan terbuka dari Fase 1.
