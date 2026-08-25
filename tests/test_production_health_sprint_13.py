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

import services.production_readiness_suite as prs
from api.health_handlers import health_handler, liveness_handler, readiness_handler
from platform_configuration.configuration_center import _normalize_postgres_url
from services.production_readiness_suite import (
    SERVICE_NAME,
    SUITE_VERSION,
    ProductionReadinessSuite,
    _service_identity,
    _telegram_required,
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
    assert "revision" in identity  # Sprint 13.1 — deployed revision metadata
    serialized = json.dumps(identity).lower()
    for marker in SECRET_MARKERS:
        assert marker not in serialized


# --- Sprint 13.1 — durable deployment hardening ------------------------------


def test_postgres_url_normalization_for_provider_urls():
    assert (
        _normalize_postgres_url("postgres://u:p@host:5432/db")
        == "postgresql+asyncpg://u:p@host:5432/db"
    )
    assert (
        _normalize_postgres_url("postgresql://u:p@host:5432/db")
        == "postgresql+asyncpg://u:p@host:5432/db"
    )
    # Explicit drivers untouched.
    assert (
        _normalize_postgres_url("postgresql+asyncpg://u:p@host/db")
        == "postgresql+asyncpg://u:p@host/db"
    )
    assert (
        _normalize_postgres_url("postgresql+psycopg2://u:p@host/db")
        == "postgresql+psycopg2://u:p@host/db"
    )
    assert _normalize_postgres_url("") == ""


def test_telegram_required_defaults_and_web_profile_flag(monkeypatch):
    # Non-production: never required (existing behavior).
    monkeypatch.setattr(prs, "IS_PRODUCTION", False)
    monkeypatch.delenv("ADOS_TELEGRAM_REQUIRED", raising=False)
    assert _telegram_required() is False

    # Production default: required (bot deployments unchanged).
    monkeypatch.setattr(prs, "IS_PRODUCTION", True)
    assert _telegram_required() is True

    # Explicit web service profile opt-out.
    monkeypatch.setenv("ADOS_TELEGRAM_REQUIRED", "false")
    assert _telegram_required() is False


@pytest.mark.asyncio
async def test_check_telegram_production_missing_token(monkeypatch):
    monkeypatch.setattr(prs, "IS_PRODUCTION", True)
    monkeypatch.setattr(prs, "BOT_TOKEN", "")

    monkeypatch.delenv("ADOS_TELEGRAM_REQUIRED", raising=False)
    required = await ProductionReadinessSuite.check_telegram()
    assert required["status"] == "unhealthy"  # default production behavior preserved

    monkeypatch.setenv("ADOS_TELEGRAM_REQUIRED", "false")
    web_profile = await ProductionReadinessSuite.check_telegram()
    assert web_profile["status"] == "skipped"
    assert web_profile["ok"] is True


@pytest.mark.asyncio
async def test_check_startup_web_profile_in_production(monkeypatch):
    monkeypatch.setattr(prs, "IS_PRODUCTION", True)
    monkeypatch.setattr(prs, "BOT_TOKEN", "")

    monkeypatch.delenv("ADOS_TELEGRAM_REQUIRED", raising=False)
    strict = await ProductionReadinessSuite.check_startup()
    assert strict["status"] == "unhealthy"

    monkeypatch.setenv("ADOS_TELEGRAM_REQUIRED", "false")
    web_profile = await ProductionReadinessSuite.check_startup()
    assert web_profile["ok"] is True
    assert web_profile["status"] in {"healthy", "degraded"}


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
    assert body["persistence"]["source"] == "postgres"
    assert body["persistence"]["readback"] in {"ok", "skipped", "unavailable"}


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
