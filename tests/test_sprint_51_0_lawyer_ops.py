"""Sprint 51.0 — Lawyer Operator Desk (legal-ops durable CRM)."""

from __future__ import annotations

import uuid

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.legal_enterprise.api.register import register_legal_enterprise_routes
from services.legal_ops import reset_legal_ops_for_tests
from services.legal_ops.rbac import can, normalize_role

OPS = "/api/legal-ops/v1"


@pytest.fixture
def app() -> web.Application:
    application = web.Application()
    register_legal_enterprise_routes(application)
    return application


@pytest.fixture
async def client(app: web.Application):
    async with TestClient(TestServer(app)) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def reset_ops():
    reset_legal_ops_for_tests()
    yield
    reset_legal_ops_for_tests()


def _hdr(org: str, role: str = "lawyer") -> dict[str, str]:
    return {"X-Organization-Id": org, "X-Role": role}


async def test_health_and_roles(client: TestClient):
    res = await client.get(f"{OPS}/health")
    assert res.status == 200
    body = await res.json()
    assert body["sprint"] in {"51.0", "51.1", "3.1", "3.2", "3.3", "3.4", "3.5", "3.6"}
    assert body["google_calendar"]["status"] in {"needs_config", "connected", "error"}
    roles = await client.get(f"{OPS}/roles")
    assert roles.status == 200
    payload = await roles.json()
    role_list = payload.get("roles") or payload.get("items") or []
    ids = {r["id"] for r in role_list}
    assert {"owner", "managing_partner", "lawyer", "paralegal", "admin", "observer"} <= ids


async def test_crud_lifecycle_and_activity(client: TestClient):
    org = f"lex-test-a-{uuid.uuid4().hex[:8]}"
    h = _hdr(org, "lawyer")

    c = await client.post(f"{OPS}/clients", json={"name": "Иванов И.И.", "email": "a@ex.com"}, headers=h)
    assert c.status == 201
    client_id = (await c.json())["item"]["id"]

    case = await client.post(
        f"{OPS}/cases",
        json={"title": "Дело №1", "client_id": client_id},
        headers=h,
    )
    assert case.status == 201
    case_id = (await case.json())["item"]["id"]

    contract = await client.post(
        f"{OPS}/contracts",
        json={"title": "Договор услуг", "client_id": client_id, "case_id": case_id},
        headers=h,
    )
    assert contract.status == 201
    contract_id = (await contract.json())["item"]["id"]

    doc = await client.post(
        f"{OPS}/documents",
        json={"title": "Иск", "case_id": case_id, "content": "текст иска"},
        headers=h,
    )
    assert doc.status == 201

    task = await client.post(
        f"{OPS}/tasks",
        json={"title": "Подать возражение", "kind": "deadline", "case_id": case_id, "due_at": "2026-08-20T10:00:00"},
        headers=h,
    )
    assert task.status == 201
    task_id = (await task.json())["item"]["id"]

    hearing = await client.post(
        f"{OPS}/hearings",
        json={"title": "Предварительное", "court_name": "Арбитраж", "scheduled_at": "2026-08-12T15:00:00", "case_id": case_id},
        headers=h,
    )
    assert hearing.status == 201

    cal = await client.post(
        f"{OPS}/calendar",
        json={"title": "Совещание", "starts_at": "2026-08-13T09:00:00", "ends_at": "2026-08-13T10:00:00"},
        headers=h,
    )
    assert cal.status == 201

    done = await client.post(f"{OPS}/tasks/{task_id}/complete", headers=h)
    assert done.status == 200
    assert (await done.json())["item"]["status"] == "done"

    approved = await client.post(
        f"{OPS}/contracts/{contract_id}",
        json={"approval_status": "approved"},
        headers=h,
    )
    assert approved.status == 200

    ai = await client.post(
        f"{OPS}/ai/analyze",
        json={"target": "contract", "target_id": contract_id, "text": "риски"},
        headers=h,
    )
    assert ai.status == 200
    assert (await ai.json())["ok"] is True

    act = await client.get(f"{OPS}/activity", headers=h)
    assert act.status == 200
    actions = {a["action"] for a in (await act.json())["items"]}
    assert "client_created" in actions
    assert "case_created" in actions
    assert "document_uploaded" in actions
    assert "task_completed" in actions
    assert "ai_analysis_executed" in actions

    dash = await client.get(f"{OPS}/dashboard", headers=h)
    assert dash.status == 200
    cards = (await dash.json())["cards"]
    assert cards["clients"] >= 1
    assert cards["open_cases"] >= 1


async def test_org_isolation(client: TestClient):
    await client.post(f"{OPS}/clients", json={"name": "OrgA"}, headers=_hdr("org-a"))
    await client.post(f"{OPS}/clients", json={"name": "OrgB"}, headers=_hdr("org-b"))
    a = await client.get(f"{OPS}/clients", headers=_hdr("org-a"))
    b = await client.get(f"{OPS}/clients", headers=_hdr("org-b"))
    names_a = [x["name"] for x in (await a.json())["items"]]
    names_b = [x["name"] for x in (await b.json())["items"]]
    assert "OrgA" in names_a and "OrgB" not in names_a
    assert "OrgB" in names_b and "OrgA" not in names_b


async def test_rbac_observer_cannot_create(client: TestClient):
    res = await client.post(
        f"{OPS}/clients",
        json={"name": "Blocked"},
        headers=_hdr("org-rbac", "observer"),
    )
    assert res.status == 403
    assert (await res.json())["error"] == "forbidden"

    ok = await client.get(f"{OPS}/clients", headers=_hdr("org-rbac", "observer"))
    assert ok.status == 200


async def test_platform_owner_can_mutate(client: TestClient):
    res = await client.post(
        f"{OPS}/clients",
        json={"name": "PO Client"},
        headers=_hdr("org-po", "platform_owner"),
    )
    assert res.status == 201


async def test_duplicate_calendar_prevention(client: TestClient):
    h = _hdr(f"org-cal-{uuid.uuid4().hex[:8]}")
    payload = {"title": "Одно событие", "starts_at": "2026-08-15T12:00:00"}
    first = await client.post(f"{OPS}/calendar", json=payload, headers=h)
    assert first.status == 201
    second = await client.post(f"{OPS}/calendar", json=payload, headers=h)
    assert second.status in (400, 409)
    body = await second.json()
    assert body["error"] == "duplicate"


async def test_gcal_honest_needs_config(client: TestClient):
    res = await client.get(f"{OPS}/integrations/google-calendar")
    assert res.status == 200
    body = await res.json()
    assert body["status"] == "needs_config"
    assert body.get("synced") is not True


def test_rbac_matrix_unit():
    assert can("observer", "list")
    assert not can("observer", "create")
    assert can("lawyer", "create")
    assert can("lawyer", "ai")
    assert can("paralegal", "create")
    assert not can("paralegal", "sync")
    assert can("platform_owner", "delete")
    assert normalize_role("viewer") == "observer"
    assert normalize_role("administrator") == "admin"
