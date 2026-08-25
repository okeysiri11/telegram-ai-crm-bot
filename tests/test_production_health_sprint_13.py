"""Sprint 13 — production liveness/readiness hardening.

Covers the additive service-identity fields on the existing Production
Readiness Suite endpoints and the liveness/readiness HTTP status contract,
without requiring live Telegram/Redis dependencies.
"""

from __future__ import annotations

import json

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from api.health_handlers import health_handler, liveness_handler, readiness_handler
from services.production_readiness_suite import (
    SERVICE_NAME,
    SUITE_VERSION,
    ProductionReadinessSuite,
    _service_identity,
)

SECRET_MARKERS = ("password", "secret", "token=", "postgresql+", "postgresql://", "redis://", "api_key")


@pytest.fixture
async def health_client():
    app = web.Application()
    app.router.add_get("/liveness", liveness_handler)
    app.router.add_get("/readiness", readiness_handler)
    app.router.add_get("/health", health_handler)
    async with TestClient(TestServer(app)) as client:
        yield client


def _ready_payload(ready: bool) -> dict:
    return {
        "suite": "production_readiness",
        "version": SUITE_VERSION,
        "checked_at": "2026-08-25T00:00:00+00:00",
        "ready": ready,
        "ok": ready,
        "status": "healthy" if ready else "unhealthy",
        "duration_ms": 1.0,
        "checks": {
            "database": {"name": "database", "status": "healthy" if ready else "unhealthy", "ok": ready},
        },
        "unhealthy": [] if ready else ["database"],
        "degraded": [],
    }


def test_service_identity_shape_and_no_secrets():
    identity = _service_identity()
    assert identity["service"] == SERVICE_NAME
    assert identity["runtime"] in {"production", "development"}
    assert identity["service_version"]
    serialized = json.dumps(identity).lower()
    for marker in SECRET_MARKERS:
        assert marker not in serialized


@pytest.mark.asyncio
async def test_liveness_reports_identity_and_keeps_existing_contract(health_client: TestClient):
    response = await health_client.get("/liveness")
    assert response.status == 200
    body = await response.json()
    # Existing contract preserved (additive change only).
    assert body["status"] == "alive"
    assert body["version"] == SUITE_VERSION
    assert body["timestamp"]
    # Sprint 13 additive identity.
    assert body["service"] == SERVICE_NAME
    assert body["runtime"] in {"production", "development"}
    assert body["service_version"]
    serialized = json.dumps(body).lower()
    for marker in SECRET_MARKERS:
        assert marker not in serialized


@pytest.mark.asyncio
async def test_readiness_returns_200_with_identity_when_ready(health_client: TestClient, monkeypatch):
    async def fake_validation(cls=None, *, persist=True):
        return _ready_payload(True)

    monkeypatch.setattr(
        ProductionReadinessSuite, "run_dependency_validation", classmethod(fake_validation)
    )
    response = await health_client.get("/readiness")
    assert response.status == 200
    body = await response.json()
    assert body["status"] == "ready"
    assert body["ready"] is True
    assert body["service"] == SERVICE_NAME
    assert body["runtime"] in {"production", "development"}
    assert body["database"] == "healthy"
    assert body["checks"]["database"] == "healthy"


@pytest.mark.asyncio
async def test_readiness_returns_503_when_critical_dependency_down(health_client: TestClient, monkeypatch):
    async def fake_validation(cls=None, *, persist=True):
        return _ready_payload(False)

    monkeypatch.setattr(
        ProductionReadinessSuite, "run_dependency_validation", classmethod(fake_validation)
    )
    response = await health_client.get("/readiness")
    assert response.status == 503
    body = await response.json()
    assert body["status"] == "not_ready"
    assert body["ready"] is False
    assert body["database"] == "unhealthy"
    assert body["unhealthy"] == ["database"]


@pytest.mark.asyncio
async def test_health_includes_identity_and_alerts(health_client: TestClient, monkeypatch):
    async def fake_validation(cls=None, *, persist=True):
        return _ready_payload(True)

    async def fake_alerts(cls=None):
        return []

    monkeypatch.setattr(
        ProductionReadinessSuite, "run_dependency_validation", classmethod(fake_validation)
    )
    monkeypatch.setattr(ProductionReadinessSuite, "get_active_alerts", classmethod(fake_alerts))
    response = await health_client.get("/health")
    assert response.status == 200
    body = await response.json()
    assert body["ok"] is True
    assert body["service"] == SERVICE_NAME
    assert body["alerts"] == []
