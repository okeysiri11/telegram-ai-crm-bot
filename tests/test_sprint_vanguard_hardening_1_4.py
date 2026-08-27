"""Sprint Recruiting 1.4 — Vanguard production hardening."""

from __future__ import annotations

import uuid

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.recruiting_enterprise.api.register import register_recruiting_enterprise_routes
from applications.vanguard_site.api.register import register_vanguard_site_routes
from services.recruiting_ops import reset_recruiting_ops_for_tests

OPS = "/api/recruiting-ops/v1"
SITE = "/api/vanguard-site/v1"


@pytest.fixture
def app() -> web.Application:
    application = web.Application()
    register_recruiting_enterprise_routes(application)
    register_vanguard_site_routes(application)
    return application


@pytest.fixture
async def client(app: web.Application):
    async with TestClient(TestServer(app)) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def reset_ops(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.delenv("VANGUARD_WEBSITE_URL", raising=False)
    monkeypatch.delenv("VANGUARD_PUBLIC_URL", raising=False)
    monkeypatch.delenv("VANGUARD_ANTIBOT_REQUIRED", raising=False)
    monkeypatch.setenv("VANGUARD_ANTIBOT_PROVIDER", "none")
    monkeypatch.setenv("VANGUARD_APPLY_RATE_LIMIT", "20")
    reset_recruiting_ops_for_tests()
    yield
    reset_recruiting_ops_for_tests()


def _hdr() -> dict[str, str]:
    return {"X-Organization-Id": "ados", "X-Role": "platform_owner"}


async def test_invalid_email_rejected(client: TestClient):
    res = await client.post(
        f"{SITE}/applications",
        json={"first_name": "Bad", "email": "not-an-email"},
    )
    assert res.status == 400
    body = await res.json()
    assert body["ok"] is False
    assert "email" in body["message_ru"].lower() or "коррект" in body["message_ru"].lower()


async def test_payload_too_large(client: TestClient, monkeypatch):
    monkeypatch.setenv("VANGUARD_APPLY_MAX_BYTES", "128")
    blob = b'{"first_name":"Huge","email":"huge@example.com","message":"' + b"x" * 400 + b'"}'
    res = await client.post(f"{SITE}/applications", data=blob, headers={"Content-Type": "application/json"})
    assert res.status == 413


async def test_idempotency_key_returns_same_lead(client: TestClient):
    payload = {
        "first_name": "Idem",
        "email": f"idem.{uuid.uuid4().hex[:8]}@example.com",
        "program": "Ops",
        "idempotency_key": f"fixed-key-{uuid.uuid4().hex[:8]}",
    }
    headers = {"Idempotency-Key": payload["idempotency_key"]}
    first = await client.post(f"{SITE}/applications", json=payload, headers=headers)
    second = await client.post(f"{SITE}/applications", json=payload, headers=headers)
    assert first.status == 201
    assert second.status == 200
    a = await first.json()
    b = await second.json()
    assert b["duplicate"] is True
    assert a["item"]["id"] == b["item"]["id"]
    assert a["reference"] == b["reference"]


async def test_rate_limit_returns_429(client: TestClient, monkeypatch):
    monkeypatch.setenv("VANGUARD_APPLY_RATE_LIMIT", "2")
    monkeypatch.setenv("VANGUARD_RATE_WINDOW_SECONDS", "60")
    reset_recruiting_ops_for_tests()
    headers = {"X-Forwarded-For": "203.0.113.9"}
    for i in range(2):
        ok = await client.post(
            f"{SITE}/applications",
            json={"first_name": "R", "email": f"r{i}@example.com", "program": f"P{i}"},
            headers=headers,
        )
        assert ok.status in {200, 201}
    limited = await client.post(
        f"{SITE}/applications",
        json={"first_name": "R", "email": "r-limit@example.com", "program": "PX"},
        headers=headers,
    )
    assert limited.status == 429
    body = await limited.json()
    assert body["error"] == "rate_limited"
    assert limited.headers.get("Retry-After")


async def test_production_antibot_required_fails_closed(monkeypatch):
    from services.recruiting_ops.antibot import verify_antibot

    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("VANGUARD_ANTIBOT_PROVIDER", "none")
    monkeypatch.delenv("VANGUARD_ANTIBOT_REQUIRED", raising=False)
    result = verify_antibot(token=None)
    assert result["ok"] is False
    assert result["error"] == "anti_bot_not_configured"
    assert result["captcha_active"] is False


async def test_test_antibot_pass_in_development(monkeypatch):
    from services.recruiting_ops.antibot import TEST_TOKEN, verify_antibot

    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("VANGUARD_ANTIBOT_PROVIDER", "test")
    monkeypatch.setenv("VANGUARD_ANTIBOT_REQUIRED", "1")
    assert verify_antibot(token=TEST_TOKEN)["ok"] is True
    assert verify_antibot(token="nope")["ok"] is False


async def test_tracking_dedup_and_delivery_status(client: TestClient):
    eid = str(uuid.uuid4())
    first = await client.post(
        f"{SITE}/events",
        json={"event_type": "page_view", "event_id": eid, "visitor_id": "v", "session_id": "s", "page": "/vanguard"},
    )
    second = await client.post(
        f"{SITE}/events",
        json={"event_type": "page_view", "event_id": eid, "visitor_id": "v", "session_id": "s", "page": "/vanguard"},
    )
    assert first.status == 201
    a = await first.json()
    assert a["delivery_status"] == "DELIVERED"
    assert second.status == 200
    assert (await second.json())["duplicate"] is True


async def test_ads_foundation_not_connected(client: TestClient):
    res = await client.get(f"{OPS}/ads/foundation")
    assert res.status == 200
    body = await res.json()
    assert body["connected"] is False
    assert body["fake_data"] is False
    assert body["providers"]["meta"]["status"] == "not_connected"
    assert body["message_ru"] == "Провайдер не подключен"


async def test_diagnostics_independent_website(client: TestClient):
    res = await client.post(f"{OPS}/projects/vanguard/integration/check", headers=_hdr())
    body = await res.json()
    diag = body["diagnostics"]
    assert diag["website"]["code"] == "NOT_CONFIGURED"
    assert diag["integration"]["code"] in {"CONNECTED", "DEGRADED", "DISCONNECTED"}
    assert diag["website"]["code"] != diag["integration"]["code"] or diag["integration"]["reason_ru"]
    assert "last_checked" in diag
    assert body["last_check_at"]


async def test_safe_error_hides_internals(client: TestClient):
    res = await client.post(f"{SITE}/applications", json={"first_name": "X", "email": "bad"})
    blob = await res.json()
    text = str(blob)
    assert "Traceback" not in text
    assert "DATABASE_URL" not in text
    assert "VANGUARD_INGEST_SECRET" not in text
