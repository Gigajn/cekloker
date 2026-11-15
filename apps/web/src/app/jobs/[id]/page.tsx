import Link from "next/link";
import { notFound } from "next/navigation";
import { getJob } from "@/lib/api";
import { formatDate, formatDateTime, formatSalary, statusLabel, workTypeLabel } from "@/lib/format";
import { Disclaimer, MockBanner } from "@/components/Banners";

export const dynamic = "force-dynamic";

export default async function JobDetail({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const { data: job, isMock } = await getJob(id);
  if (!job) notFound();

  const isActive = job.status === "active";

  return (
    <div>
      {isMock ? <MockBanner /> : null}

      {!isActive ? (
        <div className="mt-4 rounded-lg border border-amber-300 bg-amber-50 px-4 py-3 text-sm text-amber-900">
          <strong>Peringatan:</strong> lowongan ini berstatus{" "}
          <strong>{statusLabel(job.status)}</strong> — kemungkinan sudah tidak
          menerima lamaran. Periksa tautan sumber sebelum melamar.
        </div>
      ) : null}

      <h1 className="mt-4 text-2xl font-bold">{job.title}</h1>
      <p className="mt-1 text-base">
        <Link href={`/companies/${job.company.slug}`} className="font-medium text-teal-700 hover:underline">
          {job.company.name}
        </Link>
        {job.location ? ` · ${job.location}` : ""} · {workTypeLabel(job.work_type)}
      </p>

      <dl className="mt-6 space-y-2 rounded-xl border border-slate-200 bg-white p-5 text-sm shadow-sm">
        <div className="flex gap-2">
          <dt className="w-44 shrink-0 text-slate-500">Status</dt>
          <dd className="font-medium">{statusLabel(job.status)}</dd>
        </div>
        <div className="flex gap-2">
          <dt className="w-44 shrink-0 text-slate-500">Gaji</dt>
          <dd className="font-medium">{formatSalary(job.salary_min, job.salary_max, job.salary_currency)}</dd>
        </div>
        <div className="flex gap-2">
          <dt className="w-44 shrink-0 text-slate-500">Dibuka (klaim sumber)</dt>
          <dd>
            {job.posted_at ? formatDate(job.posted_at) : "Tanggal sumber tidak tersedia"}
            {job.posted_at && !job.posted_at_certain ? (
              <span className="ml-2 rounded bg-amber-100 px-1.5 py-0.5 text-xs font-medium text-amber-800">
                perkiraan — tanggal ditulis sumber sebagai tanggal relatif
                (mis. &ldquo;1 bulan lalu&rdquo;)
              </span>
            ) : null}
          </dd>
        </div>
        <div className="flex gap-2">
          <dt className="w-44 shrink-0 text-slate-500">Pertama terlihat oleh kami</dt>
          <dd>{formatDateTime(job.first_seen_at)}</dd>
        </div>
        <div className="flex gap-2">
          <dt className="w-44 shrink-0 text-slate-500">Terakhir terlihat buka</dt>
          <dd>{formatDateTime(job.last_seen_at)}</dd>
        </div>
        {job.source ? (
          <div className="flex gap-2">
            <dt className="w-44 shrink-0 text-slate-500">Sumber</dt>
            <dd>{job.source}</dd>
          </div>
        ) : null}
      </dl>

      <p className="mt-4 text-sm text-slate-600">
        &ldquo;Dibuka&rdquo; adalah tanggal yang ditulis sumber; &ldquo;Pertama
        terlihat&rdquo; adalah kapan kami pertama kali melihat lowongan ini
        masih buka. Keduanya bisa berbeda — dan itu wajar.
      </p>

      {job.source_url ? (
        <p className="mt-4">
          <a
            href={job.source_url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-block rounded-lg bg-teal-700 px-4 py-2 text-sm font-semibold text-white hover:bg-teal-800"
          >
            Lihat lowongan di sumber asli ↗
          </a>
        </p>
      ) : (
        <p className="mt-4 text-sm text-slate-600">Tautan sumber asli tidak tersedia.</p>
      )}

      <p className="mt-6 text-sm">
        <Link href="/" className="text-teal-700 hover:underline">
          ← Kembali ke daftar lowongan
        </Link>
      </p>
      <Disclaimer />
    </div>
  );
}
