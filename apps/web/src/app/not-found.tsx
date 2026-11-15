import Link from "next/link";

export default function NotFound() {
  return (
    <div>
      <h1 className="text-2xl font-bold">Halaman tidak ditemukan</h1>
      <p className="mt-2 text-sm text-slate-600">
        Lowongan atau perusahaan yang dicari tidak ada — mungkin sudah dihapus
        atau tautannya salah.
      </p>
      <p className="mt-4 text-sm">
        <Link href="/" className="text-teal-700 hover:underline">
          ← Kembali ke daftar lowongan
        </Link>
      </p>
    </div>
  );
}
