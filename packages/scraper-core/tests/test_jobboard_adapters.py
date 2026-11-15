"""Unit test adapter job board CekLoker (Fase 1).

PRINSIP: semua test memakai FIXTURE BUATAN di tests/fixtures/
(bukan salinan halaman asli, bukan data pribadi) dan parser PURE
(tanpa HTTP). TIDAK ADA test yang memanggil situs live — test live
dilarang di sini karena (a) melanggar ritme sopan, (b) hasilnya
tidak deterministik, (c) JobStreet/Indeed memang dilarang ToS-nya.

Jalankan:  .venv/bin/python -m pytest -q
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest

from scraper_core.adapters import (
    ADAPTERS,
    GlintsAdapter,
    IndeedAdapter,
    JobStreetAdapter,
    KalibrrAdapter,
)
from scraper_core.adapters.glints import (
    parse_glints_job,
    parse_sitemap,
    visible_text,
)
from scraper_core.adapters.kalibrr import (
    parse_kalibrr_job,
    parse_kalibrr_search,
)
from scraper_core.base import (
    RawJob,
    SourceFetchError,
    SourceNotPermittedError,
    allowed_by_robots,
)
from scraper_core.parsers import (
    normalize_company,
    parse_posted_at,
    parse_salary,
)

FIX = Path(__file__).parent / "fixtures"
REF = date(2026, 11, 15)  # "hari ini" versi test (Ahad, 15 Nov 2026 WIB)

GLINTS_URL = (
    "https://glints.com/id/en/opportunities/jobs/staff-programmer/"
    "ad093d00-3e7d-4f25-a56e-be88fda4632d"
)
KALIBRR_URL = (
    "https://www.kalibrr.id/c/pt-fiktif-teknologi-nusantara/"
    "jobs/100001/backend-engineer"
)


def _baca(nama: str) -> str:
    return (FIX / nama).read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Parser gaji IDR
# ---------------------------------------------------------------------------


def test_gaji_rentang_juta():
    assert parse_salary("Rp5–8 jt") == (5_000_000, 8_000_000, "IDR")


def test_gaji_rentang_juta_spasi_dan_huruf():
    assert parse_salary("Rp 5 jt - 8 jt") == (5_000_000, 8_000_000, "IDR")


def test_gaji_idr_titik_ribuan():
    assert parse_salary("IDR 5.000.000") == (5_000_000, 5_000_000, "IDR")


def test_gaji_rentang_jobstreet():
    assert parse_salary("Rp 22.000.000 – Rp 32.000.000 per month") == (
        22_000_000, 32_000_000, "IDR")


def test_gaji_per_bulan_slash():
    assert parse_salary("Rp 5.000.000/bulan") == (5_000_000, 5_000_000, "IDR")


def test_gaji_koma_desimal_juta():
    assert parse_salary("Rp 5,5 jt") == (5_500_000, 5_500_000, "IDR")


def test_gaji_tidak_dicantumkan():
    assert parse_salary("Tidak dicantumkan") == (None, None, "IDR")
    assert parse_salary("") == (None, None, "IDR")
    assert parse_salary("Gaji dirahasiakan") == (None, None, "IDR")


def test_gaji_mata_uang_asing():
    assert parse_salary("$1,000 - $1,500") == (1_000, 1_500, "USD")
    assert parse_salary("SGD 3.000") == (3_000, 3_000, "SGD")


def test_gaji_tidak_menebak():
    # "2 lowongan" bukan gaji — angka kecil tanpa penanda diabaikan.
    assert parse_salary("2 lowongan dibuka") == (None, None, "IDR")


# ---------------------------------------------------------------------------
# Parser tanggal posting
# ---------------------------------------------------------------------------


def test_tanggal_rel_tif_hari():
    tgl, pasti = parse_posted_at("2 hari lalu", REF)
    assert tgl == date(2026, 11, 13) and pasti is False


def test_tanggal_rel_tif_minggu_bulan():
    tgl, pasti = parse_posted_at("1 minggu lalu", REF)
    assert tgl == date(2026, 11, 8) and pasti is False
    tgl, _ = parse_posted_at("1 bulan lalu", REF)
    assert tgl == date(2026, 10, 16)  # 30 hari, PERKIRAAN (lihat ADR-0002)


def test_tanggal_kemarin_dan_jam():
    tgl, _ = parse_posted_at("kemarin", REF)
    assert tgl == date(2026, 11, 14)
    tgl, _ = parse_posted_at("2 jam lalu", REF)
    assert tgl == REF
    tgl, _ = parse_posted_at("baru saja", REF)
    assert tgl == REF


def test_tanggal_absolut_pasti():
    tgl, pasti = parse_posted_at("12 Nov 2026", REF)
    assert (tgl, pasti) == (date(2026, 11, 12), True)
    tgl, pasti = parse_posted_at("3 Januari 2026", REF)
    assert (tgl, pasti) == (date(2026, 1, 3), True)
    tgl, pasti = parse_posted_at("2026-11-12", REF)
    assert (tgl, pasti) == (date(2026, 11, 12), True)


def test_tanggal_inggris_kata_bilangan():
    # Gaya JobStreet: "Listed seven days ago"
    tgl, pasti = parse_posted_at("Listed seven days ago", REF)
    assert tgl == date(2026, 11, 8) and pasti is False


def test_tanggal_tidak_dikenal():
    assert parse_posted_at("segera hadir", REF) == (None, False)
    assert parse_posted_at("", REF) == (None, False)


# ---------------------------------------------------------------------------
# Normalisasi perusahaan
# ---------------------------------------------------------------------------


def test_normalisasi_perusahaan():
    assert normalize_company("PT  Maju Bersama Tbk") == "Maju Bersama"
    assert normalize_company("PT Maju Bersama") == "Maju Bersama"
    assert normalize_company("CV Seven Smarts Indonesia") == \
        "Seven Smarts Indonesia"
    assert normalize_company("Maju Bersama") == "Maju Bersama"
    # Nama asli TIDAK hilang: company_raw tetap disimpan di RawJob.
    assert normalize_company("") == ""


# ---------------------------------------------------------------------------
# Glints
# ---------------------------------------------------------------------------


def test_glints_parse_job_aktif():
    job = parse_glints_job(_baca("glints_job.html"), GLINTS_URL, REF)
    assert job.source_id == "glints"
    assert job.title == "Staff Programmer"
    assert job.company_raw == "PT Contoh Maju Bersama"
    assert job.company_norm == "Contoh Maju Bersama"
    assert job.location == "Jakarta"
    assert job.salary_min == 5_000_000 and job.salary_max == 8_000_000
    assert job.salary_currency == "IDR"
    assert job.posted_at == date(2026, 11, 13)
    assert job.is_active is True


def test_glints_i18n_bundle_tidak_menandai_tutup():
    # REGRESI uji live 15 Nov 2026: bundel i18n di <script> memuat pesan
    # "lowongan ini sudah ditutup" di SEMUA halaman detail. Lowongan
    # AKTIF (validThrough 2026-12-16 > REF) tidak boleh ditandai tutup.
    html = _baca("glints_job_i18n_bundle.html")
    assert "lowongan ini sudah ditutup" in html.lower()  # ada di mentah
    assert "lowongan ini sudah ditutup" not in visible_text(html).lower()
    job = parse_glints_job(html, GLINTS_URL, REF)
    assert job.title == "Corporate Sales Executive"
    assert job.company_raw == "PT. AME KUNINGAN JAYA"
    assert job.location == "Jakarta Selatan"
    assert job.posted_at == date(2026, 8, 27)  # datePosted ISO, pasti
    assert job.posted_at_certain is True
    assert job.salary_min == 5_000_000 and job.salary_max == 5_500_000
    assert job.is_active is True


def test_glints_validthrough_lewat_menandai_tutup():
    # validThrough 2026-11-01 sudah lewat dari REF (2026-11-15) dan
    # tidak ada penanda tutup di teks tampil: tutup lewat validThrough.
    job = parse_glints_job(
        _baca("glints_job_validthrough_lewat.html"), GLINTS_URL, REF)
    assert job.posted_at == date(2026, 9, 1)
    assert job.is_active is False


def test_glints_sitemap_dedup_varian_locale():
    # Lowongan yang sama muncul 2x di sitemap (/id/ dan /id/en/, UUID
    # sama) — discover harus mengembalikan 1 URL (uji live 15 Nov 2026).
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        "<url><loc>https://glints.com/id/opportunities/jobs/staff-programmer/"
        "ad093d00-3e7d-4f25-a56e-be88fda4632d</loc></url>"
        "<url><loc>https://glints.com/id/en/opportunities/jobs/staff-programmer/"
        "ad093d00-3e7d-4f25-a56e-be88fda4632d</loc></url>"
        "<url><loc>https://glints.com/id/opportunities/jobs/backend-engineer/"
        "11111111-2222-3333-4444-555555555555</loc></url>"
        "</urlset>"
    )
    urls = parse_sitemap(xml)
    assert len(urls) == 2
    assert urls[0].endswith("ad093d00-3e7d-4f25-a56e-be88fda4632d")


def test_glints_parse_job_tutup():
    job = parse_glints_job(_baca("glints_job_closed.html"), GLINTS_URL, REF)
    assert job.is_active is False
    assert job.posted_at == date(2026, 10, 1)


def test_glints_parse_gagal_bila_bukan_halaman_lowongan():
    with pytest.raises(Exception):
        parse_glints_job("<html><body>Kosong</body></html>", GLINTS_URL, REF)


def test_glints_sitemap_hanya_url_lowongan():
    urls = parse_sitemap(_baca("glints_sitemap.xml"))
    assert len(urls) == 2  # URL perusahaan disaring keluar
    assert all("/opportunities/jobs/" in u for u in urls)


def test_glints_robots_job_detail_diizinkan_explore_dilarang():
    robots = (
        "User-agent: *\n"
        "Disallow: */opportunities/jobs/explore?*\n"
        "Disallow: */opportunities/jobs/recommended$\n"
    )
    assert allowed_by_robots(robots, GLINTS_URL) is True
    assert allowed_by_robots(
        robots, "https://glints.com/id/opportunities/jobs/explore?x=1"
    ) is False
    assert allowed_by_robots(
        robots, "https://glints.com/id/opportunities/jobs/recommended"
    ) is False


def test_robots_jobstreet_detail_dilarang():
    robots = (
        "User-agent: *\n"
        "Disallow: */job/\n"
        "Disallow: *?\n"
    )
    assert allowed_by_robots(
        robots, "https://id.jobstreet.com/job/81234567") is False
    assert allowed_by_robots(
        robots, "https://id.jobstreet.com/id/jobs?sortmode=ListedDate"
    ) is False
    # Halaman list bersih (tanpa query) tidak dilarang robots.txt —
    # yang melarang agregasinya adalah ToS, bukan robots (K-JB1).
    assert allowed_by_robots(
        robots, "https://id.jobstreet.com/tech-indonesia-jobs/in-Jakarta"
    ) is True


def test_robots_indeed_detail_dilarang():
    robots = (
        "User-agent: *\n"
        "Allow: /\n"
        "Disallow: /viewjob\n"
        "Disallow: /job/\n"
        "Disallow: /jobs/ID/\n"
    )
    assert allowed_by_robots(
        robots, "https://id.indeed.com/viewjob?jk=abc") is False
    assert allowed_by_robots(
        robots, "https://id.indeed.com/jobs/ID/") is False
    # Halaman PENCARIAN (/jobs?q=...) tidak dilarang robots.txt —
    # yang dilarang adalah halaman DETAIL dan /jobs/<kode-negara>/.
    # (ToS tetap melarang data-mining — lihat K-JB5.)
    assert allowed_by_robots(
        robots, "https://id.indeed.com/jobs?q=engineer&start=0") is True
    assert allowed_by_robots(
        robots, "https://id.indeed.com/companies/abc") is True


# ---------------------------------------------------------------------------
# Kalibrr
# ---------------------------------------------------------------------------


def test_kalibrr_parse_job_aktif():
    job = parse_kalibrr_job(_baca("kalibrr_job.html"), KALIBRR_URL, REF)
    assert job.source_id == "kalibrr"
    assert job.title == "Backend Engineer"
    assert job.company_raw == "PT Fiktif Teknologi Nusantara"
    assert job.company_norm == "Fiktif Teknologi Nusantara"
    assert job.location == "Jakarta Selatan"
    assert job.posted_at == date(2026, 11, 10)  # dari activationDate (ISO)
    assert job.is_active is True


def test_kalibrr_parse_job_tutup():
    job = parse_kalibrr_job(_baca("kalibrr_job_closed.html"), KALIBRR_URL, REF)
    assert job.is_active is False


def test_kalibrr_search_ambil_url_detail():
    urls = parse_kalibrr_search(_baca("kalibrr_search.html"))
    assert urls == [
        "https://www.kalibrr.id/c/pt-fiktif-teknologi-nusantara/jobs/100001/backend-engineer",
        "https://www.kalibrr.id/c/pt-contoh-maju-bersama/jobs/100002/frontend-engineer",
    ]


def test_kalibrr_shell_spa_gagal_jujur_bukan_kosong():
    # REGRESI uji live 15 Nov 2026: pencarian Kalibrr mengembalikan
    # HTTP 200 berisi shell SPA tanpa __NEXT_DATA__. Parser HARUS
    # melempar SourceFetchError (worker -> unknown), BUKAN [] seolah
    # "0 lowongan".
    shell = _baca("kalibrr_search_shell.html")
    assert '<script id="__NEXT_DATA__"' not in shell
    with pytest.raises(SourceFetchError):
        parse_kalibrr_search(shell)
    with pytest.raises(SourceFetchError):
        parse_kalibrr_job(shell, KALIBRR_URL, REF)


def test_kalibrr_search_tanpa_hasil_tapi_ada_next_data_tetap_kosong():
    # Bedakan dari shell: halaman pencarian SAH yang memang 0 hasil
    # tetap punya __NEXT_DATA__ (daftar kosong) -> [] adalah jawaban
    # yang benar, bukan error.
    html = (
        '<html><head><script id="__NEXT_DATA__" type="application/json">'
        '{"props":{"pageProps":{"jobs":[]}}}'
        "</script></head><body>tidak ada lowongan</body></html>"
    )
    assert parse_kalibrr_search(html) == []


# ---------------------------------------------------------------------------
# JobStreet & Indeed: STUB — harus menolak dipakai
# ---------------------------------------------------------------------------


def test_jobstreet_stub_menolak():
    adapter = JobStreetAdapter()
    assert adapter.enabled is False
    with pytest.raises(SourceNotPermittedError):
        adapter.discover("engineer", "Jakarta")
    with pytest.raises(SourceNotPermittedError):
        adapter.fetch_job("https://id.jobstreet.com/job/81234567")
    with pytest.raises(SourceNotPermittedError):
        adapter.check_active("https://id.jobstreet.com/job/81234567")
    # SourceNotPermittedError adalah NotImplementedError (kontrak tugas).
    with pytest.raises(NotImplementedError):
        adapter.discover()


def test_indeed_stub_menolak():
    adapter = IndeedAdapter()
    assert adapter.enabled is False
    with pytest.raises(SourceNotPermittedError):
        adapter.discover("engineer", "Jakarta")
    with pytest.raises(SourceNotPermittedError):
        adapter.fetch_job("https://id.indeed.com/viewjob?jk=abc123")
    with pytest.raises(NotImplementedError):
        adapter.check_active("https://id.indeed.com/viewjob?jk=abc123")


def test_fixture_jobstreet_hanya_dokumentasi():
    # Fixture Chalice (ASUMSI) tetap bisa diparse parser bersama,
    # membuktikan parser gaji/tanggal konsisten dengan teks JobStreet.
    data = json.loads(_baca("jobstreet_chalice_sample.json"))
    assert data["data"][0]["listed"] == "Listed seven days ago"
    assert parse_salary(data["data"][0]["salary"]) == (
        22_000_000, 32_000_000, "IDR")
    tgl, _ = parse_posted_at(data["data"][0]["listed"], REF)
    assert tgl == date(2026, 11, 8)
    assert parse_salary(data["data"][1]["salary"]) == (None, None, "IDR")


# ---------------------------------------------------------------------------
# Kontrak & registry
# ---------------------------------------------------------------------------


def test_registry_empat_adapter():
    assert len(ADAPTERS) == 4
    ids = [a.source_id for a in ADAPTERS]
    assert ids == ["glints", "jobstreet", "kalibrr", "indeed"]
    aktif = [a for a in ADAPTERS if a.enabled]
    assert [a.source_id for a in aktif] == ["glints", "kalibrr"]


def test_fingerprint_dedup_dan_repost():
    a = RawJob(source_id="glints", source_url="https://x/1",
               title="Staff Programmer", company_raw="PT Contoh Maju Bersama",
               company_norm="Contoh Maju Bersama", location="Jakarta")
    b = RawJob(source_id="kalibrr", source_url="https://y/2",
               title="Staff Programmer", company_raw="Contoh Maju Bersama",
               company_norm="Contoh Maju Bersama", location="Jakarta")
    c = RawJob(source_id="glints", source_url="https://x/3",
               title="Staff Programmer", company_raw="PT Contoh Maju Bersama",
               company_norm="Contoh Maju Bersama", location="Bandung")
    # Lowongan sama di 2 sumber / URL repost baru -> fingerprint SAMA.
    assert a.fingerprint() == b.fingerprint()
    # Lokasi beda -> fingerprint beda.
    assert a.fingerprint() != c.fingerprint()


def test_user_agent_jujur():
    from scraper_core.base import user_agent
    ua = user_agent()
    assert "CekLokerBot" in ua and "cekloker" in ua.lower()
