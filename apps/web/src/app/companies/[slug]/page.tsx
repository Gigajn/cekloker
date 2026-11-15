import Link from "next/link";
import { notFound } from "next/navigation";
import { getCompany } from "@/lib/api";
import { categoryLabel, formatDate } from "@/lib/format";
import { Disclaimer, MockBanner } from "@/components/Banners";
import { ScoreBadge } from "@/components/ScoreBadge";

export const dynamic = "force-dynamic";

const CONFIDENCE_LABEL: Record<string, string> = {
  high: "Kepercayaan tinggi",
  medium: "Kepercayaan sedang",
  low: "Kepercayaan rendah",
};

export default async function CompanyProfile({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const { data: company, isMock } = await getCompany(slug);
  if (!company) notFound();

  const hasEnoughData = company.score !== null && company.label !== "Belum cukup data";
  const categories = [...new Set(company.signals.map((s) => s.category))];
  // Kategori terukur menurut API bila ada (ADR-0010 K-W1); kalau API lama
  // tidak mengirimnya, turun ke kategori yang ada di sinyal.
  const measured =
    company.measured_categories && company.measured_categories.length > 0
      ? company.measured_categories
      : categories;
  // Peringatan biaya dari API (warnings + red_override) — bukan heuristik
  // pencocokan kata di sisi web (ADR-0010 K-W4, amandemen koordinator).
  const warnings = company.warnings ?? [];
  const feeWarning = company.red_override === true || warnings.length > 0;
  const byCategory = new Map<string, typeof company.signals>();
  for (const s of company.signals) {
    const list = byCategory.get(s.category) ?? [];
    list.push(s);
    byCategory.set(s.category, list);
  }

  return (
    <div>
      {isMock ? <MockBanner /> : null}

      <h1 className="mt-4 text-2xl font-bold">{company.name}</h1>

      <div className="mt-3">
        <ScoreBadge score={company.score} label={company.label} size="lg" />
      </div>

      {!hasEnoughData ? (
        <div className="mt-4 rounded-lg border border-slate-300 bg-white px-4 py-3 text-sm text-slate-700">
          <strong>Belum cukup data.</strong> Kami belum punya cukup sinyal
          terukur (minimal 3 sinyal penentu dari 2 kategori berbeda) untuk
          memberi skor pada perusahaan ini. Ini artinya &ldquo;kami belum
          tahu&rdquo; — <strong>bukan</strong> &ldquo;perusahaan ini buruk&rdquo;.
          Sinyal yang sudah ada ditampilkan di bawah sebagai konteks.
        </div>
      ) : (
        <p className="mt-3 text-sm text-slate-600">
          Skor ternormalisasi dari {measured.length} kategori terukur (
          {measured.map(categoryLabel).join(", ")}). Skor dihitung hanya
          dari kategori yang sudah terukur — kategori yang belum diukur tidak
          dihitung sebagai nilai buruk.{" "}
          <Link href="/cara-menilai" className="text-teal-700 underline">
            Pelajari cara kami menilai
          </Link>
        </p>
      )}

      {feeWarning ? (
        <div className="mt-4 rounded-lg border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-900">
          <strong>Perhatian:</strong>{" "}
          {warnings.length > 0
            ? warnings[0]
            : "Ada sinyal permintaan biaya pada perusahaan ini."}{" "}
          Periksa buktinya di bawah sebelum melamar atau membayar apa pun.
          Jangan membayar biaya pendaftaran apa pun.
        </div>
      ) : null}

      <h2 className="mt-8 text-xl font-semibold">Rincian sinyal + bukti</h2>
      {company.signals.length === 0 ? (
        <p className="mt-2 text-sm text-slate-600">
          Belum ada sinyal yang tercatat untuk perusahaan ini.
        </p>
      ) : (
        [...byCategory.entries()].map(([category, signals]) => (
          <section key={category} className="mt-4">
            <h3 className="text-base font-semibold">{categoryLabel(category)}</h3>
            <ul className="mt-2 space-y-3">
              {signals.map((s, i) => (
                <li
                  key={`${s.key}-${i}`}
                  className="rounded-xl border border-slate-200 bg-white p-4 text-sm shadow-sm"
                >
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="font-medium">{s.key.replace(/_/g, " ")}</span>
                    <span
                      className={
                        s.points >= 0
                          ? "rounded-full bg-emerald-100 px-2 py-0.5 text-xs font-semibold text-emerald-800"
                          : "rounded-full bg-red-100 px-2 py-0.5 text-xs font-semibold text-red-800"
                      }
                    >
                      {s.points >= 0 ? `+${s.points}` : s.points} poin
                    </span>
                    <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs text-slate-600">
                      {CONFIDENCE_LABEL[s.confidence] ?? s.confidence}
                    </span>
                  </div>
                  {s.evidence_text ? (
                    <p className="mt-2 text-slate-700">&ldquo;{s.evidence_text}&rdquo;</p>
                  ) : null}
                  <p className="mt-2 text-xs text-slate-500">
                    Sumber: {s.source ?? "tidak diketahui"}
                    {s.evidence_date ? ` · Tanggal bukti: ${formatDate(s.evidence_date)}` : ""}
                  </p>
                  {s.evidence_url ? (
                    <p className="mt-1 text-sm">
                      <a
                        href={s.evidence_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-teal-700 hover:underline"
                      >
                        Lihat bukti ↗
                      </a>
                    </p>
                  ) : (
                    <p className="mt-1 text-xs font-medium text-amber-700">
                      ⚠ Sinyal ini tidak punya tautan bukti — perlakukan dengan hati-hati.
                    </p>
                  )}
                </li>
              ))}
            </ul>
          </section>
        ))
      )}

      <h2 className="mt-8 text-xl font-semibold">Minta koreksi</h2>
      <p className="mt-2 text-sm leading-relaxed text-slate-700">
        Perusahaan yang merasa datanya salah dapat meminta koreksi dengan
        mengirim bukti yang bisa diverifikasi ke pengelola CekLoker. Sinyal
        yang disengketakan ditangguhkan (tidak memengaruhi skor) dan diberi
        label &ldquo;disengketakan — sedang ditinjau&rdquo; sampai diputuskan,
        paling lambat 7 hari. Penghapusan hanya bila bukti salah, kedaluwarsa,
        atau melanggar aturan — bukan karena perusahaan tidak suka.
        Form koreksi online belum tersedia di versi ini; prosesnya
        dijelaskan lengkap di{" "}
        <Link href="/cara-menilai" className="text-teal-700 underline">
          halaman cara kami menilai
        </Link>
        .
      </p>

      <Disclaimer />
    </div>
  );
}
