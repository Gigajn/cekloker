"""Parser bersama: gaji IDR, tanggal (relatif + absolut), nama perusahaan.

Semua fungsi PURE (tidak ada I/O) sehingga mudah diuji unit test.
Tanggal relatif dihitung terhadap `ref_date` (tanggal fetch, zona
Asia/Jakarta) — dan hasilnya SELALU perkiraan: "1 bulan lalu" tidak
bisa dipastikan ke tanggal kalender (lihat ADR-0002, grill G3).
Karena itu `parse_posted_at` mengembalikan (date|None, pasti: bool).
"""

from __future__ import annotations

import re
from datetime import date, timedelta
from typing import Optional

# ---------------------------------------------------------------------------
# Gaji
# ---------------------------------------------------------------------------

# "Rp5–8 jt", "Rp 5 jt - 8 jt", "IDR 5.000.000", "Rp 22.000.000 – Rp 32.000.000"
_JUTA = re.compile(
    r"(?:rp|idr)?\s*(\d+(?:[.,]\d+)?)\s*(?:jt|juta)\b", re.IGNORECASE
)
_RUPIAH = re.compile(r"(?:rp|idr)?\s*(\d{1,3}(?:[.,]\d{3})+|\d+)", re.IGNORECASE)
_PERIODE = re.compile(r"/\s*(bulan|month|tahun|year|minggu|week|hari|day)",
                      re.IGNORECASE)
_TIDAK_DICANTUMKAN = re.compile(
    r"tidak\s+dicantumkan|not\s+disclosed|rahasia|confidential|"
    r"gaji\s+dirundingkan|negotiable",
    re.IGNORECASE,
)


def _angka_idr(teks: str) -> list[int]:
    """Ambil semua angka rupiah dari teks, kembalikan list int.

    "5,5 jt" -> 5_500_000. "5.000.000" -> 5_000_000.
    Angka polos < 1000 tanpa penanda jt diasumsikan BUKAN gaji
    (mis. "2 lowongan") dan diabaikan oleh pemanggil.
    """
    hasil: list[int] = []
    for m in _JUTA.finditer(teks):
        mentah = m.group(1).replace(",", ".")
        try:
            hasil.append(int(round(float(mentah) * 1_000_000)))
        except ValueError:
            continue
    sisa = _JUTA.sub(" ", teks)
    for m in _RUPIAH.finditer(sisa):
        mentah = m.group(1).replace(".", "").replace(",", "")
        try:
            nilai = int(mentah)
        except ValueError:
            continue
        if nilai >= 1000:  # di bawah Rp1.000 bukan gaji bulanan
            hasil.append(nilai)
    return hasil


def parse_salary(teks: str) -> tuple[Optional[int], Optional[int], str]:
    """Parse teks gaji -> (min, max, currency).

    Contoh:
    - "Rp5–8 jt" -> (5_000_000, 8_000_000, "IDR")
    - "IDR 5.000.000" -> (5_000_000, 5_000_000, "IDR")
    - "Rp 22.000.000 – Rp 32.000.000 per month" -> (22jt, 32jt, "IDR")
    - "Rp 5.000.000/bulan" -> (5jt, 5jt, "IDR")
    - "Tidak dicantumkan" / "" -> (None, None, "IDR")
    - "$1,000 - $1,500" -> (1000, 1500, "USD")  (untuk sumber global)
    - "SGD 3.000" -> (3000, 3000, "SGD")

    Aturan keras: kalau tidak ada angka yang jelas, kembalikan None —
    JANGAN menebak gaji dari judul atau UMR.
    """
    if not teks or not teks.strip():
        return None, None, "IDR"
    if _TIDAK_DICANTUMKAN.search(teks):
        return None, None, "IDR"

    # Rentang "Rp5–8 jt": sebar satuan ke kedua sisi ("Rp5 jt 8 jt")
    # supaya tiap angka tertangkap parser juta di bawah.
    teks = re.sub(r"(\d+(?:[.,]\d+)?)\s*[-–—]\s*(\d+(?:[.,]\d+)?)\s*(jt|juta)",
                  r"\1 \3 \2 \3", teks, flags=re.IGNORECASE)

    mata_uang = "IDR"
    m_cur = re.search(r"\b(USD|SGD|MYR|PHP|EUR|GBP|AUD)\b", teks, re.IGNORECASE)
    if m_cur:
        mata_uang = m_cur.group(1).upper()
    elif "$" in teks:
        mata_uang = "USD"

    angka = _angka_idr(teks)
    if not angka:
        return None, None, mata_uang
    if len(angka) == 1:
        return angka[0], angka[0], mata_uang
    lo, hi = min(angka), max(angka)
    return lo, hi, mata_uang


def salary_period(teks: str) -> str:
    """Periode gaji: "month" | "year" | "week" | "day" | "" (tak diketahui)."""
    m = _PERIODE.search(teks or "")
    if not m:
        return ""
    kata = m.group(1).lower()
    return {
        "bulan": "month", "month": "month",
        "tahun": "year", "year": "year",
        "minggu": "week", "week": "week",
        "hari": "day", "day": "day",
    }[kata]


# ---------------------------------------------------------------------------
# Tanggal posting
# ---------------------------------------------------------------------------

_BULAN_ID = {
    "jan": 1, "januari": 1, "feb": 2, "februari": 2, "mar": 3, "maret": 3,
    "apr": 4, "april": 4, "mei": 5, "may": 5, "jun": 6, "juni": 6,
    "jul": 7, "juli": 7, "agu": 8, "agustus": 8, "aug": 8,
    "sep": 9, "september": 9, "okt": 10, "oktober": 10, "oct": 10,
    "nov": 11, "november": 11, "des": 12, "desember": 12, "dec": 12,
}

_RELATIF = [
    # (pola, satuan, pengali hari) — "1 bulan lalu" = 30 hari (PERKIRAAN)
    (re.compile(r"(\d+)\s*(?:menit|minutes?|mins?)\s*(?:lalu|yang\s+lalu|ago)",
                re.IGNORECASE), "jam", 0),
    (re.compile(r"(\d+)\s*(?:jam|hours?)\s*(?:lalu|yang\s+lalu|ago)",
                re.IGNORECASE), "jam", 0),
    (re.compile(r"(\d+)\s*(?:hari|days?)\s*(?:lalu|yang\s+lalu|ago)",
                re.IGNORECASE), "hari", 1),
    (re.compile(r"(\d+)\s*(?:minggu|weeks?)\s*(?:lalu|yang\s+lalu|ago)",
                re.IGNORECASE), "hari", 7),
    (re.compile(r"(\d+)\s*(?:bulan|months?)\s*(?:lalu|yang\s+lalu|ago)",
                re.IGNORECASE), "hari", 30),
    (re.compile(r"(\d+)\s*(?:tahun|years?)\s*(?:lalu|yang\s+lalu|ago)",
                re.IGNORECASE), "hari", 365),
]

_ABSOLUT = re.compile(
    r"(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})"  # "12 Nov 2026", "3 Januari 2026"
)
_ISO = re.compile(r"(\d{4})-(\d{2})-(\d{2})")


def parse_posted_at(teks: str, ref: Optional[date] = None) -> tuple[
        Optional[date], bool]:
    """Parse teks tanggal posting -> (tanggal, pasti?).

    `ref` = tanggal fetch (default hari ini). Contoh:
    - "2 hari lalu" (ref 15 Nov 2026) -> (2026-11-13, False)
    - "1 minggu lalu" -> (ref - 7 hari, False)
    - "1 bulan lalu" -> (ref - 30 hari, False) — PERKIRAAN, tidak pasti
    - "baru saja" / "kemarin" / "2 jam lalu" -> (ref / ref-1, False)
    - "12 Nov 2026" -> (2026-11-12, True)
    - "2026-11-12" -> (2026-11-12, True)
    - "Listed seven days ago" -> (ref - 7, False)
    - "" / tak dikenal -> (None, False)

    Kata bilangan Inggris ("seven", "one", ...) didukung untuk "Listed
    seven days ago" ala JobStreet. `pasti=True` HANYA untuk tanggal
    absolut/ISO — tanggal relatif selalu False.
    """
    if not teks or not teks.strip():
        return None, False
    ref = ref or date.today()
    t = teks.strip().lower()

    if re.search(r"baru\s+saja|just\s+now|today|hari\s+ini", t):
        return ref, False
    if re.search(r"kemarin|yesterday", t):
        return ref - timedelta(days=1), False

    kata_angka = {
        "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
        "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11,
        "twelve": 12, "fourteen": 14, "sixteen": 16, "twenty": 20,
        "thirty": 30,
    }
    for kata, nilai in kata_angka.items():
        t = re.sub(rf"\b{kata}\b", str(nilai), t)

    for pola, _satuan, pengali in _RELATIF:
        m = pola.search(t)
        if m:
            jumlah = int(m.group(1))
            if pengali == 0:
                return ref, False
            return ref - timedelta(days=jumlah * pengali), False

    m = _ISO.search(t)
    if m:
        try:
            return date(int(m.group(1)), int(m.group(2)), int(m.group(3))), True
        except ValueError:
            return None, False

    m = _ABSOLUT.search(t)
    if m:
        hari, nama_bulan, tahun = int(m.group(1)), m.group(2).lower(), int(m.group(3))
        bulan = _BULAN_ID.get(nama_bulan)
        if bulan:
            try:
                return date(tahun, bulan, hari), True
            except ValueError:
                return None, False

    return None, False


# ---------------------------------------------------------------------------
# Nama perusahaan
# ---------------------------------------------------------------------------

_BADAN_HUKUM = re.compile(
    r"^(?:pt|perseroan\s+terbatas|cv|commanditaire\s+vennootschap|"
    r"tbk|persero|ud|yayasan|koperasi)\b\.?\s*|\s+"
    r"(?:pt|tbk|persero|\(persero\)|ltd|inc|co\.?|corp\.?|pte\.?|llc)\.?$",
    re.IGNORECASE,
)


def normalize_company(nama: str) -> str:
    """Normalisasi nama perusahaan untuk dedup.

    - buang spasi berlebih, huruf kapital diseragamkan (Title Case);
    - buang awalan/akhiran badan hukum ("PT ", " Tbk", "CV ", "Ltd")
      karena sumber yang sama menulis "PT Maju Bersama" dan
      "Maju Bersama" untuk perusahaan yang sama;
    - buang karakter non-alfanumerik di ujung.

    Contoh: "PT  Maju Bersama Tbk" -> "Maju Bersama".
    Hasil dipakai sebagai `company_norm` + kunci fingerprint.
    Nama ASLI tetap disimpan di `company_raw` (jangan dibuang).
    """
    if not nama:
        return ""
    n = re.sub(r"\s+", " ", nama.strip())
    n = _BADAN_HUKUM.sub("", n)
    n = _BADAN_HUKUM.sub("", n)  # dua putaran: "PT X Tbk" punya 2 imbuhan
    n = n.strip(" .,-")
    n = re.sub(r"\s+", " ", n).strip()
    return n.title() if n else nama.strip().title()


def normalize_location(lokasi: str) -> str:
    """Seragamkan lokasi: "Jakarta Selatan, DKI Jakarta" tetap apa adanya,
    hanya rapikan spasi + kapital awal tiap kata. Beda penulisan kota
    ("Jakarta" vs "DKI Jakarta") ditangani normalizer DB nanti, bukan di sini."""
    if not lokasi:
        return ""
    return re.sub(r"\s+", " ", lokasi.strip()).title()
