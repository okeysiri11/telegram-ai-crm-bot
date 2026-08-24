"""Sprint Lawyer 3.3 — monitoring / providers / Google mapping."""

from __future__ import annotations

import uuid

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.legal_enterprise.api.register import register_legal_enterprise_routes
from services.legal_ops import reset_legal_ops_for_tests
from services.legal_ops.providers import diff_states, fingerprint_state, normalize_external_state

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


async def test_health_sprint_3_3(client: TestClient):
    res = await client.get(f"{OPS}/health")
    body = await res.json()
    assert body["sprint"] in {"3.3", "3.4", "3.5", "3.6"}
    assert body["providers"]["items"]


async def test_providers_honest_status(client: TestClient):
    res = await client.get(f"{OPS}/providers")
    items = {i["provider"]: i for i in (await res.json())["items"]}
    assert items["ua_edrsr"]["status"] == "UNAVAILABLE"
    assert items["ua_enforcement"]["status"] == "REQUIRES_CONFIGURATION"
    assert items["manual_import"]["status"] == "MANUAL"
    assert "не имит" in " ".join(items["ua_edrsr"].get("limitations") or []).lower() or "недоступн" in items["ua_edrsr"]["message_ru"].lower()


def test_normalize_fingerprint_diff():
    a = normalize_external_state({"status": "open", "events": [], "documents": []}, provider="manual_import")
    b = normalize_external_state(
        {
            "status": "open",
            "events": [{"title": "Заседание", "starts_at": "2026-08-21T11:30:00+00:00"}],
            "documents": [{"title": "Решение", "external_id": "d1"}],
        },
        provider="manual_import",
    )
    assert fingerprint_state(a) != fingerprint_state(b)
    diffs = diff_states(a, b)
    types = {d["change_type"] for d in diffs}
    assert "hearing" in types
    assert "document" in types


async def test_watchlist_check_diff_and_dedupe(client: TestClient):
    org = f"org-33-w-{uuid.uuid4().hex[:8]}"
    h = _hdr(org)
    cl = await client.post(f"{OPS}/clients", json={"name": "Клиент"}, headers=h)
    client_id = (await cl.json())["item"]["id"]
    case = await client.post(f"{OPS}/cases", json={"title": "CASE-123", "client_id": client_id, "court_case_number": "CASE-123"}, headers=h)
    case_id = (await case.json())["item"]["id"]
    wl = await client.post(
        f"{OPS}/monitoring/watchlist",
        json={"case_id": case_id, "external_case_number": "CASE-123", "provider": "manual_import"},
        headers=h,
    )
    assert wl.status == 201
    wid = (await wl.json())["item"]["id"]
    # baseline import — no changes without force
    state = {
        "external_case_number": "CASE-123",
        "status": "open",
        "events": [{"title": "Заседание", "starts_at": "2026-08-21T11:30:00+00:00", "kind": "hearing"}],
        "documents": [],
    }
    c1 = await client.post(f"{OPS}/monitoring/watchlist/{wid}/check", json={"imported_state": state}, headers=h)
    assert c1.status == 200
    assert (await c1.json())["changes"] == []
    # update with new document
    state2 = {
        **state,
        "documents": [{"title": "Решение", "external_id": "dec-1", "url": "https://example.invalid"}],
    }
    c2 = await client.post(f"{OPS}/monitoring/watchlist/{wid}/check", json={"imported_state": state2}, headers=h)
    body2 = await c2.json()
    assert len(body2["changes"]) == 1
    # duplicate check — no new change
    c3 = await client.post(f"{OPS}/monitoring/watchlist/{wid}/check", json={"imported_state": state2}, headers=h)
    assert (await c3.json())["changes"] == []
    changes = await client.get(f"{OPS}/monitoring/changes", headers=h)
    assert len((await changes.json())["items"]) == 1


async def test_change_center_task_calendar_ai(client: TestClient):
    org = f"org-33-ch-{uuid.uuid4().hex[:8]}"
    h = _hdr(org)
    case = await client.post(f"{OPS}/cases", json={"title": "Дело"}, headers=h)
    case_id = (await case.json())["item"]["id"]
    wl = await client.post(
        f"{OPS}/monitoring/watchlist",
        json={"case_id": case_id, "external_case_number": "X-1", "provider": "manual_import"},
        headers=h,
    )
    wid = (await wl.json())["item"]["id"]
    await client.post(
        f"{OPS}/monitoring/watchlist/{wid}/check",
        json={"imported_state": {"status": "a", "events": [], "documents": []}},
        headers=h,
    )
    await client.post(
        f"{OPS}/monitoring/watchlist/{wid}/check",
        json={
            "imported_state": {
                "status": "a",
                "events": [{"title": "Новое заседание", "starts_at": "2026-08-21T11:30:00+00:00"}],
                "documents": [],
            }
        },
        headers=h,
    )
    items = (await (await client.get(f"{OPS}/monitoring/changes", headers=h)).json())["items"]
    assert items
    cid = items[0]["id"]
    task = await client.post(
        f"{OPS}/monitoring/changes/{cid}/actions",
        json={"action": "create_task", "confirm": True},
        headers=h,
    )
    assert task.status == 200
    cal = await client.post(
        f"{OPS}/monitoring/changes/{cid}/actions",
        json={"action": "add_calendar", "confirm": True, "starts_at": "2026-08-21T11:30:00+00:00"},
        headers=h,
    )
    assert cal.status == 200
    ai = await client.post(
        f"{OPS}/monitoring/changes/{cid}/actions",
        json={"action": "ai_analyze", "confirm": True},
        headers=h,
    )
    assert ai.status == 200


async def test_enforcement_manual(client: TestClient):
    org = f"org-33-e-{uuid.uuid4().hex[:8]}"
    h = _hdr(org)
    res = await client.post(
        f"{OPS}/monitoring/enforcement",
        json={"production_number": "ВП-1", "debtor": "ООО А", "creditor": "ООО Б"},
        headers=h,
    )
    assert res.status == 201
    listed = await client.get(f"{OPS}/monitoring/enforcement", headers=h)
    body = await listed.json()
    assert body["items"]
    assert body["provider"]["status"] == "REQUIRES_CONFIGURATION"


async def test_google_mapping_no_duplicate(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("GOOGLE_CALENDAR_CLIENT_ID", "cid")
    monkeypatch.setenv("GOOGLE_CALENDAR_CLIENT_SECRET", "sec")
    monkeypatch.setenv("GOOGLE_CALENDAR_REFRESH_TOKEN", "rtok")
    org = f"org-33-g-{uuid.uuid4().hex[:8]}"
    h = _hdr(org)
    # reset integration singleton
    import services.legal_ops.calendar_integration as ci

    ci._INT = None
    ev = await client.post(
        f"{OPS}/calendar",
        json={"title": "Встреча", "starts_at": "2026-08-22T10:00:00+00:00", "event_type": "meeting"},
        headers=h,
    )
    eid = (await ev.json())["item"]["id"]
    s1 = await client.post(f"{OPS}/calendar/{eid}/sync-google", json={}, headers=h)
    assert s1.status == 200
    m1 = (await s1.json())["mapping"]["external_event_id"]
    s2 = await client.post(f"{OPS}/calendar/{eid}/sync-google", json={}, headers=h)
    assert s2.status == 200
    m2 = (await s2.json())["mapping"]["external_event_id"]
    assert m1 == m2


async def test_tenant_isolation_watchlist(client: TestClient):
    a, b = f"org-33-a-{uuid.uuid4().hex[:6]}", f"org-33-b-{uuid.uuid4().hex[:6]}"
    await client.post(f"{OPS}/monitoring/watchlist", json={"external_case_number": "ONLY-A"}, headers=_hdr(a))
    items_b = (await (await client.get(f"{OPS}/monitoring/watchlist", headers=_hdr(b))).json())["items"]
    assert all(i.get("external_case_number") != "ONLY-A" for i in items_b)


async def test_scheduler_handler_registered():
    from services.pg_scheduler_engine import SchedulerEngineV1

    handlers = SchedulerEngineV1.job_handlers()
    assert "legal.monitor.morning" in handlers
    assert "legal.monitor.evening" in handlers
