"""Kontrak adapter scraper CekLoker + tipe data mentah lowongan.

Sesuai ARCHITECTURE.md §6 (kontrak adapter) dan §4 (model data).
Sengaja stdlib saja — lihat README paket.

Aturan kesopanan (ARCHITECTURE.md §8, ditegaskan ADR-0002):
- Patuhi robots.txt untuk path yang diminta (helper `allowed_by_robots`).
- Delay 2-5 detik per domain (default per adapter, lihat `POLITE_DELAY_S`).
- User-Agent jelas berisi nama proyek + kontak (tanpa email pribadi di sini;
  isi lewat env `CEKLOKER_CONTACT` saat deployment).
- JANGAN bypass login / paywall / CAPTCHA. Kalau sumber butuh login,
  adapter-nya harus raise `SourceNotPermittedError`, bukan diakali.
- JANGAN menyimpan credential / data pribadi pelamar.
"""

from __future__ import annotations

import hashlib
import os
import re
import time
import urllib.error
import urllib.request
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional

from .parsers import normalize_company

# ---------------------------------------------------------------------------
# Error
# ---------------------------------------------------------------------------


class SourceNotPermittedError(NotImplementedError):
    """Adapter sumber ini TIDAK BOLEH dipakai (ToS/robots melarang atau
    butuh login/izin tertulis). Bukan bug — keputusan legal yang sadar.

    Atribut `alternative` berisi jalan legal yang disarankan.
    """


class SourceBlockedError(RuntimeError):
    """Sumber menolak request (HTTP 403/429/CAPTCHA/dll). Worker HARUS
    berhenti mencoba sumber ini untuk sementara (backoff), bukan
    memutar proxy / memalsukan identitas untuk lolos."""


class SourceFetchError(RuntimeError):
    """Gagal ambil halaman karena alasan teknis (timeout, 5xx, dst)."""


# ---------------------------------------------------------------------------
# Fingerprint dedup — SATU-SATUNYA definisi (K8, Fase 1-lanjutan)
# ---------------------------------------------------------------------------


def job_fingerprint(title: str, company: Optional[str],
                    location: Optional[str]) -> str:
    """Fingerprint dedup lintas sumber: hash(judul + perusahaan + lokasi).

    Definisi TUNGGAL yang dipakai semua adapter dan ``RawJob.fingerprint()``
    (konflik K8 Fase 1: dulu ada dua definisi — satu memakai nama perusahaan
    mentah, satu memakai ``company_norm`` — kini disamakan ke yang ini):

    - perusahaan dinormalisasi dulu lewat ``normalize_company`` (buang
      imbuhan badan hukum "PT"/"Tbk"/"CV"/"Ltd", rapikan spasi, seragamkan
      kapital), jadi "PT Contoh Corp", "Contoh Corp Tbk", dan "contoh corp"
      menghasilkan fingerprint yang sama;
    - judul + lokasi hanya di-strip + lower;
    - hasil: SHA-256, 32 karakter hex pertama;
    - URL sengaja TIDAK masuk fingerprint — justru supaya repost (URL/ID
      baru, isi sama) terdeteksi sebagai lowongan yang sama.

    Batasan yang jujur (grill K8): dua lowongan BENAR-BENAR berbeda dengan
    judul + perusahaan + lokasi yang sama persis (mis. perusahaan membuka
    2 posisi "Staff Administrasi" di Jakarta) akan berbagi fingerprint.
    Karena itu fingerprint hanya sinyal kandidat dedup/repost, bukan
    identitas tunggal — normalizer wajib mengonfirmasi dengan field lain
    (``job_key``/``platform_job_id``/``posted_at``) sebelum menggabungkan.
    """
    key = "|".join(
        [
            (title or "").strip().lower(),
            normalize_company(company or "").strip().lower(),
            (location or "").strip().lower(),
        ]
    )
    return hashlib.sha256(key.encode("utf-8")).hexdigest()[:32]


# ---------------------------------------------------------------------------
# Data mentah lowongan (RawJob)
# ---------------------------------------------------------------------------


@dataclass
class RawJob:
    """Satu lowongan mentah hasil satu adapter, sebelum normalisasi DB.

    `posted_at` = tanggal yang ditulis sumber (bisa None kalau sumber
    tidak mencantumkan / hanya tanggal relatif yang tak bisa dipastikan).
    JANGAN samakan dengan `first_seen_at` — itu dicatat worker saat
    pertama melihat lowongan, bukan di sini (lihat ARCHITECTURE.md §4).
    """

    source_id: str
    source_url: str
    title: str
    company_raw: str
    company_norm: str = ""
    location: str = ""
    work_type: str = ""  # onsite | hybrid | remote | "" (tak diketahui)
    salary_min: Optional[int] = None  # dalam mata uang `salary_currency`
    salary_max: Optional[int] = None
    salary_currency: str = "IDR"
    salary_text: str = ""  # teks gaji apa adanya dari sumber
    posted_at: Optional[date] = None
    posted_raw: str = ""  # teks tanggal apa adanya, mis. "2 hari lalu"
    posted_at_certain: bool = True  # False bila posted_at hanya perkiraan ("1 bulan lalu")
    # Field tambahan untuk adapter halaman karier / ATS (disatukan koordinator):
    platform: Optional[str] = None  # greenhouse | lever | ashby | ...
    platform_job_id: Optional[str] = None
    job_key: Optional[str] = None  # identitas stabil (platform, slug, id ATS)
    department: Optional[str] = None
    repost_hint: bool = False
    raw: dict = field(default_factory=dict)  # payload mentah sumber (bukan untuk DB)
    description_text: str = ""
    is_active: bool = True  # False kalau halaman menandai "ditutup"
    fetched_at: datetime = field(default_factory=datetime.now)

    def fingerprint(self) -> str:
        """Hash dedup antar-sumber — delegasi ke ``job_fingerprint()``
        (definisi tunggal, lihat K8 di atas). Dipakai normalizer untuk
        mendeteksi lowongan yang sama tayang di 2 sumber, DAN repost
        (URL baru, isi sama). ``company_norm`` dinormalisasi ulang di
        dalam ``job_fingerprint`` (idempotent untuk nilai yang sudah
        ternormalisasi), jadi hasilnya sama walau pemanggil mengisi
        ``company_norm`` dari nama mentah."""
        return job_fingerprint(self.title, self.company_norm, self.location)


# ---------------------------------------------------------------------------
# Helper kesopanan
# ---------------------------------------------------------------------------

DEFAULT_USER_AGENT = (
    "CekLokerBot/0.1 (+https://github.com/Gigajn/cekloker; "
    "scraper riset non-komersial, patuh robots.txt)"
)


def user_agent() -> str:
    """User-Agent jujur. Kontak bisa ditimpa lewat env CEKLOKER_CONTACT."""
    contact = os.environ.get("CEKLOKER_CONTACT", "").strip()
    if contact:
        return f"CekLokerBot/0.1 (+{contact})"
    return DEFAULT_USER_AGENT


def polite_delay(domain: str, seconds: float) -> None:
    """Tidur `seconds` detik sebelum request berikutnya ke `domain`.

    Implementasi v1 sengaja sederhana (sleep). Worker produksi memakai
    rate-limiter Redis per domain; fungsi ini jadi pengaman terakhir
    agar tidak ada adapter yang menembak tanpa jeda.
    """
    if seconds > 0:
        time.sleep(seconds)


def _rule_to_regex(rule: str) -> "re.Pattern[str]":
    """Ubah satu aturan Disallow/Allow robots.txt (RFC 9309) jadi regex.

    `*` cocok dengan karakter apa pun (termasuk `/`), `$` menandai akhir
    URL. Aturan dicocokkan dari AWAL path+query.
    """
    parts = re.split(r"(\*|\$)", rule)
    out = ["^"]
    for p in parts:
        if p == "*":
            out.append(".*")
        elif p == "$":
            out.append("$")
        elif p:
            out.append(re.escape(p))
    return re.compile("".join(out))


def allowed_by_robots(robots_txt: str, url: str, agent: str = "*") -> bool:
    """Cek apakah `url` diizinkan isi `robots_txt` (teks yang sudah
    diambil). Mengembalikan False kalau ada aturan Disallow yang cocok.

    Implementasi matcher sendiri (RFC 9309, ~40 baris) karena
    `urllib.robotparser` stdlib TIDAK menangani pola `*` di tengah
    aturan dan akhiran `$` dengan benar (diuji 15 Nov 2026: aturan
    Glints `*/opportunities/jobs/explore?*` lolos dari robotparser).
    Hanya grup yang menyebut `agent` (atau `*`) yang dipakai;
    aturan terpanjang yang cocok menang; Allow mengalahkan Disallow
    bila panjangnya sama atau lebih panjang.

    Catatan jujur: ini HANYA soal robots.txt — ToS situs bisa tetap
    melarang meski robots.txt mengizinkan (lihat K-JB5 Indeed).
    """
    from urllib.parse import urlparse

    target = urlparse(url)
    path = target.path
    if target.query:
        path += "?" + target.query

    # groups: list[(agents, allow_rules, disallow_rules)]
    groups: list[tuple[list[str], list[str], list[str]]] = []
    agents: list[str] = []
    allow: list[str] = []
    disallow: list[str] = []

    def flush() -> None:
        if agents:
            groups.append((list(agents), list(allow), list(disallow)))

    for raw in robots_txt.splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line or ":" not in line:
            continue
        kunci, _, nilai = line.partition(":")
        kunci = kunci.strip().lower()
        nilai = nilai.strip()
        if kunci == "user-agent":
            if agents and (allow or disallow):
                flush()
                agents, allow, disallow = [], [], []
            agents.append(nilai.lower())
        elif kunci == "allow" and nilai:
            allow.append(nilai)
        elif kunci == "disallow" and nilai:
            disallow.append(nilai)
    flush()

    agent = agent.lower()
    best_allow = -1
    best_deny = -1
    for group_agents, group_allow, group_deny in groups:
        if agent not in group_agents and "*" not in group_agents:
            continue
        for rule in group_allow:
            if _rule_to_regex(rule).match(path):
                best_allow = max(best_allow, len(rule))
        for rule in group_deny:
            if _rule_to_regex(rule).match(path):
                best_deny = max(best_deny, len(rule))
    if best_allow == -1 and best_deny == -1:
        return True
    return best_allow >= best_deny


def fetch_text(url: str, timeout: int = 20) -> tuple[int, str]:
    """Ambil satu halaman publik lewat stdlib urllib.

    Mengembalikan (status_http, teks). 404 -> (404, "") agar
    `check_active()` bisa membedakan "tutup" dari "error".
    403/429 -> raise SourceBlockedError (jangan diakali).
    """
    req = urllib.request.Request(url, headers={"User-Agent": user_agent()})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            charset = resp.headers.get_content_charset() or "utf-8"
            return resp.status, resp.read().decode(charset, errors="replace")
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return 404, ""
        if exc.code in (401, 403, 429):
            raise SourceBlockedError(
                f"{url} menolak request (HTTP {exc.code}). "
                "Berhenti sementara; JANGAN memutar proxy / memalsukan "
                "identitas untuk lolos."
            ) from exc
        raise SourceFetchError(f"{url} gagal (HTTP {exc.code})") from exc
    except urllib.error.URLError as exc:
        raise SourceFetchError(f"{url} gagal dijangkau: {exc}") from exc


# ---------------------------------------------------------------------------
# Kontrak adapter
# ---------------------------------------------------------------------------


class JobSourceAdapter(ABC):
    """Kontrak yang WAJIB diikuti semua adapter sumber (ARCHITECTURE §6).

    Atribut kelas yang wajib diisi subclass:
    - `source_id`: mis. "glints" (stabil, dipakai FK `jobs.source_id`).
    - `base_url`: domain utama sumber.
    - `enabled`: False = adapter MATI secara default (mis. sumber
      dilarang ToS). Worker TIDAK BOLEH mengaktifkan tanpa keputusan
      eksplisit + izin tertulis. Mengubah ini butuh ADR baru.
    - `polite_delay_s`: jeda antar request ke domain ini (detik).
    - `robots_disallows`: ringkasan aturan robots.txt yang relevan,
      ditulis sebagai dokumentasi hidup (bukan pengganti cek live).
    """

    source_id: str = ""
    base_url: str = ""
    enabled: bool = True
    polite_delay_s: float = 3.0
    robots_disallows: tuple[str, ...] = ()

    # -- API utama ------------------------------------------------------

    @abstractmethod
    def discover(self, keywords: str = "", location: str = "",
                 max_pages: int = 1) -> list[str]:
        """Kembalikan daftar URL halaman detail lowongan.

        Harus memakai jalur PALING RESMI yang tersedia (urutan:
        API resmi > RSS > sitemap > halaman list publik > JSON
        tersemat di halaman). JANGAN memanggil endpoint internal
        tidak terdokumentasi sebagai jalur utama.
        """

    @abstractmethod
    def fetch_job(self, url: str) -> RawJob:
        """Ambil satu halaman detail -> RawJob + penanda aktif/tutup."""

    @abstractmethod
    def check_active(self, url: str) -> bool:
        """True kalau lowongan masih buka.

        Aturan (ADR-0002): True HANYA bila halaman berhasil diambil
        (HTTP 200) DAN tidak ada penanda tutup. 404 / penanda tutup /
        redirect ke halaman list = False. Gagal teknis (timeout/5xx)
        BUKAN False — raise SourceFetchError agar status lama
        dipertahankan sebagai `unknown`, bukan keliru jadi `closed`.
        """

    # -- Helper bersama -------------------------------------------------

    def _get(self, url: str) -> tuple[int, str]:
        polite_delay(self.base_url, self.polite_delay_s)
        return fetch_text(url)

    @classmethod
    def require_enabled(cls) -> None:
        """Panggil di awal discover/fetch/check_active bila adapter
        berstatus TUNDA. Melempar SourceNotPermittedError yang jelas."""
        if not cls.enabled:
            raise SourceNotPermittedError(
                f"Adapter '{cls.source_id}' DINONAKTIFKAN (enabled=False). "
                f"Alasan: {getattr(cls, 'disabled_reason', 'tidak dicatat')}. "
                f"Alternatif: {getattr(cls, 'alternative', 'tidak dicatat')}. "
                "Mengaktifkan butuh izin tertulis + ADR baru — JANGAN diakali."
            )


def slugify_company(name: str) -> str:
    """Slug pendek untuk URL internal (bukan untuk dedup)."""
    slug = re.sub(r"[^a-z0-9]+", "-", name.strip().lower()).strip("-")
    return slug or "perusahaan"
