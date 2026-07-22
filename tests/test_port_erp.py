"""Tests — Port ERP Foundation (Sprint 9.1)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.port_erp import port_erp
from applications.port_erp.api.register import register_port_erp_routes
from applications.port_erp.shared.models import (
    Berth,
    Cargo,
    Container,
    Customer,
    Gate,
    Port,
    PortRole,
    ShippingLine,
    Terminal,
    Vessel,
    Voyage,
)


@pytest.fixture
def app() -> web.Application:
    application = web.Application()
    register_port_erp_routes(application)
    return application


@pytest.fixture
async def client(app: web.Application):
    async with TestClient(TestServer(app)) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def reset_store():
    port_erp.reset()
    yield
    port_erp.reset()


def test_version_and_roles():
    health = port_erp.health()
    assert health["application_name"] == "Port ERP"
    assert health["application_version"] == "1.6.0-alpha"
    assert health["tracking_engine"] == "1.0"
    assert health["terminal_engine"] == "1.0"
    assert health["platform_dependency"] == "AI Platform Core v3"
    assert health["ecosystem_dependency"] == "AI Ecosystem v1.5"
    roles = set(port_erp.permissions.roles())
    assert PortRole.PORT_DIRECTOR.value in roles
    assert PortRole.AI_EXECUTIVE.value in roles
    assert len(roles) == 12


def test_bridges_only_and_docs():
    assert port_erp.platform.platform_health()["platform_dependency"] == "AI Platform Core v3"
    assert port_erp.ecosystem.ecosystem_health()["ecosystem_dependency"] == "AI Ecosystem v1.5"
    docs = Path(__file__).resolve().parents[1] / "docs" / "PORT_ERP.md"
    assert docs.exists()
    # Ensure we did not invent platform/ecosystem mutation packages inside port_erp
    integrations = Path(__file__).resolve().parents[1] / "applications" / "port_erp" / "integrations"
    assert (integrations / "platform_bridge.py").exists()
    assert (integrations / "ecosystem_bridge.py").exists()


@pytest.mark.asyncio
async def test_port_terminal_berth_vessel_flow():
    port = port_erp.core.ports.register(Port(name="Mombasa", code="KEMBA", country="KE", city="Mombasa"))
    terminal = port_erp.core.terminals.register(
        Terminal(port_id=port.port_id, name="CT1", capacity_teu=40000)
    )
    berth = port_erp.core.berths.register(
        Berth(terminal_id=terminal.terminal_id, name="B1", length_m=300, max_draft_m=14)
    )
    line = port_erp.core.companies.register_shipping_line(ShippingLine(name="OceanLine", scac="OCLN"))
    vessel = port_erp.core.vessels.register(
        Vessel(name="Pacific Star", imo="9123456", shipping_line_id=line.shipping_line_id)
    )
    voyage = port_erp.core.vessels.create_voyage(
        Voyage(
            vessel_id=vessel.vessel_id,
            voyage_number="PS001E",
            origin_port_id=port.port_id,
            destination_port_id=port.port_id,
        )
    )
    arrived = await port_erp.core.vessels.arrive(voyage.voyage_id, port_id=port.port_id)
    assert arrived.status == "arrived"
    assigned = await port_erp.core.berths.assign(
        berth.berth_id, vessel_id=vessel.vessel_id, voyage_id=voyage.voyage_id
    )
    assert assigned.status == "occupied"

    container = port_erp.core.containers.register(
        Container(container_number="MSCU1234567", terminal_id=terminal.terminal_id)
    )
    received = await port_erp.core.containers.receive(container.container_id, terminal_id=terminal.terminal_id)
    assert received.status.value == "at_port"

    customer = port_erp.core.customers.register(Customer(name="Agri Export Ltd", country="KE"))
    cargo = port_erp.core.cargo.register(
        Cargo(
            description="Maize",
            container_id=container.container_id,
            customer_id=customer.customer_id,
            weight_tons=20,
        )
    )
    loaded = await port_erp.core.cargo.load(cargo.cargo_id)
    assert loaded.status == "loaded"

    gate = port_erp.core.operations.register_gate(
        Gate(port_id=port.port_id, terminal_id=terminal.terminal_id, name="Gate A")
    )
    opened = await port_erp.core.operations.open_gate(gate.gate_id)
    assert opened.status.value == "open"
    departed = await port_erp.core.vessels.depart(voyage.voyage_id, port_id=port.port_id)
    assert departed.status == "departed"


@pytest.mark.asyncio
async def test_rest_api_foundation(client: TestClient):
    health = await client.get("/api/port/v1/health")
    assert health.status == 200
    body = await health.json()
    assert body["application_version"] == "1.6.0-alpha"
    assert body["application_name"] == "Port ERP"

    roles = await client.get("/api/port/v1/roles")
    assert roles.status == 200
    assert len((await roles.json())["items"]) == 12

    port_resp = await client.post(
        "/api/port/v1/ports",
        json={"name": "Rotterdam", "code": "NLRTM", "country": "NL", "city": "Rotterdam"},
    )
    assert port_resp.status == 201
    port = await port_resp.json()

    term_resp = await client.post(
        "/api/port/v1/terminals",
        json={"port_id": port["port_id"], "name": "ECT", "capacity_teu": 100000},
    )
    assert term_resp.status == 201

    cust = await client.post("/api/port/v1/customers", json={"name": "Euro Trade", "country": "NL"})
    assert cust.status == 201

    cont = await client.post(
        "/api/port/v1/containers",
        json={"container_number": "TGHU9876543", "container_type": "40HC"},
    )
    assert cont.status == 201

    companies = await client.get("/api/port/v1/companies")
    assert companies.status == 200

    ops = await client.get("/api/port/v1/operations")
    assert ops.status == 200
