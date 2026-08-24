"""Sprint 51.1 — Lawyer CRUD, files, archive, calendar links, Google adapter."""

from __future__ import annotations

import base64
import uuid

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.legal_enterprise.api.register import register_legal_enterprise_routes
from services.legal_ops import reset_legal_ops_for_tests
from services.legal_ops.calendar_integration import GoogleCalendarAdapter, get_calendar_integration

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


async def test_case_edit_archive_restore(client: TestClient):
    h = _hdr("org-51-1")
    created = await client.post(f"{OPS}/cases", json={"title": "Уголовное дело", "case_type": "criminal", "notes": "старт"}, headers=h)
    assert created.status == 201
    cid = (await created.json())["item"]["id"]
    edited = await client.post(f"{OPS}/cases/{cid}", json={"notes": "обновлено", "status": "open"}, headers=h)
    assert edited.status == 200
    assert (await edited.json())["item"]["notes"] == "обновлено"
    arch = await client.post(f"{OPS}/entities/case/{cid}/archive", json={}, headers=h)
    assert arch.status == 200
    listed = await client.get(f"{OPS}/cases", headers=h)
    ids = [x["id"] for x in (await listed.json())["items"]]
    assert cid not in ids
    rest = await client.post(f"{OPS}/entities/case/{cid}/restore", json={}, headers=h)
    assert rest.status == 200
    listed2 = await client.get(f"{OPS}/cases", headers=h)
    assert cid in [x["id"] for x in (await listed2.json())["items"]]


async def test_contract_edit_archive(client: TestClient):
    h = _hdr("org-51-1c")
    created = await client.post(f"{OPS}/contracts", json={"title": "Договор", "counterparty": "ООО Бетта"}, headers=h)
    cid = (await created.json())["item"]["id"]
    edited = await client.post(f"{OPS}/entities/contract/{cid}", json={"notes": "правка", "title": "Договор v2"}, headers=h)
    assert edited.status == 200
    arch = await client.post(f"{OPS}/entities/contract/{cid}/archive", json={}, headers=h)
    assert arch.status == 200


async def test_file_upload_image_and_relation(client: TestClient):
    h = _hdr("org-51-1f")
    case = await client.post(f"{OPS}/cases", json={"title": "Дело файл"}, headers=h)
    case_id = (await case.json())["item"]["id"]
    png = base64.b64encode(b"\x89PNG\r\n" + b"x" * 20).decode()
    up = await client.post(
        f"{OPS}/files",
        json={"filename": "scan.png", "mime_type": "image/png", "content_base64": png, "entity_type": "case", "entity_id": case_id},
        headers=h,
    )
    assert up.status == 201
    fid = (await up.json())["item"]["id"]
    listed = await client.get(f"{OPS}/files?entity_type=case&entity_id={case_id}", headers=h)
    assert fid in [x["id"] for x in (await listed.json())["items"]]
    content = await client.get(f"{OPS}/files/{fid}/content", headers=h)
    assert content.status == 200
    inbox = await client.post(
        f"{OPS}/files",
        json={"filename": "inbox.pdf", "mime_type": "application/pdf", "content_base64": base64.b64encode(b"%PDF-1.4").decode()},
        headers=h,
    )
    iid = (await inbox.json())["item"]["id"]
    linked = await client.post(f"{OPS}/files/{iid}/link", json={"entity_type": "case", "entity_id": case_id}, headers=h)
    assert linked.status == 200


async def test_calendar_crud_and_no_duplicate_hearing(client: TestClient):
    h = _hdr(f"org-51-1cal-{uuid.uuid4().hex[:8]}")
    hearing = await client.post(
        f"{OPS}/hearings",
        json={"title": "Заседание", "scheduled_at": "2026-08-20T10:00:00+00:00"},
        headers=h,
    )
    assert hearing.status == 201
    hid = (await hearing.json())["item"]["id"]
    cal = await client.get(f"{OPS}/calendar", headers=h)
    items = (await cal.json())["items"]
    linked = [x for x in items if x.get("source_id") == hid]
    assert len(linked) == 1
    ev = await client.post(
        f"{OPS}/calendar",
        json={"title": "Встреча", "event_type": "meeting", "starts_at": "2026-08-21T09:00:00+00:00", "reminder_minutes": 30},
        headers=h,
    )
    assert ev.status == 201
    eid = (await ev.json())["item"]["id"]
    upd = await client.post(f"{OPS}/entities/calendar/{eid}", json={"title": "Встреча 2", "location": "офис"}, headers=h)
    assert upd.status == 200
    arch = await client.post(f"{OPS}/entities/calendar/{eid}/archive", json={}, headers=h)
    assert arch.status == 200
    again = await client.get(f"{OPS}/calendar", headers=h)
    assert eid not in [x["id"] for x in (await again.json())["items"]]
    # duplicate hearing calendar
    await client.post(
        f"{OPS}/hearings",
        json={"title": "Заседание", "scheduled_at": "2026-08-20T10:00:00+00:00"},
        headers=h,
    )
    cal2 = await client.get(f"{OPS}/calendar", headers=h)
    hearing_events = [x for x in (await cal2.json())["items"] if x.get("source_kind") == "hearing"]
    assert len(hearing_events) >= 1


async def test_deadline_creates_calendar(client: TestClient):
    h = _hdr("org-51-1dl")
    t = await client.post(
        f"{OPS}/tasks",
        json={"title": "Срок иска", "kind": "deadline", "due_at": "2026-09-01T12:00:00+00:00"},
        headers=h,
    )
    assert t.status == 201
    tid = (await t.json())["item"]["id"]
    cal = await client.get(f"{OPS}/calendar", headers=h)
    assert any(x.get("source_id") == tid for x in (await cal.json())["items"])


async def test_google_adapter_boundary_and_integrations(client: TestClient):
    res = await client.get(f"{OPS}/integrations/calendars")
    assert res.status == 200
    items = (await res.json())["items"]
    providers = {x["provider"]: x for x in items}
    assert providers["google"]["status"] in {"needs_config", "needs_oauth", "connected"}
    assert providers["microsoft"]["status"] == "coming_soon"
    assert providers["google"]["status"] != "connected" or providers["google"]["ready"] is True
    connect = await client.post(f"{OPS}/integrations/google-calendar/connect")
    assert connect.status in (200, 409)
    body = await connect.json()
    assert "message_ru" in body
    adapter = GoogleCalendarAdapter()
    fake = adapter.create_event({"organization_id": "x", "id": "1"})
    assert fake.get("ok") is False or adapter.status()["status"] == "connected"


async def test_rbac_and_isolation_51_1(client: TestClient):
    await client.post(f"{OPS}/cases", json={"title": "A"}, headers=_hdr("iso-a"))
    listed = await client.get(f"{OPS}/cases", headers=_hdr("iso-b"))
    assert (await listed.json())["items"] == []
    blocked = await client.post(
        f"{OPS}/entities/case/x/archive",
        json={},
        headers=_hdr("iso-a", "observer"),
    )
    assert blocked.status == 403


async def test_activity_and_reminders(client: TestClient):
    h = _hdr("org-act")
    c = await client.post(f"{OPS}/cases", json={"title": "Дело акт", "notes": "n"}, headers=h)
    cid = (await c.json())["item"]["id"]
    await client.post(f"{OPS}/cases/{cid}", json={"notes": "n2"}, headers=h)
    act = await client.get(f"{OPS}/activity", headers=h)
    actions = {a["action"] for a in (await act.json())["items"]}
    assert "edited" in actions or "status_changed" in actions
    rem = await client.get(f"{OPS}/reminders", headers=h)
    assert rem.status == 200


async def test_case_edit_survives_rehydrate(client: TestClient):
    h = _hdr(f"org-persist-511-{uuid.uuid4().hex[:8]}")
    created = await client.post(
        f"{OPS}/cases",
        json={"title": "Уголовное persist", "case_type": "criminal", "notes": "первично"},
        headers=h,
    )
    assert created.status == 201
    cid = (await created.json())["item"]["id"]
    edited = await client.post(f"{OPS}/cases/{cid}", json={"notes": "после правки", "status": "open"}, headers=h)
    assert edited.status == 200
    from services.legal_ops.service import get_legal_ops_service

    svc = get_legal_ops_service()
    svc._hydrated.clear()
    svc._mem.clear()
    got = await client.get(f"{OPS}/entities/case/{cid}", headers=h)
    body = await got.json()
    assert body.get("ok") is True
    assert body["item"]["notes"] == "после правки"


async def test_case_deadline_calendar_no_duplicate(client: TestClient):
    h = _hdr(f"org-case-dl-{uuid.uuid4().hex[:8]}")
    created = await client.post(
        f"{OPS}/cases",
        json={"title": "Дело со сроком", "deadline_at": "2026-09-10T12:00:00+00:00"},
        headers=h,
    )
    cid = (await created.json())["item"]["id"]
    cal = await client.get(f"{OPS}/calendar", headers=h)
    linked = [x for x in (await cal.json())["items"] if x.get("source_id") == cid]
    assert len(linked) == 1
    await client.post(f"{OPS}/cases/{cid}", json={"deadline_at": "2026-09-10T12:00:00+00:00"}, headers=h)
    cal2 = await client.get(f"{OPS}/calendar", headers=h)
    assert len([x for x in (await cal2.json())["items"] if x.get("source_id") == cid]) == 1


def test_calendar_integration_catalog_unit():
    cat = get_calendar_integration().catalog()
    ids = {c["provider"] for c in cat}
    assert {"internal", "google", "microsoft"} <= ids
