"""Sprint Recruiting 1.5 — advertising control center + shared stores."""

from __future__ import annotations

import uuid

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.recruiting_enterprise.api.register import register_recruiting_enterprise_routes
from applications.vanguard_site.api.register import register_vanguard_site_routes
from services.recruiting_ops import reset_recruiting_ops_for_tests
from services.recruiting_ops.ads_control import campaign_costs
from services.recruiting_ops.attribution import preserve_first_touch, touch_payload
from services.recruiting_ops.ingest_auth import DEV_FALLBACK_SECRET, sign_ingest_body, verify_ingest_request
from services.recruiting_ops.public_limits import check_rate_limit
from services.recruiting_ops.shared_store import SharedStore, set_store_for_tests
from services.recruiting_ops.tracking_worker import MAX_ATTEMPTS, TrackingWorker

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
    monkeypatch.setenv("VANGUARD_INGEST_SECRET", DEV_FALLBACK_SECRET)
    monkeypatch.delenv("VANGUARD_WEBSITE_URL", raising=False)
    reset_recruiting_ops_for_tests()
    yield
    reset_recruiting_ops_for_tests()


def _hdr() -> dict[str, str]:
    return {"X-Organization-Id": "ados", "X-Role": "platform_owner"}


async def test_campaign_crud_and_project_mapping(client: TestClient):
    created = await client.post(
        f"{OPS}/campaigns",
        json={"name": "Vanguard Meta", "project_key": "vanguard", "campaign_code": "vg-meta", "spend": 200},
        headers=_hdr(),
    )
    assert created.status == 201
    camp = (await created.json())["item"]
    assert camp["project_key"] == "vanguard"
    assert camp["ads_api"] == "not_connected"
    updated = await client.post(
        f"{OPS}/campaigns/{camp['id']}",
        json={"status": "paused", "spend": 250},
        headers=_hdr(),
    )
    assert updated.status == 200
    body = await updated.json()
    assert body["item"]["status"] == "paused"
    listed = await client.get(f"{OPS}/campaigns?project=vanguard", headers=_hdr())
    ids = {item["id"] for item in (await listed.json())["items"]}
    assert camp["id"] in ids


async def test_attribution_first_touch_preserved_last_touch_updates():
    first = touch_payload({"utm_source": "meta", "utm_medium": "cpc", "utm_campaign": "launch"})
    assert first["first_touch_source"] == "meta"
    existing = {**first, "id": "lead-1", "utm_source": "meta"}
    patch = preserve_first_touch(existing, {"utm_source": "google", "utm_medium": "cpc", "utm_campaign": "retarget"})
    assert "first_touch_source" not in patch
    assert patch["last_touch_source"] == "google"


async def test_ingest_duplicate_preserves_first_touch(client: TestClient):
    payload = {
        "first_name": "Touch",
        "email": f"touch.{uuid.uuid4().hex[:6]}@example.com",
        "program": "Ops",
        "source": "vanguard",
        "utm_source": "meta",
        "utm_campaign": "first-camp",
        "external_id": f"VG-T{uuid.uuid4().hex[:5].upper()}",
        "vacancy_id": "vac-touch",
    }
    first = await client.post(f"{SITE}/applications", json=payload)
    assert first.status == 201
    lead = (await first.json())["item"]
    assert lead["first_touch_source"] == "meta"
    payload["utm_source"] = "google"
    payload["utm_campaign"] = "second-camp"
    second = await client.post(f"{SITE}/applications", json=payload)
    body = await second.json()
    item = body["item"]
    assert body.get("duplicate") is True or item["id"] == lead["id"]
    assert item["first_touch_source"] == "meta"
    assert item["last_touch_source"] == "google"


async def test_funnel_and_cost_calculations(client: TestClient):
    campaign_code = f"cost-{uuid.uuid4().hex[:8]}"
    await client.post(
        f"{OPS}/campaigns",
        json={"name": "Cost Camp", "project_key": "vanguard", "campaign_code": campaign_code, "spend": 100, "impressions": None, "clicks": None},
        headers=_hdr(),
    )
    email = f"funnel.{uuid.uuid4().hex[:6]}@example.com"
    applied = await client.post(
        f"{SITE}/applications",
        json={"first_name": "Funnel", "email": email, "program": "Ops", "utm_campaign": campaign_code, "utm_source": "meta"},
    )
    lead_id = (await applied.json())["item"]["id"]
    await client.post(f"{OPS}/leads/{lead_id}/qualify", json={}, headers=_hdr())
    await client.post(f"{OPS}/leads/{lead_id}/convert", json={}, headers=_hdr())
    overview = await (await client.get(f"{OPS}/projects/vanguard", headers=_hdr())).json()
    steps = {s["id"]: s["count"] for s in overview["funnel"]["steps"]}
    assert steps["lead"] >= 1
    assert steps["qualified"] >= 1
    assert steps["candidate"] >= 1
    camp = next(c for c in overview["marketing"]["campaigns"] if c.get("campaign_code") == campaign_code)
    assert camp["cpl"] == 100
    assert camp["missing_provider_metrics"] is True
    assert camp["fake_data"] is False


def test_missing_provider_metrics_are_null():
    costs = campaign_costs(spend=50, impressions=None, clicks=None, applications=2, leads=2, candidates=1)
    assert costs["ctr"] is None
    assert costs["cpc"] is None
    assert costs["cpl"] == 25
    assert costs["cost_per_candidate"] == 50
    assert costs["missing_provider_metrics"] is True
    assert costs["message_ru"] == "Нет данных провайдера"


async def test_shared_rate_limiting_across_instances():
    mapping: dict = {}
    shared = SharedStore(backend="memory_shared", shared=True, mapping=mapping)
    other = SharedStore(backend="memory_shared", shared=True, mapping=mapping)
    set_store_for_tests(shared)
    assert check_rate_limit(key="apply:ip:shared", limit=2)["allowed"] is True
    set_store_for_tests(other)
    assert check_rate_limit(key="apply:ip:shared", limit=2)["allowed"] is True
    limited = check_rate_limit(key="apply:ip:shared", limit=2)
    assert limited["allowed"] is False
    assert limited["shared"] is True


async def test_distributed_replay_rejection():
    mapping: dict = {}
    a = SharedStore(backend="memory_shared", shared=True, mapping=mapping)
    b = SharedStore(backend="memory_shared", shared=True, mapping=mapping)
    set_store_for_tests(a)
    raw = b'{"first_name":"R","email":"r@example.com"}'
    ts = "1000000000"
    nonce = "shared-nonce-1"
    sig = sign_ingest_body(body=raw, timestamp=ts, nonce=nonce, secret=DEV_FALLBACK_SECRET)
    first = verify_ingest_request(body=raw, signature=sig, timestamp=ts, nonce=nonce, now=1_000_000_000)
    assert first["ok"] is True
    set_store_for_tests(b)
    second = verify_ingest_request(body=raw, signature=sig, timestamp=ts, nonce=nonce, now=1_000_000_000)
    assert second["ok"] is False
    assert second["error"] == "bad_signature"


async def test_tracking_retries_then_deliver():
    worker = TrackingWorker()
    calls = {"n": 0}

    async def persist(event):
        calls["n"] += 1
        if calls["n"] < 2:
            raise RuntimeError("transient")
        return {**event, "id": "trk-1"}

    worker.enqueue({"event_id": "e1", "event_type": "page_view"})
    first = await worker.tick(persist, force=True)
    assert first == []
    assert worker.pending[0]["delivery_status"] == "RETRYING"
    second = await worker.tick(persist, force=True)
    assert second[0]["delivery_status"] == "DELIVERED"


async def test_tracking_terminal_failure():
    worker = TrackingWorker()

    async def persist(_event):
        raise RuntimeError("down")

    worker.enqueue({"event_id": "e-fail", "event_type": "page_view"})
    for _ in range(MAX_ATTEMPTS):
        await worker.tick(persist, force=True)
    assert worker.pending[0]["delivery_status"] == "DEAD_LETTER"
    assert worker.pending[0]["attempt"] >= MAX_ATTEMPTS
    assert worker.pending[0]["last_error"]


async def test_messaging_journal_not_sent(client: TestClient):
    res = await client.post(
        f"{OPS}/communications",
        json={"channel": "TELEGRAM", "body": "Напоминание об интервью", "project_key": "vanguard"},
        headers=_hdr(),
    )
    assert res.status == 201
    item = (await res.json())["item"]
    assert item["channel"] == "TELEGRAM"
    assert item["sent"] is False
    assert item["delivery"] == "manual_log_only"


async def test_website_not_configured_independent(client: TestClient):
    res = await client.post(f"{OPS}/projects/vanguard/integration/check", headers=_hdr())
    body = await res.json()
    assert body["diagnostics"]["website"]["code"] == "NOT_CONFIGURED"
    assert body["diagnostics"]["integration"]["code"] in {"CONNECTED", "DEGRADED", "DISCONNECTED"}
    assert body["diagnostics"]["website"]["code"] != body["diagnostics"]["integration"]["code"]


async def test_ads_control_center_providers_not_connected(client: TestClient):
    res = await client.get(f"{OPS}/ads/control-center?project=vanguard", headers=_hdr())
    assert res.status == 200
    body = await res.json()
    assert body["connected"] is False
    assert body["fake_data"] is False
    assert body["providers"]["meta"]["status"] == "not_connected"
    assert body["providers"]["google"]["status"] == "not_connected"
    assert body["providers"]["tiktok"]["status"] == "not_connected"
    assert body["message_ru"] == "Провайдер не подключен"


async def test_health_reports_stores_and_worker(client: TestClient):
    body = await (await client.get(f"{OPS}/health")).json()
    assert body["sprint"] in {"recruiting_1.5", "recruiting_1.6", "recruiting_1.7", "recruiting_1.8", "recruiting_1.9", "recruiting_1.10"}
    assert body["rate_limit_store"]["backend"] in {"redis", "process_local"}
    assert body["replay_store"]["backend"] in {"redis", "process_local"}
    assert body["tracking_worker"]["enabled"] is True
