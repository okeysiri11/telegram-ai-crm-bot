"""Tests — Agricultural AI Agents & Smart Recommendations (Sprint 8.4)."""

from __future__ import annotations

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.agro_marketplace import agro_marketplace
from applications.agro_marketplace.api.register import register_agro_marketplace_routes
from applications.agro_marketplace.ai.models import AgroAgentType
from applications.agro_marketplace.marketplace.models import (
    AgriculturalLead,
    BuyerProfile,
    FarmerProfile,
    PurchaseRequest,
    SalesOffer,
)
from applications.agro_marketplace.product_catalog.models import AgriculturalProduct, AvailabilityStatus


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


def test_agent_registry_has_ten_agents():
    agents = agro_marketplace.agro_ai.agents.list_agents()
    assert len(agents) == 10
    types = {a.agent_type for a in agents}
    assert AgroAgentType.EXECUTIVE_AGRO_AI in types
    assert AgroAgentType.CROP_ADVISOR in types


@pytest.mark.asyncio
async def test_assistant_and_agent_invoke():
    result = await agro_marketplace.agro_ai.assistant.ask(
        "Advise on maize harvest moisture",
        role="crop",
        user_id="u1",
    )
    assert result["agent_type"] == "crop_advisor"
    assert result["reply"]

    invocation = await agro_marketplace.agro_ai.agents.invoke(
        AgroAgentType.PRICING_ADVISOR,
        "Estimate fair wheat price",
        user_id="u2",
    )
    assert invocation.reply


@pytest.mark.asyncio
async def test_recommendations_forecast_knowledge():
    await agro_marketplace.product_catalog.create(
        AgriculturalProduct(
            name="Rift Maize",
            crop_id="maize",
            region="Rift",
            quantity=40,
            price=170,
            status=AvailabilityStatus.AVAILABLE,
        )
    )
    farmer = await agro_marketplace.crm_engine.register_farmer(
        FarmerProfile(name="F", email="f@t.com", crops=["maize"])
    )
    buyer = await agro_marketplace.crm_engine.register_buyer(
        BuyerProfile(name="B", email="b@t.com", preferred_crops=["maize"], budget_max=20000)
    )
    offer = await agro_marketplace.offers.publish(
        SalesOffer(seller_id=farmer.farmer_id, crop_id="maize", quantity=20, price=175, region="Rift")
    )
    agro_marketplace.marketplace.create_purchase_request(
        PurchaseRequest(buyer_id=buyer.buyer_id, crop_id="maize", quantity=15, max_price=190, region="Rift")
    )

    products = await agro_marketplace.agro_ai.recommendations.recommend_products(buyer_id=buyer.buyer_id)
    assert products.kind == "product"
    buyers = await agro_marketplace.agro_ai.recommendations.recommend_buyers(offer.offer_id)
    assert buyers.kind == "buyer"
    opportunities = await agro_marketplace.agro_ai.recommendations.detect_trade_opportunities()
    assert opportunities.kind == "trade_opportunity"

    price = await agro_marketplace.agro_ai.forecasting.forecast_price("maize", region="Rift")
    demand = await agro_marketplace.agro_ai.forecasting.forecast_demand("maize", region="Rift")
    supply = await agro_marketplace.agro_ai.forecasting.forecast_supply("maize")
    harvest = await agro_marketplace.agro_ai.forecasting.forecast_harvest("maize")
    risk = await agro_marketplace.agro_ai.forecasting.estimate_risk("maize")
    assert price.values and demand.values and supply.values and harvest.values and risk.values

    knowledge = agro_marketplace.agro_ai.knowledge.search("moisture")
    assert knowledge
    taxonomy = agro_marketplace.agro_ai.knowledge.crop_taxonomy()
    assert taxonomy


@pytest.mark.asyncio
async def test_ai_workflows():
    lead = await agro_marketplace.crm_engine.create_lead(
        AgriculturalLead(
            name="Hot Lead",
            email="hot@t.com",
            role="buyer",
            crop_interest="maize",
            region="Rift",
            source="rfq",
        )
    )
    qualified = await agro_marketplace.agro_ai.workflow.qualify_lead(lead.lead_id)
    assert qualified["lead"]["score"] > 0

    farmer = await agro_marketplace.crm_engine.register_farmer(
        FarmerProfile(name="SF", email="sf@t.com", crops=["wheat"])
    )
    buyer = await agro_marketplace.crm_engine.register_buyer(
        BuyerProfile(name="SB", email="sb@t.com", preferred_crops=["wheat"], budget_max=30000)
    )
    await agro_marketplace.offers.publish(
        SalesOffer(seller_id=farmer.farmer_id, crop_id="wheat", quantity=10, price=200, region="Nakuru")
    )
    agro_marketplace.marketplace.create_purchase_request(
        PurchaseRequest(buyer_id=buyer.buyer_id, crop_id="wheat", quantity=8, max_price=210, region="Nakuru")
    )
    matched = await agro_marketplace.agro_ai.workflow.auto_match_offers()
    assert matched["matched"] >= 1

    report = await agro_marketplace.agro_ai.workflow.executive_report(title="Weekly Agro")
    assert report.report_id
    assert agro_marketplace.agro_ai.workflow.list_tasks()


def test_health_sprint_84():
    health = agro_marketplace.health()
    assert health["application_version"] == "1.4.0-alpha"
    assert health["agro_ai"] == "1.0"
    assert health["ai"]["agro_ai"] == "1.0"
    assert health["ai"]["agents"]["agents"] == 10


@pytest.mark.asyncio
async def test_rest_ai_endpoints(client: TestClient):
    health = await client.get("/api/agro/v1/ai/health")
    assert health.status == 200
    data = await health.json()
    assert data["agro_ai"] == "1.0"

    agents = await client.get("/api/agro/v1/ai/agents")
    assert agents.status == 200
    agent_data = await agents.json()
    assert len(agent_data["items"]) == 10

    ask = await client.post(
        "/api/agro/v1/ai/assistant",
        json={"message": "Help me plan maize season", "role": "crop"},
    )
    assert ask.status == 200

    forecast = await client.post(
        "/api/agro/v1/forecast/price",
        json={"subject": "maize", "region": "Rift", "horizon_days": 30},
    )
    assert forecast.status == 200

    knowledge = await client.get("/api/agro/v1/knowledge/search", params={"q": "export"})
    assert knowledge.status == 200
    kn = await knowledge.json()
    assert kn["items"]

    recs = await client.get("/api/agro/v1/recommendations/products")
    assert recs.status == 200
