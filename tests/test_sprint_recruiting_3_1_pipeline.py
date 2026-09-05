"""Sprint Recruiting 3.1 — full pipeline persistence + TEST traffic exclusion."""

from __future__ import annotations

import uuid

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.recruiting_enterprise.api.register import register_recruiting_enterprise_routes
from services.recruiting_ops import reset_recruiting_ops_for_tests
from services.recruiting_ops.attribution import (
    classify_traffic,
    is_test_traffic,
    production_cohort,
)

OPS = "/api/recruiting-ops/v1"


@pytest.fixture
def app() -> web.Application:
    application = web.Application()
    register_recruiting_enterprise_routes(application)
    return application


@pytest.fixture
async def client(app: web.Application):
    async with TestClient(TestServer(app)) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def reset_ops():
    reset_recruiting_ops_for_tests()
    yield
    reset_recruiting_ops_for_tests()


def _hdr(org: str, role: str = "platform_owner") -> dict[str, str]:
    return {"X-Organization-Id": org, "X-Role": role, "X-Recruiting-Organization-Id": org}


def test_test_traffic_markers():
    assert is_test_traffic({"utm_source": "e2e_test", "utm_campaign": "vanguard_e2e"})
    assert is_test_traffic({"utm_campaign": "e2e-historical"})
    assert is_test_traffic({"traffic_class": "TEST"})
    assert is_test_traffic({"external_id": "e2e-timofii-d88c3ef1"})
    assert not is_test_traffic({"source": "vanguard", "utm_campaign": "launch"})
    assert classify_traffic({"utm_source": "e2e_test"}) == "TEST"
    assert classify_traffic({"source": "vanguard"}) == "PRODUCTION"
    cohort = production_cohort(
        [{"id": "t", "utm_source": "e2e_test"}, {"id": "p", "source": "vanguard"}],
        [{"id": "c1", "lead_id": "t"}, {"id": "c2", "lead_id": "p", "source": "vanguard"}],
    )
    assert [item["id"] for item in cohort["leads"]] == ["p"]
    assert [item["id"] for item in cohort["candidates"]] == ["c2"]
    assert cohort["excluded_test_leads"] == 1
    assert cohort["excluded_test_candidates"] == 1


async def _json(res):
    body = await res.json()
    assert res.status in {200, 201}, body
    return body


async def test_full_pipeline_persists_and_excludes_test_traffic(client: TestClient):
    org = f"rec-31-{uuid.uuid4().hex[:8]}"
    h = _hdr(org)

    vacancy = await _json(await client.post(f"{OPS}/vacancies", json={"title": "Логист Vanguard"}, headers=h))
    vacancy_id = vacancy["item"]["id"]

    real = await _json(
        await client.post(
            f"{OPS}/leads",
            json={
                "name": "Анна Коваль",
                "phone": "+380501112233",
                "email": "anna.31@example.com",
                "source": "vanguard",
                "vacancy_id": vacancy_id,
            },
            headers=h,
        )
    )
    real_lead = real["item"]
    assert real_lead["traffic_class"] == "PRODUCTION"
    real_id = real_lead["id"]

    test = await _json(
        await client.post(
            f"{OPS}/leads",
            json={
                "name": "E2E Candidate",
                "phone": "+37281090000",
                "email": "e2e.31@example.com",
                "source": "vanguard",
                "utm_source": "e2e_test",
                "utm_campaign": "vanguard_e2e",
                "vacancy_id": vacancy_id,
            },
            headers=h,
        )
    )
    test_lead = test["item"]
    assert test_lead["traffic_class"] == "TEST"
    test_id = test_lead["id"]

    listed = await _json(await client.get(f"{OPS}/leads", headers=h))
    listed_ids = {item["id"] for item in listed["items"]}
    assert {real_id, test_id} <= listed_ids

    assigned = await _json(await client.post(f"{OPS}/leads/{test_id}/assign", json={"assignee": "recruiter.ira"}, headers=h))
    assert assigned["item"]["assignee"] == "recruiter.ira"

    qualified = await _json(await client.post(f"{OPS}/leads/{test_id}/qualify", headers=h))
    assert qualified["item"]["status"] == "qualified"

    converted = await _json(await client.post(f"{OPS}/leads/{test_id}/convert", headers=h))
    candidate = converted["item"]
    candidate_id = candidate["id"]
    assert candidate["pipeline_stage"] == "QUALIFIED"
    assert candidate["assignee"] == "recruiter.ira"
    assert candidate["traffic_class"] == "TEST"

    cand_assign = await _json(
        await client.post(f"{OPS}/candidates/{candidate_id}/assign", json={"assignee": "recruiter.ira"}, headers=h)
    )
    assert cand_assign["item"]["assignee"] == "recruiter.ira"

    stage_q = await _json(
        await client.post(f"{OPS}/candidates/{candidate_id}/stage", json={"pipeline_stage": "QUALIFIED"}, headers=h)
    )
    assert stage_q["item"]["pipeline_stage"] == "QUALIFIED"

    interview = await _json(await client.post(f"{OPS}/candidates/{candidate_id}/interview", json={}, headers=h))
    assert interview["item"]["pipeline_stage"] == "INTERVIEW"
    assert interview.get("interview_scheduled") is True

    approved = await _json(
        await client.post(f"{OPS}/candidates/{candidate_id}/stage", json={"pipeline_stage": "APPROVED"}, headers=h)
    )
    assert approved["item"]["pipeline_stage"] == "APPROVED"

    hired = await _json(
        await client.post(f"{OPS}/candidates/{candidate_id}/stage", json={"pipeline_stage": "HIRED"}, headers=h)
    )
    assert hired["item"]["pipeline_stage"] == "HIRED"

    reloaded = await _json(await client.get(f"{OPS}/candidates", headers=h))
    again = next(item for item in reloaded["items"] if item["id"] == candidate_id)
    assert again["pipeline_stage"] == "HIRED"
    assert again["assignee"] == "recruiter.ira"
    assert any(item["id"] == candidate_id for item in reloaded["pipeline"]["HIRED"])

    lead_reload = await _json(await client.get(f"{OPS}/leads", headers=h))
    test_again = next(item for item in lead_reload["items"] if item["id"] == test_id)
    assert test_again["assignee"] == "recruiter.ira"
    assert test_again["status"] == "converted"
    assert test_again["candidate_id"] == candidate_id

    activity = await _json(await client.get(f"{OPS}/activity", headers=h))
    actions = [row["action"] for row in activity["items"]]
    assert "lead_assigned" in actions
    assert "lead_qualified" in actions
    assert "lead_converted" in actions
    assert "candidate_assigned" in actions
    assert "interview_scheduled" in actions
    moves = [row for row in activity["items"] if row["action"] == "pipeline_moved"]
    pairs = {
        ((row.get("payload") or {}).get("from_stage"), (row.get("payload") or {}).get("to_stage"))
        for row in moves
    }
    assert ("QUALIFIED", "INTERVIEW") in pairs
    assert ("INTERVIEW", "APPROVED") in pairs
    assert ("APPROVED", "HIRED") in pairs

    tasks = await _json(await client.get(f"{OPS}/tasks", headers=h))
    assert any("интервью" in str(item.get("title") or "").lower() and item.get("candidate_id") == candidate_id for item in tasks["items"])

    await _json(await client.post(f"{OPS}/leads/{real_id}/qualify", headers=h))
    await _json(await client.post(f"{OPS}/leads/{real_id}/convert", headers=h))

    analytics = await _json(await client.get(f"{OPS}/analytics", headers=h))
    assert analytics["traffic"]["production_only"] is True
    assert analytics["traffic"]["excluded_test_leads"] >= 1
    assert analytics["traffic"]["excluded_test_candidates"] >= 1
    assert analytics["funnel"]["leads"] == 1
    assert analytics["funnel"]["qualified"] == 1
    assert analytics["funnel"]["hired"] == 0
    assert not any(row["id"] == "e2e_test" for row in analytics["by_source"])

    ads = await _json(await client.get(f"{OPS}/ads/control-center?project=vanguard", headers=h))
    assert ads["traffic"]["excluded_test_leads"] >= 1
    assert ads["fake_data"] is False
    sources = {row["source"] for row in (ads.get("source_analytics") or {}).get("items") or []}
    assert "e2e_test" not in sources


async def test_provider_regression_stays_honest(client: TestClient):
    org = f"rec-31-reg-{uuid.uuid4().hex[:8]}"
    h = _hdr(org)
    health = await _json(await client.get(f"{OPS}/health"))
    assert health["telegram"]["frozen"] is True
    assert health["ads"]["connected"] is False
    ads = await _json(await client.get(f"{OPS}/ads/control-center?project=vanguard", headers=h))
    assert ads["connected"] is False
    assert ads["fake_data"] is False
    assert ads["providers"]["meta"]["status"] == "not_connected"
    assert ads["providers"]["google"]["status"] == "not_connected"
    providers = await _json(await client.get(f"{OPS}/providers", headers=h))
    by_id = {str(item.get("provider")): item for item in providers.get("items") or [] if isinstance(item, dict)}
    for key in ("whatsapp", "meta", "google"):
        card = by_id[key]
        assert card["connected"] is False
        assert str(card.get("tracking_status") or "").upper() == "WAITING_PROVIDER"
        assert str(card.get("status") or "").upper() in {"NOT_CONFIGURED", "WAITING_PROVIDER", "DISCONNECTED", "DISABLED"}
    msg = await _json(await client.post(f"{OPS}/messages", json={"channel": "whatsapp", "to": "1", "body": "hi"}, headers=h))
    assert msg["item"]["status"] == "WAITING_PROVIDER"
