"""Sprint Recruiting tracking recovery — lifecycle, health, migration."""

from __future__ import annotations

import os
import uuid

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.recruiting_enterprise.api.register import register_recruiting_enterprise_routes
from applications.vanguard_site.api.register import register_vanguard_site_routes
from services.recruiting_ops import get_recruiting_ops_service, reset_recruiting_ops_for_tests
from services.recruiting_ops.tracking_lifecycle import (
    DEAD_LETTER,
    DELIVERED,
    MAX_ATTEMPTS,
    RETRYING,
    WAITING_PROVIDER,
    build_tracking_diagnostics,
    classify_lifecycle,
    migration_patch,
)
from services.recruiting_ops.tracking_worker import TrackingWorker

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
    monkeypatch.delenv("META_ADS_ACCESS_TOKEN", raising=False)
    monkeypatch.delenv("META_ADS_ACCOUNT_ID", raising=False)
    reset_recruiting_ops_for_tests()
    yield
    reset_recruiting_ops_for_tests()


def test_failed_unconfigured_provider_is_waiting_not_dead():
    item = {
        "id": "trk-meta",
        "destination": "meta",
        "delivery_status": "FAILED",
        "durable": False,
        "created_at": "2026-01-02T00:00:00Z",
    }
    assert classify_lifecycle(item) == WAITING_PROVIDER
    patch = migration_patch(item)
    assert patch is not None
    assert patch["delivery_status"] == WAITING_PROVIDER


def test_waiting_provider_does_not_degrade_health():
    events = [
        {
            "id": "meta-1",
            "destination": "meta",
            "delivery_status": WAITING_PROVIDER,
            "durable": True,
            "storage": "postgres",
        }
    ]
    diag = build_tracking_diagnostics(events, worker={"enabled": True, "pending": 0, "retrying": 0})
    assert diag["waiting_provider"] == 1
    assert diag["retrying"] == 0
    assert diag["code"] == "CONNECTED"
    assert diag["provider_not_configured"] == 1


def test_dead_letter_is_exposed_and_does_not_hide():
    events = [
        {
            "id": "dead-1",
            "destination": "recruiting_db",
            "delivery_status": DEAD_LETTER,
            "attempt": MAX_ATTEMPTS,
            "last_error": "down",
            "dead_letter_reason": "max_attempts_exceeded",
            "durable": False,
        }
    ]
    diag = build_tracking_diagnostics(events, worker={"enabled": True, "pending": 0, "retrying": 0})
    assert diag["dead_letter"] == 1
    assert diag["failed"] == 1
    assert "dead_letter" in diag


def test_historical_postgres_retrying_is_deliverable():
    item = {
        "id": "hist-1",
        "destination": "recruiting_db",
        "delivery_status": RETRYING,
        "durable": True,
        "storage": "postgres",
        "persistence_mode": "POSTGRES",
        "event_type": "page_view",
    }
    assert classify_lifecycle(item) == DELIVERED
    patch = migration_patch(item)
    assert patch is not None
    assert patch["delivery_status"] == DELIVERED
    assert patch["recovery_reason"] == "persisted_in_postgres"


async def test_unconfigured_provider_lands_waiting_not_retrying(client: TestClient):
    res = await client.post(
        f"{SITE}/events",
        json={
            "event_type": "page_view",
            "visitor_id": "v-meta",
            "session_id": "s-meta",
            "page": "/vanguard",
            "event_id": str(uuid.uuid4()),
            "destination": "meta",
        },
    )
    assert res.status in {200, 201}
    body = await res.json()
    assert body["item"]["delivery_status"] == WAITING_PROVIDER
    assert body["item"]["delivery_status"] != RETRYING
    from services.recruiting_ops.tracking_worker import get_tracking_worker

    assert any(
        str(p.get("event_id") or p.get("id")) == body["item"]["event_id"]
        and p.get("delivery_status") == WAITING_PROVIDER
        for p in get_tracking_worker().pending
    )
    health = await (await client.get(f"{OPS}/health")).json()
    assert health["tracking_health"]["code"] == "CONNECTED"
    assert health["tracking_health"]["waiting_provider"] >= 1
    assert health["tracking_health"]["retrying"] == 0


async def test_provider_becomes_retryable_when_configured(monkeypatch):
    import services.recruiting_ops.tracking_worker as tw

    monkeypatch.setattr(tw, "provider_is_configured", lambda dest: False)
    worker = TrackingWorker()
    worker.enqueue({"event_id": "p1", "destination": "meta", "event_type": "page_view"})
    assert worker.pending[0]["delivery_status"] == WAITING_PROVIDER

    monkeypatch.setattr(tw, "provider_is_configured", lambda dest: dest == "meta")
    calls = {"n": 0}

    async def persist(event):
        calls["n"] += 1
        return {**event, "id": "ok"}

    done = await worker.tick(persist, force=True)
    assert done[0]["delivery_status"] == DELIVERED
    assert calls["n"] == 1


async def test_bounded_retry_then_dead_letter():
    worker = TrackingWorker()

    async def persist(_event):
        raise RuntimeError("still-down")

    worker.enqueue({"event_id": "x", "event_type": "page_view", "destination": "recruiting_db"})
    for _ in range(MAX_ATTEMPTS):
        await worker.tick(persist, force=True)
    assert worker.pending[0]["delivery_status"] == DEAD_LETTER
    assert worker.pending[0]["attempt"] == MAX_ATTEMPTS
    assert "still-down" in worker.pending[0]["last_error"]
    extra = await worker.tick(persist, force=True)
    assert extra == []
    assert worker.pending[0]["attempt"] == MAX_ATTEMPTS


async def test_historical_migration_via_recover(monkeypatch):
    org = f"mig-{uuid.uuid4().hex[:8]}"
    monkeypatch.setenv("VANGUARD_ORGANIZATION_ID", org)
    svc = get_recruiting_ops_service()
    await svc.ensure_hydrated(org)
    svc._bag(org)["tracking"].append(
        {
            "id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            "delivery_status": RETRYING,
            "durable": True,
            "storage": "postgres",
            "persistence_mode": "POSTGRES",
            "destination": "recruiting_db",
            "event_type": "page_view",
            "created_at": "2026-08-01T00:00:00+00:00",
        }
    )
    result = await svc.recover_tracking_records(org)
    assert result["deleted"] == 0
    assert result["recovered"] >= 1
    item = svc._find(org, "tracking", "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
    assert item["delivery_status"] == DELIVERED
    diag = svc.tracking_diagnostics()
    assert diag["code"] == "CONNECTED"
    assert diag["retrying"] == 0


async def test_worker_restart_rehydrates_retrying(monkeypatch):
    org = f"wh-{uuid.uuid4().hex[:8]}"
    monkeypatch.setenv("VANGUARD_ORGANIZATION_ID", org)
    svc = get_recruiting_ops_service()
    await svc.ensure_hydrated(org)
    event = {
        "id": str(uuid.uuid4()),
        "event_id": str(uuid.uuid4()),
        "delivery_status": RETRYING,
        "durable": False,
        "destination": "recruiting_db",
        "event_type": "page_view",
        "organization_id": org,
        "next_attempt_at": "2000-01-01T00:00:00+00:00",
    }
    svc._bag(org)["tracking"].append(event)
    from services.recruiting_ops.tracking_worker import get_tracking_worker

    n = get_tracking_worker().rehydrate(svc._bag(org)["tracking"])
    assert n >= 1
    assert any(p.get("event_id") == event["event_id"] for p in get_tracking_worker().pending)


async def test_core_event_persists_delivered(client: TestClient):
    eid = str(uuid.uuid4())
    res = await client.post(
        f"{SITE}/events",
        json={
            "event_type": "page_view",
            "visitor_id": "v-core",
            "session_id": "s-core",
            "page": "/vanguard",
            "event_id": eid,
            "destination": "recruiting_db",
        },
    )
    assert res.status in {200, 201}
    body = await res.json()
    assert body["item"]["delivery_status"] == DELIVERED
    assert body["item"]["durable"] is True
    health = await (await client.get(f"{OPS}/health")).json()
    assert health["sprint"] in {"recruiting_1.8", "recruiting_1.9", "recruiting_1.10", "recruiting_1.11"}
    assert health["tracking_health"]["code"] == "CONNECTED"
