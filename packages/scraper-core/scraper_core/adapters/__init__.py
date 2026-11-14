"""Registry adapter job board CekLoker (Fase 1).

Satu tempat untuk mengimpor semua adapter + memeriksa statusnya.
Worker HANYA boleh memakai adapter yang `enabled=True`.
"""

from .career_page import CareerPageAdapter
from .glints import GlintsAdapter
from .indeed import IndeedAdapter
from .jobstreet import JobStreetAdapter
from .kalibrr import KalibrrAdapter

ADAPTERS = (GlintsAdapter, JobStreetAdapter, KalibrrAdapter, IndeedAdapter)

# Adapter halaman karier langsung (1 perusahaan = 1 board ATS / halaman custom).
# Bukan bagian ADAPTERS job board — diinstansiasi per perusahaan (board_url).
DIRECT_ADAPTERS = (CareerPageAdapter,)

__all__ = [
    "ADAPTERS",
    "GlintsAdapter",
    "JobStreetAdapter",
    "KalibrrAdapter",
    "IndeedAdapter",
    "CareerPageAdapter",
    "DIRECT_ADAPTERS",
]
