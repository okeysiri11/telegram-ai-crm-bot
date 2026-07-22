"""Tests — Buyer AI, Negotiation & Ownership (Sprint 13.4)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.auto_marketplace import auto_marketplace
from applications.auto_marketplace.api.register import register_auto_marketplace_routes
from applications.auto_marketplace.shared.exceptions import ValidationError


ROOT = Path(__file__).resolve().parents[1]
PREFIX = "/api/buyer-ai/v1"
DC = "/api/dealer-crm/v1"
IA = "/api/inspection-ai/v1"
VI = "/api/vin-intelligence/v1"


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


def test_version_buyer_ai_ready():
    health = auto_marketplace.health()
    assert health["application_version"] == "4.1.7-enterprise"
    assert health["enterprise_foundation"] == "Enterprise Platform v4.1.6-enterprise"
    assert health["buyer_ai_ready"] is True
    assert health["negotiation_ai_ready"] is True
    assert health["ownership_assistant_ready"] is True
    assert health["purchase_intelligence_ready"] is True


def test_buyer_profile_and_search():
    suite = auto_marketplace.buyer_ai
    boot = suite.bootstrap()
    assert boot["bootstrap"] is True
    buyer = suite.profile.create(name="Pat", budget_max=20000, preferred_brands=["Nissan"], ev_preference=False)
    suite.profile.update_budget(buyer["buyer_id"], budget_max=22000)
    listing = suite.search.index_listing(
        vin="JN1TBNT31U0000001",
        make="Nissan",
        model="Leaf",
        price=14000,
        fuel="electric",
        dealer="EV Hub",
    )
    results = suite.search.natural_language_search(query="Nissan Leaf under 15000", buyer_id=buyer["buyer_id"])
    assert results["count"] >= 1
    recs = suite.search.recommend(buyer_id=buyer["buyer_id"])
    assert "recommendations" in recs
    cmp = suite.search.compare(listing_ids=[boot["listing_id"], listing["listing_id"]])
    assert cmp["price_range"]["min"] <= cmp["price_range"]["max"]


def test_negotiation_and_purchase():
    suite = auto_marketplace.buyer_ai
    buyer = suite.profile.create(name="Sam", budget_max=30000)
    listing = suite.search.index_listing(vin="WBA3A5C50EF000001", make="BMW", model="320i", price=21000, dealer="Bavaria")
    neg = suite.negotiation.start(buyer_id=buyer["buyer_id"], listing_id=listing["listing_id"])
    offer = suite.negotiation.generate_offer(neg["negotiation_id"], strategy="aggressive")
    assert offer["amount"] < 21000
    counter = suite.negotiation.generate_counter(neg["negotiation_id"], seller_offer=20500)
    assert counter["amount"] > offer["amount"]
    strategy = suite.negotiation.strategy(neg["negotiation_id"])
    assert strategy["dealer_discount_prediction"] >= 0
    intel = suite.purchase.analyze(price=21000, mileage=60000, fuel="gasoline", years=4)
    assert intel["total_ownership_cost"] > 21000
    assert intel["loan"]["monthly_payment"] > 0
    protection = suite.protection.assess(vin="WBA3A5C50EF000001", listing_price=21000)
    assert protection["vin_verified"] is True
    with pytest.raises(ValidationError):
        suite.protection.assess(vin="SHORT")


def test_ownership_and_assistant():
    suite = auto_marketplace.buyer_ai
    buyer = suite.profile.create(name="Owner")
    ownership = suite.ownership.create_plan(buyer_id=buyer["buyer_id"], vin="1HGCM82633A000001")
    rem = suite.ownership.add_reminder(ownership["ownership_id"], title="Inspection", due_at="2026-10-01T00:00:00Z")
    assert rem["status"] == "scheduled"
    doc = suite.ownership.store_document(ownership["ownership_id"], name="title.pdf", doc_type="title")
    assert doc["doc_id"]
    reply = suite.assistant.ask(mode="maintenance", message="When is the next service?", buyer_id=buyer["buyer_id"])
    assert reply["reply"]
    for dtype in ("buyer", "purchase", "ownership", "savings"):
        assert suite.dashboard.render(dashboard_type=dtype)["dashboard_type"] == dtype


@pytest.mark.asyncio
async def test_api_buyer_ai(client):
    health = await client.get(f"{PREFIX}/health")
    body = await health.json()
    assert body["application_version"] == "4.1.7-enterprise"
    assert body["buyer_ai_ready"] is True

    assert (await client.get(f"{DC}/health")).status == 200
    assert (await client.get(f"{IA}/health")).status == 200
    assert (await client.get(f"{VI}/health")).status == 200

    boot = await client.post(f"{PREFIX}/bootstrap", json={})
    assert boot.status == 201
    boot_body = await boot.json()

    search = await client.post(
        f"{PREFIX}/search",
        json={"query": "Golf under 20000", "buyer_id": boot_body["buyer_id"]},
    )
    assert search.status == 201

    offer = await client.post(
        f"{PREFIX}/negotiation",
        json={"action": "offer", "negotiation_id": boot_body["negotiation_id"], "strategy": "fair"},
    )
    assert offer.status == 201

    purchase = await client.post(f"{PREFIX}/purchase", json={"price": 18500, "mileage": 45000})
    assert purchase.status == 201

    protection = await client.post(
        f"{PREFIX}/protection",
        json={"vin": "WVWZZZ1JZXW000001", "listing_price": 18500},
    )
    assert protection.status == 201

    ownership = await client.post(
        f"{PREFIX}/ownership",
        json={"action": "reminder", "ownership_id": boot_body["ownership_id"], "title": "Tires", "due_at": "2026-11-01T00:00:00Z"},
    )
    assert ownership.status == 201

    assistant = await client.post(
        f"{PREFIX}/assistant",
        json={"mode": "chat", "message": "Help me decide", "buyer_id": boot_body["buyer_id"]},
    )
    assert assistant.status == 201

    dash = await client.get(f"{PREFIX}/dashboard?type=savings")
    assert dash.status == 200


def test_docs_and_regression_13_4():
    for name in ("BUYER_AI.md", "NEGOTIATION_AI.md", "OWNERSHIP_ASSISTANT.md", "PURCHASE_INTELLIGENCE.md"):
        assert (ROOT / "docs" / name).exists()
    assert (ROOT / "knowledge" / "applications" / "BUYER_AI.md").exists()
    assert (ROOT / "applications" / "auto_marketplace" / "buyer_ai" / "facade.py").exists()
    assert (ROOT / "applications" / "auto_marketplace" / "dealer_crm" / "facade.py").exists()
    assert (ROOT / "applications" / "auto_marketplace" / "inspection_ai" / "facade.py").exists()
    assert (ROOT / "applications" / "auto_marketplace" / "vin_intelligence" / "facade.py").exists()
    assert (ROOT / "applications" / "auto_marketplace" / "enterprise_automotive" / "facade.py").exists()
    manifest = (ROOT / "applications" / "auto_marketplace" / "manifest.json").read_text()
    assert "4.1.7-enterprise" in manifest
    assert "13.7" in manifest

    from applications.ai_os.config import DEFAULT_CONFIG as AIOS
    from applications.enterprise.config import DEFAULT_CONFIG as ENT

    assert AIOS.application_version == "3.4.0-alpha"
    assert ENT.application_version == "4.0.0-enterprise"
