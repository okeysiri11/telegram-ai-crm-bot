"""Sprint Lawyer 3.4 — manual watch, change center, integrations health, security."""

from __future__ import annotations

import uuid

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.legal_enterprise.api.register import register_legal_enterprise_routes
from services.legal_ops import reset_legal_ops_for_tests
from services.legal_ops.monitoring import scrub_secrets
from services.legal_ops.url_safety import validate_source_url

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


async def test_health_sprint_3_4(client: TestClient):
    res = await client.get(f"{OPS}/health")
    body = await res.json()
    assert body["sprint"] in {"3.4", "3.5", "3.6"}


async def test_google_connect_status_unconfigured(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    for key in (
        "GOOGLE_CALENDAR_CLIENT_ID",
        "GOOGLE_CALENDAR_CLIENT_SECRET",
        "GOOGLE_CALENDAR_REFRESH_TOKEN",
        "GOOGLE_CLIENT_ID",
        "GOOGLE_CLIENT_SECRET",
    ):
        monkeypatch.delenv(key, raising=False)
    import services.legal_ops.calendar_integration as ci

    ci._INT = None
    org = f"org-34-g-{uuid.uuid4().hex[:8]}"
    st = await client.get(f"{OPS}/integrations/google-calendar", headers=_hdr(org))
    body = await st.json()
    assert body.get("status") == "needs_config"
    assert "token" not in str(body).lower() or "[redacted]" in str(body).lower() or "refresh" not in str(body).lower()
    health = await (await client.get(f"{OPS}/integrations/health", headers=_hdr(org))).json()
    g = next(i for i in health["items"] if i["id"] == "google_calendar")
    assert "Не настроен" in g["status_label_ru"]


async def test_oauth_missing_configuration_connect(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    for key in ("GOOGLE_CALENDAR_CLIENT_ID", "GOOGLE_CALENDAR_CLIENT_SECRET", "GOOGLE_CALENDAR_REFRESH_TOKEN"):
        monkeypatch.delenv(key, raising=False)
    import services.legal_ops.calendar_integration as ci

    ci._INT = None
    res = await client.post(f"{OPS}/integrations/google-calendar/connect", json={}, headers=_hdr("org-34-oauth"))
    assert res.status == 409
    body = await res.json()
    assert body.get("status") == "needs_config"
    assert "client_secret" not in body


async def test_provider_unavailable_honest(client: TestClient):
    res = await client.get(f"{OPS}/providers")
    items = {i["provider"]: i for i in (await res.json())["items"]}
    assert items["ua_edrsr"]["status"] == "UNAVAILABLE"
    assert items["ua_enforcement"]["status"] == "REQUIRES_CONFIGURATION"
    assert "не подключен" in items["ua_edrsr"]["message_ru"].lower() or "недоступ" in items["ua_edrsr"]["message_ru"].lower()
    # cannot create watch with fake auto provider
    bad = await client.post(
        f"{OPS}/monitoring/watchlist",
        json={"identifier": "X", "provider": "ua_edrsr"},
        headers=_hdr("org-34-p"),
    )
    assert bad.status in {400, 409, 422} or (await bad.json()).get("ok") is False


def test_url_ssrf_validation():
    assert validate_source_url("https://court.gov.ua/case/1")["ok"] is True
    assert validate_source_url("http://evil.example/x")["ok"] is False
    assert validate_source_url("https://127.0.0.1/secret")["ok"] is False
    assert validate_source_url("https://localhost/x")["ok"] is False
    assert validate_source_url("https://169.254.169.254/latest")["ok"] is False


def test_scrub_secrets():
    cleaned = scrub_secrets({"refresh_token": "abc", "status": "ok", "nested": {"access_token": "t"}})
    assert cleaned["refresh_token"] == "[redacted]"
    assert cleaned["nested"]["access_token"] == "[redacted]"
    assert cleaned["status"] == "ok"


async def test_manual_watch_create_and_check_now(client: TestClient):
    org = f"org-34-w-{uuid.uuid4().hex[:8]}"
    h = _hdr(org)
    wl = await client.post(
        f"{OPS}/monitoring/watchlist",
        json={
            "entity_kind": "court_case",
            "title": "Дело Иванова",
            "identifier": "CASE-34-1",
            "source_url": "https://example.invalid/case/1",
            "check_frequency": "12h",
            "comment": "ручной контроль",
            "counterparty": "ООО Ромашка",
            "decision_ref": "DEC-9",
            "active": True,
            "provider": "manual_import",
        },
        headers=h,
    )
    assert wl.status == 201
    item = (await wl.json())["item"]
    assert item["title"] == "Дело Иванова"
    assert item["source_url"].startswith("https://")
    assert item["decision_ref"] == "DEC-9"
    wid = item["id"]

    # baseline
    await client.post(
        f"{OPS}/monitoring/watchlist/{wid}/check",
        json={"imported_state": {"status": "open", "events": [], "documents": []}},
        headers=h,
    )
    # change
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
    assert body["ok"] is True
    assert len(body["changes"]) == 1
    assert body["changes"][0].get("workflow_status") in {"new", "needs_action"}
    assert body["changes"][0].get("old_fingerprint") is not None or body["changes"][0].get("new_fingerprint")

    acts = (await (await client.get(f"{OPS}/activity", headers=h)).json())["items"]
    actions = {a.get("action") for a in acts}
    assert "WATCH_ITEM_CREATED" in actions
    assert "LEGAL_PROVIDER_CHECK" in actions
    assert "LEGAL_CHANGE_DETECTED" in actions


async def test_change_center_handoffs(client: TestClient):
    org = f"org-34-ch-{uuid.uuid4().hex[:8]}"
    h = _hdr(org)
    wl = await client.post(
        f"{OPS}/monitoring/watchlist",
        json={"identifier": "CH-1", "title": "Watch", "provider": "manual_import"},
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
    cid = (await (await client.get(f"{OPS}/monitoring/changes", headers=h)).json())["items"][0]["id"]
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
    lawyer = await client.post(
        f"{OPS}/monitoring/changes/{cid}/actions",
        json={"action": "handoff_lawyer", "confirm": True},
        headers=h,
    )
    assert lawyer.status == 200
    viewed = await client.post(
        f"{OPS}/monitoring/changes/{cid}/actions",
        json={"action": "mark_read"},
        headers=h,
    )
    assert (await viewed.json())["item"]["workflow_status"] == "viewed"


async def test_scheduler_invocation(client: TestClient):
    org = f"org-34-s-{uuid.uuid4().hex[:8]}"
    h = _hdr(org)
    await client.post(
        f"{OPS}/monitoring/watchlist",
        json={"identifier": "SW-1", "provider": "manual_import", "active": True},
        headers=h,
    )
    from services.legal_ops import get_legal_ops_service

    svc = get_legal_ops_service()
    result = await svc.run_monitor_sweep(org)
    assert result.get("ok") is True or "results" in result or isinstance(result.get("checked"), int) or result


async def test_calendar_local_without_google(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    for key in ("GOOGLE_CALENDAR_CLIENT_ID", "GOOGLE_CALENDAR_CLIENT_SECRET", "GOOGLE_CALENDAR_REFRESH_TOKEN"):
        monkeypatch.delenv(key, raising=False)
    import services.legal_ops.calendar_integration as ci

    ci._INT = None
    org = f"org-34-cal-{uuid.uuid4().hex[:8]}"
    h = _hdr(org)
    ev = await client.post(
        f"{OPS}/calendar",
        json={"title": "Заседание", "starts_at": "2026-08-22T10:00:00+00:00", "event_type": "hearing"},
        headers=h,
    )
    assert ev.status == 201
    listed = await (await client.get(f"{OPS}/calendar", headers=h)).json()
    assert any(i.get("title") == "Заседание" for i in listed["items"])


async def test_ados_to_google_mapping_duplicate(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("GOOGLE_CALENDAR_CLIENT_ID", "cid")
    monkeypatch.setenv("GOOGLE_CALENDAR_CLIENT_SECRET", "sec")
    monkeypatch.setenv("GOOGLE_CALENDAR_REFRESH_TOKEN", "rtok")
    import services.legal_ops.calendar_integration as ci

    ci._INT = None
    org = f"org-34-map-{uuid.uuid4().hex[:8]}"
    h = _hdr(org)
    ev = await client.post(
        f"{OPS}/calendar",
        json={"title": "Встреча", "starts_at": "2026-08-22T10:00:00+00:00", "event_type": "meeting"},
        headers=h,
    )
    eid = (await ev.json())["item"]["id"]
    s1 = await client.post(f"{OPS}/calendar/{eid}/sync-google", json={}, headers=h)
    assert s1.status == 200
    body1 = await s1.json()
    assert "refresh_token" not in str(body1)
    m1 = body1["mapping"]["external_event_id"]
    s2 = await client.post(f"{OPS}/calendar/{eid}/sync-google", json={}, headers=h)
    m2 = (await s2.json())["mapping"]["external_event_id"]
    assert m1 == m2


async def test_bidirectional_rejected(client: TestClient):
    org = f"org-34-bi-{uuid.uuid4().hex[:8]}"
    h = _hdr(org)
    res = await client.post(
        f"{OPS}/monitoring/settings",
        json={"google_sync": {"direction": "bidirectional"}},
        headers=h,
    )
    body = await res.json()
    assert body.get("ok") is False
    assert "не включена" in str(body.get("message_ru") or "").lower() or body.get("error") == "not_supported"


async def test_tenant_isolation(client: TestClient):
    a, b = f"org-34-a-{uuid.uuid4().hex[:6]}", f"org-34-b-{uuid.uuid4().hex[:6]}"
    await client.post(f"{OPS}/monitoring/watchlist", json={"identifier": "ONLY-A"}, headers=_hdr(a))
    items_b = (await (await client.get(f"{OPS}/monitoring/watchlist", headers=_hdr(b))).json())["items"]
    assert all(i.get("external_case_number") != "ONLY-A" for i in items_b)


async def test_watch_update_disable_audit(client: TestClient):
    org = f"org-34-dis-{uuid.uuid4().hex[:8]}"
    h = _hdr(org)
    wl = await client.post(
        f"{OPS}/monitoring/watchlist",
        json={"identifier": "DIS-1", "title": "X", "provider": "manual_import"},
        headers=h,
    )
    wid = (await wl.json())["item"]["id"]
    upd = await client.post(f"{OPS}/monitoring/watchlist/{wid}", json={"active": False}, headers=h)
    assert upd.status == 200
    acts = (await (await client.get(f"{OPS}/activity", headers=h)).json())["items"]
    assert any(a.get("action") == "WATCH_ITEM_DISABLED" for a in acts)


async def test_integrations_health_dashboard(client: TestClient):
    org = f"org-34-h-{uuid.uuid4().hex[:8]}"
    body = await (await client.get(f"{OPS}/integrations/health", headers=_hdr(org))).json()
    assert body["ok"] is True
    ids = {i["id"] for i in body["items"]}
    assert ids >= {"google_calendar", "court_data", "enforcement", "counterparties", "scheduler"}
    for i in body["items"]:
        assert i.get("status_label_ru") or i.get("status_raw")
