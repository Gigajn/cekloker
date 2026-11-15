import { getJobs } from "@/lib/api";
import type { JobFilters } from "@/lib/types";
import { Disclaimer, MockBanner } from "@/components/Banners";
import { JobCard } from "@/components/JobCard";

export const dynamic = "force-dynamic";

type SearchParams = Record<string, string | string[] | undefined>;

function first(v: string | string[] | undefined): string | undefined {
  return Array.isArray(v) ? v[0] : v;
}

export default async function Home({
  searchParams,
}: {
  searchParams: Promise<SearchParams>;
}) {
  const sp = await searchParams;
  const filters: JobFilters = {
    q: first(sp.q),
    posted_from: first(sp.posted_from),
    posted_to: first(sp.posted_to),
    location: first(sp.location),
    salary_min: first(sp.salary_min),
    score_min: first(sp.score_min),
    status: first(sp.status) ?? "active",
  };

  const { data: jobs, isMock } = await getJobs(filters);
  const status = filters.status ?? "active";

  return (
    <div>
      <h1 className="text-2xl font-bold">Lowongan yang masih buka</h1>
      <p className="mt-1 text-sm text-slate-600">
        Hanya lowongan yang terakhir terlihat masih aktif yang tampil secara
        default. Tanggal buka ditampilkan apa adanya dari sumber — beserta
        kapan pertama kali kami melihatnya.
      </p>

      {isMock ? (
        <div className="mt-4">
          <MockBanner />
        </div>
      ) : null}

      <form method="get" className="mt-6 rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
        <div className="grid gap-3 sm:grid-cols-2">
          <label className="block text-sm font-medium text-slate-700">
            Pencarian teks
            <input
              type="search"
              name="q"
              defaultValue={filters.q ?? ""}
              placeholder="Judul, perusahaan, atau lokasi"
              className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 font-normal"
            />
          </label>
          <label className="block text-sm font-medium text-slate-700">
            Lokasi
            <input
              type="text"
              name="location"
              defaultValue={filters.location ?? ""}
              placeholder="mis. Jakarta"
              className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 font-normal"
            />
          </label>
          <label className="block text-sm font-medium text-slate-700">
            Dibuka dari tanggal
            <input
              type="date"
              name="posted_from"
              defaultValue={filters.posted_from ?? ""}
              className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 font-normal"
            />
          </label>
          <label className="block text-sm font-medium text-slate-700">
            Dibuka sampai tanggal
            <input
              type="date"
              name="posted_to"
              defaultValue={filters.posted_to ?? ""}
              className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 font-normal"
            />
          </label>
          <label className="block text-sm font-medium text-slate-700">
            Gaji minimum (Rp/bulan)
            <input
              type="number"
              name="salary_min"
              min={0}
              step={100000}
              defaultValue={filters.salary_min ?? ""}
              placeholder="mis. 5000000"
              className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 font-normal"
            />
          </label>
          <label className="block text-sm font-medium text-slate-700">
            Skor perusahaan minimum (0–100)
            <input
              type="number"
              name="score_min"
              min={0}
              max={100}
              defaultValue={filters.score_min ?? ""}
              placeholder="mis. 70"
              className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 font-normal"
            />
          </label>
          <label className="block text-sm font-medium text-slate-700">
            Status lowongan
            <select
              name="status"
              defaultValue={status}
              className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 font-normal"
            >
              <option value="active">Aktif</option>
              <option value="semua">Semua status</option>
              <option value="closed">Ditutup</option>
              <option value="expired">Kedaluarsa</option>
              <option value="unknown">Tidak diketahui</option>
            </select>
          </label>
        </div>
        <div className="mt-4 flex gap-3">
          <button
            type="submit"
            className="rounded-lg bg-teal-700 px-4 py-2 text-sm font-semibold text-white hover:bg-teal-800"
          >
            Terapkan filter
          </button>
          <a
            href="/"
            className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-100"
          >
            Reset
          </a>
        </div>
      </form>

      <p className="mt-6 text-sm text-slate-600" aria-live="polite">
        {jobs.length === 0
          ? "Tidak ada lowongan yang cocok dengan filter ini."
          : `${jobs.length} lowongan ditemukan.`}
      </p>

      {jobs.length === 0 ? (
        <div className="mt-4 rounded-xl border border-dashed border-slate-300 bg-white p-6 text-sm text-slate-600">
          Coba longgarkan filter (mis. hapus skor minimum atau rentang
          tanggal), atau pilih status &ldquo;Semua status&rdquo; untuk melihat
          lowongan yang sudah ditutup.
        </div>
      ) : (
        <div className="mt-4 grid gap-4">
          {jobs.map((job) => (
            <JobCard key={job.id} job={job} />
          ))}
        </div>
      )}

      <Disclaimer />
    </div>
  );
}
