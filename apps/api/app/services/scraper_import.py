"""Impor scraper-core dari repo ini — tanpa mengubah paket itu.

`scraper_core` tinggal di packages/scraper-core (bukan dependensi pip).
Supaya API + worker bisa memakainya baik saat dijalankan dari repo
maupun dari image Docker (PYTHONPATH berisi mount paket), modul ini
mencari paket itu di: (1) sys.path yang sudah ada, (2) PYTHONPATH,
(3) relatif terhadap root repo ini.

Bila paket TIDAK ditemukan (mis. API dijalankan tanpa mount paket),
modul ini TIDAK menggagalkan start aplikasi: endpoint baca tetap jalan,
tapi worker recheck mengembalikan `skipped` untuk semua job
(`SCRAPER_CORE_AVAILABLE = False`). Alasannya: API baca (janji produk
ke web) tidak boleh mati hanya karena paket scraper belum ter-mount.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

SCRAPER_CORE_AVAILABLE = False


def _try_import():
    global SCRAPER_CORE_AVAILABLE
    from scraper_core.base import RawJob, slugify_company  # noqa: F401
    from scraper_core.base import (  # noqa: F401
        SourceBlockedError,
        SourceFetchError,
        SourceNotPermittedError,
    )

    SCRAPER_CORE_AVAILABLE = True
    return RawJob, slugify_company, SourceBlockedError, SourceFetchError, SourceNotPermittedError


try:
    RawJob, slugify_company, SourceBlockedError, SourceFetchError, SourceNotPermittedError = (
        _try_import()
    )
except ImportError:
    repo_root = Path(__file__).resolve().parents[3]
    pkg_dir = repo_root / "packages" / "scraper-core"
    if pkg_dir.is_dir() and str(pkg_dir) not in sys.path:
        sys.path.insert(0, str(pkg_dir))
    try:
        RawJob, slugify_company, SourceBlockedError, SourceFetchError, SourceNotPermittedError = (
            _try_import()
        )
    except ImportError:
        # Fallback: API tetap bisa start tanpa scraper-core.
        # Kelas error lokal ini HANYA penanda tipe — tidak pernah
        # di-raise tanpa scraper-core, karena adapter pun tidak ada.
        class SourceNotPermittedError(Exception):  # type: ignore[no-redef]
            """Pengganti lokal bila scraper-core tidak ter-mount."""

        class SourceBlockedError(Exception):  # type: ignore[no-redef]
            """Pengganti lokal bila scraper-core tidak ter-mount."""

        class SourceFetchError(Exception):  # type: ignore[no-redef]
            """Pengganti lokal bila scraper-core tidak ter-mount."""

        RawJob = None  # type: ignore[assignment]

        def slugify_company(name: str) -> str:  # type: ignore[no-redef]
            """Salinan minimal slugify_company (base.py) untuk mode tanpa paket."""
            slug = re.sub(r"[^a-z0-9]+", "-", name.strip().lower()).strip("-")
            return slug or "perusahaan"
