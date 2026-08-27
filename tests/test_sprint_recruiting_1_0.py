"""Sprint Recruiting 1.0 — Recruiting Ops desk + Vanguard inbound contract."""

from __future__ import annotations

import uuid

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.recruiting_enterprise.api.register import register_recruiting_enterprise_routes
from services.recruiting_ops import reset_recruiting_ops_for_tests
from services.recruiting_ops.rbac import can, normalize_role

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


def _hdr(org: str, role: str = "recruiter") -> dict[str, str]:
    return {"X-Organization-Id": org, "X-Role": role}


async def test_health_roles_and_vanguard_contract(client: TestClient):
    res = await client.get(f"{OPS}/health")
    assert res.status == 200
    body = await res.json()
    assert body["sprint"] in {"recruiting_1.0", "recruiting_1.1", "recruiting_1.2", "recruiting_1.3", "recruiting_1.4", "recruiting_1.5", "recruiting_1.6", "recruiting_1.7", "recruiting_1.8", "recruiting_1.9"}
    assert body["vanguard"]["connected"] is False
    assert body["visits_available"] is False

    roles = await (await client.get(f"{OPS}/roles")).json()
    ids = {r["id"] for r in roles["roles"]}
    assert {"owner", "recruiter", "hiring_manager", "observer"} <= ids

    contract = await (await client.get(f"{OPS}/vanguard/contract")).json()
    assert contract["connected"] is False
    assert contract["inbound"]["path"] == f"{OPS}/vanguard/leads"
    assert contract["inbound"]["auth"] == "hmac-sha256"
    assert contract["inbound"]["secret_frontend_exposure"] is False
    assert "first_name|name" in contract["inbound"]["required"]
    assert "TELEGRAM" in contract["channels_prepared"]
    assert contract["ads_apis"]["meta"] == "not_connected"


async def test_full_user_cycle_lead_to_pipeline_and_analytics(client: TestClient):
    org = f"rec-cycle-{uuid.uuid4().hex[:8]}"
    h = _hdr(org, "platform_owner")

    vacancy = await client.post(f"{OPS}/vacancies", json={"title": "Рекрутер Vanguard"}, headers=h)
    assert vacancy.status == 201
    vacancy_id = (await vacancy.json())["item"]["id"]

    campaign = await client.post(
        f"{OPS}/campaigns",
        json={"name": "Career site", "source": "vanguard", "vacancy_id": vacancy_id},
        headers=h,
    )
    assert campaign.status == 201
    campaign_id = (await campaign.json())["item"]["id"]

    created = await client.post(
        f"{OPS}/leads",
        json={
            "name": "Анна Коваль",
            "phone": "+380501112233",
            "email": "anna@example.com",
            "source": "vanguard",
            "campaign_id": campaign_id,
            "vacancy_id": vacancy_id,
        },
        headers=h,
    )
    assert created.status == 201
    lead = (await created.json())["item"]
    lead_id = lead["id"]
    assert lead["data_mode"] == "REAL"

    listed = await client.get(f"{OPS}/leads", headers=h)
    assert listed.status == 200
    names = [x["name"] for x in (await listed.json())["items"]]
    assert "Анна Коваль" in names

    assigned = await client.post(f"{OPS}/leads/{lead_id}/assign", json={"assignee": "recruiter.ira"}, headers=h)
    assert assigned.status == 200
    assert (await assigned.json())["item"]["assignee"] == "recruiter.ira"

    noted = await client.post(f"{OPS}/leads/{lead_id}/notes", json={"notes": "Сильный профиль, связаться сегодня"}, headers=h)
    assert noted.status == 200
    assert "Сильный профиль" in ((await noted.json())["item"].get("notes") or "")

    qualified = await client.post(f"{OPS}/leads/{lead_id}/qualify", headers=h)
    assert qualified.status == 200
    assert (await qualified.json())["item"]["status"] == "qualified"

    converted = await client.post(f"{OPS}/leads/{lead_id}/convert", headers=h)
    assert converted.status == 201
    candidate = (await converted.json())["item"]
    candidate_id = candidate["id"]
    assert candidate["lead_id"] == lead_id
    assert candidate["pipeline_stage"] == "QUALIFIED"

    pipe = await client.get(f"{OPS}/candidates", headers=h)
    assert pipe.status == 200
    pipe_body = await pipe.json()
    assert any(c["id"] == candidate_id for c in pipe_body["items"])
    assert any(c["id"] == candidate_id for c in pipe_body["pipeline"]["QUALIFIED"])

    moved = await client.post(
        f"{OPS}/candidates/{candidate_id}/stage",
        json={"pipeline_stage": "INTERVIEW"},
        headers=h,
    )
    assert moved.status == 200
    assert (await moved.json())["item"]["pipeline_stage"] == "INTERVIEW"

    refreshed = await client.get(f"{OPS}/candidates", headers=h)
    refreshed_body = await refreshed.json()
    again = next(c for c in refreshed_body["items"] if c["id"] == candidate_id)
    assert again["pipeline_stage"] == "INTERVIEW"
    assert any(c["id"] == candidate_id for c in refreshed_body["pipeline"]["INTERVIEW"])

    analytics = await (await client.get(f"{OPS}/analytics", headers=h)).json()
    assert analytics["visits"]["available"] is False
    assert analytics["visits"]["message_ru"] == "Нет данных о посещениях"
    assert analytics["visits"]["count"] is None
    assert analytics["funnel"]["leads"] >= 1
    assert analytics["funnel"]["qualified"] >= 1
    assert analytics["funnel"]["interviews"] >= 1
    assert analytics["funnel"]["visits"] is None
    assert any(row["count"] >= 1 for row in analytics["by_source"] if row["id"] == "vanguard")
    assert any(row["id"] == campaign_id for row in analytics["by_campaign"])
    assert any(row["id"] == vacancy_id for row in analytics["by_vacancy"])

    activity = await (await client.get(f"{OPS}/activity", headers=h)).json()
    actions = {a["action"] for a in activity["items"]}
    assert "lead_created" in actions
    assert "lead_assigned" in actions
    assert "note_added" in actions
    assert "lead_qualified" in actions
    assert "lead_converted" in actions
    assert "pipeline_moved" in actions

    dash = await (await client.get(f"{OPS}/dashboard", headers=h)).json()
    assert dash["cards"]["leads"] >= 1
    assert dash["cards"]["candidates"] >= 1
    assert dash["visits"]["message_ru"] == "Нет данных о посещениях"


async def test_tasks_overdue_and_manual_communication(client: TestClient):
    org = f"rec-tasks-{uuid.uuid4().hex[:8]}"
    h = _hdr(org)
    lead = await client.post(f"{OPS}/leads", json={"name": "Пётр"}, headers=h)
    lead_id = (await lead.json())["item"]["id"]
    overdue = await client.post(
        f"{OPS}/tasks",
        json={"title": "Позвонить", "lead_id": lead_id, "assignee": "ira", "due_date": "2020-01-01", "notes": "утро"},
        headers=h,
    )
    assert overdue.status == 201
    nxt = await client.post(
        f"{OPS}/tasks",
        json={"title": "Провести интервью", "lead_id": lead_id, "due_date": "2099-01-01"},
        headers=h,
    )
    assert nxt.status == 201
    dash = await (await client.get(f"{OPS}/dashboard", headers=h)).json()
    assert dash["cards"]["overdue_tasks"] >= 1
    assert dash["cards"]["next_tasks"] >= 1
    assert any(t["title"] == "Позвонить" for t in dash["overdue_tasks"])
    assert any(t["title"] == "Провести интервью" for t in dash["next_tasks"])

    comm = await client.post(
        f"{OPS}/communications",
        json={"channel": "PHONE", "body": "Позвонили кандидату — ожидает решение.", "lead_id": lead_id},
        headers=h,
    )
    assert comm.status == 201
    item = (await comm.json())["item"]
    assert item["channel"] == "PHONE"
    assert item["sent"] is False
    assert item["body"] == "Позвонили кандидату — ожидает решение."


async def test_org_isolation_and_owner_access(client: TestClient):
    await client.post(f"{OPS}/leads", json={"name": "OrgA"}, headers=_hdr("org-a"))
    await client.post(f"{OPS}/leads", json={"name": "OrgB"}, headers=_hdr("org-b"))
    a = [x["name"] for x in (await (await client.get(f"{OPS}/leads", headers=_hdr("org-a"))).json())["items"]]
    b = [x["name"] for x in (await (await client.get(f"{OPS}/leads", headers=_hdr("org-b"))).json())["items"]]
    assert "OrgA" in a and "OrgB" not in a
    assert "OrgB" in b and "OrgA" not in b

    owner = await client.post(
        f"{OPS}/leads",
        json={"name": "Owner lead"},
        headers=_hdr("org-po", "platform_owner"),
    )
    assert owner.status == 201

    forbidden = await client.post(
        f"{OPS}/leads",
        json={"name": "Blocked"},
        headers=_hdr("org-rbac", "observer"),
    )
    assert forbidden.status == 403
    listed = await client.get(f"{OPS}/leads", headers=_hdr("org-rbac", "observer"))
    assert listed.status == 200


async def test_validation_rejects_empty_lead(client: TestClient):
    res = await client.post(f"{OPS}/leads", json={"phone": "1"}, headers=_hdr("org-val"))
    assert res.status == 400
    assert (await res.json())["error"] == "validation"


def test_rbac_matrix_unit():
    assert can("observer", "list")
    assert not can("observer", "create")
    assert can("recruiter", "create")
    assert can("recruiter", "convert")
    assert can("hiring_manager", "qualify")
    assert not can("hiring_manager", "convert")
    assert can("platform_owner", "admin")
    assert can("platform_owner", "convert")
    assert normalize_role("viewer") == "observer"
    assert normalize_role("hr") == "recruiter"
    assert normalize_role("platformowner") == "platform_owner"
