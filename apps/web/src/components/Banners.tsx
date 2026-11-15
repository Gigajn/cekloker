export function MockBanner() {
  return (
    <div className="rounded-lg border border-amber-300 bg-amber-50 px-4 py-3 text-sm text-amber-900">
      <strong>Data contoh (mock).</strong> API CekLoker belum terhubung, jadi
      halaman ini menampilkan data contoh — bukan lowongan atau perusahaan
      nyata. Isi env <code className="rounded bg-amber-100 px-1">NEXT_PUBLIC_API_URL</code>{" "}
      dan jalankan API agar data asli tampil.
    </div>
  );
}

export function Disclaimer() {
  return (
    <p className="mt-3 text-xs leading-relaxed text-slate-500">
      Skor ini ringkasan sinyal publik, bukan penilaian hukum atau jaminan.
      Selalu cek langsung ke perusahaan sebelum memutuskan. Lihat{" "}
      <a href="/cara-menilai" className="text-teal-700 underline">
        cara kami menilai
      </a>
      .
    </p>
  );
}
