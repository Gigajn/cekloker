# ADR-0002 — Kontrak adapter + cara deteksi aktif / tanggal buka

> **Penomoran:** seri ADR khusus CekLoker mulai 0001 (perintah tugas
> Fase 1). Lihat catatan tabrakan penomoran di ADR-0001 (ADR-0007 sudah
> ada dari tim lain).

- **Status:** Diterima (tim job-board, 15 Nov 2026).
- **Tanggal:** 15 November 2026
- **Konteks terkait:** `ARCHITECTURE.md` §3 (alur data), §4 (model data),
  §6 (kontrak adapter), §8 (legal); `docs/fase1-riset-jobboard.md`
  (§4 Hasil Grill G2–G5, konflik K-JB4).

## Status

Diterima.

## Konteks

ARCHITECTURE.md §6 menetapkan kontrak adapter 3 metode
(`discover` / `fetch_job` / `check_active`) dan §4 menetapkan
`posted_at` + `first_seen_at` + `last_seen_at` + `status`. Tetapi
dokumen itu tidak menjawab: apa arti "aktif" bila request gagal
teknis? Seberapa pasti `posted_at` dari tanggal relatif? Bagaimana
mendeteksi repost? Apa yang terjadi bila sumber memblokir? ADR ini
mengunci jawabannya sebelum satu baris worker ditulis.

## Keputusan

### 1. Kontrak adapter (3 metode, `RawJob` dataclass)

```python
class JobSourceAdapter:
    source_id: str          # stabil, dipakai FK jobs.source_id
    base_url: str
    enabled: bool = True    # False = adapter MATI (butuh ADR baru untuk nyalakan)
    polite_delay_s: float   # 3.0 Glints/Kalibrr; 5.0 bila JobStreet/Indeed diizinkan nanti
    robots_disallows: tuple[str, ...]  # dokumentasi hidup aturan robots.txt

    def discover(self, keywords="", location="", max_pages=1) -> list[str]: ...
    def fetch_job(self, url: str) -> RawJob: ...
    def check_active(self, url: str) -> bool: ...
```

- `discover` memakai jalur PALING RESMI (API resmi > RSS > sitemap >
  halaman list publik > JSON tersemat). Endpoint internal tidak
  terdokumentasi DILARANG sebagai jalur utama.
- `RawJob` adalah dataclass (bukan dict): semua adapter mengisi field
  yang sama; field yang tidak diketahui = `None`, bukan tebakan.
- `enabled=False` + `require_enabled()` membuat adapter yang ditunda
  (JobStreet, Indeed) mustahil "tidak sengaja" aktif — ia raise
  `SourceNotPermittedError` dengan alasan + alternatif legal.

### 2. Deteksi aktif — 3 sinyal, 1 aturan gagal

`check_active(url)` mengembalikan `True` HANYA bila:
- HTTP 200, DAN
- tidak ada penanda tutup di halaman (Glints: "This job was closed";
  Kalibrr: "Ditutup."; tiap adapter WAJIB mendokumentasikan penandanya).

`False` bila: HTTP 404, penanda tutup ditemukan, atau redirect ke
halaman list/pencarian.

**Gagal teknis (timeout, 5xx, 403/429) BUKAN `False`.** Metode itu
melempar `SourceFetchError` / `SourceBlockedError` sehingga worker
mempertahankan status lama sebagai `unknown`. Alasan: "tidak bisa
dicek" ≠ "sudah tutup". Aturan 2x kunjungan hilang → `closed`
(ARCHITECTURE.md §3) tetap berlaku di atas hasil `check_active`.

### 3. Tanggal buka — dua tanggal, dua tingkat kepastian

- `posted_at` = klaim sumber. `parse_posted_at` mengembalikan
  `(tanggal, pasti)`: `pasti=True` HANYA untuk tanggal absolut/ISO
  ("12 Nov 2026", "2026-11-12", `activationDate` Kalibrr).
  Tanggal relatif ("2 hari lalu", "1 bulan lalu" = ref − 30 hari,
  "Listed seven days ago") selalu `pasti=False` — itu perkiraan.
- `first_seen_at` / `last_seen_at` dicatat WORKER (fakta pengamatan),
  bukan adapter. UI menampilkan keduanya berdampingan; bila
  `posted_at` None, UI menulis "tanggal sumber tidak tersedia —
  pertama terlihat …" dan TIDAK menebak.
- Tanggal relatif dihitung terhadap tanggal fetch dalam Asia/Jakarta;
  selisih ±1 hari diterima sebagai batas ketelitian (zona waktu server
  sumber belum tentu WIB).

### 4. Repost & dedup — fingerprint

`RawJob.fingerprint()` = SHA-256 (32 karakter) dari
`judul + company_norm + lokasi`. Lowongan yang sama di dua sumber,
atau repost dengan URL/ID baru, punya fingerprint sama. Normalizer
menyimpan `first_seen_at` paling awal dan menandai "kemungkinan
repost". Tidak sempurna (judul diubah sedikit lolos), tetapi lebih
jujur daripada menganggap tiap URL baru sebagai lowongan baru.

### 5. Kesopanan & error — dua tipe error, dua perilaku worker

- `SourceNotPermittedError` (turunan `NotImplementedError`): larangan
  legal. Worker tidak pernah retry; butuh ADR baru + izin tertulis.
- `SourceBlockedError` (403/429/CAPTCHA): worker berhenti sementara
  (backoff). DILARANG memutar proxy / memalsukan User-Agent / meniru
  TLS browser untuk lolos.
- User-Agent jujur berisi `CekLokerBot` + kontak. Delay 2–5 dtk/domain.
  `allowed_by_robots()` memakai matcher RFC 9309 sendiri karena
  `urllib.robotparser` stdlib tidak menangani pola `*` tengah aturan
  dan akhiran `$` (diuji 15 Nov 2026).

### 6. Dependensi paket — stdlib saja

`scraper-core` runtime memakai **stdlib Python 3.12 saja**
(`urllib`, `html.parser`, `json`, `re`). Alasan: data v1 tersemat
sebagai JSON (JSON-LD, `__NEXT_DATA__`). Tanpa bs4/httpx, nol
dependensi runtime = image Docker kecil + tanpa rantai pasok.

## Alternatif yang ditolak + alasan

| Alternatif | Alasan ditolak |
|---|---|
| Satu fungsi `scrape()` serba bisa | Tidak bisa diuji per-bagian; re-check aktif saja jadi mustahil tanpa ambil detail penuh (mahal + tidak sopan). |
| Adapter mengembalikan `dict` bebas | Normalizer harus menebak field; `posted_at` kosong tidak bisa dibedakan dari "lupa diisi". Dataclass memaksa kejujuran. |
| `check_active` tanpa pemisah gagal teknis | Satu kali timeout akan menandai ratusan lowongan `closed` secara keliru — kerusakan data massal dari satu gangguan jaringan. |
| `posted_at` = `first_seen_at` bila sumber tak menulis tanggal | Dua hal berbeda (klaim sumber vs fakta pengamatan). Menyamakannya = memalsukan "tanggal buka". |
| Repost diabaikan ("URL baru = lowongan baru") | Ghost job (ARCHITECTURE.md §5, −10 poin) justru bekerja lewat repost. Tanpa fingerprint, CekLoker ikut menyebarkan ghost job. |
| bs4 + httpx sebagai dependensi wajib | Manfaat nol di v1 (semua data dari JSON tersemat); menambah rantai pasok + ukuran image tanpa alasan. |
| `urllib.robotparser` untuk cek robots.txt | Diuji 15 Nov 2026: aturan Glints `*/opportunities/jobs/explore?*` lolos (dianggap diizinkan padahal dilarang). Matcher sendiri ~40 baris, dites unit. |

## Konsekuensi

- **Positif:** Status aktif punya definisi yang bisa diuji (84 unit test,
  0 gagal — semuanya dari fixture, tanpa HTTP live). Keputusan "tutup"
  konservatif (lebih baik `unknown` daripada `closed` yang keliru).
  Kontrak yang sama dipakai 4 adapter — 1 sumber mati tidak mematikan
  produk.
- **Negatif:** `check_active` butuh 1 request per lowongan per kunjungan
  ulang (biaya request 2x lipat dibanding "cek dari halaman list").
  Diterima: kebenaran status adalah janji produk #1.
- **Netral:** Bila ada sumber yang butuh JS/DOM berat (halaman karier
  perusahaan), adapter itu BOLEH memakai Playwright/bs4 sebagai
  dependensi opsionalnya sendiri — bukan beban paket inti. Keputusan
  itu butuh ADR/penilaian sendiri saat dibutuhkan.

## Hasil grill yang mengubah keputusan

- **G2** memisahkan `check_active` dari `fetch_job` dan menolak dict
  bebas → lahir `RawJob` dataclass + kontrak 3 metode yang ketat.
- **G3** menemukan 5 celah deteksi aktif/tanggal (repost, tanggal
  relatif, zona waktu, cache, penanda tutup tak universal) → lahir
  aturan `(tanggal, pasti)`, fingerprint repost, dan aturan "gagal
  teknis ≠ tutup". Sebelum grill, `posted_at` diperlakukan sebagai
  tanggal pasti — itu kesalahan yang sekarang terkunci sebagai aturan.
- **G4** ("apa yang terjadi kalau sumber memblokir besok?") → lahir
  pemisahan `SourceBlockedError` vs `SourceNotPermittedError` dan
  aturan "job lama jadi `unknown`, bukan `closed`".
- **G5** menguji stdlib-only dan justru menguatkannya (bukan mengubah).
  Lihat `docs/fase1-riset-jobboard.md` §4.

## Amandemen koordinator Fase 1-lanjutan (15 Nov 2026) — check_active

`CareerPageAdapter.check_active` sempat mengembalikan `False` untuk
kegagalan teknis (board tidak bisa dibaca / halaman tidak bisa diparse),
yang setelah 2x kunjungan akan menandai lowongan aktif sebagai `closed`
— melanggar aturan "gagal teknis ≠ tutup" di ADR ini. Perbaikan:
kegagalan teknis kini melempar `SourceFetchError` (worker → `unknown`);
hanya HTTP 404 / lowongan benar-benar tidak ada di board yang berarti
`False`. Test baru: `test_check_active_custom_404_is_closed_not_error`,
`test_check_active_custom_500_raises_fetch_error`,
`test_check_active_custom_no_json_ld_raises_fetch_error`,
`test_check_active_board_unparseable_raises_fetch_error`.
