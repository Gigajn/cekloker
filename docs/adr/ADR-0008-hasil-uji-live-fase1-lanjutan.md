# ADR-0008 — Hasil uji live Fase 1-lanjutan: Glints, Kalibrr, ATS, 9 perusahaan

- **Status:** Diterima (tim uji live, 15 Nov 2026).
- **Tanggal:** 15 November 2026
- **Konteks terkait:** `docs/fase1-konsolidasi.md` §8 (daftar uji live wajib),
  §3 (K9, K10, K11); ADR-0001 (sumber job board), ADR-0002 (kontrak adapter),
  ADR-0003 (halaman karier + ATS); `docs/fase1-lanjutan-uji-live.md` (laporan lengkap).

## Status

Diterima.

## Konteks

Fase 1 selesai tanpa satu pun request live — semua adapter + test memakai
fixture buatan. Konsolidasi §8 mewajibkan 6 butir uji live sebelum klaim apa
pun "jalan": (1–2) sitemap + JSON-LD Glints, (3) pencarian Kalibrr `?query=`,
(4) 1 board live per ATS, (5) 9 perusahaan Direct yang belum dibaca,
(6) Instagram (ditunda oleh D11). Uji dilakukan 15 Nov 2026, sopan,
±43 request HTTP total, hanya stdlib urllib, User-Agent jujur
(`CekLokerBot/0.1`, kontak lewat env `CEKLOKER_CONTACT` — kosong di VM,
jadi dipakai UA default bertautan repo GitHub).

## Keputusan

1. **Glints — TETAP BANGUN, dengan 2 perbaikan adapter.** Sitemap index
   berisi 4.898 child sitemap; sitemap lowongan berisi 200 URL yang
   semuanya cocok pola lowongan. JSON-LD `JobPosting` ada di halaman detail
   (`datePosted` ISO + `validThrough` + gaji). Namun uji live menemukan
   BUG: penanda tutup `"lowongan ini sudah ditutup"` ternyata ada di bundel
   i18n `<script>` semua halaman, sehingga adapter lama menandai lowongan
   AKTIF sebagai tutup. Perbaikan: penanda tutup hanya dicari di teks
   tampil (di luar `<script>`/`<style>`); `validThrough` jadi sinyal kedua;
   `check_active()` memakai satu sumber kebenaran; sitemap didedup per UUID
   (varian locale `/id/` vs `/id/en/`).
2. **Kalibrr — TETAP BANGUN di kode, tapi DINYATAKAN GAGAL dari VM ini.**
   Pencarian `?query=software+engineer` mengembalikan HTTP 200 berisi shell
   SPA ~2,3 KB tanpa `__NEXT_DATA__` dan tanpa URL lowongan — jadi
   `?query=` TIDAK TERVERIFIKASI bekerja dan jumlah hasil tidak bisa
   dihitung. Adapter TIDAK dimatikan (temuan ini bisa spesifik-egress VM —
   shell memuat penanda `__KB_THIS_IS_A_503__`), tapi perilakunya diubah:
   bila halaman tanpa `__NEXT_DATA__`, parser melempar `SourceFetchError`
   (worker → `unknown`), bukan diam-diam `[]`. Nasib akhir Kalibrr
   diputuskan di D13 (uji ulang dari jaringan Indonesia dulu).
3. **Klaim robots.txt Kalibrr DINYATAKAN TIDAK TERVERIFIKASI.** `robots.txt`
   Kalibrr (.id maupun .com) mengembalikan shell SPA, bukan file robots —
   jadi klaim Fase 1 ("hanya melarang /root dan /candidate/profile") tidak
   bisa berasal dari fetch langsung. `robots_disallows` dipertahankan
   sebagai catatan klaim lama sampai ada robots.txt sungguhan yang terbaca.
4. **ATS — TETAP BANGUN, semua field tanggal terverifikasi live.**
   Greenhouse board `discord` (26 lowongan): `first_published` ada di
   daftar 26/26 — K-D1 terjawab sebagian (dokumen resmi tidak lengkap,
   data live lebih lengkap). Lever board `spotify` (87): `createdAt` ada
   87/87 — K-D2 terjawab. Ashby board `ashby` (76): `publishedAt` ada,
   dan lowongan pertama punya `publishedAt` 2024-03-04 — bukti langsung
   K-D3 (bukan tanggal buka). Workable board `huggingface` (6):
   `published_on` tanggal saja. Tidak ada perubahan logika parser ATS.
5. **GoTo Indonesia BUKAN di Lever (K-D5 TERBANTAH).**
   `api.lever.co/v0/postings/goto` → 404. Halaman karier GoTo adalah JS
   tanpa JSON-LD/tanpa tautan ATS di HTML statis. GoTo dilacak lewat Glints
   untuk sekarang (D15).
6. **Board kosong tetap AMBIGU (K-D4).** Board Lever milik Lever sendiri:
   HTTP 200, 0 lowongan — tidak boleh disimpulkan "tidak merekrut".
   Aturan ADR-0003 dipertahankan, tanpa perubahan kode.
7. **Perusahaan Direct Indonesia: 0 dari 9 memberi lowongan contoh dari
   HTML statis.** GoTo/BCA/Blibli terjangkau tapi tanpa data terstruktur;
   Tokopedia timeout; Bukalapak HTTP 406; Xendit/Ruangguru/Telkom/DANA
   koneksi ditutup server. Semuanya perlu uji ulang dari jaringan Giga
   sebelum disimpulkan BLOKIR permanen (D14). Jalur direct Indonesia
   praktis baru terbukti untuk Traveloka (Fase 1) + ATS global.
8. **Instagram TETAP TIDAK DIUJI** (D11: lead manual, tanpa token) — bukan
   kelalaian, melainkan keputusan.

## Alternatif yang ditolak + alasan

| Alternatif | Alasan ditolak |
|---|---|
| Kalibrr langsung dimatikan (`enabled=False`) setelah gagal dari VM | Temuan bisa spesifik-egress (penanda 503 di shell). Mematikan permanen berdasarkan 1 jaringan adalah kesimpulan berlebih — D13 meminta uji ulang dari jaringan Indonesia dulu. |
| Kalibrr mengembalikan `[]` saja saat shell SPA (status quo) | `[]` dibaca worker sebagai "0 lowongan" — data yang salah. `SourceFetchError` (unknown) adalah jawaban jujur sesuai ADR-0002 ("gagal teknis ≠ tutup"). |
| Mencari endpoint XHR internal Kalibrr untuk ganti `__NEXT_DATA__` | Endpoint tidak terdokumentasi; "bisa diakses" ≠ "diizinkan" — alasan yang sama saat menolak GraphQL Glints (ADR-0001, K-JB2). Butuh grill + keputusan Giga (D13 opsi c), bukan jalan pintas diam-diam. |
| Penanda tutup Glints tetap dicari di HTML mentah | Terbukti false positive di SEMUA halaman (bundel i18n). Mempertahankannya berarti semua lowongan Glints ditandai tutup — merusak janji produk #1 (status aktif terverifikasi). |
| Memakai `validThrough` sebagai SATU-SATUNYA penanda tutup Glints | Tidak semua halaman punya `validThrough`; penanda teks tampil tetap sinyal utama. Keduanya dipakai bersama. |
| Menyimpulkan Xendit/Ruangguru/Telkom/DANA "memblokir CekLoker" | Pola penolakan identik di 4 domain + Bukalapak 406 + Tokopedia timeout dalam satu sesi dari satu egress lebih cocok dijelaskan sebagai filter egress/datacenter daripada kebijakan tiap situs. Perlu pembanding dari jaringan lain (D14). |
| Uji live diulang dari browser / UA browser | Meniru UA browser untuk lolos filter adalah pemalsuan identitas — dilarang aturan proyek (ADR-0002, § "kesopanan & error"). Hasil dari UA jujur adalah hasil yang sah dilaporkan. |

## Konsekuensi

- **Positif:** Glints kini benar-benar bisa membedakan aktif/tutup
  (sebelum perbaikan, semua lowongan akan ditandai tutup). Kalibrr gagal
  secara jujur, bukan diam-diam kosong. 4 platform ATS terverifikasi live
  dengan field tanggal nyata — K9/K10 sebagian besar tertutup.
- **Negatif:** Cakupan Direct Indonesia tetap tipis (hanya Traveloka yang
  terbukti). Kalibrr belum bisa dipakai dari VM — butuh D13.
- **Netral:** 7 fixture + 9 test baru mengunci temuan live sebagai regresi
  (97 test scraper-core lolos, 0 gagal — lihat laporan uji live §3).
- **Butuh jawaban Giga:** D13 (nasib Kalibrr), D14 (uji ulang 6 perusahaan
  dari jaringan Giga), D15 (GoTo tanpa Lever), D16 (Playwright untuk
  halaman karier JS — ditunda sampai D13/D14 dijawab).

## Hasil grill yang mengubah keputusan

(Grill penuh: `docs/fase1-lanjutan-uji-live.md` §2.)

- **G-L1** (apa di halaman yang mengandung frasa tutup tapi bukan pesan
  tutup?) → bundel i18n ditemukan; logika penanda tutup Glints ditulis ulang.
- **G-L2** (apakah klaim skill Juli 2026 masih berlaku hari ini untuk UA
  bot jujur?) → `__NEXT_DATA__` Kalibrr terbukti tidak ada; adapter diubah
  gagal jujur.
- **G-L8** (dari mana klaim robots.txt Kalibrr berasal, kalau URL-nya
  mengembalikan shell SPA?) → klaim dinyatakan tidak terverifikasi.
