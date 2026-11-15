-- CekLoker — migrasi awal 001 (PostgreSQL 16)
-- Cerminan ARCHITECTURE.md §4 + ADR-0009 (perubahan dicatat di bawah).
-- Jalankan: psql "$DATABASE_URL" -f migrations/001_init.sql
--          (atau: docker compose exec postgres psql -U postgres -d loker_greenflag -f /migrations/001_init.sql)
-- Idempotent: aman dijalankan 2x (IF NOT EXISTS / ON CONFLICT DO NOTHING).
--
-- Penyimpangan dari ARCH §4 (lihat ADR-0009):
--  * companies.aliases: jsonb, bukan text[] — supaya model SQLAlchemy
--    yang sama jalan di SQLite (test) dan Postgres.
--  * jobs.missed_checks (int) + jobs.board_url (text, nullable) — tambahan
--    untuk aturan 2x kunjungan hilang (ARCH §3) dan recheck ATS.
--  * jobs.posted_at_certain (boolean) — flag kepastian tanggal (ADR-0002).
--  * signals.value: jsonb, bukan numeric — nilai sinyal bisa dict/bool.
--  * signals.decisive + red_override — dibaca flag-engine (ADR-0005).
--  * Tabel sources, admin_users, admin_sessions — tambahan ADR-0009.

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS companies (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name text NOT NULL,
  slug text NOT NULL UNIQUE,
  aliases jsonb NOT NULL DEFAULT '[]'::jsonb,
  website text,
  linkedin_url text,
  glassdoor_url text,
  industry text,
  size_range text,
  location_hq text,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_companies_slug ON companies (slug);

CREATE TABLE IF NOT EXISTS sources (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  slug text NOT NULL UNIQUE,
  name text NOT NULL,
  enabled boolean NOT NULL DEFAULT true,
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_sources_slug ON sources (slug);

CREATE TABLE IF NOT EXISTS jobs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  company_id uuid NOT NULL REFERENCES companies (id),
  source_id uuid NOT NULL REFERENCES sources (id),
  source_url text NOT NULL UNIQUE,
  board_url text,
  title text NOT NULL,
  location text NOT NULL DEFAULT '',
  work_type text NOT NULL DEFAULT '' CHECK (work_type IN ('','onsite','hybrid','remote')),
  salary_min int,
  salary_max int,
  salary_currency text NOT NULL DEFAULT 'IDR',
  posted_at date,
  posted_at_certain boolean NOT NULL DEFAULT true,
  expires_at date,
  first_seen_at timestamptz NOT NULL DEFAULT now(),
  last_seen_at timestamptz NOT NULL DEFAULT now(),
  status text NOT NULL DEFAULT 'active'
    CHECK (status IN ('active','closed','expired','unknown')),
  missed_checks int NOT NULL DEFAULT 0,
  description_text text NOT NULL DEFAULT '',
  fingerprint text NOT NULL DEFAULT '',
  raw_snapshot_key text,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_jobs_company ON jobs (company_id);
CREATE INDEX IF NOT EXISTS ix_jobs_source ON jobs (source_id);
CREATE INDEX IF NOT EXISTS ix_jobs_status ON jobs (status);
CREATE INDEX IF NOT EXISTS ix_jobs_fingerprint ON jobs (fingerprint);
CREATE INDEX IF NOT EXISTS ix_jobs_status_posted ON jobs (status, posted_at);

CREATE TABLE IF NOT EXISTS job_snapshots (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  job_id uuid NOT NULL REFERENCES jobs (id),
  seen_at timestamptz NOT NULL DEFAULT now(),
  status text NOT NULL,
  snapshot_key text,
  hash text
);
CREATE INDEX IF NOT EXISTS ix_job_snapshots_job ON job_snapshots (job_id);

CREATE TABLE IF NOT EXISTS signals (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  company_id uuid NOT NULL REFERENCES companies (id),
  category text NOT NULL,
  key text NOT NULL,
  value jsonb,
  points int NOT NULL DEFAULT 0,
  evidence_url text NOT NULL,
  -- K4 (fase1-konsolidasi.md §3) + ADR-0006: evidence_text NULLABLE,
  -- dan untuk sumber google_places WAJIB kosong (Places API melarang
  -- menyimpan teks ulasan — hanya rating, jumlah, place_id, tautan).
  evidence_text text,
  evidence_date date,
  source text NOT NULL,
  confidence text NOT NULL DEFAULT 'medium'
    CHECK (confidence IN ('high','medium','low')),
  decisive boolean NOT NULL DEFAULT false,
  red_override boolean NOT NULL DEFAULT false,
  notes text NOT NULL DEFAULT '',
  created_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT ck_signals_google_places_no_text
    CHECK (source <> 'google_places' OR evidence_text IS NULL)
);
CREATE INDEX IF NOT EXISTS ix_signals_company ON signals (company_id);
CREATE INDEX IF NOT EXISTS ix_signals_company_category ON signals (company_id, category);

CREATE TABLE IF NOT EXISTS admin_users (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  email text NOT NULL UNIQUE,
  password_hash text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_admin_users_email ON admin_users (email);

CREATE TABLE IF NOT EXISTS admin_sessions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL REFERENCES admin_users (id),
  token_hash text NOT NULL UNIQUE,
  expires_at timestamptz NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_admin_sessions_token ON admin_sessions (token_hash);

-- Sumber Fase 1 (status sesuai fase1-konsolidasi.md §6).
INSERT INTO sources (slug, name, enabled) VALUES
  ('glints', 'Glints', true),
  ('kalibrr', 'Kalibrr', true),
  ('jobstreet', 'JobStreet', false),
  ('indeed', 'Indeed', false),
  ('career-greenhouse', 'Greenhouse (halaman karier)', true),
  ('career-lever', 'Lever (halaman karier)', true),
  ('career-ashby', 'Ashby (halaman karier)', true),
  ('career-workable', 'Workable (halaman karier)', true),
  ('career-custom', 'Halaman karier custom (JSON-LD)', true)
ON CONFLICT (slug) DO NOTHING;
