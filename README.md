# CekLoker

Website pencari kerja yang menjawab dua hal sebelum melamar:
**lowongan ini masih buka beneran, sejak kapan?** dan **perusahaan ini green flag atau red flag?**

> Status: Fase 0 — Blueprint. Lihat [ARCHITECTURE.md](ARCHITECTURE.md) untuk arsitektur lengkap.

## Janji produk

1. **Status aktif diverifikasi** — `posted_at` dari sumber + `first_seen_at` / `last_seen_at` dari scraper kami. Lowongan yang sudah hilang tidak terus tampil sebagai "masih buka".
2. **Skor transparan** — setiap poin skor punya bukti yang bisa diklik (link + tanggal). Tidak ada skor tanpa bukti.
3. **Murah & open source** — modular monolith, Docker Compose, MIT (rencana).

## Stack (v1)

- **Backend + scraper:** Python 3.12 + FastAPI + Playwright / httpx
- **Frontend:** TypeScript + Next.js + Tailwind
- **DB:** PostgreSQL 16 · **Queue/cache:** Redis · **Snapshot:** S3-compatible storage

## Jalankan (rencana, setelah Fase 1)

```bash
cp .env.example .env
docker compose up
# web: http://localhost:3000  |  api: http://localhost:8000/docs
```

## Struktur

```
apps/web/              # Next.js
apps/api/              # FastAPI
packages/scraper-core/ # Adapter per sumber lowongan
packages/flag-engine/  # Aturan skor Green/Red Flag (rule-based v1)
infra/                 # docker-compose, Caddy
docs/                  # SCORING.md, ADAPTER_GUIDE.md, LEGAL.md
```

## Legal & etika

Patuhi `robots.txt` dan ToS sumber, jangan bypass login/paywall, jangan simpan data pribadi pelamar. Lihat `ARCHITECTURE.md` §8 dan `docs/LEGAL.md` (segera).

## Lisensi

MIT (rencana saat dibuka publik — Fase 5).
