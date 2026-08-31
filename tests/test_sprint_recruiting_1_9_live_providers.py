"""Sprint Recruiting 1.9 — live providers: OAuth, health, metrics, messaging."""

from __future__ import annotations

import uuid

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.recruiting_enterprise.api.register import register_recruiting_enterprise_routes
from services.recruiting_ops import get_recruiting_ops_service, reset_recruiting_ops_for_tests
from services.recruiting_ops.provider_adapters import get_adapter
from services.recruiting_ops.provider_http import set_http_transport
from services.recruiting_ops.provider_metrics import normalize_metric_row
from services.recruiting_ops.provider_oauth import decode_state, encode_state
from services.recruiting_ops.provider_registry import provider_registry
from services.recruiting_ops.secret_store import get_secret_store

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


def _hdr(org: str = "ados") -> dict[str, str]:
    return {"X-Organization-Id": org, "X-Role": "platform_owner"}


def _graph_transport(method: str, url: str, headers: dict[str, str], body: bytes | None, timeout: float) -> dict:
    if "graph.facebook.com" in url and "/oauth/access_token" in url:
        return {"status": 200, "ok": True, "json": {"access_token": "injected-token", "expires_in": 3600}, "text": "{}"}
    if "graph.facebook.com" in url and "/me/adaccounts" in url:
        return {"status": 200, "ok": True, "json": {"data": [{"id": "act_1", "name": "Acct"}]}, "text": "{}"}
    if "graph.facebook.com" in url and "/campaigns" in url:
        return {"status": 200, "ok": True, "json": {"data": [{"id": "c1", "name": "Hire", "status": "ACTIVE"}]}, "text": "{}"}
    if "graph.facebook.com" in url and "/insights" in url:
        return {"status": 200, "ok": True, "json": {"data": [{"campaign_id": "c1", "spend": "12.5", "impressions": "100", "clicks": "4"}]}, "text": "{}"}
    if "graph.facebook.com" in url and "/me" in url:
        return {"status": 200, "ok": True, "json": {"id": "99", "name": "Meta User"}, "text": "{}"}
    if "graph.facebook.com" in url and "act_" in url:
        return {"status": 200, "ok": True, "json": {"id": "act_1", "name": "Acct", "account_status": 1}, "text": "{}"}
    if "oauth2.googleapis.com" in url:
        return {"status": 200, "ok": True, "json": {"access_token": "g-access", "refresh_token": "g-refresh", "expires_in": 3600}, "text": "{}"}
    if "googleads.googleapis.com" in url:
        return {
            "status": 200,
            "ok": True,
            "json": {"results": [{"customer": {"id": "123", "descriptiveName": "Cust"}, "campaign": {"id": "9", "name": "G", "status": "ENABLED"}, "metrics": {"impressions": "10", "clicks": "1", "costMicros": "1000000"}}]},
            "text": "{}",
        }
    if "tiktok.com" in url and "oauth2" in url:
        return {"status": 200, "ok": True, "json": {"code": 0, "data": {"access_token": "tt"}}, "text": "{}"}
    if "tiktok.com" in url and "advertiser/info" in url:
        return {"status": 200, "ok": True, "json": {"code": 0, "data": {"list": [{"advertiser_id": "tt1", "name": "TT"}]}}, "text": "{}"}
    if "tiktok.com" in url and "campaign/get" in url:
        return {"status": 200, "ok": True, "json": {"code": 0, "data": {"list": [{"campaign_id": "t1", "name": "T", "status": "ENABLE"}], "page_info": {"page": 1, "total_page": 1}}}, "text": "{}"}
    if "tiktok.com" in url and "report" in url:
        return {"status": 200, "ok": True, "json": {"code": 0, "data": {"list": [{"metrics": {"spend": 3, "impressions": 20, "clicks": 2}, "dimensions": {"campaign_id": "t1"}}]}}, "text": "{}"}
    if "api.telegram.org" in url and "getMe" in url:
        return {"status": 200, "ok": True, "json": {"ok": True, "result": {"id": 7, "username": "hire_bot", "first_name": "Hire"}}, "text": "{}"}
    if "api.telegram.org" in url and "sendMessage" in url:
        return {"status": 200, "ok": True, "json": {"ok": True, "result": {"message_id": 44}}, "text": "{}"}
    if "graph.facebook.com" in url and "/messages" in url:
        return {"status": 200, "ok": True, "json": {"messages": [{"id": "wamid.1"}]}, "text": "{}"}
    if "graph.facebook.com" in url:
        return {"status": 200, "ok": True, "json": {"id": "123", "verified_name": "WA", "display_phone_number": "+100"}, "text": "{}"}
    return {"status": 404, "ok": False, "json": {"error": "missing"}, "text": "missing"}


def test_provider_registry_lists_all():
    payload = provider_registry([])
    ids = [item["provider_id"] for item in payload["items"]]
    assert ids == ["meta", "google", "tiktok", "telegram", "whatsapp", "email"]
    assert payload["items"][0]["status"] == "NOT_CONFIGURED"


def test_oauth_state_rejects_tamper():
    state = encode_state(provider="meta", organization_id="org-1")
    ok = decode_state(state)
    assert ok["ok"] is True
    assert ok["provider"] == "meta"
    bad = decode_state(state[:-2] + "ab")
    assert bad["ok"] is False


def test_metrics_keep_null_not_zero():
    row = normalize_metric_row("meta", {"campaign_id": "c1", "spend": "5"})
    assert row["spend"] == 5
    assert row["impressions"] is None
    assert row["fake_data"] is False


def test_live_write_requires_approval():
    paused = get_adapter("meta", mode="LIVE").pause_campaign(campaign_id="c1")
    assert paused["ok"] is False
    assert paused["error"] == "APPROVAL_REQUIRED"


def test_http_retry_bounds():
    from services.recruiting_ops.provider_http import MAX_ATTEMPTS, backoff_seconds

    assert MAX_ATTEMPTS == 4
    assert backoff_seconds(8) <= 60


async def test_secret_not_returned_by_api(client: TestClient):
    org = f"sec-{uuid.uuid4().hex[:8]}"
    token = "super-secret-live-token"
    await client.post(f"{OPS}/providers/meta/configure", json={"ad_account_id": "act_1", "access_token": token}, headers=_hdr(org))
    listed = await (await client.get(f"{OPS}/providers", headers=_hdr(org))).json()
    blob = str(listed)
    assert token not in blob
    tested = await (await client.post(f"{OPS}/providers/meta/test-connection", json={}, headers=_hdr(org))).json()
    assert token not in str(tested)
    assert tested.get("status") in {"NOT_CONFIGURED", "ERROR", "CONFIGURING"}


async def test_meta_health_with_injected_http_is_not_live_verified(client: TestClient):
    org = f"meta-{uuid.uuid4().hex[:8]}"
    set_http_transport(_graph_transport)
    get_secret_store().put("meta", "access_token", "injected")
    res = await client.post(f"{OPS}/providers/meta/test-connection", json={}, headers=_hdr(org))
    body = await res.json()
    assert body["status"] == "CONNECTED"
    assert body["mocked_http"] is True
    assert body["live_verified"] is False
    assert body["account_identity"]["id"] in {"99", "act_1"}


async def test_google_and_tiktok_injected_health(client: TestClient):
    set_http_transport(_graph_transport)
    store = get_secret_store()
    store.put("google", "refresh_token", "r")
    store.put("google", "developer_token", "d")
    store.put("google", "client_id", "cid")
    store.put("google", "client_secret", "csec")
    store.put("google", "customer_id", "123")
    store.put("tiktok", "access_token", "t")
    store.put("tiktok", "advertiser_id", "tt1")
    org = f"ads-{uuid.uuid4().hex[:8]}"
    google = await (await client.post(f"{OPS}/providers/google/test-connection", json={}, headers=_hdr(org))).json()
    tiktok = await (await client.post(f"{OPS}/providers/tiktok/test-connection", json={}, headers=_hdr(org))).json()
    assert google["status"] == "CONNECTED"
    assert tiktok["status"] == "CONNECTED"
    assert google["live_verified"] is False


async def test_telegram_smtp_whatsapp_injected(client: TestClient):
    set_http_transport(_graph_transport)
    get_secret_store().put("telegram", "bot_token", "bot")
    get_secret_store().put("whatsapp", "access_token", "wa")
    get_secret_store().put("whatsapp", "phone_number_id", "123")

    class DummySMTP:
        def __init__(self, *a, **k):
            pass
        def __enter__(self):
            return self
        def __exit__(self, *a):
            return False
        def ehlo(self):
            return True
        def starttls(self, context=None):
            return True
        def login(self, *a):
            return True
        def send_message(self, *a):
            return True

    from services.recruiting_ops.provider_live import set_smtp_factory

    set_smtp_factory(lambda host, port: DummySMTP())
    get_secret_store().put("email", "smtp_host", "smtp.example")
    get_secret_store().put("email", "email_from", "hr@example.com")
    org = f"msg-{uuid.uuid4().hex[:8]}"
    tg = await (await client.post(f"{OPS}/providers/telegram/test-connection", json={}, headers=_hdr(org))).json()
    wa = await (await client.post(f"{OPS}/providers/whatsapp/test-connection", json={}, headers=_hdr(org))).json()
    em = await (await client.post(f"{OPS}/providers/email/test-connection", json={}, headers=_hdr(org))).json()
    assert tg["status"] in {"DISABLED", "FROZEN"}
    assert tg.get("frozen") is True or tg["status"] == "DISABLED"
    assert wa["status"] == "CONNECTED"
    assert em["status"] == "CONNECTED"


async def test_oauth_start_without_app_is_not_configured(client: TestClient):
    res = await client.get(f"{OPS}/providers/meta/oauth/start", headers=_hdr(f"oa-{uuid.uuid4().hex[:8]}"))
    body = await res.json()
    assert body["ok"] is False
    assert body["error"] == "NOT_CONFIGURED"


async def test_oauth_callback_with_injected_exchange(client: TestClient, monkeypatch):
    monkeypatch.setenv("META_ADS_APP_ID", "app")
    monkeypatch.setenv("META_ADS_APP_SECRET", "secret")
    set_http_transport(_graph_transport)
    org = f"cb-{uuid.uuid4().hex[:8]}"
    state = encode_state(provider="meta", organization_id=org)
    res = await client.get(f"{OPS}/oauth/meta/callback?code=abc&state={state}&format=json")
    body = await res.json()
    assert "injected-token" not in str(body)
    assert body.get("ok") is True


async def test_campaign_write_and_message_approval(client: TestClient):
    org = f"wr-{uuid.uuid4().hex[:8]}"
    created = await client.post(f"{OPS}/campaign-writes", json={"action": "pause", "provider": "meta", "campaign_id": "c1"}, headers=_hdr(org))
    assert created.status == 201
    item = (await created.json())["item"]
    assert item["status"] == "ACTION_PENDING_APPROVAL"
    decided = await (await client.post(f"{OPS}/campaign-writes/{item['id']}/decision", json={"decision": "REJECT"}, headers=_hdr(org))).json()
    assert decided["item"]["live_applied"] is False
    msg = await client.post(f"{OPS}/messages", json={"channel": "telegram", "to": "1", "body": "hi"}, headers=_hdr(org))
    body = await msg.json()
    assert body["item"]["status"] == "WAITING_PROVIDER"


async def test_ai_cannot_mutate_live(client: TestClient):
    rec = await client.post(f"{OPS}/ai/recommendations", json={"recommendation": "pause_campaign"}, headers=_hdr())
    rec_id = (await rec.json())["item"]["id"]
    decided = await (await client.post(f"{OPS}/ai/recommendations/{rec_id}/decision", json={"decision": "APPROVE"}, headers=_hdr())).json()
    assert decided["item"]["live_applied"] is False
    assert decided["item"]["advisory_only"] is True


async def test_whatsapp_webhook_does_not_invent_events(client: TestClient):
    posted = await (await client.post(f"{OPS}/webhooks/whatsapp", json={"entry": []})).json()
    assert posted["received"] is False
    assert posted["items"] == []


async def test_green_gate_sprint_and_no_live_data(client: TestClient):
    health = await (await client.get(f"{OPS}/health")).json()
    assert health["sprint"] in {"recruiting_1.9", "recruiting_1.10", "recruiting_1.11", "recruiting_1.12"}
    assert health["tracking_health"]["code"] == "CONNECTED"
    ads = await (await client.get(f"{OPS}/ads/control-center?project=vanguard", headers=_hdr())).json()
    assert ads["overview"]["no_live_data"] is True
    assert ads["overview"]["spend"] is None
    assert ads["connected"] is False
    diag = await (await client.get(f"{OPS}/ops/diagnostics", headers=_hdr())).json()
    assert diag["provider_health"]["infra_independent"] is True
