"""Tests — Agro CRM, Marketplace & Trading (Sprint 8.3)."""

from __future__ import annotations

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.agro_marketplace import agro_marketplace
from applications.agro_marketplace.api.register import register_agro_marketplace_routes
from applications.agro_marketplace.marketplace.models import (
    AgriculturalLead,
    BuyerProfile,
    CRMContactEntry,
    CRMTask,
    FarmerProfile,
    MarketplaceDeal,
    MarketplaceOrder,
    PriceRequest,
    PurchaseRequest,
    SalesOffer,
    SupplierProfile,
)


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


@pytest.mark.asyncio
async def test_crm_profiles_leads_tasks():
    farmer = await agro_marketplace.crm_engine.register_farmer(
        FarmerProfile(name="Ada Farms", email="ada@farm.test", region="Rift", crops=["maize"])
    )
    buyer = await agro_marketplace.crm_engine.register_buyer(
        BuyerProfile(
            name="Mill Co",
            email="mill@buy.test",
            preferred_crops=["maize"],
            budget_max=100000,
        )
    )
    supplier = agro_marketplace.crm_engine.register_supplier(
        SupplierProfile(name="Seed Co", email="seed@sup.test", products=["maize", "fertilizer"])
    )
    assert farmer.email and buyer.buyer_id and supplier.supplier_id

    lead = await agro_marketplace.crm_engine.create_lead(
        AgriculturalLead(
            name="Export Lead",
            email="lead@ex.test",
            role="exporter",
            crop_interest="maize",
            region="Rift",
            source="rfq",
        )
    )
    assert lead.score > 0
    assigned = await agro_marketplace.crm_engine.assign_lead(lead.lead_id, "agent-1")
    assert assigned.status.value == "assigned"
    qualified = agro_marketplace.crm_engine.qualify_lead(lead.lead_id)
    assert qualified.status.value == "qualified"

    agro_marketplace.crm_engine.add_contact(
        CRMContactEntry(profile_id=buyer.profile_id, subject="Intro", body="Hello")
    )
    assert agro_marketplace.crm_engine.timeline(buyer.profile_id)
    task = agro_marketplace.crm_engine.create_task(
        CRMTask(title="Follow up", related_id=lead.lead_id, assignee_id="agent-1")
    )
    assert task.task_id


@pytest.mark.asyncio
async def test_marketplace_match_negotiate_order_contract_trade():
    farmer = await agro_marketplace.crm_engine.register_farmer(
        FarmerProfile(name="Farmer", email="f@test.com", crops=["wheat"])
    )
    buyer = await agro_marketplace.crm_engine.register_buyer(
        BuyerProfile(name="Buyer", email="b@test.com", preferred_crops=["wheat"], budget_max=50000)
    )
    offer = await agro_marketplace.offers.publish(
        SalesOffer(
            seller_id=farmer.farmer_id,
            crop_id="wheat",
            quantity=25,
            price=200,
            region="Nakuru",
        )
    )
    request = agro_marketplace.marketplace.create_purchase_request(
        PurchaseRequest(
            buyer_id=buyer.buyer_id,
            crop_id="wheat",
            quantity=20,
            max_price=220,
            region="Nakuru",
        )
    )
    match = await agro_marketplace.marketplace.match_offer(offer.offer_id, request.request_id)
    assert match["matched"] is True

    negotiation = await agro_marketplace.negotiations.start(
        offer_id=offer.offer_id,
        buyer_id=buyer.buyer_id,
        seller_id=farmer.farmer_id,
        price=200,
        quantity=20,
        request_id=request.request_id,
    )
    countered = await agro_marketplace.negotiations.counter_offer(
        negotiation.negotiation_id, price=195, quantity=20, actor_id=buyer.buyer_id
    )
    assert countered.status.value == "countered"
    agreed = await agro_marketplace.negotiations.agree(negotiation.negotiation_id)
    assert agreed.status.value == "agreed"

    order = agro_marketplace.marketplace_orders.create(
        MarketplaceOrder(
            buyer_id=buyer.buyer_id,
            seller_id=farmer.farmer_id,
            offer_id=offer.offer_id,
            negotiation_id=negotiation.negotiation_id,
            quantity=20,
            unit_price=195,
        )
    )
    confirmed = await agro_marketplace.marketplace_orders.confirm(order.order_id)
    assert confirmed.status.value == "confirmed"

    contract = await agro_marketplace.contracts.prepare(
        order_id=order.order_id,
        negotiation_id=negotiation.negotiation_id,
    )
    signed = await agro_marketplace.contracts.sign(contract.contract_id)
    assert signed.status.value == "signed"

    deal = agro_marketplace.marketplace.create_deal(
        MarketplaceDeal(
            order_id=order.order_id,
            contract_id=contract.contract_id,
            buyer_id=buyer.buyer_id,
            seller_id=farmer.farmer_id,
            amount=confirmed.total,
        )
    )
    completed = await agro_marketplace.marketplace.complete_trade(deal.deal_id)
    assert completed.status.value == "completed"

    opportunities = agro_marketplace.marketplace.opportunities()
    assert isinstance(opportunities, list)


@pytest.mark.asyncio
async def test_trading_rfq_and_ai_hooks():
    farmer = await agro_marketplace.crm_engine.register_farmer(
        FarmerProfile(name="Tea Farm", email="tea@test.com", crops=["tea"])
    )
    await agro_marketplace.crm_engine.register_buyer(
        BuyerProfile(name="Buyer", email="tb@test.com", preferred_crops=["tea"], budget_max=20000)
    )
    offer = await agro_marketplace.offers.publish(
        SalesOffer(seller_id=farmer.farmer_id, crop_id="tea", quantity=5, price=90, region="Kericho")
    )
    rfq = agro_marketplace.trading.create_rfq(
        PriceRequest(buyer_id="b1", crop_id="tea", quantity=4, target_price=85)
    )
    responded = agro_marketplace.trading.respond_to_rfq(rfq.rfq_id, offer.offer_id)
    assert offer.offer_id in responded.responses
    price = await agro_marketplace.trading.price_recommendation(offer.offer_id)
    assert "recommended_price" in price
    buyers = await agro_marketplace.trading_ai.recommend_buyers(
        offer, agro_marketplace.crm_engine.list_buyer_profiles()
    )
    assert buyers


def test_health_sprint_83_layers():
    health = agro_marketplace.health()
    assert health["application_version"] == "2.0.0"
    assert health["crm_layer"] == "1.0"
    assert health["marketplace_layer"] == "1.0"
    assert health["trading_layer"] == "1.0"
    assert health["negotiation_layer"] == "1.0"


@pytest.mark.asyncio
async def test_rest_crm_and_marketplace(client: TestClient):
    farmer = await client.post(
        "/api/agro/v1/crm/farmers",
        json={"name": "REST Farmer", "email": "rf@test.com", "crops": ["beans"]},
    )
    assert farmer.status == 201
    buyer = await client.post(
        "/api/agro/v1/crm/buyers",
        json={"name": "REST Buyer", "email": "rb@test.com", "preferred_crops": ["beans"], "budget_max": 10000},
    )
    assert buyer.status == 201
    buyer_data = await buyer.json()
    farmer_data = await farmer.json()

    offer = await client.post(
        "/api/agro/v1/marketplace/offers",
        json={
            "seller_id": farmer_data["farmer_id"],
            "crop_id": "beans",
            "quantity": 8,
            "price": 120,
            "region": "Embu",
        },
    )
    assert offer.status == 201
    offer_data = await offer.json()

    request = await client.post(
        "/api/agro/v1/marketplace/requests",
        json={
            "buyer_id": buyer_data["buyer_id"],
            "crop_id": "beans",
            "quantity": 6,
            "max_price": 130,
            "region": "Embu",
        },
    )
    assert request.status == 201
    request_data = await request.json()

    match = await client.post(
        "/api/agro/v1/marketplace/match",
        json={"offer_id": offer_data["offer_id"], "request_id": request_data["request_id"]},
    )
    assert match.status == 200
    match_data = await match.json()
    assert match_data["matched"] is True
