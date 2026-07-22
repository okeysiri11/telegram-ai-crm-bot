"""Tests — Auto Marketplace Enterprise & Commercial Release (Sprint 10.8)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.auto_marketplace import auto_marketplace
from applications.auto_marketplace.api.register import register_auto_marketplace_routes
from applications.auto_marketplace.enterprise.models import (
    ConnectorKind,
    EnterpriseConnector,
    ExchangeOffer,
    NetworkListing,
    NetworkPartner,
    PartnerKind,
)


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


def test_version_modules_docs_bridges():
    health = auto_marketplace.health()
    assert health["application_version"] == "4.1.1-enterprise"
    assert health["enterprise_engine"] == "1.0"
    assert health["global_network"] == "1.0"
    assert health["production_ready"] is True
    assert "enterprise" in health
    root = Path(__file__).resolve().parents[1]
    for doc in ("AUTO_ENTERPRISE.md", "AUTO_RELEASE.md", "AUTO_MARKETPLACE.md"):
        text = (root / "docs" / doc).read_text(encoding="utf-8")
        assert "4.1.1-enterprise" in text
    assert auto_marketplace.platform.platform_health()["platform_dependency"] == "AI Platform Core v3"
    app_root = root / "applications" / "auto_marketplace"
    for name in (
        "enterprise",
        "integrations",
        "production",
        "deployment",
        "release",
        "health",
        "monitoring",
        "analytics_global",
        "network",
        "partner_registry",
        "digital_exchange",
    ):
        assert (app_root / name).is_dir()


def test_enterprise_connectors_and_cross_platform():
    items = auto_marketplace.enterprise.connectors.bootstrap_defaults()
    assert len(items) >= 9
    ping = auto_marketplace.enterprise.connectors.ping(items[0].connector_id)
    assert ping["status"] == "healthy"
    custom = auto_marketplace.enterprise.connectors.register(
        EnterpriseConnector(name="Custom ERP", kind=ConnectorKind.ERP, endpoint="/x")
    )
    assert custom.name == "Custom ERP"
    link = auto_marketplace.enterprise.cross_platform.link(target="agro_marketplace")
    assert "identity" in link.shared
    status = auto_marketplace.enterprise.cross_platform.status()
    assert "agro" in status and "port_erp" in status


def test_network_and_partners():
    partner = auto_marketplace.enterprise.partners.register(
        NetworkPartner(name="Euro Dealer", kind=PartnerKind.DEALER, country="DE", region="EU", rating=4.5)
    )
    listing = auto_marketplace.enterprise.network.publish(
        NetworkListing(vehicle_id="v1", country="DE", region="EU", dealer_id=partner.partner_id, price=22000)
    )
    assert auto_marketplace.enterprise.network.search(country="DE")
    federated = auto_marketplace.enterprise.network.federate_dealer(
        partner.partner_id,
        [NetworkListing(vehicle_id="v2", vin="JTDBR32E720123456", country="FR", region="EU", price=18000)],
    )
    assert federated[0].federated
    offer = auto_marketplace.enterprise.exchange.create_offer(
        ExchangeOffer(from_partner_id=partner.partner_id, vehicle_id="v1", price=21000)
    )
    accepted = auto_marketplace.enterprise.exchange.accept(offer.offer_id)
    assert accepted.status == "accepted"


def test_production_validation_and_release():
    report = auto_marketplace.enterprise.production.generate_report()
    assert report.application_version == "4.1.1-enterprise"
    assert report.production_ready is True
    assert report.certified is True
    assert report.migration_ok is True
    failed = [c for c in report.checks if c.status.value == "fail"]
    assert not failed, failed
    cert = auto_marketplace.enterprise.release.certify()
    assert cert["certified"] is True
    pre = auto_marketplace.enterprise.deployment.preflight(version="4.1.1-enterprise")
    assert pre["ok"] is True
    deep = auto_marketplace.enterprise.health.deep()
    assert deep["production_ready"] is True
    assert deep["dependencies"]["untouched"]["platform_core"] is True


@pytest.mark.asyncio
async def test_enterprise_api_routes(client: TestClient):
    health = await client.get("/api/auto/v1/health")
    body = await health.json()
    assert body["application_version"] == "4.1.1-enterprise"
    assert body["production_ready"] is True

    deep = await client.get("/api/auto/v1/health/deep")
    assert deep.status == 200

    connectors = await client.post("/api/auto/v1/enterprise/connectors", json={"bootstrap": True})
    assert connectors.status == 201

    partner = await client.post(
        "/api/auto/v1/partners",
        json={"name": "API Partner", "kind": "transport", "country": "NL"},
    )
    assert partner.status == 201

    listing = await client.post(
        "/api/auto/v1/network/listings",
        json={"vehicle_id": "v9", "country": "NL", "price": 15000},
    )
    assert listing.status == 201

    validate = await client.post("/api/auto/v1/production/validate")
    assert validate.status == 200
    report = await validate.json()
    assert report["production_ready"] is True


def test_platform_agro_port_untouched():
    root = Path(__file__).resolve().parents[1]
    # Bridges exist inside auto_marketplace only
    assert (root / "applications" / "auto_marketplace" / "integrations" / "agro_bridge.py").exists()
    assert (root / "applications" / "auto_marketplace" / "integrations" / "port_bridge.py").exists()
    assert not (root / "platform_ai" / "enterprise").exists()
    # Sprint 10.8 must not create enterprise packages under agro/port
    assert not (root / "applications" / "agro_marketplace" / "enterprise_auto_bridge.py").exists()
    assert not (root / "applications" / "port_erp" / "auto_marketplace_bridge.py").exists()
