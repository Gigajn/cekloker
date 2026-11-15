import Link from "next/link";
import type { ReactNode } from "react";
import "./globals.css";

export const metadata = {
  title: "CekLoker — Lowongan aktif & Green/Red Flag perusahaan",
  description:
    "Lowongan yang masih buka beneran, sejak kapan, plus ringkasan sinyal publik perusahaan (Green/Mixed/Red) beserta buktinya.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="id">
      <body className="min-h-screen bg-slate-50 text-slate-900 antialiased">
        <header className="border-b border-slate-200 bg-white">
          <div className="mx-auto flex max-w-4xl flex-wrap items-center gap-x-6 gap-y-2 px-4 py-4">
            <Link href="/" className="text-xl font-bold text-teal-700">
              CekLoker
            </Link>
            <nav className="flex gap-4 text-sm font-medium text-slate-700">
              <Link href="/" className="hover:text-teal-700">
                Lowongan
              </Link>
              <Link href="/cara-menilai" className="hover:text-teal-700">
                Cara kami menilai
              </Link>
            </nav>
          </div>
        </header>

        <main className="mx-auto max-w-4xl px-4 py-8">{children}</main>

        <footer className="border-t border-slate-200 bg-white">
          <div className="mx-auto max-w-4xl px-4 py-6 text-sm text-slate-600">
            <p>
              <strong>CekLoker</strong> — alat pribadi (non-komersial) untuk
              memeriksa lowongan aktif dan sinyal publik perusahaan.
            </p>
            <p className="mt-2 text-xs leading-relaxed text-slate-500">
              Skor ini ringkasan sinyal publik, bukan penilaian hukum atau
              jaminan. Selalu cek langsung ke perusahaan sebelum memutuskan.
              Tidak ada data pribadi pelamar yang ditampilkan, dan tidak ada
              pelacakan pihak ketiga di situs ini.
            </p>
          </div>
        </footer>
      </body>
    </html>
  );
}
