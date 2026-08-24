"""Sprint Lawyer 3.5 — attachments, notifications, calendar UX, CRUD polish."""

from __future__ import annotations

import base64
import uuid

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.legal_enterprise.api.register import register_legal_enterprise_routes
from services.legal_ops import reset_legal_ops_for_tests

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


TINY_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
)


async def test_health_sprint_3_5(client: TestClient):
    body = await (await client.get(f"{OPS}/health")).json()
    assert body["sprint"] in {"3.5", "3.6"}


async def test_google_status_and_mapping(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    for key in ("GOOGLE_CALENDAR_CLIENT_ID", "GOOGLE_CALENDAR_CLIENT_SECRET", "GOOGLE_CALENDAR_REFRESH_TOKEN"):
        monkeypatch.delenv(key, raising=False)
    import services.legal_ops.calendar_integration as ci

    ci._INT = None
    org = f"org-35-g-{uuid.uuid4().hex[:8]}"
    st = await (await client.get(f"{OPS}/integrations/google-calendar", headers=_hdr(org))).json()
    assert st.get("status") == "needs_config"
    assert "client_secret" not in st
    monkeypatch.setenv("GOOGLE_CALENDAR_CLIENT_ID", "cid")
    monkeypatch.setenv("GOOGLE_CALENDAR_CLIENT_SECRET", "sec")
    monkeypatch.setenv("GOOGLE_CALENDAR_REFRESH_TOKEN", "rtok")
    ci._INT = None
    ev = await client.post(
        f"{OPS}/calendar",
        json={"title": "Встреча", "starts_at": "2026-08-22T10:00:00+00:00", "event_type": "meeting"},
        headers=_hdr(org),
    )
    eid = (await ev.json())["item"]["id"]
    s1 = await client.post(f"{OPS}/calendar/{eid}/sync-google", json={}, headers=_hdr(org))
    assert s1.status == 200
    m1 = (await s1.json())["mapping"]["external_event_id"]
    s2 = await client.post(f"{OPS}/calendar/{eid}/sync-google", json={}, headers=_hdr(org))
    assert (await s2.json())["mapping"]["external_event_id"] == m1


async def test_monitoring_crud_check_change_center(client: TestClient):
    org = f"org-35-m-{uuid.uuid4().hex[:8]}"
    h = _hdr(org)
    wl = await client.post(
        f"{OPS}/monitoring/watchlist",
        json={"title": "Тестовое дело", "identifier": "TEST-001", "entity_kind": "court_case", "provider": "manual_import"},
        headers=h,
    )
    assert wl.status == 201
    wid = (await wl.json())["item"]["id"]
    upd = await client.post(f"{OPS}/monitoring/watchlist/{wid}", json={"comment": "note", "active": True}, headers=h)
    assert upd.status == 200
    await client.post(
        f"{OPS}/monitoring/watchlist/{wid}/check",
        json={"imported_state": {"status": "open", "events": [], "documents": []}},
        headers=h,
    )
    chk = await client.post(
        f"{OPS}/monitoring/watchlist/{wid}/check",
        json={
            "imported_state": {
                "status": "open",
                "events": [{"title": "Заседание", "starts_at": "2026-08-21T11:30:00+00:00"}],
                "documents": [],
            }
        },
        headers=h,
    )
    body = await chk.json()
    assert len(body["changes"]) == 1
    # duplicate
    chk2 = await client.post(
        f"{OPS}/monitoring/watchlist/{wid}/check",
        json={
            "imported_state": {
                "status": "open",
                "events": [{"title": "Заседание", "starts_at": "2026-08-21T11:30:00+00:00"}],
                "documents": [],
            }
        },
        headers=h,
    )
    assert (await chk2.json())["changes"] == []
    changes = (await (await client.get(f"{OPS}/monitoring/changes", headers=h)).json())["items"]
    assert len(changes) == 1
    cid = changes[0]["id"]
    assert (await client.post(f"{OPS}/monitoring/changes/{cid}/actions", json={"action": "create_task", "confirm": True}, headers=h)).status == 200
    assert (
        await client.post(
            f"{OPS}/monitoring/changes/{cid}/actions",
            json={"action": "add_calendar", "confirm": True, "starts_at": "2026-08-21T11:30:00+00:00"},
            headers=h,
        )
    ).status == 200
    assert (
        await client.post(f"{OPS}/monitoring/changes/{cid}/actions", json={"action": "handoff_lawyer", "confirm": True}, headers=h)
    ).status == 200
    notes = (await (await client.get(f"{OPS}/notifications", headers=h)).json())["items"]
    assert notes
    assert "заседани" in notes[0]["title"].lower() or "изменен" in notes[0]["title"].lower()
    assert notes[0].get("deeplink")


async def test_provider_unavailable_no_fake(client: TestClient):
    items = {i["provider"]: i for i in (await (await client.get(f"{OPS}/providers")).json())["items"]}
    assert items["ua_edrsr"]["status"] == "UNAVAILABLE"
    bad = await client.post(
        f"{OPS}/monitoring/watchlist",
        json={"identifier": "X", "provider": "ua_edrsr"},
        headers=_hdr("org-35-p"),
    )
    assert (await bad.json()).get("ok") is False


async def test_enforcement_crud(client: TestClient):
    org = f"org-35-e-{uuid.uuid4().hex[:8]}"
    h = _hdr(org)
    created = await client.post(
        f"{OPS}/monitoring/enforcement",
        json={"production_number": "ВП-35", "debtor": "А"},
        headers=h,
    )
    assert created.status == 201
    eid = (await created.json())["item"]["id"]
    upd = await client.post(f"{OPS}/monitoring/enforcement/{eid}", json={"status": "closed"}, headers=h)
    assert upd.status == 200
    assert (await upd.json())["item"]["status"] == "closed"


async def test_attachment_rename_relink(client: TestClient):
    org = f"org-35-f-{uuid.uuid4().hex[:8]}"
    h = _hdr(org)
    case = await client.post(f"{OPS}/cases", json={"title": "Дело"}, headers=h)
    case_id = (await case.json())["item"]["id"]
    up = await client.post(
        f"{OPS}/files",
        json={
            "filename": "scan.png",
            "mime_type": "image/png",
            "content_base64": base64.b64encode(TINY_PNG).decode(),
            "entity_type": "case",
            "entity_id": case_id,
        },
        headers=h,
    )
    assert up.status in {200, 201}
    fid = (await up.json())["item"]["id"]
    ren = await client.post(f"{OPS}/files/{fid}/rename", json={"filename": "renamed.png"}, headers=h)
    assert ren.status == 200
    assert (await ren.json())["item"]["filename"] == "renamed.png"
    client_res = await client.post(f"{OPS}/clients", json={"name": "Клиент"}, headers=h)
    client_id = (await client_res.json())["item"]["id"]
    link = await client.post(
        f"{OPS}/files/{fid}/link",
        json={"entity_type": "client", "entity_id": client_id},
        headers=h,
    )
    assert link.status == 200
    assert (await link.json())["item"]["entity_type"] == "client"


async def test_tenant_isolation(client: TestClient):
    a, b = f"org-35-a-{uuid.uuid4().hex[:6]}", f"org-35-b-{uuid.uuid4().hex[:6]}"
    await client.post(f"{OPS}/monitoring/watchlist", json={"identifier": "ONLY-A"}, headers=_hdr(a))
    items = (await (await client.get(f"{OPS}/monitoring/watchlist", headers=_hdr(b))).json())["items"]
    assert all(i.get("external_case_number") != "ONLY-A" for i in items)


async def test_scheduler_idempotency(client: TestClient):
    org = f"org-35-s-{uuid.uuid4().hex[:8]}"
    h = _hdr(org)
    wl = await client.post(
        f"{OPS}/monitoring/watchlist",
        json={"identifier": "SW", "provider": "manual_import"},
        headers=h,
    )
    wid = (await wl.json())["item"]["id"]
    state = {"status": "open", "events": [{"title": "H", "starts_at": "2026-08-21T11:30:00+00:00"}], "documents": []}
    await client.post(f"{OPS}/monitoring/watchlist/{wid}/check", json={"imported_state": {"status": "open", "events": [], "documents": []}}, headers=h)
    await client.post(f"{OPS}/monitoring/watchlist/{wid}/check", json={"imported_state": state}, headers=h)
    from services.legal_ops import get_legal_ops_service

    svc = get_legal_ops_service()
    r1 = await svc.run_monitor_sweep(org)
    r2 = await svc.run_monitor_sweep(org)
    assert r1.get("ok") and r2.get("ok")
    changes = (await (await client.get(f"{OPS}/monitoring/changes", headers=h)).json())["items"]
    assert len(changes) == 1
