import type { CompanyLabel } from "@/lib/types";

const STYLE: Record<CompanyLabel, string> = {
  Green: "bg-emerald-100 text-emerald-800",
  Mixed: "bg-amber-100 text-amber-800",
  Red: "bg-red-100 text-red-800",
  "Belum cukup data": "bg-slate-200 text-slate-700",
};

export function ScoreBadge({
  score,
  label,
  size = "md",
}: {
  score: number | null;
  label: CompanyLabel;
  size?: "md" | "lg";
}) {
  if (score === null || label === "Belum cukup data") {
    return (
      <span
        className={`inline-block rounded-full px-3 py-1 font-semibold ${STYLE["Belum cukup data"]} ${
          size === "lg" ? "text-base" : "text-xs"
        }`}
      >
        Belum cukup data
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-2">
      <span
        className={`inline-block rounded-full px-3 py-1 font-bold ${STYLE[label]} ${
          size === "lg" ? "text-xl" : "text-sm"
        }`}
      >
        {score}/100
      </span>
      <span
        className={`inline-block rounded-full px-3 py-1 font-semibold ${STYLE[label]} ${
          size === "lg" ? "text-base" : "text-xs"
        }`}
      >
        {label}
      </span>
    </span>
  );
}
