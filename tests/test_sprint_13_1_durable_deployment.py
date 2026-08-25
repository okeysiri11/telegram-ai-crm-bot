"""Sprint 13.1 — durable production deployment and CI foundation."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from api.health_handlers import health_handler, liveness_handler, readiness_handler
from applications.auto_marketplace import auto_marketplace
from applications.auto_marketplace.api.register import register_auto_marketplace_routes
from scripts.crm_production_smoke import smoke_payloads
from services.production_readiness_suite import _service_identity

ROOT = Path(__file__).resolve().parents[1]
AUTH = {"Authorization": "Bearer test"}


@pytest.fixture
def app() -> web.Application:
    application = web.Application()
    register_auto_marketplace_routes(application)
    return application


@pytest.fixture
async def client(app: web.Application):
    async with TestClient(TestServer(app)) as test_client:
        yield test_client


@pytest.fixture
async def health_client():
    application = web.Application()
    application.router.add_get("/liveness", liveness_handler)
    application.router.add_get("/readiness", readiness_handler)
    application.router.add_get("/health", health_handler)
    async with TestClient(TestServer(application)) as test_client:
        yield test_client


def test_durable_artifacts_and_tunnel_demotion():
    assert (ROOT / "Dockerfile").is_file()
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    assert "HEALTHCHECK" in dockerfile
    assert "USER ados" in dockerfile
    assert "GIT_SHA" in dockerfile
    compose = (ROOT / "docker-compose.prod.yml").read_text(encoding="utf-8")
    assert "NOT production" in compose
    assert "GIT_SHA" in compose
    nginx = (ROOT / "nginx.conf").read_text(encoding="utf-8")
    assert "location /liveness" in nginx
    assert "location /readiness" in nginx
    preview = (ROOT / "scripts" / "start_public_host.py").read_text(encoding="utf-8")
    assert "NOT production" in preview
    assert "PREVIEW HOST VERIFIED" in preview
    docs = (ROOT / "docs" / "deployment.md").read_text(encoding="utf-8")
    assert "PREVIEW" in docs
    assert "not production" in docs.lower()
    assert (ROOT / "render.yaml").is_file()
    assert (ROOT / "Dockerfile.web").is_file()
    assert (ROOT / "scripts" / "run_production_web.py").is_file()
    assert (ROOT / "scripts" / "rollback_production.sh").is_file()
    assert (ROOT / "scripts" / "production_doctor.py").is_file()
    assert (ROOT / "docs" / "ENVIRONMENT_CONTRACT.md").is_file()
    assert (ROOT / "docs" / "PRODUCTION_ROLLBACK.md").is_file()
    rollback = (ROOT / "docs" / "PRODUCTION_ROLLBACK.md").read_text(encoding="utf-8")
    assert "alembic downgrade" in rollback.lower() or "Alembic" in rollback


def test_revision_identity_has_no_secrets(monkeypatch):
    monkeypatch.setenv("GIT_SHA", "abc123def456")
    identity = _service_identity()
    assert identity["revision"] == "abc123def456"
    assert identity["service"] == "ados-platform-api"
    blob = str(identity).lower()
    assert "password" not in blob
    assert "postgresql" not in blob


@pytest.mark.asyncio
async def test_liveness_includes_revision(health_client: TestClient, monkeypatch):
    monkeypatch.setenv("GIT_SHA", "rev-13-1")
    response = await health_client.get("/liveness")
    assert response.status == 200
    body = await response.json()
    assert body["status"] == "alive"
    assert body["revision"] == "rev-13-1"
    assert body["service"]


@pytest.mark.asyncio
async def test_crm_manager_routes_remain_authenticated(client: TestClient):
    for path in (
        "/api/auto/v1/crm/manager/command-center",
        "/api/auto/v1/crm/manager/forecast",
        "/api/auto/v1/crm/manager/operational-summary",
    ):
        unauth = await client.get(path)
        assert unauth.status == 401, path
    metrics = await client.get("/api/auto/v1/crm/metrics", headers=AUTH)
    assert metrics.status == 200


@pytest.mark.asyncio
async def test_production_rejects_unverified_bearer(client: TestClient, monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    forged = await client.get(
        "/api/auto/v1/crm/manager/command-center",
        headers={"Authorization": "Bearer not-a-real-token"},
    )
    assert forged.status == 401
    body = await forged.json()
    assert "Authentication required" in body.get("error", "")


def test_crm_smoke_contract_helpers():
    checks = smoke_payloads(
        liveness={"status": "alive", "service": "ados-platform-api", "revision": "abc"},
        unauth_manager=401,
    )
    assert all(checks.values())


def test_env_example_documents_git_sha():
    example = (ROOT / ".env.example").read_text(encoding="utf-8")
    assert "GIT_SHA" in example
    assert "PREVIEW" in example or "not production" in example.lower()
