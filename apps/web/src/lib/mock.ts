// ---------------------------------------------------------------------------
// DATA CONTOH (MOCK) — HANYA dipakai bila API belum bisa dijangkau.
// Setiap halaman yang memakai data ini menampilkan spanduk "Data contoh
// (mock)". JANGAN pernah mengklaim data ini sebagai lowongan nyata.
// Lihat ADR-0010 W3. Hapus file ini (dan pemakaiannya di api.ts) begitu
// API sudah stabil — atau biarkan sebagai fallback berlabel.
// ---------------------------------------------------------------------------

import type { Company, Job, JobFilters } from "./types";

export const MOCK_COMPANIES: Company[] = [
  {
    id: "mock-c1",
    slug: "pt-maju-bersama",
    name: "PT Maju Bersama",
    score: 72,
    label: "Mixed",
    signals: [
      {
        category: "transparansi",
        key: "salary_transparency",
        points: 15,
        evidence_url: "https://contoh.invalid/lowongan/maju-bersama-1",
        evidence_text: "Gaji dicantumkan di 8 dari 10 lowongan.",
        evidence_date: "2026-11-10",
        source: "Glints",
        confidence: "high",
      },
      {
        category: "reputasi",
        key: "repeated_complaint_overtime",
        points: -15,
        evidence_url: "https://contoh.invalid/ulasan/maju-bersama",
        evidence_text: "Keluhan lembur berulang di 5 ulasan.",
        evidence_date: "2026-10-28",
        source: "JobStreet (entri manual)",
        confidence: "medium",
      },
      {
        category: "stabilitas",
        key: "company_age",
        points: 10,
        evidence_url: "https://contoh.invalid/berita/maju-bersama-ekspansi",
        evidence_text: "Berdiri 8 tahun; berita ekspansi dari 2 media.",
        evidence_date: "2026-09-15",
        source: "Google News RSS",
        confidence: "medium",
      },
    ],
  },
  {
    id: "mock-c2",
    slug: "pt-baru-jaya",
    name: "PT Baru Jaya",
    score: null,
    label: "Belum cukup data",
    signals: [
      {
        category: "transparansi",
        key: "salary_transparency",
        points: 5,
        evidence_url: "https://contoh.invalid/lowongan/baru-jaya-1",
        evidence_text: "Gaji dicantumkan di 1 dari 2 lowongan.",
        evidence_date: "2026-11-12",
        source: "Kalibrr",
        confidence: "low",
      },
    ],
  },
  {
    id: "mock-c3",
    slug: "pt-amanah-karya",
    name: "PT Amanah Karya",
    score: 85,
    label: "Green",
    signals: [
      {
        category: "transparansi",
        key: "salary_transparency",
        points: 15,
        evidence_url: "https://contoh.invalid/lowongan/amanah-karya-1",
        evidence_text: "Gaji dicantumkan di 9 dari 10 lowongan.",
        evidence_date: "2026-11-11",
        source: "Glints",
        confidence: "high",
      },
      {
        category: "reputasi",
        key: "high_rating",
        points: 15,
        evidence_url: "https://contoh.invalid/ulasan/amanah-karya",
        evidence_text: "Rating 4,4 dari 155 ulasan.",
        evidence_date: "2026-11-05",
        source: "JobStreet (entri manual)",
        confidence: "high",
      },
      {
        category: "gaji",
        key: "above_umr_bpjs",
        points: 10,
        evidence_url: "https://contoh.invalid/lowongan/amanah-karya-2",
        evidence_text: "Gaji di atas UMR dan BPJS disebut.",
        evidence_date: "2026-11-11",
        source: "Glints",
        confidence: "medium",
      },
    ],
  },
];

export const MOCK_JOBS: Job[] = [
  {
    id: "mock-j1",
    title: "Backend Engineer (Python)",
    company: { name: "PT Maju Bersama", slug: "pt-maju-bersama" },
    location: "Jakarta Selatan",
    work_type: "hybrid",
    salary_min: 8000000,
    salary_max: 12000000,
    salary_currency: "IDR",
    posted_at: "2026-11-10",
    posted_at_certain: true,
    first_seen_at: "2026-11-10T09:14:00+07:00",
    last_seen_at: "2026-11-15T08:00:00+07:00",
    status: "active",
    source: "Glints",
    source_url: "https://contoh.invalid/lowongan/maju-bersama-1",
  },
  {
    id: "mock-j2",
    title: "Staff Administrasi",
    company: { name: "PT Baru Jaya", slug: "pt-baru-jaya" },
    location: "Bandung",
    work_type: "onsite",
    salary_min: null,
    salary_max: null,
    salary_currency: "IDR",
    posted_at: "2026-10-12",
    posted_at_certain: false, // dari "1 bulan lalu" — perkiraan
    first_seen_at: "2026-11-12T10:02:00+07:00",
    last_seen_at: "2026-11-15T08:00:00+07:00",
    status: "active",
    source: "Kalibrr",
    source_url: "https://contoh.invalid/lowongan/baru-jaya-1",
  },
  {
    id: "mock-j3",
    title: "Frontend Engineer (React)",
    company: { name: "PT Amanah Karya", slug: "pt-amanah-karya" },
    location: "Remote (Indonesia)",
    work_type: "remote",
    salary_min: 10000000,
    salary_max: 15000000,
    salary_currency: "IDR",
    posted_at: "2026-11-13",
    posted_at_certain: true,
    first_seen_at: "2026-11-13T11:30:00+07:00",
    last_seen_at: "2026-11-15T08:00:00+07:00",
    status: "active",
    source: "Glints",
    source_url: "https://contoh.invalid/lowongan/amanah-karya-1",
  },
  {
    id: "mock-j4",
    title: "Sales Executive",
    company: { name: "PT Maju Bersama", slug: "pt-maju-bersama" },
    location: "Surabaya",
    work_type: "onsite",
    salary_min: 5000000,
    salary_max: 7000000,
    salary_currency: "IDR",
    posted_at: "2026-09-01",
    posted_at_certain: true,
    first_seen_at: "2026-09-02T09:00:00+07:00",
    last_seen_at: "2026-11-01T08:00:00+07:00",
    status: "closed",
    source: "Glints",
    source_url: "https://contoh.invalid/lowongan/maju-bersama-2",
  },
];

function companyScore(slug: string): number | null {
  return MOCK_COMPANIES.find((c) => c.slug === slug)?.score ?? null;
}

/** Filter data mock dengan aturan yang sama seperti filter di URL. */
export function filterMockJobs(filters: JobFilters): Job[] {
  const status = filters.status ?? "active";
  return MOCK_JOBS.filter((job) => {
    if (status !== "semua" && job.status !== status) return false;
    if (filters.q) {
      const q = filters.q.toLowerCase();
      const hay = `${job.title} ${job.company.name} ${job.location ?? ""}`.toLowerCase();
      if (!hay.includes(q)) return false;
    }
    if (filters.location && !(job.location ?? "").toLowerCase().includes(filters.location.toLowerCase()))
      return false;
    if (filters.posted_from && job.posted_at && job.posted_at < filters.posted_from) return false;
    if (filters.posted_to && job.posted_at && job.posted_at > filters.posted_to) return false;
    if (filters.salary_min) {
      const min = Number(filters.salary_min);
      if (!Number.isNaN(min) && (job.salary_min ?? job.salary_max ?? 0) < min) return false;
    }
    if (filters.score_min) {
      const min = Number(filters.score_min);
      const score = companyScore(job.company.slug);
      if (!Number.isNaN(min) && (score === null || score < min)) return false;
    }
    return true;
  });
}
