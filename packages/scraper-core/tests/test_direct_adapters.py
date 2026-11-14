"""Unit test adapter Direct (halaman karier + sosial perusahaan).

Fixture di tests/fixtures/ adalah contoh MINI BUATAN SENDIRI mengikuti
bentuk respons resmi (Greenhouse/Lever/Ashby/Workable/IG Graph API),
BUKAN salinan utuh dari situs asli mana pun.

Jalan:  python -m pytest packages/scraper-core/tests/test_direct_adapters.py -v
"""

import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scraper_core.adapters.career_page import (  # noqa: E402
    CareerPageAdapter,
    RawJob,
    board_api_url,
    detect_platform,
    detect_workday_board,
    extract_json_ld_job_postings,
    extract_slug,
    job_fingerprint,
    parse_ashby_board,
    parse_board,
    parse_greenhouse_board,
    parse_greenhouse_single_job,
    parse_iso_date,
    parse_json_ld_job_posting,
    parse_lever_board,
    parse_relative_posted_on,
    parse_workable_board,
    strip_html_to_text,
)
from scraper_core.adapters.social_company import (  # noqa: E402
    ManualSocialLead,
    classify_caption_as_job_post,
    extract_job_links,
    instagram_profile_job_links,
    is_job_link,
    parse_instagram_business_discovery,
    to_job_lead,
    to_job_lead_manual,
)

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def load_fixture(name: str):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Deteksi platform & slug
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("url,expected", [
    ("https://boards.greenhouse.io/contohcorp", "greenhouse"),
    ("https://job-boards.greenhouse.io/contohcorp/jobs/101", "greenhouse"),
    ("https://jobs.lever.co/contohcorp", "lever"),
    ("https://jobs.eu.lever.co/contohcorp", "lever"),
    ("https://jobs.ashbyhq.com/contohcorp", "ashby"),
    ("https://apply.workable.com/contohcorp", "workable"),
    ("https://jobs.smartrecruiters.com/ContohCorp", "smartrecruiters"),
    ("https://contohcorp.wd1.myworkdayjobs.com/External", "workday"),
    ("https://contohcorp.recruitee.com", "recruitee"),
    ("https://careers.contohcorp.id", "custom"),
    ("https://www.contohcorp.id/karir", "custom"),
    ("not-a-url", None),
    ("", None),
])
def test_detect_platform(url, expected):
    assert detect_platform(url) == expected


@pytest.mark.parametrize("url,expected", [
    ("https://boards.greenhouse.io/contohcorp", "contohcorp"),
    ("https://boards.greenhouse.io/contohcorp/jobs/101", "contohcorp"),
    ("https://jobs.lever.co/contohcorp", "contohcorp"),
    ("https://jobs.ashbyhq.com/contohcorp/abc-123", "contohcorp"),
    ("https://apply.workable.com/contohcorp", "contohcorp"),
    ("https://boards.greenhouse.io/embed/job_board?for=contohcorp", "contohcorp"),
    ("https://contohcorp.wd1.myworkdayjobs.com/External", None),  # Workday: tak bisa ditebak
    ("https://careers.contohcorp.id", None),
])
def test_extract_slug(url, expected):
    assert extract_slug(url) == expected


def test_detect_workday_board():
    board = detect_workday_board("https://intel.wd1.myworkdayjobs.com/External")
    assert board == {"tenant": "intel", "shard": "wd1", "site": "External"}
    assert detect_workday_board("https://boards.greenhouse.io/acme") is None


def test_board_api_url():
    assert board_api_url("greenhouse", "acme") == (
        "https://boards-api.greenhouse.io/v1/boards/acme/jobs?content=true")
    assert board_api_url("lever", "acme") == (
        "https://api.lever.co/v0/postings/acme?mode=json&limit=500")
    assert board_api_url("ashby", "acme") == (
        "https://api.ashbyhq.com/posting-api/job-board/acme?includeCompensation=true")
    assert board_api_url("workable", "acme") == (
        "https://apply.workable.com/api/v1/widget/accounts/acme?details=true")
    assert board_api_url("custom", "acme") is None


# ---------------------------------------------------------------------------
# Util tanggal & teks
# ---------------------------------------------------------------------------

def test_strip_html_double_encoded_greenhouse():
    # Greenhouse mengembalikan content yang di-encode DUA kali.
    raw = "&amp;lt;p&amp;gt;Kami mencari &amp;lt;strong&amp;gt;Backend&amp;lt;/strong&amp;gt; Engineer.&amp;lt;/p&amp;gt;"
    assert strip_html_to_text(raw) == "Kami mencari Backend Engineer."


def test_parse_iso_date():
    assert parse_iso_date("2026-11-05T08:00:00+07:00") == date(2026, 11, 5)
    assert parse_iso_date("2026-11-09") == date(2026, 11, 9)
    assert parse_iso_date("2021-04-30T16:21:55.393+00:00") == date(2021, 4, 30)
    assert parse_iso_date(None) is None
    assert parse_iso_date("bukan-tanggal") is None


def test_parse_relative_posted_on():
    today = date(2026, 11, 15)
    assert parse_relative_posted_on("Posted Yesterday", today) == date(2026, 11, 14)
    assert parse_relative_posted_on("Posted 20 Days Ago", today) == date(2026, 10, 26)
    assert parse_relative_posted_on("Posted Today", today) == today
    assert parse_relative_posted_on("Posted 3 Weeks Ago", today) is None


def test_job_fingerprint_same_for_repost():
    # Judul + perusahaan + lokasi sama -> fingerprint sama walau id beda.
    assert job_fingerprint("Backend Engineer", "Contoh Corp", "Jakarta") == \
        job_fingerprint("backend engineer ", "contoh corp", "Jakarta")
    assert job_fingerprint("Backend Engineer", "Contoh Corp", "Jakarta") != \
        job_fingerprint("Frontend Engineer", "Contoh Corp", "Jakarta")


# ---------------------------------------------------------------------------
# Parser board ATS
# ---------------------------------------------------------------------------

def test_parse_greenhouse_board():
    jobs = parse_greenhouse_board(load_fixture("greenhouse_board.json"), "contohcorp")
    assert len(jobs) == 2
    first, second = jobs
    assert first.title == "Backend Engineer"
    assert first.location == "Jakarta, Indonesia"
    assert first.company_raw == "Contoh Corp"
    assert first.department == "Engineering"
    assert first.platform_job_id == "101"
    assert first.job_key == "greenhouse:contohcorp:101"
    # content double-encoded harus bersih jadi teks polos
    assert first.description_text == "Kami mencari Backend Engineer."
    # K-D1: list resmi TIDAK menjamin first_published -> boleh None
    assert first.posted_at is None
    assert second.work_type == "remote"
    assert second.source_url == "https://boards.greenhouse.io/contohcorp/jobs/102"


def test_parse_greenhouse_single_job_first_published_and_salary():
    job = parse_greenhouse_single_job(
        load_fixture("greenhouse_single_job.json"), "contohcorp")
    assert job.posted_at == date(2026, 11, 5)
    # pay_input_ranges dalam sen -> rupiah
    assert job.salary_min == 15_000_000
    assert job.salary_max == 22_000_000
    assert job.salary_currency == "IDR"


def test_parse_lever_board():
    jobs = parse_lever_board(load_fixture("lever_board.json"), "contohcorp")
    assert len(jobs) == 2
    first, second = jobs
    assert first.title == "Software Engineer, Backend"
    assert first.location == "Jakarta"
    assert first.work_type == "hybrid"
    assert first.posted_at == date(2026, 11, 9)  # createdAt epoch ms
    assert first.salary_min == 180_000_000
    assert first.salary_max == 240_000_000
    assert first.salary_currency == "IDR"
    assert first.description_text == "Membangun layanan backend."
    assert first.job_key.startswith("lever:contohcorp:")
    assert second.work_type == "onsite"
    # Lever tidak mengembalikan nama perusahaan
    assert first.company_raw == ""


def test_parse_lever_empty_board_is_ambiguous():
    # [] bisa berarti "bukan pelanggan Lever" ATAU "0 lowongan" — parser
    # mengembalikan list kosong; pemanggil tidak boleh menyimpulkan.
    assert parse_lever_board([], "contohcorp") == []
    assert parse_lever_board(None, "contohcorp") == []


def test_parse_ashby_board():
    jobs = parse_ashby_board(load_fixture("ashby_board.json"), "contohcorp")
    assert len(jobs) == 1
    job = jobs[0]
    # Judul Ashby sering punya spasi di depan — harus di-trim.
    assert job.title == "Security Engineer, Cloud"
    assert job.location == "Jakarta, Indonesia, Remote (Indonesia)"
    assert job.work_type == "hybrid"
    # K-D3: publishedAt = TERAKHIR dipublikasikan, bukan pertama dibuka.
    assert job.posted_at == date(2026, 11, 8)
    assert job.salary_min == 200_000_000
    assert job.salary_max == 300_000_000
    assert job.salary_currency == "IDR"
    assert job.job_key.startswith("ashby:contohcorp:")


def test_parse_workable_board():
    jobs = parse_workable_board(load_fixture("workable_board.json"), "contohcorp")
    assert len(jobs) == 1
    job = jobs[0]
    assert job.title == "Frontend Engineer"
    assert job.company_raw == "Contoh Corp"
    assert job.posted_at == date(2026, 11, 9)
    assert job.work_type == "remote"  # telecommuting=true
    assert job.platform_job_id == "ABC12345"
    assert job.location == "Indonesia"  # city/state null -> hanya country
    assert job.salary_min is None  # Workable: tidak ada gaji terstruktur


def test_parse_board_dispatch_and_unknown():
    assert len(parse_board("lever", load_fixture("lever_board.json"), "contohcorp")) == 2
    assert len(parse_board("greenhouse", load_fixture("greenhouse_board.json"), "contohcorp")) == 2
    with pytest.raises(ValueError):
        parse_board("workday", {}, "contohcorp")
    with pytest.raises(ValueError):
        parse_board("tidak-ada", {}, "contohcorp")


# ---------------------------------------------------------------------------
# Halaman karier custom (JSON-LD)
# ---------------------------------------------------------------------------

def test_json_ld_extraction_and_parse():
    html_text = (FIXTURES / "custom_career_page.html").read_text(encoding="utf-8")
    postings = extract_json_ld_job_postings(html_text)
    assert len(postings) == 1
    job = parse_json_ld_job_posting(postings[0], "https://careers.contohcorp.id/mobile-engineer")
    assert job.title == "Mobile Engineer"
    assert job.company_raw == "Contoh Corp"
    assert job.location == "Yogyakarta, ID"
    assert job.posted_at == date(2026, 11, 7)
    assert job.salary_min == 120_000_000
    assert job.salary_max == 180_000_000
    assert job.salary_currency == "IDR"
    assert job.description_text == "Membangun aplikasi Android."
    assert job.platform == "custom"


def test_json_ld_ignores_non_job_posting():
    html_text = '<script type="application/ld+json">{"@type":"Organization","name":"X"}</script>'
    assert extract_json_ld_job_postings(html_text) == []
    assert extract_json_ld_job_postings("<html>tanpa json-ld</html>") == []


# ---------------------------------------------------------------------------
# Adapter end-to-end dengan fetcher palsu (tanpa jaringan)
# ---------------------------------------------------------------------------

class FakeFetcher:
    """Fetcher palsu: peta URL -> (status, body). Mencatat urutan request."""

    def __init__(self, mapping: dict[str, tuple[int, bytes]]):
        self.mapping = mapping
        self.calls: list[str] = []

    def __call__(self, url: str):
        self.calls.append(url)
        return (*self.mapping.get(url, (404, b"")), url)


def test_adapter_greenhouse_discover_fetch_check_active():
    board = load_fixture("greenhouse_board.json")
    single = load_fixture("greenhouse_single_job.json")
    fetcher = FakeFetcher({
        "https://boards-api.greenhouse.io/v1/boards/contohcorp/jobs?content=true": (
            200, json.dumps(board).encode()),
        "https://boards-api.greenhouse.io/v1/boards/contohcorp/jobs/101": (
            200, json.dumps(single).encode()),
        # Job 102 tidak punya endpoint single (simulasi: tetap None).
        "https://boards-api.greenhouse.io/v1/boards/contohcorp/jobs/102": (404, b""),
    })
    adapter = CareerPageAdapter(
        "Contoh Corp", "https://boards.greenhouse.io/contohcorp",
        fetcher=fetcher, polite_delay=0)
    assert adapter.platform == "greenhouse"
    assert adapter.source_id == "career-greenhouse"
    urls = adapter.discover()
    assert len(urls) == 2
    assert urls[0] == "https://boards.greenhouse.io/contohcorp/jobs/101"
    # fetch_job melengkapi first_published dari endpoint satu job
    job = adapter.fetch_job(urls[0])
    assert isinstance(job, RawJob)
    assert job.posted_at == date(2026, 11, 5)
    assert job.salary_min == 15_000_000
    # check_active: masih ada di board -> True; URL asing -> False
    assert adapter.check_active(urls[1]) is True
    assert adapter.check_active("https://boards.greenhouse.io/contohcorp/jobs/999") is False


def test_adapter_404_board_means_no_jobs_not_error():
    fetcher = FakeFetcher({})
    adapter = CareerPageAdapter(
        "Tidak Ada", "https://boards.greenhouse.io/tidakada",
        fetcher=fetcher, polite_delay=0)
    assert adapter.discover() == []


def test_adapter_custom_json_ld():
    html_text = (FIXTURES / "custom_career_page.html").read_text(encoding="utf-8")
    fetcher = FakeFetcher({
        "https://careers.contohcorp.id": (200, html_text.encode()),
        "https://careers.contohcorp.id/mobile-engineer": (200, html_text.encode()),
    })
    adapter = CareerPageAdapter(
        "Contoh Corp", "https://careers.contohcorp.id",
        fetcher=fetcher, polite_delay=0)
    assert adapter.platform == "custom"
    urls = adapter.discover()
    assert urls == ["https://careers.contohcorp.id"]
    job = adapter.fetch_job("https://careers.contohcorp.id/mobile-engineer")
    assert job.title == "Mobile Engineer"
    assert adapter.check_active("https://careers.contohcorp.id/mobile-engineer") is True
    assert adapter.check_active("https://careers.contohcorp.id/sudah-tutup") is False


def test_adapter_workday_raises_not_implemented():
    adapter = CareerPageAdapter(
        "Contoh", "https://contoh.wd1.myworkdayjobs.com/External",
        fetcher=FakeFetcher({}), polite_delay=0)
    with pytest.raises(NotImplementedError):
        adapter.discover()


# ---------------------------------------------------------------------------
# Sosial perusahaan
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("caption,expected", [
    ("We're hiring! Backend Engineer — lamar di link bio.", True),
    ("Lowongan: Data Analyst, penempatan Jakarta.", True),
    ("Bergabung dengan kami sebagai Product Designer.", True),
    ("Suasana kantor kami hari ini.", False),
    ("Selamat ulang tahun perusahaan ke-10!", False),
    ("", False),
    (None, False),
])
def test_classify_caption_as_job_post(caption, expected):
    assert classify_caption_as_job_post(caption) is expected


def test_extract_job_links_only_job_urls():
    text = ("Lowongan baru: https://boards.greenhouse.io/contohcorp "
            "dan baca blog kami https://contohcorp.id/blog/halo "
            "serta https://careers.contohcorp.id")
    links = extract_job_links(text)
    assert "https://boards.greenhouse.io/contohcorp" in links
    assert "https://careers.contohcorp.id" in links
    assert "https://contohcorp.id/blog/halo" not in links


def test_is_job_link():
    assert is_job_link("https://jobs.lever.co/acme") is True
    assert is_job_link("https://contoh.id/karir") is True
    assert is_job_link("https://contoh.id/blog/tips-karir") is False


def test_parse_instagram_business_discovery():
    posts = parse_instagram_business_discovery(
        load_fixture("instagram_business_discovery.json"), "contohcorp")
    assert len(posts) == 2
    hiring, office = posts
    assert hiring.is_job_announcement is True
    assert hiring.posted_at == datetime(2026, 11, 10, 8, 0, tzinfo=timezone.utc)
    assert hiring.post_url == "https://www.instagram.com/p/ABCdef12345/"
    assert hiring.job_links == ["https://boards.greenhouse.io/contohcorp"]
    assert hiring.date_reliability == "post_date_only"
    assert hiring.caption_excerpt.startswith("We're hiring!")
    assert office.is_job_announcement is False
    assert office.job_links == []
    # Bio: link karier ikut terbaca
    bio_links = instagram_profile_job_links(
        load_fixture("instagram_business_discovery.json")
        ["business_discovery"]["biography"])
    assert bio_links == ["https://careers.contohcorp.id"]


def test_to_job_lead_never_sets_job_posted_at():
    """GRILL: tanggal posting IG TIDAK BOLEH jadi posted_at lowongan."""
    posts = parse_instagram_business_discovery(
        load_fixture("instagram_business_discovery.json"), "contohcorp")
    lead = to_job_lead(posts[0])
    assert lead["job_posted_at"] is None
    assert lead["posted_on_platform_at"] == "2026-11-10T08:00:00+00:00"
    assert "Verifikasi" in lead["next_step"]
    assert lead["job_links_found"] == ["https://boards.greenhouse.io/contohcorp"]


def test_manual_social_lead_linkedin_has_no_auto_fetch():
    """LinkedIn: tidak ada fetcher otomatis — hanya catatan manual."""
    lead = ManualSocialLead(
        platform="linkedin",
        company_name="Contoh Corp",
        post_url="https://www.linkedin.com/company/contohcorp/posts/abc123",
        seen_at=datetime(2026, 11, 15, 10, 0, tzinfo=timezone.utc),
        posted_at_claimed=datetime(2026, 11, 14, 9, 0, tzinfo=timezone.utc),
        caption_excerpt="We are hiring Backend Engineers.",
        job_links=["https://careers.contohcorp.id"],
        is_job_announcement=True,
    )
    out = to_job_lead_manual(lead)
    assert out["kind"] == "social_lead_manual"
    assert out["job_posted_at"] is None
    assert out["recorded_by"] == "operator-manual"
    assert out["date_reliability"] == "post_date_only"
