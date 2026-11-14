# Rubrik Skor Green / Red Flag — v1 (draft)

Total 100 poin. Label: Green 70–100, Mixed 40–69, Red 0–39, Belum cukup data (<3 sinyal).

Lihat ARCHITECTURE.md §5 untuk prinsip: skor tanpa bukti tidak tampil.

## Kategori

- Transparansi lowongan (25): gaji dicantumkan, deskripsi jelas, tidak minta biaya.
  - Minta biaya pendaftaran = langsung Red + peringatan, apa pun skor lainnya.
- Reputasi & ulasan (25): rating Glassdoor/JobStreet/Google, keluhan berulang.
- Stabilitas & legalitas (20): umur perusahaan, terdaftar resmi, berita PHK/pailit.
- Praktik rekrutmen (15): ghost job (tayang >90 hari tanpa perubahan), respon lambat.
- Gaji & benefit (15): gaji vs UMR, BPJS disebut, benefit jelas.

## Aturan bukti

Setiap sinyal wajib: `evidence_url`, `evidence_date`, `source`, `confidence`.
Kutipan singkat saja, bukan salinan penuh. Perusahaan bisa minta koreksi.

*Detail per sinyal + contoh perhitungan menyusul di Fase 2, setelah 50 perusahaan pertama diuji.*
