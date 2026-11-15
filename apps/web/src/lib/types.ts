// Tipe data sesuai kontrak API (lihat ADR-0010). JANGAN ubah sepihak —
// bila kontrak berubah, ubah di sini + catat di ADR.

export type JobStatus = "active" | "closed" | "expired" | "unknown";

export type CompanyLabel = "Green" | "Mixed" | "Red" | "Belum cukup data";

export interface JobCompany {
  name: string;
  slug: string;
}

export interface Job {
  id: string;
  title: string;
  company: JobCompany;
  location: string | null;
  work_type: string | null;
  salary_min: number | null;
  salary_max: number | null;
  salary_currency: string | null;
  posted_at: string | null; // tanggal (YYYY-MM-DD) klaim sumber
  posted_at_certain: boolean;
  first_seen_at: string | null; // ISO timestamp, pengamatan kami
  last_seen_at: string | null; // ISO timestamp, pengamatan kami
  status: JobStatus;
  source: string | null;
  source_url: string | null;
}

export interface Signal {
  category: string;
  key: string;
  points: number;
  evidence_url: string | null;
  evidence_text: string | null;
  evidence_date: string | null;
  source: string | null;
  confidence: "high" | "medium" | "low" | string;
}

export interface Company {
  id: string;
  slug: string;
  name: string;
  /** null = belum cukup data (jangan tampilkan skor palsu). */
  score: number | null;
  label: CompanyLabel;
  signals: Signal[];
  /** Kategori yang terukur menurut API (ADR-0010 K-W1). Opsional. */
  measured_categories?: string[];
  /** Jumlah sinyal penentu (ADR-0010 K-W1). Opsional. */
  decisive_signals?: number;
  /** True bila ada sinyal red override, mis. permintaan biaya. */
  red_override?: boolean;
  /** Peringatan keselamatan dari API (mis. permintaan biaya). */
  warnings?: string[];
}

export interface JobFilters {
  q?: string;
  posted_from?: string;
  posted_to?: string;
  location?: string;
  salary_min?: string;
  score_min?: string;
  status?: string;
}
