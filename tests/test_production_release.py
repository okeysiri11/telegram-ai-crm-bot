"""Tests — Production Release & Go-Live (Sprint 6.8)."""

from __future__ import annotations

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.auto_marketplace import auto_marketplace
from applications.auto_marketplace.api.register import register_auto_marketplace_routes
from applications.auto_marketplace.config import DEFAULT_CONFIG
from applications.auto_marketplace.release.models import ValidationStatus


@pytest.fixture
def app() -> web.Application:
    application = web.Application()
    register_auto_marketplace_routes(application)
    return application


@pytest.fixture
async def client(app: web.Application):
    async with TestClient(TestServer(app)) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def reset_store():
    auto_marketplace.reset()
    yield
    auto_marketplace.reset()


def test_version_and_release_status():
    assert DEFAULT_CONFIG.application_version == "1.4.0-alpha"
    assert DEFAULT_CONFIG.release_status == "Service Alpha"
    assert DEFAULT_CONFIG.platform_dependency == "AI Platform Core v3"
    assert DEFAULT_CONFIG.ecosystem_dependency == "AI Ecosystem v1.5"


@pytest.mark.asyncio
async def test_production_validation():
    validations = await auto_marketplace.production_engine.validator.validate_all()
    assert len(validations) >= 10
    failed = [v for v in validations if v.status == ValidationStatus.FAILED]
    assert not failed, [f"{v.check_id}: {v.message}" for v in failed]


@pytest.mark.asyncio
async def test_performance_benchmarks():
    benchmarks = await auto_marketplace.production_engine.performance.run_all(iterations=3)
    assert len(benchmarks) == 6
    for bench in benchmarks:
        assert bench.operations == 3


@pytest.mark.asyncio
async def test_security_audit():
    audit = await auto_marketplace.production_engine.security.run_audit()
    assert len(audit) >= 5
    failed = [a for a in audit if a.status == ValidationStatus.FAILED]
    assert not failed, [f"{a.check_id}: {a.message}" for a in failed]


@pytest.mark.asyncio
async def test_release_report_production_ready():
    report = await auto_marketplace.production_engine.generate_release_report(run_benchmarks=True)
    assert report.application_version == "1.4.0-alpha"
    assert report.release_status == "Service Alpha"
    assert report.production_ready, report.to_dict()


@pytest.mark.asyncio
async def test_backup_and_restore():
    snapshot = auto_marketplace.production_engine.backups.create_snapshot()
    assert snapshot["snapshot_id"]
    assert auto_marketplace.production_engine.backups.verify_snapshot(snapshot)


def test_maintenance_mode():
    auto_marketplace.production_engine.maintenance.enable(message="Upgrade in progress")
    assert auto_marketplace.production_engine.maintenance.enabled
    auto_marketplace.production_engine.maintenance.disable()
    assert not auto_marketplace.production_engine.maintenance.enabled


def test_deployment_checklist():
    checklist = auto_marketplace.production_engine.go_live_checklist()
    assert len(checklist) >= 8


def test_release_manifest():
    manifest = auto_marketplace.production_engine.release_manifest()
    assert manifest["application_version"] == "1.4.0-alpha"
    assert manifest["release_status"] == "Service Alpha"


@pytest.mark.asyncio
async def test_ops_api(client: TestClient):
    resp = await client.get("/api/auto/v1/ops/health")
    assert resp.status == 200
    data = await resp.json()
    assert data["application_version"] == "1.4.0-alpha"

    resp = await client.get("/api/auto/v1/ops/release/report")
    assert resp.status == 200
    report = await resp.json()
    assert report["production_ready"] is True

    resp = await client.get("/api/auto/v1/ops/deployment/checklist")
    assert resp.status == 200
