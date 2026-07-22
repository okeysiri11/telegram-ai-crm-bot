"""Tests — Auto Marketplace Enterprise Platform (Sprint 13.0)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.auto_marketplace import auto_marketplace
from applications.auto_marketplace.api.register import register_auto_marketplace_routes
from applications.auto_marketplace.shared.exceptions import ValidationError


ROOT = Path(__file__).resolve().parents[1]
PREFIX = "/api/auto-marketplace/v1"
LEGACY = "/api/auto/v1"


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


def test_version_auto_marketplace_ready():
    health = auto_marketplace.health()
    assert health["application_version"] == "4.1.5-enterprise"
    assert health["enterprise_foundation"] == "Enterprise Platform v4.1.4-enterprise"
    assert health["auto_marketplace_ready"] is True
    assert health["auto_ai_ready"] is True
    assert health["dealer_platform_ready"] is True
    assert health["enterprise_automotive_suite_ready"] is True


def test_marketplace_core_and_vehicle_types():
    suite = auto_marketplace.enterprise_automotive
    boot = suite.bootstrap()
    assert boot["bootstrap"] is True
    assert boot["dealer_id"]

    dealer = suite.marketplace.register_dealer(name="City Auto")
    for vtype in ("motorcycle", "truck", "hybrid", "commercial"):
        veh = suite.marketplace.register_vehicle(
            vin=f"TESTVIN{vtype.upper()}01XX",
            vehicle_type=vtype,
            make="Brand",
            model=vtype,
            year=2022,
            price=12000,
            dealer_id=dealer["dealer_id"],
        )
        assert veh["vehicle_type"] == vtype
    assert suite.marketplace.list_vehicles("truck")
    auction = suite.marketplace.create_auction(vehicle_id=boot["vehicle_ids"][0], reserve_price=15000)
    bid = suite.sales.place_bid(auction_id=auction["auction_id"], bidder_id="cust_x", amount=15100)
    assert bid["bids"] == 1


def test_crm_and_sales():
    suite = auto_marketplace.enterprise_automotive
    dealer = suite.marketplace.register_dealer(name="CRM Motors")
    cust = suite.marketplace.register_customer(name="Pat", email="pat@example.com")
    veh = suite.marketplace.register_vehicle(
        vin="JN1TBNT31U0000001",
        vehicle_type="car",
        make="Nissan",
        model="Leaf",
        year=2019,
        price=14000,
        dealer_id=dealer["dealer_id"],
    )
    lead = suite.crm.create_lead(name="Pat", interest="Leaf", source="whatsapp", dealer_id=dealer["dealer_id"])
    suite.crm.advance_funnel(lead["lead_id"], stage="negotiation")
    suite.crm.notify(recipient=cust["customer_id"], title="Offer", body="Reserved price")
    suite.crm.schedule_followup(lead_id=lead["lead_id"], due_at="2026-07-30T12:00:00Z")
    assert suite.crm.funnel_snapshot()["funnel"]["negotiation"] == 1

    for action in ("buy", "contract", "payment", "delivery"):
        sale = suite.sales.create(
            action=action,
            vehicle_id=veh["vehicle_id"],
            customer_id=cust["customer_id"],
            dealer_id=dealer["dealer_id"],
            amount=14000 if action == "buy" else 100,
        )
        assert sale["action"] == action


def test_ai_analytics_integrations_dashboard():
    suite = auto_marketplace.enterprise_automotive
    dealer = suite.marketplace.register_dealer(name="AI Garage")
    veh = suite.marketplace.register_vehicle(
        vin="WBA3A5C50EF000001",
        vehicle_type="car",
        make="BMW",
        model="320i",
        year=2018,
        price=21000,
        dealer_id=dealer["dealer_id"],
    )
    assert suite.ai.decode_vin(veh["vin"])["decoded"] is True
    assert suite.ai.estimate_price(vehicle_id=veh["vehicle_id"], mileage=60000)["estimate"] > 0
    assert suite.ai.predict_damage(vehicle_id=veh["vehicle_id"], signals={"impact_score": 0.8})["risk"] == "high"
    fraud = suite.ai.detect_fraud(vehicle_id=veh["vehicle_id"], vin=veh["vin"], listing_price=500)
    assert fraud["fraudulent"] is True
    assert suite.ai.predict_maintenance(vehicle_id=veh["vehicle_id"], mileage=85000)["due"]
    assert suite.ai.vehicle_history(vin=veh["vin"])["title_clean"] is True
    assert suite.ai.purchase_advisor(budget=25000, vehicle_type="car")["recommendations"]
    with pytest.raises(ValidationError):
        suite.ai.run(capability="telepathy")

    for rt in ("market", "price", "sales", "inventory", "demand_forecast", "profit"):
        assert suite.analytics.generate(report_type=rt)["report_type"] == rt

    suite.integrations.connect(channel="whatsapp", endpoint="wa://bot")
    suite.integrations.dispatch(channel="email", payload={"to": "a@b.c", "subject": "Quote"})
    assert suite.integrations.list_connections()

    for dtype in ("dealer", "sales", "inventory", "financial", "ai_insights"):
        board = suite.dashboard.render(dashboard_type=dtype, dealer_id=dealer["dealer_id"])
        assert board["dashboard_type"] == dtype


@pytest.mark.asyncio
async def test_api_auto_marketplace(client):
    health = await client.get(f"{PREFIX}/health")
    body = await health.json()
    assert body["application_version"] == "4.1.5-enterprise"
    assert body["auto_marketplace_ready"] is True

    legacy = await client.get(f"{LEGACY}/health")
    assert legacy.status == 200
    legacy_body = await legacy.json()
    assert legacy_body["application_version"] == "4.1.5-enterprise"

    boot = await client.post(f"{PREFIX}/bootstrap", json={})
    assert boot.status == 201

    dealer = await client.post(f"{PREFIX}/marketplace", json={"action": "dealer", "name": "API Motors"})
    assert dealer.status == 201
    dealer_body = await dealer.json()

    veh = await client.post(
        f"{PREFIX}/marketplace",
        json={
            "vin": "1HGCM82633A000001",
            "vehicle_type": "car",
            "make": "Honda",
            "model": "Accord",
            "year": 2020,
            "price": 17000,
            "dealer_id": dealer_body["dealer_id"],
        },
    )
    assert veh.status == 201
    veh_body = await veh.json()

    ai = await client.post(f"{PREFIX}/ai", json={"capability": "market_price", "vehicle_id": veh_body["vehicle_id"], "mileage": 30000})
    assert ai.status == 201

    crm = await client.post(f"{PREFIX}/crm", json={"name": "API Lead", "interest": "Accord"})
    assert crm.status == 201

    sales = await client.post(
        f"{PREFIX}/sales",
        json={"action": "reservation", "vehicle_id": veh_body["vehicle_id"], "dealer_id": dealer_body["dealer_id"], "amount": 200},
    )
    assert sales.status == 201

    analytics = await client.post(f"{PREFIX}/analytics", json={"report_type": "sales", "title": "API Sales"})
    assert analytics.status == 201

    integ = await client.post(f"{PREFIX}/integrations", json={"channel": "gps", "endpoint": "gps://fleet"})
    assert integ.status == 201

    dash = await client.get(f"{PREFIX}/dashboard?type=ai_insights")
    assert dash.status == 200


def test_docs_and_regression_13_0():
    for name in ("AUTO_MARKETPLACE.md", "AUTO_AI.md", "AUTO_CRM.md", "AUTO_ANALYTICS.md"):
        assert (ROOT / "docs" / name).exists()
    assert (ROOT / "knowledge" / "applications" / "AUTO_MARKETPLACE.md").exists()
    manifest = (ROOT / "applications" / "auto_marketplace" / "manifest.json").read_text()
    assert "4.1.5-enterprise" in manifest
    assert "13.5" in manifest
    assert (ROOT / "applications" / "auto_marketplace" / "enterprise_automotive" / "facade.py").exists()

    from applications.ai_os.config import DEFAULT_CONFIG as AIOS
    from applications.enterprise.config import DEFAULT_CONFIG as ENT

    assert AIOS.application_version == "3.4.0-alpha"
    assert ENT.application_version == "4.0.0-enterprise"
    assert AIOS.api_prefix == "/api/ai-os/v1"
    assert ENT.api_prefix == "/api/enterprise/v1"
