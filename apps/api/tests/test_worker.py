"""Test worker recheck (ADR-0002 + ARCH §3 aturan 2x).

Semua test memakai adapter PALSU — tidak ada HTTP live.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app import worker as worker_mod
from app.models import JobSnapshot
from app.services.scraper_import import (
    SourceBlockedError,
    SourceFetchError,
    SourceNotPermittedError,
)


class FakeAdapter:
    """check_active yang perilakunya diatur per test."""

    def __init__(self, behaviour):
        self.behaviour = behaviour  # True | False | Exception instance

    def check_active(self, url):
        if isinstance(self.behaviour, Exception):
            raise self.behaviour
        return self.behaviour


def _snapshot_statuses(db, job_id):
    rows = (
        db.query(JobSnapshot)
        .filter(JobSnapshot.job_id == job_id)
        .order_by(JobSnapshot.seen_at)
        .all()
    )
    return [r.status for r in rows]


def test_recheck_masih_buka_update_last_seen(db, seeded):
    job = seeded["job1"]
    before = job.last_seen_at
    result = worker_mod.recheck_job(db, job, adapter=FakeAdapter(True))
    assert result["outcome"] == "still_active"
    assert job.status == "active"
    assert job.missed_checks == 0
    assert job.last_seen_at >= before
    assert _snapshot_statuses(db, job.id) == ["active"]


def test_satu_kunjungan_hilang_belum_tutup(db, seeded):
    job = seeded["job1"]
    seen_before = job.last_seen_at
    result = worker_mod.recheck_job(db, job, adapter=FakeAdapter(False))
    assert result["outcome"] == "still_active"  # belum 2x
    assert result["missed_checks"] == 1
    assert job.status == "active"
    # last_seen_at TIDAK berubah — "terakhir terlihat buka" tetap jujur.
    assert job.last_seen_at == seen_before
    assert _snapshot_statuses(db, job.id) == ["missed"]


def test_dua_kunjungan_hilang_jadi_closed(db, seeded):
    job = seeded["job1"]
    worker_mod.recheck_job(db, job, adapter=FakeAdapter(False))
    result = worker_mod.recheck_job(db, job, adapter=FakeAdapter(False))
    assert result["outcome"] == "closed"
    assert job.status == "closed"
    assert job.missed_checks == 2
    assert _snapshot_statuses(db, job.id) == ["missed", "closed"]


def test_kunjungan_hilang_lalu_buka_lagi_reset(db, seeded):
    job = seeded["job1"]
    worker_mod.recheck_job(db, job, adapter=FakeAdapter(False))
    result = worker_mod.recheck_job(db, job, adapter=FakeAdapter(True))
    assert result["outcome"] == "still_active"
    assert job.missed_checks == 0
    assert job.status == "active"


def test_gagal_teknis_jadi_unknown_bukan_closed(db, seeded):
    job = seeded["job1"]
    for exc in (SourceFetchError("timeout"), SourceBlockedError("403")):
        result = worker_mod.recheck_job(db, job, adapter=FakeAdapter(exc))
        assert result["outcome"] == "unknown", exc
        assert job.status == "unknown"
    assert _snapshot_statuses(db, job.id) == ["unknown", "unknown"]


def test_adapter_dimatikan_jadi_skipped(db, seeded):
    job = seeded["job1"]
    result = worker_mod.recheck_job(
        db, job, adapter=FakeAdapter(SourceNotPermittedError("dilarang ToS")))
    assert result["outcome"] == "skipped"
    assert job.status == "active"  # tidak diubah apa pun
    assert _snapshot_statuses(db, job.id) == []


def test_refresh_jobs_mengurutkan_yang_paling_lama(db, seeded):
    # job2 dibuat terakhir di seed; ubah last_seen_at agar job1 paling tua.
    job1, job2 = seeded["job1"], seeded["job2"]
    job1.last_seen_at = datetime(2026, 11, 1, tzinfo=timezone.utc)
    job2.last_seen_at = datetime(2026, 11, 14, tzinfo=timezone.utc)
    db.commit()

    urutan = []

    def factory(job):
        urutan.append(str(job.id))
        return FakeAdapter(True)

    summary = worker_mod.refresh_jobs(db, limit=10, delay_s=0, adapter_factory=factory)
    assert summary["checked"] == 2
    assert summary["still_active"] == 2
    assert urutan[0] == str(job1.id)  # paling lama tidak dicek dulu


def test_refresh_satu_job_id(db, seeded):
    job1 = seeded["job1"]
    summary = worker_mod.refresh_jobs(
        db, job_id=job1.id, delay_s=0,
        adapter_factory=lambda job: FakeAdapter(False),
    )
    assert summary["checked"] == 1
    assert summary["still_active"] == 1  # 1x hilang saja
