"""Tests — Port ERP Enterprise, Network & Production Release (Sprint 9.8)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.port_erp import port_erp
from applications.port_erp.api.register import register_port_erp_routes
from applications.port_erp.enterprise.models import (
    ExchangeOffer,
    NetworkPartner,
    NetworkRoute,
    PartnerType,
    RegistryEntry,
    RegistryKind,
    TradeLane,
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


def test_version_enterprise_docs_bridges():
    health = port_erp.health()
    assert health["application_version"] == "2.0.0"
    assert health["enterprise_engine"] == "1.0"
    assert health["global_network"] == "1.0"
    assert "enterprise" in health
    docs_root = Path(__file__).resolve().parents[1] / "docs"
    for name in ("PORT_NETWORK.md", "PORT_ENTERPRISE.md", "PORT_RELEASE.md", "PORT_ERP.md"):
        path = docs_root / name
        assert path.exists()
        assert "2.0.0" in path.read_text(encoding="utf-8")
    assert port_erp.platform.platform_health()["platform_dependency"] == "AI Platform Core v3"
    assert port_erp.ecosystem.ecosystem_health()["ecosystem_dependency"] == "AI Ecosystem v1.5"
    root = Path(__file__).resolve().parents[1] / "applications" / "port_erp"
    for name in (
        "enterprise",
        "integration",
        "network",
        "digital_exchange",
        "global_registry",
        "partners",
        "analytics_global",
        "production",
        "deployment",
        "health",
    ):
        assert (root / name).is_dir()


def test_enterprise_integration_bootstrap():
    result = port_erp.enterprise.enterprise.bootstrap()
    assert "agro_marketplace" in result["matrix"]
    assert "communication_bus" in result["matrix"]
    assert all(status == "connected" for status in result["matrix"].values())
    assert len(port_erp.enterprise.integration.targets()) == 12


def test_partner_network_and_recommendations():
    carrier = port_erp.enterprise.partners.register(
        NetworkPartner(
            name="Ocean Line A",
            partner_type=PartnerType.SHIPPING_LINE,
            region="east-africa",
            capabilities=["deep_sea", "reefer"],
            capacity_teu=5000,
            avg_price=1200,
            reliability_score=0.9,
            risk_score=0.15,
        )
    )
    port_erp.enterprise.partners.register(
        NetworkPartner(
            name="Rail Kenya",
            partner_type=PartnerType.RAILWAY,
            region="east-africa",
            capabilities=["rail"],
            capacity_teu=800,
            risk_score=0.25,
        )
    )
    discovered = port_erp.enterprise.network.discover_partners(
        capability="deep_sea", region="east-africa"
    )
    assert len(discovered) == 1
    assert discovered[0].partner_id == carrier.partner_id

    port_erp.enterprise.network.register_lane(
        TradeLane(
            name="Mombasa-Rotterdam",
            origin_port="Mombasa",
            destination_port="Rotterdam",
            transit_days=22,
        )
    )
    cheap = port_erp.enterprise.network.register_route(
        NetworkRoute(
            name="Direct SEA",
            origin="Mombasa",
            destination="Rotterdam",
            carrier_id=carrier.partner_id,
            price=1100,
            capacity_teu=4000,
            eta_hours=480,
            risk_score=0.2,
        )
    )
    port_erp.enterprise.network.register_route(
        NetworkRoute(
            name="Slow SEA",
            origin="Mombasa",
            destination="Rotterdam",
            carrier_id=carrier.partner_id,
            price=900,
            capacity_teu=2000,
            eta_hours=600,
            risk_score=0.35,
        )
    )
    recs = port_erp.enterprise.network.recommend_carriers(
        origin="Mombasa", destination="Rotterdam"
    )
    assert len(recs) == 2
    prices = port_erp.enterprise.network.compare_prices(
        origin="Mombasa", destination="Rotterdam"
    )
    assert prices[0]["price"] == 900
    eta = port_erp.enterprise.network.optimize_eta(origin="Mombasa", destination="Rotterdam")
    assert eta["best_route"]["route_id"] == cheap.route_id
    risk = port_erp.enterprise.network.analyze_risk(origin="Mombasa", destination="Rotterdam")
    assert risk["level"] in ("low", "medium", "high")
    trade = port_erp.enterprise.network.trade_recommendations(region="Mombasa")
    assert trade and trade[0]["available_routes"] == 2


def test_global_registry_exchange_and_dashboard():
    port_erp.enterprise.registry.register(
        RegistryEntry(kind=RegistryKind.PORT, name="Port of Mombasa", region="KE")
    )
    port_erp.enterprise.registry.register(
        RegistryEntry(kind=RegistryKind.TERMINAL, name="CT1", region="KE")
    )
    summary = port_erp.enterprise.registry.summary()
    assert summary["ports"] == 1
    assert summary["terminals"] == 1

    partner = port_erp.enterprise.partners.register(
        NetworkPartner(name="WH Partner", partner_type=PartnerType.WAREHOUSE)
    )
    offer = port_erp.enterprise.exchange.publish(
        ExchangeOffer(
            partner_id=partner.partner_id,
            origin="Mombasa",
            destination="Nairobi",
            capacity_teu=100,
            price=250,
        )
    )
    matched = port_erp.enterprise.exchange.match(
        origin="Mombasa", destination="Nairobi", min_capacity=50
    )
    assert matched[0].offer_id == offer.offer_id

    report = port_erp.enterprise.analytics.executive_report()
    assert "global" in report and "financial" in report and "risk" in report
    assert report["global"]["partners"] >= 1


def test_production_validation_and_release():
    ready = port_erp.enterprise.production.readiness()
    assert ready["application_version"] == "2.0.0"
    assert ready["ready"] is True
    assert ready["blockers"] == []
    bench = port_erp.enterprise.production.performance_benchmark()
    assert bench["passed"] is True
    report = port_erp.enterprise.production.verify_release()
    assert report.ready is True
    assert report.application_version == "2.0.0"
    profiles = port_erp.enterprise.deployment.list_profiles()
    assert profiles and profiles[0].environment == "production"


@pytest.mark.asyncio
async def test_rest_enterprise_network_production(client: TestClient):
    resp = await client.get("/api/port/v1/enterprise")
    assert resp.status == 200
    body = await resp.json()
    assert body["application_version"] == "2.0.0"
    assert body["enterprise_engine"] == "1.0"

    boot = await client.post("/api/port/v1/enterprise/bootstrap")
    assert boot.status == 201

    partner = await client.post(
        "/api/port/v1/network/partners",
        json={
            "name": "Terminal Ops Co",
            "partner_type": "terminal_operators",
            "region": "global",
            "capabilities": ["handling"],
        },
    )
    assert partner.status == 201
    partner_body = await partner.json()

    route = await client.post(
        "/api/port/v1/network/routes",
        json={
            "name": "Lane A",
            "origin": "A",
            "destination": "B",
            "carrier_id": partner_body["partner_id"],
            "price": 500,
            "capacity_teu": 1000,
            "eta_hours": 72,
        },
    )
    assert route.status == 201

    compare = await client.post(
        "/api/port/v1/network/compare",
        json={"origin": "A", "destination": "B"},
    )
    assert compare.status == 200
    compare_body = await compare.json()
    assert compare_body["prices"]

    registry = await client.post(
        "/api/port/v1/global/registry",
        json={"kind": "companies", "name": "Global Port Co", "region": "AF"},
    )
    assert registry.status == 201

    dash = await client.get("/api/port/v1/global/dashboard")
    assert dash.status == 200

    prod = await client.get("/api/port/v1/production/readiness")
    assert prod.status == 200
    prod_body = await prod.json()
    assert prod_body["ready"] is True

    verify = await client.post("/api/port/v1/production/verify")
    assert verify.status == 201
    verify_body = await verify.json()
    assert verify_body["ready"] is True
    assert verify_body["application_version"] == "2.0.0"


def test_platform_core_untouched_paths():
    root = Path(__file__).resolve().parents[1]
    # Sprint 9.8 must not create or require edits under platform / ecosystem packages.
    assert (root / "applications" / "port_erp" / "enterprise").is_dir()
    assert not (root / "ecosystem" / "port_erp").exists()
