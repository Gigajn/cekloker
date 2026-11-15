// Lapisan akses API. Satu-satunya file yang tahu soal HTTP ke FastAPI.
// Bila API tidak bisa dijangkau, kembalikan data mock BERLABEL (isMock: true)
// — jangan pernah lempar error mentah ke halaman. Lihat ADR-0010 W3.
//
// Kontrak yang dipegang (jangan diubah sepihak — lihat ADR-0010 K-W1..K-W6):
//   base  = NEXT_PUBLIC_API_URL (default http://localhost:8000)
//   list  = GET {base}/api/v1/jobs?status=...&posted_from=...&posted_to=...
//             &location=...&salary_min=...&score_min=...&q=...
//           -> array Job, atau { items: Job[], total: number }
//   job   = GET {base}/api/v1/jobs/{id}            -> Job
//   company = GET {base}/api/v1/companies/{slug}  -> Company

import { filterMockJobs, MOCK_COMPANIES, MOCK_JOBS } from "./mock";
import type { Company, Job, JobFilters } from "./types";

export interface ApiResult<T> {
  data: T;
  /** true bila data berasal dari mock lokal, bukan API. */
  isMock: boolean;
}

function apiBase(): string {
  const raw = process.env.NEXT_PUBLIC_API_URL ?? "";
  return raw.replace(/\/+$/, "") || "http://localhost:8000";
}

async function fetchJson<T>(path: string): Promise<T> {
  const res = await fetch(`${apiBase()}${path}`, {
    // Gagal cepat: API lokal yang mati tidak boleh menggantung render.
    signal: AbortSignal.timeout(5000),
    headers: { Accept: "application/json" },
  });
  if (!res.ok) throw new Error(`API ${res.status} untuk ${path}`);
  return (await res.json()) as T;
}

function buildQuery(filters: JobFilters): string {
  const params = new URLSearchParams();
  const status = filters.status ?? "active";
  params.set("status", status);
  if (filters.q) params.set("q", filters.q);
  if (filters.posted_from) params.set("posted_from", filters.posted_from);
  if (filters.posted_to) params.set("posted_to", filters.posted_to);
  if (filters.location) params.set("location", filters.location);
  if (filters.salary_min) params.set("salary_min", filters.salary_min);
  if (filters.score_min) params.set("score_min", filters.score_min);
  return params.toString();
}

export async function getJobs(filters: JobFilters): Promise<ApiResult<Job[]>> {
  try {
    const raw = await fetchJson<Job[] | { items: Job[]; total: number }>(
      `/api/v1/jobs?${buildQuery(filters)}`,
    );
    const jobs = Array.isArray(raw) ? raw : raw.items ?? [];
    return { data: jobs, isMock: false };
  } catch {
    // API belum jalan / belum ada: fallback mock berlabel.
    return { data: filterMockJobs(filters), isMock: true };
  }
}

export async function getJob(id: string): Promise<ApiResult<Job | null>> {
  try {
    const job = await fetchJson<Job>(`/api/v1/jobs/${encodeURIComponent(id)}`);
    return { data: job, isMock: false };
  } catch {
    return { data: MOCK_JOBS.find((j) => j.id === id) ?? null, isMock: true };
  }
}

export async function getCompany(slug: string): Promise<ApiResult<Company | null>> {
  try {
    const company = await fetchJson<Company>(
      `/api/v1/companies/${encodeURIComponent(slug)}`,
    );
    return { data: company, isMock: false };
  } catch {
    return {
      data: MOCK_COMPANIES.find((c) => c.slug === slug) ?? null,
      isMock: true,
    };
  }
}
