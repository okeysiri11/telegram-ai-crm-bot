"""Tests — Port & Logistics Enterprise Foundation (Sprint 15.0)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.port_enterprise import port_enterprise
from applications.port_enterprise.api.register import register_port_enterprise_routes
from applications.port_enterprise.shared.exceptions import ValidationError


ROOT = Path(__file__).resolve().parents[1]
PREFIX = "/api/port-enterprise/v1"
AGRO = "/api/agro-enterprise/v1"
AEC = "/api/agro-enterprise-certification/v1"


@pytest.fixture
def app() -> web.Application:
    application = web.Application()
    register_port_enterprise_routes(application)
    return application


@pytest.fixture
async def client(app: web.Application):
    async with TestClient(TestServer(app)) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def reset_store():
    port_enterprise.reset()
    yield
    port_enterprise.reset()


def test_version_port_enterprise_ready():
    health = port_enterprise.health()
    assert health["application_version"] == "4.5.3-enterprise"
    assert health["enterprise_foundation"] == "Enterprise Platform v4.5.2-enterprise"
    assert health["port_enterprise_foundation_ready"] is True
    assert health["terminal_platform_ready"] is True
    assert health["cargo_registry_ready"] is True
    assert health["fleet_registry_ready"] is True
    assert health["operations_foundation_ready"] is True


def test_port_registry_and_terminals():
    port = port_enterprise.ports.register_port(name="Test Port", unlocode="TEST1", country="UA")
    term = port_enterprise.ports.register_terminal(
        port_id=port["port_id"], name="CT", terminal_type="container"
    )
    dock = port_enterprise.ports.register_dock(terminal_id=term["terminal_id"], name="D1")
    berth = port_enterprise.ports.register_berth(dock_id=dock["dock_id"], name="B1")
    assert berth["status"] == "available"
    cap = port_enterprise.terminals.set_capacity(
        terminal_id=term["terminal_id"], capacity_teu=1000, utilized_teu=400
    )
    assert cap["utilization_pct"] == 40.0
    with pytest.raises(ValidationError):
        port_enterprise.ports.register_terminal(
            port_id=port["port_id"], name="X", terminal_type="airport"
        )


def test_cargo_fleet_operations():
    boot = port_enterprise.bootstrap()
    assert boot["port_id"] and boot["vessel_id"] and boot["cargo_id"]
    tracked = port_enterprise.cargo.track(boot["cargo_id"], status="loaded", location="Berth A1")
    assert tracked["status"] == "loaded"
    vessel = port_enterprise.fleet.set_status(boot["vessel_id"], status="alongside")
    assert vessel["status"] == "alongside"
    turnaround = port_enterprise.operations.turnaround_analytics(boot["port_id"])
    assert turnaround["arrivals"] >= 1
    for dtype in ("port", "terminal", "cargo", "fleet", "operations"):
        assert port_enterprise.dashboard.render(dashboard_type=dtype)["dashboard_type"] == dtype


@pytest.mark.asyncio
async def test_api_port_enterprise(client):
    health = await client.get(f"{PREFIX}/health")
    body = await health.json()
    assert body["application_version"] == "4.5.3-enterprise"
    assert body["port_enterprise_foundation_ready"] is True
    assert body["operations_foundation_ready"] is True

    boot = await client.post(f"{PREFIX}/bootstrap", json={})
    assert boot.status == 201
    boot_body = await boot.json()

    cargo = await client.post(
        f"{PREFIX}/cargo",
        json={"action": "track", "cargo_id": boot_body["cargo_id"], "status": "gate_out"},
    )
    assert cargo.status == 201

    ops = await client.get(f"{PREFIX}/operations?port_id={boot_body['port_id']}")
    assert ops.status == 200

    dash = await client.get(f"{PREFIX}/dashboard?type=fleet")
    assert dash.status == 200


@pytest.mark.asyncio
async def test_prior_platforms_health_untouched():
    from applications.agro_enterprise.api.register import register_agro_enterprise_routes

    application = web.Application()
    register_agro_enterprise_routes(application)
    register_port_enterprise_routes(application)
    async with TestClient(TestServer(application)) as client:
        assert (await client.get(f"{AGRO}/health")).status == 200
        assert (await client.get(f"{AEC}/health")).status == 200
        assert (await client.get(f"{PREFIX}/health")).status == 200


def test_docs_and_regression_15_0():
    for name in (
        "PORT_ENTERPRISE.md",
        "PORT_OPERATIONS.md",
        "TERMINAL_MANAGEMENT.md",
        "CARGO_MANAGEMENT.md",
        "FLEET_REGISTRY.md",
    ):
        assert (ROOT / "docs" / name).exists()
    assert (ROOT / "knowledge" / "applications" / "PORT_ENTERPRISE.md").exists()
    assert (ROOT / "applications" / "port_enterprise" / "application.py").exists()
    assert (ROOT / "applications" / "port_enterprise" / "manifest.json").exists()

    from applications.ai_os.config import DEFAULT_CONFIG as AIOS
    from applications.enterprise.config import DEFAULT_CONFIG as ENT
    from applications.auto_marketplace.config import DEFAULT_CONFIG as AUTO
    from applications.agro_enterprise.config import DEFAULT_CONFIG as AGRO
    from applications.port_erp.config import DEFAULT_CONFIG as PORT_ERP

    assert AIOS.application_version == "3.4.0-alpha"
    assert ENT.application_version == "4.0.0-enterprise"
    assert AUTO.application_version == "4.2.0-enterprise"
    assert AGRO.application_version == "4.4.0-enterprise"
    assert PORT_ERP.application_version == "2.0.0"
    manifest = (ROOT / "applications" / "port_enterprise" / "manifest.json").read_text()
    assert "4.5.3-enterprise" in manifest
    assert "15.3" in manifest
