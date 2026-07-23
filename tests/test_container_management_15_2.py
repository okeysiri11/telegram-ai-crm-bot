"""Tests — Container Management, Yard & Equipment (Sprint 15.2)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.port_enterprise import port_enterprise
from applications.port_enterprise.api.register import register_port_enterprise_routes
from applications.port_enterprise.shared.exceptions import ValidationError


ROOT = Path(__file__).resolve().parents[1]
PREFIX = "/api/port-containers/v1"
NAV = "/api/port-navigation/v1"
PE = "/api/port-enterprise/v1"


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


def test_version_container_ready():
    health = port_enterprise.health()
    assert health["application_version"] == "4.5.6-enterprise"
    assert health["enterprise_foundation"] == "Enterprise Platform v4.5.5-enterprise"
    assert health["container_platform_ready"] is True
    assert health["yard_automation_ready"] is True
    assert health["port_equipment_ready"] is True
    assert health["digital_twin_ready"] is True
    assert health["terminal_automation_ready"] is True


def test_container_yard_equipment():
    suite = port_enterprise.container_management
    ctr = suite.containers.register(container_number="TESTU1234567", iso_type="20GP")
    suite.operations.gate_in(ctr["container_id"])
    yard = suite.yard.register_yard(name="Y1", capacity_teu=100)
    block = suite.yard.create_block(yard_id=yard["yard_id"], name="B1")
    slot = suite.yard.allocate_slot(
        block_id=block["block_id"], row=1, bay=1, tier=1, container_id=ctr["container_id"]
    )
    assert "position" in slot
    eq = suite.equipment.register(name="STS-X", equipment_type="sts", yard_id=yard["yard_id"])
    suite.equipment.health(eq["equipment_id"], health_score=50)
    with pytest.raises(ValidationError):
        suite.containers.register(container_number="X", iso_type="99XX")


def test_automation_and_twin():
    suite = port_enterprise.container_management
    boot = suite.bootstrap()
    assert boot["twin_id"] and boot["task_id"]
    twin = suite.twin.simulate(boot["twin_id"], hours=12)
    assert twin["projected_moves"] > 0
    with pytest.raises(ValidationError):
        suite.equipment.register(name="Bad", equipment_type="drone")
    for dtype in ("container", "yard", "equipment", "automation", "digital_twin"):
        assert suite.dashboard.render(dashboard_type=dtype)["dashboard_type"] == dtype


@pytest.mark.asyncio
async def test_api_containers(client):
    health = await client.get(f"{PREFIX}/health")
    body = await health.json()
    assert body["application_version"] == "4.5.6-enterprise"
    assert body["container_platform_ready"] is True
    assert body["digital_twin_ready"] is True

    assert (await client.get(f"{NAV}/health")).status == 200
    assert (await client.get(f"{PE}/health")).status == 200

    boot = await client.post(f"{PREFIX}/bootstrap", json={})
    assert boot.status == 201
    boot_body = await boot.json()

    ops = await client.post(
        f"{PREFIX}/operations",
        json={"action": "reserve", "container_id": boot_body["container_id"], "party": "Agent"},
    )
    assert ops.status == 201

    twin = await client.post(
        f"{PREFIX}/twin",
        json={"action": "forecast", "twin_id": boot_body["twin_id"], "days": 3},
    )
    assert twin.status == 201

    dash = await client.get(f"{PREFIX}/dashboard?type=yard")
    assert dash.status == 200


def test_docs_and_regression_15_2():
    for name in (
        "CONTAINER_MANAGEMENT.md",
        "YARD_AUTOMATION.md",
        "PORT_EQUIPMENT.md",
        "DIGITAL_TWIN.md",
        "TERMINAL_AUTOMATION.md",
    ):
        assert (ROOT / "docs" / name).exists()
    assert (ROOT / "knowledge" / "applications" / "PORT_CONTAINERS.md").exists()
    assert (ROOT / "applications" / "port_enterprise" / "container_management" / "facade.py").exists()
    assert (ROOT / "applications" / "port_enterprise" / "navigation" / "facade.py").exists()

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
    assert "4.5.6-enterprise" in manifest
    assert "15.6" in manifest
