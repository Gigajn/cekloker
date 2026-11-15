# CekLoker — Web (Next.js)

Halaman publik CekLoker: daftar lowongan aktif, detail lowongan, profil
perusahaan (skor Green/Mixed/Red + bukti), dan penjelasan cara menilai.
Alat pribadi (non-komersial) — lihat `docs/decisions-d6-d12.md` (D8, D9).

Keputusan desain: `docs/adr/ADR-0010-desain-web.md`.
Kontrak API yang dipegang: `src/lib/api.ts` (jangan diubah sepihak).

## Stack

- Next.js 15 (App Router) + React 19 + TypeScript + Tailwind CSS v4
- Node.js ≥ 20. Tanpa dependensi berbayar, tanpa pelacakan pihak ketiga.

## Menjalankan

```bash
cd apps/web
npm install
cp .env.example .env   # opsional, bila perlu ubah URL API
npm run dev            # http://localhost:3000
```

Build produksi:

```bash
npm run build
npm run start
```

## Env yang dibutuhkan

| Variabel | Default | Keterangan |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | URL dasar API FastAPI (tanpa `/api/v1`, itu ditambah kode) |

## Menghubungkan ke API

Web memanggil API secara server-side:

| Kebutuhan | Endpoint yang dipakai |
|---|---|
| Daftar lowongan + filter | `GET {API}/api/v1/jobs?status=&q=&posted_from=&posted_to=&location=&salary_min=&score_min=` → array `Job`, atau `{ items, total }` |
| Detail lowongan | `GET {API}/api/v1/jobs/{id}` → `Job` |
| Profil perusahaan | `GET {API}/api/v1/companies/{slug}` → `Company` |

Bentuk `Job` / `Company` persisnya ada di `src/lib/types.ts`. Bila API
belum jalan, web menampilkan **data contoh (mock)** dengan spanduk yang
jelas — bukan data nyata (`src/lib/mock.ts`, `isMock` di `src/lib/api.ts`).
Begitu API menjawab, mock mati otomatis tanpa ubah kode UI.

Konflik/kekurangan kontrak API yang masih terbuka (tim API perlu
mengonfirmasi): lihat ADR-0010 bagian K-W1–K-W7 — antara lain tidak ada
field `red_override`, tidak ada flag `decisive` per sinyal, dan nama
parameter filter belum dikunci bersama.

## Halaman

| Route | Isi |
|---|---|
| `/` | Daftar lowongan aktif (default `status=active`): filter tanggal buka, lokasi, gaji_min, skor_min, pencarian teks; tiap kartu: judul, perusahaan, lokasi, gaji (atau "Gaji tidak dicantumkan"), tanggal dibuka (+ label "perkiraan" bila tidak pasti), "Pertama terlihat", status. |
| `/jobs/[id]` | Detail + `last_seen_at` + sumber + tautan ke sumber asli + peringatan bila status bukan aktif. |
| `/companies/[slug]` | Skor ternormalisasi + label (Green/Mixed/Red/"Belum cukup data" bila skor null), rincian per sinyal + bukti yang bisa diklik (+ tanggal bukti). |
| `/cara-menilai` | Rubrik, normalisasi, sumber bukti, batasan, disclaimer, cara minta koreksi. |

## Catatan

- Tanpa login untuk halaman publik (D8). Tanpa cookie pelacak.
- Jangan simpan credential/API key di repo ini — secret hanya di `.env`
  (tidak di-commit).
