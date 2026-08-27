"""Sprint Recruiting 1.3 — live Vanguard application → Recruiting funnel."""

from __future__ import annotations

import uuid

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.recruiting_enterprise.api.register import register_recruiting_enterprise_routes
from applications.vanguard_site.api.register import register_vanguard_site_routes
from services.recruiting_ops import reset_recruiting_ops_for_tests

OPS = "/api/recruiting-ops/v1"
SITE = "/api/vanguard-site/v1"


@pytest.fixture
def app() -> web.Application:
    application = web.Application()
    register_recruiting_enterprise_routes(application)
    register_vanguard_site_routes(application)
    return application


@pytest.fixture
async def client(app: web.Application):
    async with TestClient(TestServer(app)) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def reset_ops(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.delenv("VANGUARD_WEBSITE_URL", raising=False)
    reset_recruiting_ops_for_tests()
    yield
    reset_recruiting_ops_for_tests()


def _hdr(org: str = "ados", role: str = "platform_owner") -> dict[str, str]:
    return {"X-Organization-Id": org, "X-Role": role}


async def test_vanguard_form_creates_recruiting_lead(client: TestClient):
    apply = await client.post(
        f"{SITE}/applications",
        json={
            "first_name": "E2E_LIVE",
            "last_name": "Applicant",
            "email": f"e2e.live.{uuid.uuid4().hex[:8]}@example.com",
            "country": "UA",
            "preferred_language": "ru",
            "unit": "Operations",
            "program": "Frontend Recruiter",
            "message": "Хочу в команду",
            "utm_source": "organic",
            "utm_medium": "website",
            "utm_campaign": "career-q3",
            "visitor_id": "vis-1",
            "session_id": "ses-1",
            "referrer": "https://example.com",
            "landing_page": "/vanguard",
        },
    )
    assert apply.status == 201
    body = await apply.json()
    assert body["ok"] is True
    assert body["application_received"] is True
    reference = body["reference"]
    assert reference.startswith("VG-")
    item = body["item"]
    assert item["source"] == "vanguard"
    assert item["project_key"] == "vanguard"
    assert item["external_id"] == reference
    assert item["country"] == "UA"
    assert item["preferred_language"] == "ru"
    assert item["unit_of_interest"] == "Operations"
    assert item["program_of_interest"] == "Frontend Recruiter"
    assert item["application_message"] == "Хочу в команду"
    assert item["utm_campaign"] == "career-q3"

    listed = await (await client.get(f"{OPS}/leads?project=vanguard", headers=_hdr())).json()
    assert any(row["external_id"] == reference for row in listed["items"])
    activity = await (await client.get(f"{OPS}/activity?project=vanguard", headers=_hdr())).json()
    assert any(row["action"] == "vanguard_lead_ingested" for row in activity["items"])


async def test_duplicate_application_is_idempotent(client: TestClient):
    payload = {
        "first_name": "Dup",
        "email": f"dup.live.{uuid.uuid4().hex[:8]}@example.com",
        "program": "Same Role",
    }
    first = await client.post(f"{SITE}/applications", json=payload)
    second = await client.post(f"{SITE}/applications", json=payload)
    assert first.status == 201
    assert second.status == 200
    a = await first.json()
    b = await second.json()
    assert b["duplicate"] is True
    assert a["item"]["id"] == b["item"]["id"]


async def test_qualify_convert_interview_persists(client: TestClient):
    applied = await client.post(
        f"{SITE}/applications",
        json={"first_name": "Pipeline", "email": f"pipe.{uuid.uuid4().hex[:8]}@example.com", "program": "Ops"},
    )
    lead_id = (await applied.json())["item"]["id"]
    h = _hdr()
    q = await client.post(f"{OPS}/leads/{lead_id}/qualify", headers=h, json={})
    assert q.status == 200
    conv = await client.post(f"{OPS}/leads/{lead_id}/convert", headers=h, json={})
    assert conv.status in {200, 201}
    cand_id = (await conv.json())["item"]["id"]
    moved = await client.post(f"{OPS}/candidates/{cand_id}/stage", headers=h, json={"pipeline_stage": "INTERVIEW"})
    assert moved.status == 200
    listed = await (await client.get(f"{OPS}/candidates?project=vanguard", headers=h)).json()
    row = next(item for item in listed["items"] if item["id"] == cand_id)
    assert row["pipeline_stage"] == "INTERVIEW"


async def test_tracking_contract_and_forbidden_fields(client: TestClient):
    ok = await client.post(
        f"{SITE}/events",
        json={"event_type": "page_view", "visitor_id": "v1", "session_id": "s1", "page": "/vanguard", "event_id": str(uuid.uuid4())},
    )
    assert ok.status == 201
    bad = await client.post(f"{SITE}/events", json={"event_type": "hack", "password": "nope"})
    assert bad.status == 400
    blob = await bad.json()
    assert "password" not in (blob.get("item") or {})


async def test_integration_website_independent_from_recruiting(client: TestClient):
    integ = await (await client.get(f"{OPS}/projects/vanguard/integration", headers=_hdr())).json()
    assert integ["website_status"]["code"] == "NOT_CONFIGURED"
    assert integ["website_status"]["reason_ru"]
    assert integ["integration_status"]["code"] in {"CONNECTED", "DEGRADED", "DISCONNECTED"}
    assert integ["website_status"]["code"] != integ["integration_status"]["code"] or integ["integration_status"]["reason_ru"]
    checked = await client.post(f"{OPS}/projects/vanguard/integration/check", headers=_hdr())
    assert checked.status == 200
    body = await checked.json()
    assert body["last_check_at"]
    assert any(stage["reason_ru"] for stage in body["stages"])


async def test_campaign_model_prepares_ads_without_connecting(client: TestClient):
    created = await client.post(
        f"{OPS}/campaigns",
        json={
            "name": "Career Organic",
            "project_key": "vanguard",
            "source": "vanguard",
            "channel": "Organic",
            "medium": "website",
            "campaign_code": "career-q3",
            "landing_url": "/vanguard",
        },
        headers=_hdr(),
    )
    assert created.status == 201
    item = (await created.json())["item"]
    assert item["channel"] == "Organic"
    assert item["ads_api"] == "not_connected"
    overview = await (await client.get(f"{OPS}/projects/vanguard", headers=_hdr())).json()
    assert overview["marketing"]["ads_apis"]["meta"] == "not_connected"
    assert overview["funnel"]["steps"][0]["id"] == "visit"
