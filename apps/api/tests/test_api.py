"""Test endpoint API CekLoker (TestClient + SQLite in-memory)."""

from __future__ import annotations


def test_health_ok(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["db"] == "ok"


def test_list_jobs_default_hanya_active(client, seeded):
    resp = client.get("/api/v1/jobs")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["total"] == 2  # job3 closed tidak tampil
    assert all(item["status"] == "active" for item in data["items"])
    assert data["page"] == 1 and data["per_page"] == 20


def test_job_out_memuat_kontrak_web(client, seeded):
    resp = client.get("/api/v1/jobs")
    item = resp.json()["items"][0]
    for kunci in (
        "id", "title", "company", "location", "work_type",
        "salary_min", "salary_max", "salary_currency", "posted_at",
        "posted_at_certain", "first_seen_at", "last_seen_at",
        "status", "source", "source_url",
    ):
        assert kunci in item, f"kontrak web kurang: {kunci}"
    assert set(item["company"].keys()) == {"name", "slug"}


def test_filter_status_closed(client, seeded):
    resp = client.get("/api/v1/jobs", params={"status": "closed"})
    assert resp.json()["total"] == 1


def test_filter_status_tidak_valid(client, seeded):
    resp = client.get("/api/v1/jobs", params={"status": "buka"})
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "validation_error"


def test_filter_q_dan_lokasi(client, seeded):
    resp = client.get("/api/v1/jobs", params={"q": "programmer"})
    assert resp.json()["total"] == 1
    resp = client.get("/api/v1/jobs", params={"location": "bandung"})
    assert resp.json()["total"] == 1


def test_filter_gaji_min(client, seeded):
    # gaji_min=6jt: hanya job1 (min 5jt) TIDAK lolos, job2 tanpa gaji tidak lolos.
    resp = client.get("/api/v1/jobs", params={"gaji_min": 6_000_000})
    assert resp.json()["total"] == 0
    resp = client.get("/api/v1/jobs", params={"gaji_min": 5_000_000})
    assert resp.json()["total"] == 1


def test_filter_skor_min(client, seeded):
    # Maju Mixed 56; Fiktif Belum cukup data (score null -> tidak lolos).
    resp = client.get("/api/v1/jobs", params={"skor_min": 50})
    assert resp.json()["total"] == 2  # kedua lowongan Maju
    resp = client.get("/api/v1/jobs", params={"skor_min": 60})
    assert resp.json()["total"] == 0


def test_filter_rentang_tanggal_buka(client, seeded):
    resp = client.get("/api/v1/jobs", params={
        "posted_from": "2026-11-13", "posted_to": "2026-11-13",
    })
    assert resp.json()["total"] == 2
    resp = client.get("/api/v1/jobs", params={"posted_from": "2026-11-14"})
    assert resp.json()["total"] == 0


def test_paginasi(client, seeded):
    resp = client.get("/api/v1/jobs", params={"per_page": 1, "page": 2})
    data = resp.json()
    assert data["total"] == 2 and data["pages"] == 2 and len(data["items"]) == 1


def test_get_job_detail_dan_404(client, seeded):
    job_id = str(seeded["job1"].id)
    resp = client.get(f"/api/v1/jobs/{job_id}")
    assert resp.status_code == 200
    assert resp.json()["title"] == "Staff Programmer"
    assert resp.json()["posted_at_certain"] is True
    resp = client.get("/api/v1/jobs/00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "not_found"


def test_error_tidak_bocorkan_stack_trace(client, seeded):
    resp = client.get("/api/v1/jobs/bukan-uuid")
    assert resp.status_code == 422
    assert "Traceback" not in resp.text
    assert "stack" not in resp.text.lower()


def test_companies_list_dan_filter_label(client, seeded):
    resp = client.get("/api/v1/companies")
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert resp.json()["total"] == 2
    by_slug = {i["slug"]: i for i in items}
    assert by_slug["pt-contoh-maju-bersama"]["score"] == 56
    assert by_slug["pt-contoh-maju-bersama"]["label"] == "Mixed"
    assert by_slug["pt-fiktif-teknologi-nusantara"]["score"] is None
    assert by_slug["pt-fiktif-teknologi-nusantara"]["label"] == "Belum cukup data"
    resp = client.get("/api/v1/companies", params={"label": "Mixed"})
    assert resp.json()["total"] == 1


def test_company_detail_memuat_sinyal_dan_bukti(client, seeded):
    resp = client.get("/api/v1/companies/pt-contoh-maju-bersama")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["score"] == 56 and data["label"] == "Mixed"
    assert len(data["signals"]) == 3
    for kunci in ("category", "key", "points", "evidence_url",
                  "evidence_text", "evidence_date", "source", "confidence"):
        assert kunci in data["signals"][0], f"kontrak sinyal kurang: {kunci}"
    assert all(s["evidence_url"] for s in data["signals"])
    resp = client.get("/api/v1/companies/tidak-ada")
    assert resp.status_code == 404


def test_signals_per_company(client, seeded):
    cid = str(seeded["fiktif"].id)
    resp = client.get("/api/v1/signals", params={"company_id": cid})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    # K4: sinyal google_places WAJIB evidence_text null.
    places = [s for s in data if s["source"] == "google_places"]
    assert len(places) == 1 and places[0]["evidence_text"] is None
    resp = client.get("/api/v1/signals",
                      params={"company_id": cid, "category": "reputasi"})
    assert len(resp.json()) == 2


def test_login_salah_dan_benar(client, seeded):
    resp = client.post("/api/v1/admin/login",
                       json={"email": "giga@contoh.invalid", "password": "salah"})
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "invalid_credentials"
    resp = client.post("/api/v1/admin/login",
                       json={"email": "tidak@ada.invalid", "password": "salah"})
    assert resp.status_code == 401  # pesan sama — jangan bocorkan email ada/tidak
    resp = client.post("/api/v1/admin/login",
                       json={"email": "giga@contoh.invalid", "password": "rahasia-kuat"})
    assert resp.status_code == 200
    assert resp.json()["token"]


def test_refresh_butuh_auth(client, seeded):
    resp = client.post("/api/v1/admin/refresh", json={})
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "unauthorized"
    resp = client.post("/api/v1/admin/refresh", json={},
                       headers={"Authorization": "Bearer token-palsu"})
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "unauthorized"


def test_refresh_dengan_auth_memanggil_worker(client, seeded, admin_token, monkeypatch):
    from app.routers import admin as admin_mod

    calls = {}

    def fake_refresh(db, limit=20, job_id=None):
        calls["limit"] = limit
        calls["job_id"] = job_id
        return {"checked": 1, "still_active": 1, "closed": 0,
                "unknown": 0, "skipped": 0,
                "results": [{"job_id": "x", "outcome": "still_active"}]}

    monkeypatch.setattr(admin_mod.worker_mod, "refresh_jobs", fake_refresh)
    resp = client.post("/api/v1/admin/refresh", json={"limit": 5},
                       headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["checked"] == 1 and data["still_active"] == 1
    assert calls["limit"] == 5
