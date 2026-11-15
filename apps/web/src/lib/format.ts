// Format tampilan: rupiah + tanggal Indonesia.
// Tanggal-only (YYYY-MM-DD) diparse manual supaya tidak bergeser zona waktu.

const BULAN = [
  "Januari", "Februari", "Maret", "April", "Mei", "Juni",
  "Juli", "Agustus", "September", "Oktober", "November", "Desember",
];

export function formatDate(value: string | null): string {
  if (!value) return "—";
  const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(value);
  if (m) {
    const [, y, mo, d] = m;
    return `${parseInt(d, 10)} ${BULAN[parseInt(mo, 10) - 1]} ${y}`;
  }
  const dt = new Date(value);
  if (Number.isNaN(dt.getTime())) return value;
  return `${dt.getDate()} ${BULAN[dt.getMonth()]} ${dt.getFullYear()}`;
}

export function formatDateTime(value: string | null): string {
  if (!value) return "—";
  const dt = new Date(value);
  if (Number.isNaN(dt.getTime())) return formatDate(value);
  const jam = dt.toLocaleTimeString("id-ID", {
    hour: "2-digit",
    minute: "2-digit",
    timeZone: "Asia/Jakarta",
  });
  return `${formatDate(value)}, ${jam} WIB`;
}

export function formatSalary(
  min: number | null,
  max: number | null,
  currency: string | null,
): string {
  if (min == null && max == null) return "Gaji tidak dicantumkan";
  const cur = currency && currency !== "IDR" ? `${currency} ` : "Rp";
  const fmt = (n: number) => `${cur}${n.toLocaleString("id-ID")}`;
  if (min != null && max != null) {
    return min === max ? fmt(min) : `${fmt(min)} – ${fmt(max)}`;
  }
  if (min != null) return `Mulai ${fmt(min)}`;
  return `Sampai ${fmt(max as number)}`;
}

export function statusLabel(status: string): string {
  switch (status) {
    case "active":
      return "Aktif";
    case "closed":
      return "Ditutup";
    case "expired":
      return "Kedaluarsa";
    case "unknown":
      return "Tidak diketahui";
    default:
      return status;
  }
}

export function workTypeLabel(workType: string | null): string {
  if (!workType) return "—";
  switch (workType.toLowerCase()) {
    case "onsite":
      return "Onsite";
    case "hybrid":
      return "Hybrid";
    case "remote":
      return "Remote";
    default:
      return workType;
  }
}

/** Label kategori sinyal yang ramah dibaca (fallback: nama kategori apa adanya). */
export function categoryLabel(category: string): string {
  const map: Record<string, string> = {
    transparansi: "Transparansi lowongan",
    reputasi: "Reputasi & ulasan",
    stabilitas: "Stabilitas & legalitas",
    rekrutmen: "Praktik rekrutmen",
    gaji: "Gaji & benefit",
  };
  return map[category.toLowerCase()] ?? category;
}
