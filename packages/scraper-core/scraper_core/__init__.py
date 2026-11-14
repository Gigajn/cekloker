"""scraper_core — kontrak adapter + parser scraper CekLoker (Fase 1)."""

from .base import (
    JobSourceAdapter,
    RawJob,
    SourceBlockedError,
    SourceFetchError,
    SourceNotPermittedError,
    allowed_by_robots,
    fetch_text,
    polite_delay,
    user_agent,
)
from .parsers import normalize_company, normalize_location, parse_posted_at, parse_salary

__all__ = [
    "JobSourceAdapter",
    "RawJob",
    "SourceBlockedError",
    "SourceFetchError",
    "SourceNotPermittedError",
    "allowed_by_robots",
    "fetch_text",
    "polite_delay",
    "user_agent",
    "normalize_company",
    "normalize_location",
    "parse_posted_at",
    "parse_salary",
]
