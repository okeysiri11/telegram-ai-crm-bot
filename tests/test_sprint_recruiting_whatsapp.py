"""Sprint Recruiting 1.11 — WhatsApp production connectivity."""

from __future__ import annotations

import hashlib
import hmac
import json
import uuid

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.recruiting_enterprise.api.register import register_recruiting_enterprise_routes
from services.observability import prometheus_text
from services.recruiting_ops import reset_recruiting_ops_for_tests
from services.recruiting_ops.provider_http import set_http_transport
from services.recruiting_ops.secret_store import get_secret_store
from services.recruiting_ops.whatsapp_ops import match_candidate, normalize_phone

OPS = "/api/recruiting-ops/v1"
TOKEN = "wa-super-secret-token"


def _hdr(org: str = "ados", role: str = "platform_owner") -> dict[str, str]:
    return {"X-Organization-Id": org, "X-Role": role}


def _wa_transport(status: int = 200, body: dict | None = None, retry_after=None):
    payload = body or {"id": "123", "verified_name": "WA", "display_phone_number": "+100"}

    def _fn(method: str, url: str, headers: dict[str, str], raw: bytes | None, timeout: float) -> dict:
        if "graph.facebook.com" in url and "/messages" in url and method == "POST":
            return {
                "status": status if status != 200 or method == "POST" else 200,
                "ok": status < 300,
                "json": {"messages": [{"id": "wamid.1"}]} if status < 300 else {"error": {"message": "fail"}},
                "text": "{}",
                "retry_after": retry_after,
            }
        if "message_templates" in url:
            return {"status": 200, "ok": True, "json": {"data": [{"id": "t1", "name": "hello", "status": "APPROVED"}]}, "text": "{}"}
        return {"status": 200, "ok": True, "json": payload, "text": "{}", "retry_after": None}

    return _fn


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
def reset_ops(monkeypatch):
    for name in (
        "WHATSAPP_TOKEN",
        "WHATSAPP_ACCESS_TOKEN",
        "WHATSAPP_PHONE_NUMBER_ID",
        "WHATSAPP_VERIFY_TOKEN",
        "WHATSAPP_APP_SECRET",
        "WHATSAPP_BUSINESS_ACCOUNT_ID",
        "META_ADS_APP_SECRET",
        "META_APP_SECRET",
        "WHATSAPP_SEND_RATE_LIMIT",
    ):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("ENVIRONMENT", "development")
    reset_recruiting_ops_for_tests()
    yield
    reset_recruiting_ops_for_tests()


async def test_credentials_absent_not_configured(client: TestClient):
    body = await (await client.post(f"{OPS}/providers/whatsapp/test-connection", json={}, headers=_hdr())).json()
    assert body["status"] == "NOT_CONFIGURED"


async def test_credentials_saved_not_automatically_connected(client: TestClient):
    org = f"cfg-{uuid.uuid4().hex[:8]}"
    res = await client.post(
        f"{OPS}/providers/whatsapp/configure",
        json={"phone_number_id": "pnid", "access_token": TOKEN, "verify_token": "verify"},
        headers=_hdr(org),
    )
    item = (await res.json())["item"]
    assert item["status"] == "CONFIGURING"
    assert item["connected"] is False
    assert TOKEN not in str(item)


async def test_successful_health_connected_and_failed_auth(client: TestClient):
    org = f"h-{uuid.uuid4().hex[:8]}"
    set_http_transport(_wa_transport())
    get_secret_store().put("whatsapp", "access_token", TOKEN)
    get_secret_store().put("whatsapp", "phone_number_id", "123")
    ok = await (await client.post(f"{OPS}/providers/whatsapp/test-connection", json={}, headers=_hdr(org))).json()
    assert ok["status"] == "CONNECTED"
    assert ok["live_verified"] is False
    assert ok["mocked_http"] is True
    set_http_transport(lambda *a, **k: {"status": 401, "ok": False, "json": {"error": {"message": "auth"}}, "text": "auth"})
    bad = await (await client.post(f"{OPS}/providers/whatsapp/test-connection", json={}, headers=_hdr(f"e-{uuid.uuid4().hex[:8]}"))).json()
    assert bad["status"] == "ERROR"


async def test_secret_redaction(client: TestClient):
    org = f"sec-{uuid.uuid4().hex[:8]}"
    await client.post(
        f"{OPS}/providers/whatsapp/configure",
        json={"phone_number_id": "pnid", "access_token": TOKEN},
        headers=_hdr(org),
    )
    listed = await (await client.get(f"{OPS}/providers", headers=_hdr(org))).json()
    assert TOKEN not in str(listed)


async def test_webhook_verification_success_and_failure(client: TestClient):
    get_secret_store().put("whatsapp", "verify_token", "hook-secret")
    ok = await client.get(f"{OPS}/webhooks/whatsapp?hub.mode=subscribe&hub.verify_token=hook-secret&hub.challenge=abc")
    assert ok.status == 200
    assert await ok.text() == "abc"
    bad = await (await client.get(f"{OPS}/webhooks/whatsapp?hub.mode=subscribe&hub.verify_token=wrong&hub.challenge=abc")).json()
    assert bad["ok"] is False


async def test_incoming_duplicate_and_phone_matching(client: TestClient):
    org = f"in-{uuid.uuid4().hex[:8]}"
    from services.recruiting_ops.whatsapp_ops import register_phone_org

    register_phone_org("pn-1", org)
    created = await client.post(f"{OPS}/candidates", json={"name": "Анна", "phone": "+7 900 111-22-33"}, headers=_hdr(org))
    cid = (await created.json())["item"]["id"]
    payload = {
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "metadata": {"phone_number_id": "pn-1"},
                            "messages": [{"id": "wamid.in1", "from": "79001112233", "timestamp": "1", "type": "text", "text": {"body": "привет"}}],
                        }
                    }
                ]
            }
        ]
    }
    first = await (await client.post(f"{OPS}/webhooks/whatsapp", json=payload)).json()
    assert first["received"] is True
    second = await (await client.post(f"{OPS}/webhooks/whatsapp", json=payload)).json()
    assert second["duplicate_count"] >= 1
    conv = await (await client.get(f"{OPS}/whatsapp/conversations?candidate_id={cid}", headers=_hdr(org))).json()
    assert conv["items"][0]["direction"] == "incoming"
    assert conv["items"][0]["unresolved"] is False
    other = await (await client.get(f"{OPS}/whatsapp/conversations", headers=_hdr(f"other-{uuid.uuid4().hex[:8]}"))).json()
    assert other["items"] == []


async def test_unresolved_sender(client: TestClient):
    org = f"un-{uuid.uuid4().hex[:8]}"
    from services.recruiting_ops.whatsapp_ops import register_phone_org

    register_phone_org("pn-2", org)
    payload = {
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "metadata": {"phone_number_id": "pn-2"},
                            "messages": [{"id": "wamid.unknown", "from": "79990000000", "text": {"body": "hi"}}],
                        }
                    }
                ]
            }
        ]
    }
    await client.post(f"{OPS}/webhooks/whatsapp", json=payload)
    conv = await (await client.get(f"{OPS}/whatsapp/conversations", headers=_hdr(org))).json()
    assert conv["items"][0]["unresolved"] is True


async def test_outbound_requires_human_and_accepted_not_delivered(client: TestClient):
    org = f"out-{uuid.uuid4().hex[:8]}"
    set_http_transport(_wa_transport())
    get_secret_store().put("whatsapp", "access_token", TOKEN)
    get_secret_store().put("whatsapp", "phone_number_id", "123")
    await client.post(f"{OPS}/providers/whatsapp/test-connection", json={}, headers=_hdr(org))
    created = await client.post(f"{OPS}/candidates", json={"name": "Борис", "phone": "79005556677"}, headers=_hdr(org))
    cid = (await created.json())["item"]["id"]
    pending = await (await client.post(f"{OPS}/candidates/{cid}/whatsapp", json={"body": "hello"}, headers=_hdr(org))).json()
    assert pending.get("approval_required") is True
    assert pending.get("sent") is False
    sent = await (await client.post(f"{OPS}/candidates/{cid}/whatsapp", json={"body": "hello", "confirm": True}, headers=_hdr(org))).json()
    item = sent["item"]
    assert item["status"] == "SENT"
    assert item["delivered"] is False
    assert TOKEN not in str(sent)


async def test_ai_cannot_send_directly(client: TestClient):
    org = f"ai-{uuid.uuid4().hex[:8]}"
    draft = await (await client.post(f"{OPS}/whatsapp/ai-draft", json={"name": "Анна", "candidate_id": "x"}, headers=_hdr(org))).json()
    assert draft["sent"] is False
    assert draft["live_write_access"] is False
    rec = await client.post(f"{OPS}/ai/recommendations", json={"recommendation": "pause_campaign"}, headers=_hdr(org))
    rec_id = (await rec.json())["item"]["id"]
    decided = await (await client.post(f"{OPS}/ai/recommendations/{rec_id}/decision", json={"decision": "APPROVE"}, headers=_hdr(org))).json()
    assert decided["item"]["live_applied"] is False


async def test_delivery_read_failed_webhooks(client: TestClient):
    org = f"st-{uuid.uuid4().hex[:8]}"
    set_http_transport(_wa_transport())
    get_secret_store().put("whatsapp", "access_token", TOKEN)
    get_secret_store().put("whatsapp", "phone_number_id", "123")
    from services.recruiting_ops.whatsapp_ops import register_phone_org

    register_phone_org("123", org)
    await client.post(f"{OPS}/providers/whatsapp/test-connection", json={}, headers=_hdr(org))
    created = await client.post(f"{OPS}/candidates", json={"name": "Кира", "phone": "79001230000"}, headers=_hdr(org))
    cid = (await created.json())["item"]["id"]
    sent = await (await client.post(f"{OPS}/candidates/{cid}/whatsapp", json={"body": "ping", "confirm": True}, headers=_hdr(org))).json()
    pid = sent["item"]["provider_message_id"]
    await client.post(
        f"{OPS}/webhooks/whatsapp",
        json={"entry": [{"changes": [{"value": {"metadata": {"phone_number_id": "123"}, "statuses": [{"id": pid, "status": "delivered"}]}}]}]},
    )
    await client.post(
        f"{OPS}/webhooks/whatsapp",
        json={"entry": [{"changes": [{"value": {"metadata": {"phone_number_id": "123"}, "statuses": [{"id": pid, "status": "read"}]}}]}]},
    )
    conv = await (await client.get(f"{OPS}/whatsapp/conversations?candidate_id={cid}", headers=_hdr(org))).json()
    row = next(item for item in conv["items"] if item.get("provider_message_id") == pid)
    assert row["delivered"] is True
    assert row["read"] is True
    await client.post(
        f"{OPS}/webhooks/whatsapp",
        json={
            "entry": [
                {
                    "changes": [
                        {
                            "value": {
                                "metadata": {"phone_number_id": "123"},
                                "statuses": [{"id": "wamid.fail", "status": "failed", "errors": [{"code": 131047, "title": "Message undeliverable"}]}],
                            }
                        }
                    ]
                }
            ]
        },
    )


async def test_retry_and_rate_limit(client: TestClient, monkeypatch):
    calls = {"n": 0}

    def flaky(method, url, headers, raw, timeout):
        if "/messages" in url and method == "POST":
            calls["n"] += 1
            if calls["n"] < 2:
                return {"status": 429, "ok": False, "json": {"error": {"message": "rate"}}, "text": "rate", "retry_after": "1"}
            return {"status": 200, "ok": True, "json": {"messages": [{"id": "wamid.retry"}]}, "text": "{}"}
        return {"status": 200, "ok": True, "json": {"id": "123", "verified_name": "WA"}, "text": "{}"}

    set_http_transport(flaky)
    get_secret_store().put("whatsapp", "access_token", TOKEN)
    get_secret_store().put("whatsapp", "phone_number_id", "123")
    org = f"rt-{uuid.uuid4().hex[:8]}"
    await client.post(f"{OPS}/providers/whatsapp/test-connection", json={}, headers=_hdr(org))
    created = await client.post(f"{OPS}/candidates", json={"name": "Ретри", "phone": "79001110000"}, headers=_hdr(org))
    cid = (await created.json())["item"]["id"]
    sent = await (await client.post(f"{OPS}/candidates/{cid}/whatsapp", json={"body": "retry", "confirm": True}, headers=_hdr(org))).json()
    assert sent["item"]["status"] == "SENT"
    monkeypatch.setenv("WHATSAPP_SEND_RATE_LIMIT", "1")
    org2 = f"rl-{uuid.uuid4().hex[:8]}"
    await client.post(f"{OPS}/providers/whatsapp/test-connection", json={}, headers=_hdr(org2))
    c2 = await client.post(f"{OPS}/candidates", json={"name": "Лим", "phone": "79001110001"}, headers=_hdr(org2))
    cid2 = (await c2.json())["item"]["id"]
    first = await client.post(f"{OPS}/candidates/{cid2}/whatsapp", json={"body": "one", "confirm": True}, headers=_hdr(org2))
    assert first.status in {200, 201}
    second = await client.post(f"{OPS}/candidates/{cid2}/whatsapp", json={"body": "two", "confirm": True}, headers=_hdr(org2))
    body = await second.json()
    assert second.status == 429 or body.get("error") == "RATE_LIMITED"


async def test_audit_and_metrics_and_telegram_frozen(client: TestClient):
    org = f"aud-{uuid.uuid4().hex[:8]}"
    await client.post(
        f"{OPS}/providers/whatsapp/configure",
        json={"phone_number_id": "pnid", "access_token": TOKEN},
        headers=_hdr(org),
    )
    activity = await (await client.get(f"{OPS}/activity", headers=_hdr(org))).json()
    assert TOKEN not in str(activity)
    assert any("provider" in str(item.get("action") or "") or "credential" in str(item.get("action") or "") for item in activity.get("items") or [])
    health = await (await client.get(f"{OPS}/health")).json()
    assert health["sprint"] == "recruiting_1.11"
    assert health["telegram"]["frozen"] is True
    text = prometheus_text()
    for name in (
        "whatsapp_send_attempt_total",
        "whatsapp_send_success_total",
        "whatsapp_send_failure_total",
        "whatsapp_webhook_received_total",
        "whatsapp_webhook_duplicate_total",
        "whatsapp_message_delivered_total",
        "whatsapp_message_read_total",
        "whatsapp_provider_health",
        "whatsapp_rate_limited_total",
        "whatsapp_send_latency",
    ):
        assert name in text


def test_phone_matching_unit():
    assert match_candidate([{"id": "1", "phone": "+7 (900) 111-22-33"}], "79001112233")["id"] == "1"
    assert match_candidate([{"id": "1", "phone": "123"}], "999") is None
    assert normalize_phone("+7 900 111 22 33").endswith("9001112233")


async def test_webhook_signature_failure(client: TestClient):
    get_secret_store().put("whatsapp", "app_secret", "app-secret")
    res = await client.post(
        f"{OPS}/webhooks/whatsapp",
        json={"entry": []},
        headers={"X-Hub-Signature-256": "sha256=deadbeef"},
    )
    body = await res.json()
    assert body["ok"] is False
    raw = json.dumps({"entry": []}, separators=(",", ":")).encode("utf-8")
    digest = hmac.new(b"app-secret", raw, hashlib.sha256).hexdigest()
    signed = await client.post(
        f"{OPS}/webhooks/whatsapp",
        data=b'{"entry":[]}',
        headers={"Content-Type": "application/json", "X-Hub-Signature-256": f"sha256={digest}"},
    )
    ok = await signed.json()
    assert ok["ok"] is True
