"""Tests — Dealer CRM, Trade-In AI & Inventory Intelligence (Sprint 13.3)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.auto_marketplace import auto_marketplace
from applications.auto_marketplace.api.register import register_auto_marketplace_routes
from applications.auto_marketplace.shared.exceptions import ValidationError


ROOT = Path(__file__).resolve().parents[1]
PREFIX = "/api/dealer-crm/v1"
IA = "/api/inspection-ai/v1"
VI = "/api/vin-intelligence/v1"
EA = "/api/auto-marketplace/v1"


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


def test_version_dealer_crm_ready():
    health = auto_marketplace.health()
    assert health["application_version"] == "4.2.0-enterprise"
    assert health["enterprise_foundation"] == "Enterprise Platform v4.1.8-enterprise"
    assert health["dealer_crm_ready"] is True
    assert health["trade_in_ai_ready"] is True
    assert health["inventory_intelligence_ready"] is True
    assert health["sales_ai_ready"] is True


def test_crm_pipeline():
    suite = auto_marketplace.dealer_crm
    boot = suite.bootstrap()
    assert boot["bootstrap"] is True
    dealer = suite.crm.create_dealership(name="City CRM")
    cust = suite.crm.create_customer(name="Pat", dealership_id=dealer["dealership_id"])
    lead = suite.crm.create_lead(name="Pat", interest="Leaf", dealership_id=dealer["dealership_id"], customer_id=cust["customer_id"])
    suite.crm.advance_pipeline(lead["lead_id"], stage="appointment")
    suite.crm.log_contact(channel="call", related_id=lead["lead_id"], summary="Booked visit")
    suite.crm.create_task(title="Prepare paperwork", related_id=lead["lead_id"])
    suite.crm.schedule_appointment(title="Visit", starts_at="2026-07-28T09:00:00Z", customer_id=cust["customer_id"])
    assert suite.crm.pipeline_snapshot()["pipeline"]["appointment"] >= 1


def test_tradein_and_inventory():
    suite = auto_marketplace.dealer_crm
    evaluation = suite.tradein.evaluate(vin="WBA3A5C50EF000001", mileage=60000, damage_score=0.4, market_value=21000)
    assert evaluation["trade_in_offer"] < evaluation["market_value"]
    offer = suite.tradein.generate_offer(evaluation["evaluation_id"], customer_id="c1")
    assert offer["amount"] == evaluation["trade_in_offer"]
    with pytest.raises(ValidationError):
        suite.tradein.evaluate(vin="SHORT")

    inv = suite.inventory.add_vehicle(vin="1HGCM82633A000001", make="Honda", model="Accord", price=17000, status="available")
    suite.inventory.update_status(inv["inventory_id"], status="reserved")
    assert suite.inventory.search_vin("1HGCM82633A000001")[0]["status"] == "reserved"
    opt = suite.inventory.optimize()
    assert opt["suggestions"]
    rec = suite.inventory.recommend(budget=20000, make="Honda")
    assert "recommendation_id" in rec


def test_sales_ai_and_analytics():
    suite = auto_marketplace.dealer_crm
    dealer = suite.crm.create_dealership(name="AI Motors")
    lead = suite.crm.create_lead(name="Sam", source="walk_in", dealership_id=dealer["dealership_id"])
    q = suite.sales_ai.qualify_lead(lead_id=lead["lead_id"], budget=25000, intent="buy")
    assert q["qualified"] is True
    intent = suite.sales_ai.predict_intent(customer_id="c1", signals={"vehicle_views": 6, "messages": 2})
    assert intent["intent"] == "buy"
    neg = suite.sales_ai.negotiate(list_price=20000, customer_offer=18000)
    assert neg["suggested_counter"] > 18000
    fc = suite.sales_ai.forecast(dealership_id=dealer["dealership_id"])
    assert fc["forecast_units"] >= 1
    suite.integrations.connect(target="workflow_studio", endpoint="/api/workflow-studio/v1")
    for dtype in ("sales", "inventory", "trade_in", "profit", "marketing", "ai_insights"):
        assert suite.analytics.render(dashboard_type=dtype)["dashboard_type"] == dtype


@pytest.mark.asyncio
async def test_api_dealer_crm(client):
    health = await client.get(f"{PREFIX}/health")
    body = await health.json()
    assert body["application_version"] == "4.2.0-enterprise"
    assert body["dealer_crm_ready"] is True

    assert (await client.get(f"{IA}/health")).status == 200
    assert (await client.get(f"{VI}/health")).status == 200
    assert (await client.get(f"{EA}/health")).status == 200

    boot = await client.post(f"{PREFIX}/bootstrap", json={})
    assert boot.status == 201
    boot_body = await boot.json()

    lead = await client.post(f"{PREFIX}/crm", json={"name": "API Lead", "dealership_id": boot_body["dealership_id"]})
    assert lead.status == 201

    tradein = await client.post(
        f"{PREFIX}/tradein",
        json={"vin": "JN1TBNT31U0000001", "mileage": 40000, "damage_score": 0.2, "market_value": 14000},
    )
    assert tradein.status == 201

    inv = await client.post(
        f"{PREFIX}/inventory",
        json={"vin": "JN1TBNT31U0000001", "make": "Nissan", "model": "Leaf", "price": 14000, "dealership_id": boot_body["dealership_id"]},
    )
    assert inv.status == 201

    sales = await client.post(
        f"{PREFIX}/sales",
        json={"action": "forecast", "dealership_id": boot_body["dealership_id"]},
    )
    assert sales.status == 201

    analytics = await client.get(f"{PREFIX}/analytics?type=ai_insights")
    assert analytics.status == 200

    integ = await client.post(f"{PREFIX}/integrations", json={"target": "digital_passport"})
    assert integ.status == 201


def test_docs_and_regression_13_3():
    for name in ("DEALER_CRM.md", "TRADE_IN_AI.md", "INVENTORY_AI.md", "SALES_AI.md"):
        assert (ROOT / "docs" / name).exists()
    assert (ROOT / "knowledge" / "applications" / "DEALER_CRM.md").exists()
    assert (ROOT / "applications" / "auto_marketplace" / "dealer_crm" / "facade.py").exists()
    assert (ROOT / "applications" / "auto_marketplace" / "inspection_ai" / "facade.py").exists()
    assert (ROOT / "applications" / "auto_marketplace" / "vin_intelligence" / "facade.py").exists()
    assert (ROOT / "applications" / "auto_marketplace" / "enterprise_automotive" / "facade.py").exists()
    manifest = (ROOT / "applications" / "auto_marketplace" / "manifest.json").read_text()
    assert "4.2.0-enterprise" in manifest
    assert "13.9" in manifest

    from applications.ai_os.config import DEFAULT_CONFIG as AIOS
    from applications.enterprise.config import DEFAULT_CONFIG as ENT

    assert AIOS.application_version == "3.4.0-alpha"
    assert ENT.application_version == "4.0.0-enterprise"
