"""Sprint Recruiting 1.6 — Redis shared stores, tracking health, provider readiness."""

from __future__ import annotations

import os
import time
import uuid

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.recruiting_enterprise.api.register import register_recruiting_enterprise_routes
from applications.vanguard_site.api.register import register_vanguard_site_routes
from services.recruiting_ops import get_recruiting_ops_service, reset_recruiting_ops_for_tests
from services.recruiting_ops.ingest_auth import DEV_FALLBACK_SECRET, sign_ingest_body, verify_ingest_request
from services.recruiting_ops.provider_readiness import ads_readiness, antibot_readiness, messaging_readiness, redact_mapping
from services.recruiting_ops.shared_store import SharedStore, redis_reachable, set_store_for_tests

OPS = "/api/recruiting-ops/v1"
SITE = "/api/vanguard-site/v1"
REDIS_SKIP = not redis_reachable()


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
    monkeypatch.setenv("VANGUARD_INGEST_SECRET", DEV_FALLBACK_SECRET)
    monkeypatch.delenv("VANGUARD_WEBSITE_URL", raising=False)
    monkeypatch.delenv("META_ADS_ACCESS_TOKEN", raising=False)
    monkeypatch.delenv("META_ADS_ACCOUNT_ID", raising=False)
    reset_recruiting_ops_for_tests()
    yield
    reset_recruiting_ops_for_tests()


def _two_redis() -> tuple[SharedStore, SharedStore]:
    url = (os.getenv("VANGUARD_SHARED_STORE_URL") or os.getenv("REDIS_URL") or "").strip()
    import redis

    a = SharedStore(
        backend="redis",
        shared=True,
        redis_client=redis.Redis.from_url(url, decode_responses=True, socket_connect_timeout=0.4),
    )
    b = SharedStore(
        backend="redis",
        shared=True,
        redis_client=redis.Redis.from_url(url, decode_responses=True, socket_connect_timeout=0.4),
    )
    return a, b


def test_process_local_never_reports_shared():
    store = SharedStore(backend="process_local", shared=True)
    assert store.shared is False
    assert store.describe()["shared"] is False


def test_production_missing_redis_fail_closed(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.delenv("REDIS_URL", raising=False)
    monkeypatch.delenv("VANGUARD_SHARED_STORE_URL", raising=False)
    store = SharedStore.connect()
    assert store.backend == "unavailable"
    assert store.shared is False
    assert store.fail_closed is True
    hit = store.hit_rate("k", 5, 60)
    assert hit["allowed"] is False
    assert hit["error"] == "store_unavailable"
    assert store.claim_nonce("n1", 10) is False


def test_production_unreachable_redis_fail_closed(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.delenv("VANGUARD_SHARED_STORE_URL", raising=False)
    monkeypatch.setenv("REDIS_URL", "redis://127.0.0.1:1/0")
    store = SharedStore.connect()
    assert store.backend == "unavailable"
    assert store.shared is False
    assert store.fail_closed is True


@pytest.mark.skipif(REDIS_SKIP, reason="REDIS_UNAVAILABLE")
def test_real_redis_connectivity():
    a, _b = _two_redis()
    assert a.backend == "redis"
    assert a.shared is True
    ping = a._redis.ping()
    assert ping is True


@pytest.mark.skipif(REDIS_SKIP, reason="REDIS_UNAVAILABLE")
def test_shared_rate_limit_cross_instance():
    a, b = _two_redis()
    key = f"rl-x-{uuid.uuid4().hex}"
    for _ in range(3):
        assert a.hit_rate(key, 3, 60)["allowed"] is True
    blocked = b.hit_rate(key, 3, 60)
    assert blocked["allowed"] is False
    assert blocked["error"] == "rate_limited"
    assert a.shared is True and b.shared is True


@pytest.mark.skipif(REDIS_SKIP, reason="REDIS_UNAVAILABLE")
def test_replay_cross_instance_and_ttl():
    a, b = _two_redis()
    nonce = f"n-{uuid.uuid4().hex}"
    assert a.claim_nonce(nonce, 2) is True
    assert b.claim_nonce(nonce, 2) is False
    ttl = a.nonce_ttl(nonce)
    assert ttl is not None and ttl <= 2
    time.sleep(2.3)
    assert a.nonce_ttl(nonce) is None
    assert b.claim_nonce(nonce, 2) is True


async def test_fail_closed_apply_returns_503(client: TestClient):
    set_store_for_tests(SharedStore(backend="unavailable", shared=False, fail_closed=True))
    res = await client.post(
        f"{SITE}/applications",
        json={"first_name": "Closed", "email": f"closed.{uuid.uuid4().hex[:6]}@example.com"},
    )
    assert res.status == 503
    body = await res.json()
    assert body["error"] == "store_unavailable"
    assert body.get("ok") is False


def test_fail_closed_ingest_is_not_bad_signature():
    set_store_for_tests(SharedStore(backend="unavailable", shared=False, fail_closed=True))
    raw = b'{"email":"a@b.co","first_name":"A"}'
    ts = str(time.time())
    nn = uuid.uuid4().hex
    sig = sign_ingest_body(body=raw, timestamp=ts, nonce=nn, secret=DEV_FALLBACK_SECRET)
    result = verify_ingest_request(body=raw, signature=sig, timestamp=ts, nonce=nn)
    assert result["ok"] is False
    assert result["error"] == "store_unavailable"


async def test_tracking_recover_durable_failed_without_delete(monkeypatch):
    org = f"recov-{uuid.uuid4().hex[:8]}"
    monkeypatch.setenv("VANGUARD_ORGANIZATION_ID", org)
    svc = get_recruiting_ops_service()
    await svc.ensure_hydrated(org)
    svc._bag(org)["tracking"].append(
        {
            "id": "trk-durable-failed",
            "delivery_status": "FAILED",
            "durable": True,
            "storage": "postgres",
            "persistence_mode": "POSTGRES",
            "destination": "recruiting_db",
            "created_at": "2026-01-01T00:00:00Z",
        }
    )
    recovered = await svc.recover_tracking_records()
    assert recovered["deleted"] == 0
    assert "trk-durable-failed" in recovered["ids"]
    item = svc._find(org, "tracking", "trk-durable-failed")
    assert item is not None
    assert item["delivery_status"] == "DELIVERED"
    assert item["recovery_reason"] == "persisted_in_postgres"
    diag = svc.tracking_diagnostics()
    assert diag["code"] == "CONNECTED"
    assert diag["failed"] == 0
    assert diag["delivered"] >= 1


async def test_provider_not_configured_does_not_poison_tracking(monkeypatch):
    org = f"pnc-{uuid.uuid4().hex[:8]}"
    monkeypatch.setenv("VANGUARD_ORGANIZATION_ID", org)
    svc = get_recruiting_ops_service()
    await svc.ensure_hydrated(org)
    svc._bag(org)["tracking"].append(
        {
            "id": "trk-meta",
            "delivery_status": "FAILED",
            "destination": "meta",
            "durable": False,
            "created_at": "2026-01-02T00:00:00Z",
        }
    )
    diag = svc.tracking_diagnostics()
    assert diag["provider_not_configured"] >= 1
    assert diag["code"] == "CONNECTED"


def test_provider_not_configured_and_secret_redaction():
    ads = ads_readiness()
    assert ads["providers"]["meta"]["status"] == "NOT_CONFIGURED"
    assert ads["providers"]["google"]["status"] == "NOT_CONFIGURED"
    assert ads["providers"]["tiktok"]["status"] == "NOT_CONFIGURED"
    assert ads["connected"] is False
    assert "META_ADS_ACCESS_TOKEN" not in ads["providers"]["meta"]["missing"]
    msg = messaging_readiness()
    assert msg["channels"]["telegram"]["sent"] is False
    assert msg["channels"]["telegram"]["journal_only"] is True
    assert msg["channels"]["telegram"]["status"] == "NOT_CONFIGURED"
    anti = antibot_readiness()
    assert anti["status"] == "NOT_CONFIGURED"
    assert anti["captcha_active"] is False
    redacted = redact_mapping({"META_ADS_ACCESS_TOKEN": "super-secret-token", "META_ADS_ACCOUNT_ID": "act_1"})
    assert redacted["META_ADS_ACCESS_TOKEN"] is True
    assert "super-secret-token" not in str(redacted)
    assert redacted["META_ADS_ACCOUNT_ID"] == "act_1"


async def test_ops_diagnostics_api(client: TestClient):
    res = await client.get(f"{OPS}/ops/diagnostics", headers={"X-Organization-Id": "ados", "X-Role": "platform_owner"})
    assert res.status == 200
    body = await res.json()
    assert body["ok"] is True
    assert body["sprint"] == "recruiting_1.7"
    components = body["components"]
    for key in (
        "postgresql",
        "redis",
        "rate_limit_store",
        "replay_store",
        "tracking_worker",
        "vanguard_integration",
        "vanguard_website",
        "meta_ads",
        "google_ads",
        "tiktok_ads",
        "telegram",
        "whatsapp",
        "email",
        "anti_bot",
        "ci_e2e",
    ):
        assert key in components
        assert components[key]["label_ru"] in {"Работает", "Не настроено", "Ограничено", "Ошибка"}
    assert components["meta_ads"]["code"] == "NOT_CONFIGURED"
    assert components["meta_ads"]["label_ru"] == "Не настроено"
    assert components["vanguard_website"]["code"] == "NOT_CONFIGURED"
    assert "VANGUARD_WEBSITE_URL" in str(components["vanguard_website"])
    store = body["store"]
    if store["backend"] != "redis":
        assert store["shared"] is False
    assert body["tracking"]["provider_not_configured"] >= 0
    health = await (await client.get(f"{OPS}/health")).json()
    assert health["sprint"] == "recruiting_1.7"


async def test_journal_communication_never_sent(client: TestClient):
    res = await client.post(
        f"{OPS}/communications",
        json={"body": "Журнал", "channel": "TELEGRAM"},
        headers={"X-Organization-Id": "ados", "X-Role": "recruiter"},
    )
    assert res.status == 201
    item = (await res.json())["item"]
    assert item["sent"] is False
    assert item["journal_only"] is True
    assert item["provider_status"] == "NOT_CONFIGURED"
