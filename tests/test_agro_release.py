"""Tests — Production Validation & Commercial Release (Sprint 8.8)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.agro_marketplace import agro_marketplace
from applications.agro_marketplace.api.register import register_agro_marketplace_routes


@pytest.fixture
def app() -> web.Application:
    application = web.Application()
    register_agro_marketplace_routes(application)
    return application


@pytest.fixture
async def client(app: web.Application):
    async with TestClient(TestServer(app)) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def reset_store():
    agro_marketplace.reset()
    yield
    agro_marketplace.reset()


def test_version_production_ready():
    health = agro_marketplace.health()
    assert health["application_version"] == "2.0.0"
    assert health["application_status"] == "Production Ready"
    assert health["release"] == "Commercial"
    version = agro_marketplace.ops.version_info()
    assert version["application_version"] == "2.0.0"
    assert version["application_status"] == "Production Ready"


def test_release_documentation_present():
    docs = Path(__file__).resolve().parents[1] / "docs"
    for name in (
        "AGRO_RELEASE.md",
        "DEPLOYMENT.md",
        "OPERATIONS.md",
        "USER_GUIDE.md",
        "ADMIN_GUIDE.md",
    ):
        assert (docs / name).exists(), name


@pytest.mark.asyncio
async def test_full_validation_and_certification():
    report = await agro_marketplace.ops.validation.run_full_validation()
    assert report.ok, report.summary
    assert report.failed == 0
    assert report.passed >= 15

    readiness = await agro_marketplace.ops.readiness()
    assert readiness.ready is True
    assert readiness.score >= 80

    release = await agro_marketplace.ops.certify()
    assert release.version == "2.0.0"
    assert release.certified is True
    assert release.release_type == "Commercial"

    deployment = await agro_marketplace.ops.verify_deployment()
    assert deployment["verified"] is True

    quality = agro_marketplace.ops.qa.quality_report()
    security = agro_marketplace.ops.qa.security_report()
    performance = agro_marketplace.ops.qa.performance_report()
    assert quality.ok and security.ok and performance.ok


@pytest.mark.asyncio
async def test_production_bundle():
    bundle = await agro_marketplace.ops.production_bundle()
    assert bundle["production_ready"] is True
    assert bundle["version"]["application_version"] == "2.0.0"
    assert set(bundle["reports"]) >= {
        "production",
        "quality",
        "security",
        "performance",
        "compatibility",
        "deployment",
    }


@pytest.mark.asyncio
async def test_ops_api(client: TestClient):
    health = await client.get("/api/agro/v1/ops/health")
    assert health.status == 200
    body = await health.json()
    assert body["application_version"] == "2.0.0"
    assert body["application_status"] == "Production Ready"

    version = await client.get("/api/agro/v1/ops/version")
    assert version.status == 200
    assert (await version.json())["release"] == "Commercial"

    validation = await client.post("/api/agro/v1/ops/validation")
    assert validation.status == 200
    assert (await validation.json())["ok"] is True

    readiness = await client.post("/api/agro/v1/ops/readiness")
    assert readiness.status == 200
    assert (await readiness.json())["ready"] is True

    release = await client.post("/api/agro/v1/ops/release", json={})
    assert release.status == 201
    data = await release.json()
    assert data["production_ready"] is True
