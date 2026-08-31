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


def _inbound_payload(phone_number_id: str, from_phone: str, msg_id: str = "wamid.in1", ts: str | None = None):
    import time

    return {
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "metadata": {"phone_number_id": phone_number_id},
                            "messages": [
                                {
                                    "id": msg_id,
                                    "from": from_phone,
                                    "timestamp": ts or str(int(time.time())),
                                    "type": "text",
                                    "text": {"body": "привет"},
                                }
                            ],
                        }
                    }
                ]
            }
        ]
    }


async def _open_window(client: TestClient, org: str, phone_number_id: str, from_phone: str, msg_id: str = "wamid.in1"):
    from services.recruiting_ops.whatsapp_ops import register_phone_org

    register_phone_org(phone_number_id, org)
    return await client.post(f"{OPS}/webhooks/whatsapp", json=_inbound_payload(phone_number_id, from_phone, msg_id))


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
    health = await (await client.get(f"{OPS}/health")).json()
    assert health["whatsapp"]["env_status"] == "NOT_CONFIGURED"
    assert TOKEN not in str(health)
    assert "wa-super" not in str(health)


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
    await _open_window(client, org, "123", "79005556677", "wamid.session-out")
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
    await _open_window(client, org, "123", "79001230000", "wamid.session-kira")
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
    await _open_window(client, org, "123", "79001110000", "wamid.session-retry")
    sent = await (await client.post(f"{OPS}/candidates/{cid}/whatsapp", json={"body": "retry", "confirm": True}, headers=_hdr(org))).json()
    assert sent["item"]["status"] == "SENT"
    monkeypatch.setenv("WHATSAPP_SEND_RATE_LIMIT", "1")
    org2 = f"rl-{uuid.uuid4().hex[:8]}"
    await client.post(f"{OPS}/providers/whatsapp/test-connection", json={}, headers=_hdr(org2))
    c2 = await client.post(f"{OPS}/candidates", json={"name": "Лим", "phone": "79001110001"}, headers=_hdr(org2))
    cid2 = (await c2.json())["item"]["id"]
    await _open_window(client, org2, "123", "79001110001", "wamid.session-lim")
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
    assert health["sprint"] in {"recruiting_1.11", "recruiting_1.12"}
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


def test_template_message_payload_creation():
    from services.recruiting_ops.whatsapp_ops import build_template_message, session_window

    payload = build_template_message(
        to="+7 900 111-22-33",
        name="hello_world",
        language="en_US",
        components=[{"type": "body", "parameters": [{"type": "text", "text": "Anna"}]}],
    )
    assert payload["type"] == "template"
    assert payload["messaging_product"] == "whatsapp"
    assert payload["to"].endswith("9001112233")
    assert payload["template"]["name"] == "hello_world"
    assert payload["template"]["language"]["code"] == "en_US"
    assert payload["template"]["components"][0]["parameters"][0]["text"] == "Anna"
    first = session_window({}, [])
    assert first["template_required"] is True
    assert first["reason"] == "TEMPLATE_REQUIRED_NO_INBOUND"


async def test_env_alias_and_readiness_states(client: TestClient, monkeypatch):
    health = await (await client.get(f"{OPS}/health")).json()
    assert health["whatsapp"]["env_status"] == "NOT_CONFIGURED"
    monkeypatch.setenv("WHATSAPP_TOKEN", TOKEN)
    monkeypatch.setenv("WHATSAPP_PHONE_NUMBER_ID", "123")
    from services.recruiting_ops.whatsapp_ops import env_readiness

    partial = env_readiness()
    assert partial["status"] == "PARTIALLY_CONFIGURED"
    assert partial["alias_used"] is True
    assert TOKEN not in str(partial)
    monkeypatch.setenv("WHATSAPP_ACCESS_TOKEN", TOKEN)
    monkeypatch.setenv("WHATSAPP_VERIFY_TOKEN", "verify")
    monkeypatch.setenv("WHATSAPP_APP_SECRET", "app-secret")
    ready = env_readiness()
    assert ready["status"] == "READY_FOR_LIVE_CHECK"
    assert ready["live_verified"] is False
    assert ready["health_sends_message"] is False


async def test_template_send_success_and_meta_failure(client: TestClient):
    org = f"tpl-{uuid.uuid4().hex[:8]}"
    captured: dict = {}

    def transport(method, url, headers, raw, timeout):
        if "/messages" in url and method == "POST":
            captured["raw"] = raw
            captured["n"] = captured.get("n", 0) + 1
            return {"status": 200, "ok": True, "json": {"messages": [{"id": "wamid.tpl"}]}, "text": "{}"}
        return {"status": 200, "ok": True, "json": {"id": "123", "verified_name": "WA"}, "text": "{}"}

    set_http_transport(transport)
    get_secret_store().put("whatsapp", "access_token", TOKEN)
    get_secret_store().put("whatsapp", "phone_number_id", "123")
    await client.post(f"{OPS}/providers/whatsapp/test-connection", json={}, headers=_hdr(org))
    created = await client.post(f"{OPS}/candidates", json={"name": "Анна", "phone": "79001112233"}, headers=_hdr(org))
    cid = (await created.json())["item"]["id"]
    sent = await (
        await client.post(
            f"{OPS}/candidates/{cid}/whatsapp",
            json={
                "confirm": True,
                "template_name": "hello_world",
                "language": "en_US",
                "parameters": ["Anna"],
            },
            headers=_hdr(org),
        )
    ).json()
    assert sent["ok"] is True
    assert sent["item"]["status"] == "SENT"
    body = json.loads(captured["raw"].decode("utf-8"))
    assert body["type"] == "template"
    assert body["template"]["name"] == "hello_world"
    assert TOKEN not in str(sent)

    set_http_transport(_wa_transport(status=400))
    failed = await (
        await client.post(
            f"{OPS}/candidates/{cid}/whatsapp",
            json={"confirm": True, "template_name": "hello_world", "language": "en_US"},
            headers=_hdr(org),
        )
    ).json()
    assert failed.get("item", {}).get("status") == "FAILED" or failed.get("ok") is False


async def test_text_inside_window_and_template_outside(client: TestClient):
    org = f"win-{uuid.uuid4().hex[:8]}"
    set_http_transport(_wa_transport())
    get_secret_store().put("whatsapp", "access_token", TOKEN)
    get_secret_store().put("whatsapp", "phone_number_id", "123")
    await client.post(f"{OPS}/providers/whatsapp/test-connection", json={}, headers=_hdr(org))
    created = await client.post(f"{OPS}/candidates", json={"name": "Окно", "phone": "79004445566"}, headers=_hdr(org))
    cid = (await created.json())["item"]["id"]
    first = await (await client.post(f"{OPS}/candidates/{cid}/whatsapp", json={"body": "hello", "confirm": True}, headers=_hdr(org))).json()
    assert first["ok"] is False
    assert first["error"] == "TEMPLATE_REQUIRED"
    assert first["reason"] == "TEMPLATE_REQUIRED_NO_INBOUND"
    await _open_window(client, org, "123", "79004445566", "wamid.win")
    inside = await (await client.post(f"{OPS}/candidates/{cid}/whatsapp", json={"body": "hello", "confirm": True}, headers=_hdr(org))).json()
    assert inside["item"]["status"] == "SENT"
    created2 = await client.post(f"{OPS}/candidates", json={"name": "Истекло", "phone": "79004445567"}, headers=_hdr(org))
    cid2 = (await created2.json())["item"]["id"]
    from datetime import datetime, timedelta, timezone

    old_ts = str(int((datetime.now(timezone.utc) - timedelta(hours=25)).timestamp()))
    await client.post(f"{OPS}/webhooks/whatsapp", json=_inbound_payload("123", "79004445567", "wamid.old", ts=old_ts))
    expired = await (await client.post(f"{OPS}/candidates/{cid2}/whatsapp", json={"body": "later", "confirm": True}, headers=_hdr(org))).json()
    assert expired["ok"] is False
    assert expired["error"] == "TEMPLATE_REQUIRED"
    assert expired["reason"] == "TEMPLATE_REQUIRED_WINDOW_EXPIRED"
    tpl = await (
        await client.post(
            f"{OPS}/candidates/{cid2}/whatsapp",
            json={"confirm": True, "template_name": "hello_world", "language": "ru"},
            headers=_hdr(org),
        )
    ).json()
    assert tpl["item"]["status"] == "SENT"


async def test_outbound_idempotency(client: TestClient):
    org = f"idm-{uuid.uuid4().hex[:8]}"
    calls = {"n": 0}

    def transport(method, url, headers, raw, timeout):
        if "/messages" in url and method == "POST":
            calls["n"] += 1
            return {"status": 200, "ok": True, "json": {"messages": [{"id": f"wamid.idm{calls['n']}"}]}, "text": "{}"}
        return {"status": 200, "ok": True, "json": {"id": "123"}, "text": "{}"}

    set_http_transport(transport)
    get_secret_store().put("whatsapp", "access_token", TOKEN)
    get_secret_store().put("whatsapp", "phone_number_id", "123")
    await client.post(f"{OPS}/providers/whatsapp/test-connection", json={}, headers=_hdr(org))
    created = await client.post(f"{OPS}/candidates", json={"name": "Идем", "phone": "79007778899"}, headers=_hdr(org))
    cid = (await created.json())["item"]["id"]
    await _open_window(client, org, "123", "79007778899", "wamid.idm-in")
    headers = {**_hdr(org), "Idempotency-Key": "send-once-1"}
    first = await (await client.post(f"{OPS}/candidates/{cid}/whatsapp", json={"body": "same", "confirm": True}, headers=headers)).json()
    second = await (await client.post(f"{OPS}/candidates/{cid}/whatsapp", json={"body": "same", "confirm": True}, headers=headers)).json()
    assert first["item"]["status"] == "SENT"
    assert second.get("duplicate") is True
    assert calls["n"] == 1
    fail_calls = {"n": 0}

    def flaky(method, url, headers, raw, timeout):
        if "/messages" in url and method == "POST":
            fail_calls["n"] += 1
            if fail_calls["n"] == 1:
                return {"status": 400, "ok": False, "json": {"error": {"message": "fail"}}, "text": "fail"}
            return {"status": 200, "ok": True, "json": {"messages": [{"id": "wamid.retry-ok"}]}, "text": "{}"}
        return {"status": 200, "ok": True, "json": {"id": "123"}, "text": "{}"}

    set_http_transport(flaky)
    fail_headers = {**_hdr(org), "Idempotency-Key": "retry-failed-1"}
    failed = await (await client.post(f"{OPS}/candidates/{cid}/whatsapp", json={"body": "retry-me", "confirm": True}, headers=fail_headers)).json()
    assert failed["item"]["status"] == "FAILED"
    retried = await (await client.post(f"{OPS}/candidates/{cid}/whatsapp", json={"body": "retry-me", "confirm": True}, headers=fail_headers)).json()
    assert retried["item"]["status"] == "SENT"
    assert fail_calls["n"] == 2


async def test_phone_number_org_survives_cache_reset(client: TestClient):
    org = f"map-{uuid.uuid4().hex[:8]}"
    await client.post(
        f"{OPS}/providers/whatsapp/configure",
        json={"phone_number_id": "pn-restart", "access_token": TOKEN},
        headers=_hdr(org),
    )
    from services.recruiting_ops import get_recruiting_ops_service
    from services.recruiting_ops.whatsapp_ops import org_for_phone_number_id, reset_whatsapp_runtime_for_tests

    reset_whatsapp_runtime_for_tests()
    assert org_for_phone_number_id("pn-restart") is None
    resolved = await get_recruiting_ops_service().resolve_whatsapp_org("pn-restart")
    assert resolved == org
    payload = _inbound_payload("pn-restart", "79990001111", "wamid.map1")
    posted = await (await client.post(f"{OPS}/webhooks/whatsapp", json=payload)).json()
    assert posted["ok"] is True
    conv = await (await client.get(f"{OPS}/whatsapp/conversations", headers=_hdr(org))).json()
    assert conv["items"]


async def test_unknown_phone_and_malformed_webhook(client: TestClient):
    unknown = await (
        await client.post(
            f"{OPS}/webhooks/whatsapp",
            json=_inbound_payload("unknown-pn", "79000000000", "wamid.unk"),
        )
    ).json()
    assert unknown["ok"] is False
    assert unknown["error"] == "UNKNOWN_PHONE_NUMBER_ID"
    malformed = await (await client.post(f"{OPS}/webhooks/whatsapp", json={"entry": [{"changes": "bad"}]})).json()
    assert malformed["ok"] is False
    assert malformed["error"] == "MALFORMED_WEBHOOK"
