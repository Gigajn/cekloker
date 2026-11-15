# ADR-0010 — Desain Web CekLoker (Next.js, Fase 1-lanjutan)

> Catatan koordinator Fase 1-lanjutan: nomor ini semula ADR-0008, di-rename
> menjadi 0010 karena dua tim paralel sama-sama memakai 0008 (uji live
> tetap 0008, API 0009). Isi tidak berubah.

- **Status:** Diterima (tim WEB, Fase 1-lanjutan)
- **Tanggal:** 15 November 2026
- **Penulis:** Tim WEB CekLoker
- **Terkait:** `ARCHITECTURE.md §2, §5`, `docs/decisions-d6-d12.md` (D7, D8, D9, D10),
  `docs/fase1-konsolidasi.md §7–§8`, ADR-0005, ADR-0006, `docs/SCORING.md`,
  `docs/glossary.md`, `apps/web/README.md`.

## Konteks

Fase 1-lanjutan membangun web publik CekLoker (Next.js App Router +
TypeScript + Tailwind, ARCH §2) dengan 4 halaman: daftar lowongan `/`,
detail `/jobs/[id]`, profil perusahaan `/companies/[slug]`, dan penjelasan
`/cara-menilai`. Pengguna pertama adalah Giga sendiri (D8: alat pribadi
dulu, publik boleh dibaca tanpa login). Skor ternormalisasi sudah
dikunci D7 (ADR-0005). API FastAPI belum ada saat web ini dibangun
(`apps/api/` masih placeholder) — kontrak API di bawah ini adalah
spesifikasi yang dipegang web, bukan hasil yang sudah teruji live.

## Keputusan (hasil grill)

### W1. Server Components + fetch server-side, bukan fetch dari browser
Halaman mengambil data dari API di server (Next.js Server Component).
Alasan: SEO penting untuk halaman perusahaan/lowongan (ARCH §2);
filter dan data tidak butuh JavaScript klien; tidak ada secret yang
bocor ke browser (hanya `NEXT_PUBLIC_API_URL`). Yang di-grill: fetch
client-side akan membuat halaman kosong saat pertama dibuka dan
merusak indeks Google — ditolak.

### W2. Filter lewat query string URL, bukan state lokal
Semua filter (`q`, `posted_from`, `posted_to`, `location`,
`salary_min`, `score_min`, `status`) hidup di URL (`/?q=...&...`).
Form filter memakai method GET biasa. Alasan: hasil filter bisa
dibagikan (copy URL), di-bookmark, dan tombol back browser bekerja.
Yang di-grill: state di `useState` saja membuat hasil tidak bisa
dibagikan — ditolak.

### W3. Mock hanya sebagai fallback, selalu berlabel, tidak pernah mengaku data nyata
Bila API tidak bisa dijangkau saat halaman di-render, web memakai data
seed/mock lokal dan menampilkan spanduk jelas "Data contoh (mock) —
API belum terhubung" di setiap halaman yang memakai mock, plus label
`MOCK` di kode (`src/lib/mock.ts`, `isMock: true` di lapisan API).
Alasan: web harus bisa didemokan sebelum API selesai, tapi klaim
"ada lowongan X" dari data palsu adalah kebohongan produk. Mock
dimatikan otomatis begitu API menjawab.
Yang di-grill: mock tanpa label / mock sebagai sumber utama — ditolak.

### W4. Skor: percaya `score`/`label` dari API, tapi jangan pernah tampilkan skor palsu
- Bila API mengembalikan `score: null` → tampilkan "Belum cukup data",
  tanpa angka, tanpa label Green/Mixed/Red.
- Bila `score` ada → tampilkan skor ternormalisasi (0–100) + label,
  plus jumlah kategori terukur yang dihitung dari sinyal yang diterima.
- Sinyal tanpa `evidence_url` tetap ditampilkan sebagai "tanpa tautan
  bukti" (peringatan di UI), tidak disembunyikan — sesuai ADR-0006
  butir 9, pelanggaran kontrak API harus terlihat, bukan ditutup-tutupi.
Yang di-grill: menampilkan skor dari penjumlahan mentah di web (duplikasi
logika flag-engine) — ditolak; normalisasi adalah urusan API/flag-engine
(ADR-0005), web hanya menampilkan.

### W5. Tanggal: `posted_at` dan `first_seen_at` tidak pernah dicampur
Kartu lowongan menampilkan keduanya secara terpisah, sesuai ARCH §4:
"Dibuka (klaim sumber)" dan "Pertama terlihat oleh kami". Bila
`posted_at_certain` false → tambahkan label "perkiraan" di samping
tanggal. Bila `posted_at` null → tulis "Tanggal sumber tidak tersedia".
Yang di-grill: menampilkan `first_seen_at` sebagai tanggal buka —
ditolak (itu dua fakta berbeda; lihat glossary).

### W6. Tanpa login, tanpa pelacakan pihak ketiga, tanpa data pribadi
Halaman publik bisa dibaca tanpa login (D8). Tidak ada script analitik
pihak ketiga, tidak ada cookie pelacak, tidak ada form yang meminta
data pribadi. Satu-satunya penyimpanan: tidak ada. Yang di-grill:
menambah Google Analytics "supaya tahu pengunjung" — ditolak untuk v1
(D10 $0 + privasi ADR-0006 butir 15).

### W7. Bahasa anti-vonis di seluruh UI (ADR-0006 butir 11)
Tidak ada kata "penipu", "melanggar UU", atau sejenisnya di UI mana pun.
Label Red selalu disertai kalimat "ringkasan sinyal publik" + tautan
"Lihat bukti". Disclaimer yang sama muncul di footer setiap halaman dan
lengkap di `/cara-menilai`. Peringatan biaya (red override) ditampilkan
sebagai "Ada laporan permintaan biaya — periksa buktinya" + tautan bukti,
bukan sebagai vonis.

### W8. Stack v1: Next.js 15 + React 19 + Tailwind v4 (CSS-first)
Tailwind v4 (`@import "tailwindcss"`, tanpa `tailwind.config.js`)
dipilih supaya konfigurasi minimal dan build tidak bergantung file
konfigurasi JS tambahan. Node ≥ 20. Tidak ada dependensi runtime
berbayar; tidak ada CMS, tidak ada auth library di v1.

### W9. Cara perusahaan minta koreksi (sampai ada form, v1 = petunjuk tertulis)
`/cara-menilai` menjelaskan: perusahaan bisa meminta koreksi dengan
mengirim bukti yang bisa diverifikasi ke pengelola; sinyal yang
disengketakan ditangguhkan dan diberi label "disengketakan — sedang
ditinjau" (ADR-0006 butir 12) dengan batas tanggapan ≤ 7 hari.
Form koreksi online belum dibangun di v1 — halaman ini menulis itu
secara jujur, bukan berpura-pura ada form. (Konflik terbuka: belum ada
alamat kontak/form resmi — lihat K-W7 di "Konflik kontrak API".)

## Alternatif yang ditolak + alasan

| Alternatif | Alasan ditolak |
|---|---|
| Fetch client-side (`useEffect`) | Halaman kosong saat load awal, SEO rusak (ARCH §2 menuntut halaman terindeks). |
| Filter di state lokal saja | Hasil tidak bisa dibagikan/di-bookmark; tombol back rusak. |
| Mock tanpa label | Menyesatkan — pengguna mengira lowongan contoh itu lowongan nyata. |
| Web menghitung ulang skor dari sinyal mentah | Duplikasi flag-engine; risiko web dan API menampilkan angka berbeda; normalisasi urusan API (ADR-0005). |
| Skor ditampilkan walau bukti belum cukup (angka kecil "sementara") | Melanggar prinsip "skor tanpa bukti tidak tampil" (ARCH §5, ADR-0006 butir 9). |
| Analitik pihak ketiga di v1 | D10 ($0) + privasi; belum ada kebutuhan yang membenarkan pelacakan. |
| Klaim "form koreksi" padahal belum ada | Dishonest UI; halaman menulis status sebenarnya. |

## Konflik kontrak API (dicatat, JANGAN diubah sepihak oleh tim WEB)

Kontrak yang dipegang web (dari tugas Fase 1-lanjutan):

- Base URL: env `NEXT_PUBLIC_API_URL`, default `http://localhost:8000`.
- Prefix path yang diasumsikan web: `/api/v1` (ARCH §6).
- Job: `{id, title, company{name,slug}, location, work_type, salary_min,
  salary_max, salary_currency, posted_at, posted_at_certain,
  first_seen_at, last_seen_at, status, source, source_url}`.
- Company: `{id, slug, name, score (null bila belum cukup data), label,
  signals:[{category, key, points, evidence_url, evidence_text,
  evidence_date, source, confidence}]}`.

| ID | Konflik / kekurangan kontrak | Sikap web v1 |
|---|---|---|
| **K-W1** | Company response tidak punya `measured_categories` / flag `decisive` per sinyal. Web tidak bisa memverifikasi sendiri syarat "≥2 kategori penentu" (ADR-0005 butir 3) — hanya bisa percaya `score: null` dari API. | Web menghitung kategori berbeda dari sinyal yang diterima sebagai info tampilan saja, bukan sebagai penentu label. |
| **K-W2** | Bentuk respons list lowongan tidak ditentukan (array polos vs `{items, total}`). | Web menerima keduanya (array langsung, atau `items` + `total`). |
| **K-W3** | Nama parameter filter tidak ditentukan. | Web mengirim `status, posted_from, posted_to, location, salary_min, score_min, q`. Tim API harus mengonfirmasi / menyamakan. |
| **K-W4** | Tidak ada field `red_override` / peringatan di company response. Web tidak bisa membedakan Red biasa dari Red karena permintaan biaya. | Web menampilkan peringatan biaya bila ada sinyal dengan `key` mengandung `fee`/`biaya` dan `points` 0/override — heuristik rapuh, dicatat sebagai kekurangan kontrak. API sebaiknya menambah `red_override: boolean` + `warnings: string[]`. |
| **K-W5** | Tidak ada endpoint detail lowongan yang dinyatakan eksplisit (`GET /api/v1/jobs/{id}` hanya asumsi). | Web memakai asumsi itu; bila 404, tampilkan halaman "tidak ditemukan" + tautan kembali, bukan error mentah. |
| **K-W6** | Tidak ada endpoint yang dinyatakan untuk detail perusahaan (`GET /api/v1/companies/{slug}` hanya asumsi). | Sama seperti K-W5. |
| **K-W7** | Belum ada alamat kontak / form koreksi resmi untuk perusahaan. | `/cara-menilai` menulis proses + batas 7 hari tanpa mengarang alamat email. Perlu keputusan Giga/tim API sebelum publik. |

## Konsekuensi

- **Positif:** 4 halaman bisa jalan dan didemokan dengan mock berlabel
  sebelum API selesai; begitu API menjawab, mock mati otomatis tanpa
  ubah kode UI; skor tidak pernah tampil tanpa dasar; filter bisa
  dibagikan lewat URL.
- **Negatif / risiko:** bila kontrak API ternyata berbeda (K-W1–K-W6),
  web perlu penyesuaian kecil di `src/lib/api.ts` saja (satu file) —
  UI tidak perlu ditulis ulang; halaman perusahaan bergantung penuh
  pada `score`/`label` API, jadi kesalahan API langsung terlihat di
  publik — perlu pengujian API sebelum klaim apa pun.
- **Dependensi:** tim API (Fase 1-lanjutan) mengonfirmasi K-W1–K-W6;
  kalibrasi ambang rubrik tetap urusan flag-engine (ADR-0005 butir 10).

## Hasil grill yang mengubah keputusan

- **G-W1 (SEO vs client fetch):** memaksa W1 — fetch server-side.
- **G-W2 (hasil filter tidak bisa dibagikan):** memaksa W2 — filter di URL.
- **G-W3 (mock = data palsu yang disangka nyata):** memaksa W3 — spanduk
  mock di semua halaman + `isMock` di lapisan API.
- **G-W4 (web menghitung skor sendiri):** memaksa W4 — web hanya
  menampilkan, tidak menghitung ulang.
- **G-W5 (tanggal buka vs pertama terlihat):** memaksa W5 — dua tanggal
  terpisah + label "perkiraan" (konsisten dengan ADR-0002).
- **G-W6 (analitik "gratis" pihak ketiga):** memaksa W6 — ditolak.
- **G-W7 (kata vonis di UI):** memaksa W7 — bahasa anti-vonis + disclaimer
  di footer + `/cara-menilai`.
- **G-W8 (form koreksi fiktif):** memaksa W9 — tulis status sebenarnya.
