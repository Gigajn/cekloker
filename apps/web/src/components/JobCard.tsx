import Link from "next/link";
import { formatDate, formatDateTime, formatSalary, statusLabel, workTypeLabel } from "@/lib/format";
import type { Job } from "@/lib/types";

export function JobCard({ job }: { job: Job }) {
  return (
    <article className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-start justify-between gap-3">
        <h2 className="text-lg font-semibold text-slate-900">
          <Link href={`/jobs/${job.id}`} className="hover:underline">
            {job.title}
          </Link>
        </h2>
        <span
          className={
            job.status === "active"
              ? "shrink-0 rounded-full bg-emerald-100 px-2.5 py-1 text-xs font-semibold text-emerald-800"
              : "shrink-0 rounded-full bg-slate-200 px-2.5 py-1 text-xs font-semibold text-slate-700"
          }
        >
          {statusLabel(job.status)}
        </span>
      </div>

      <p className="mt-1 text-sm text-slate-700">
        <Link href={`/companies/${job.company.slug}`} className="font-medium text-teal-700 hover:underline">
          {job.company.name}
        </Link>
        {job.location ? ` · ${job.location}` : ""} · {workTypeLabel(job.work_type)}
      </p>

      <p className="mt-2 text-sm font-medium text-slate-900">
        {formatSalary(job.salary_min, job.salary_max, job.salary_currency)}
      </p>

      <dl className="mt-3 space-y-1 text-sm text-slate-600">
        <div className="flex gap-2">
          <dt className="w-36 shrink-0 text-slate-500">Dibuka (klaim sumber)</dt>
          <dd>
            {job.posted_at ? formatDate(job.posted_at) : "Tanggal sumber tidak tersedia"}
            {job.posted_at && !job.posted_at_certain ? (
              <span className="ml-2 rounded bg-amber-100 px-1.5 py-0.5 text-xs font-medium text-amber-800">
                perkiraan
              </span>
            ) : null}
          </dd>
        </div>
        <div className="flex gap-2">
          <dt className="w-36 shrink-0 text-slate-500">Pertama terlihat</dt>
          <dd>{formatDateTime(job.first_seen_at)}</dd>
        </div>
        {job.source ? (
          <div className="flex gap-2">
            <dt className="w-36 shrink-0 text-slate-500">Sumber</dt>
            <dd>{job.source}</dd>
          </div>
        ) : null}
      </dl>

      <p className="mt-3">
        <Link href={`/jobs/${job.id}`} className="text-sm font-medium text-teal-700 hover:underline">
          Lihat detail →
        </Link>
      </p>
    </article>
  );
}
