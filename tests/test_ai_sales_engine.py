"""Tests — AI Sales Agents & Customer Intelligence (Sprint 6.4)."""

from __future__ import annotations

import asyncio

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.auto_marketplace import auto_marketplace
from applications.auto_marketplace.ai_sales.models import AgentType
from applications.auto_marketplace.api.register import register_auto_marketplace_routes
from applications.auto_marketplace.crm.models import CRMLead, CustomerProfile, LeadSource
from applications.auto_marketplace.vehicle_catalog.models import CatalogVehicle


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


@pytest.mark.asyncio
async def test_ai_agent_dispatch():
    result = await auto_marketplace.ai_sales_engine.dispatch_agent(
        AgentType.CUSTOMER_ASSISTANT,
        {"message": "Looking for an SUV under $40k"},
    )
    assert result["agent"] == AgentType.CUSTOMER_ASSISTANT.value
    assert "response" in result


@pytest.mark.asyncio
async def test_customer_intelligence_analysis():
    profile = await auto_marketplace.crm_engine.customers.create(
        CustomerProfile(
            first_name="Intel",
            email="intel@test.com",
            preferences={"budget_max": 45000, "make": "Toyota"},
            intent_score=65,
        )
    )
    intel = await auto_marketplace.ai_sales_engine.intelligence.analyze_profile(profile.customer_id)
    assert intel.customer_id == profile.customer_id
    assert intel.budget_max == 45000
    assert "Toyota" in intel.preferred_makes or intel.preferred_makes == ["Toyota"]


@pytest.mark.asyncio
async def test_personalized_recommendations():
    profile = await auto_marketplace.crm_engine.customers.create(
        CustomerProfile(email="rec@test.com", preferences={"budget_max": 50000})
    )
    auto_marketplace.store.catalog_vehicles.save(
        "v-rec-1",
        CatalogVehicle(vehicle_id="v-rec-1", brand="Toyota", model="Camry", price=28000, year=2022),
    )
    items = await auto_marketplace.ai_sales_engine.recommendations.personalized(profile.customer_id)
    assert len(items) >= 1
    assert items[0].recommendation_type == "personalized"


@pytest.mark.asyncio
async def test_lead_intelligence_scoring():
    customer = await auto_marketplace.crm_engine.customers.create(CustomerProfile(email="lead@test.com"))
    lead = await auto_marketplace.crm_engine.leads.create(
        CRMLead(customer_id=customer.customer_id, vehicle_id="v1", source=LeadSource.WEB),
        customer,
    )
    report = await auto_marketplace.ai_sales_engine.leads.analyze_lead(lead.lead_id)
    assert report.score > 0
    assert report.temperature.value in {"hot", "warm", "cold"}


@pytest.mark.asyncio
async def test_conversation_memory_and_summary():
    profile = await auto_marketplace.crm_engine.customers.create(CustomerProfile(email="conv@test.com"))
    session = await auto_marketplace.ai_sales_engine.conversations.start_session(profile.customer_id)
    await auto_marketplace.ai_sales_engine.conversations.append_turn(
        session.session_id, role="user", content="I want a hybrid SUV"
    )
    summary = await auto_marketplace.ai_sales_engine.conversations.summarize(session.session_id)
    assert summary
    suggestion = await auto_marketplace.ai_sales_engine.conversations.suggest_response(session.session_id)
    assert "suggestion" in suggestion


@pytest.mark.asyncio
async def test_negotiation_offer_generation():
    profile = await auto_marketplace.crm_engine.customers.create(CustomerProfile(email="offer@test.com"))
    auto_marketplace.store.catalog_vehicles.save(
        "v-offer",
        CatalogVehicle(vehicle_id="v-offer", brand="Honda", model="CR-V", price=32000, year=2023),
    )
    offer = await auto_marketplace.ai_sales_engine.negotiation.generate_offer(
        profile.customer_id, "v-offer", dealer_id="d1"
    )
    assert offer.amount == 32000
    terms = await auto_marketplace.ai_sales_engine.negotiation.negotiate_terms(offer.offer_id, 30000)
    assert "revised_amount" in terms


@pytest.mark.asyncio
async def test_knowledge_search():
    articles = auto_marketplace.ai_sales_engine.knowledge.search("financing")
    assert len(articles) >= 1


@pytest.mark.asyncio
async def test_ai_sales_api(client: TestClient):
    resp = await client.post(
        "/api/auto/v1/ai/leads/setup",
        json={"email": "api-ai@test.com", "preferences": {"budget_max": 40000}},
        headers={"Authorization": "Bearer test"},
    )
    assert resp.status == 201
    data = await resp.json()
    lead_id = data["lead"]["lead_id"]
    customer_id = data["customer"]["customer_id"]

    resp = await client.get(
        f"/api/auto/v1/ai/leads/{lead_id}/intelligence",
        headers={"Authorization": "Bearer test"},
    )
    assert resp.status == 200

    resp = await client.get(
        f"/api/auto/v1/ai/customers/{customer_id}/intent",
        headers={"Authorization": "Bearer test"},
    )
    assert resp.status == 200


@pytest.mark.asyncio
async def test_recommendation_generated_event():
    received: list = []
    from events import subscribe

    subscribe("RecommendationGeneratedEvent", lambda e: received.append(e))
    profile = await auto_marketplace.crm_engine.customers.create(CustomerProfile(email="evt@test.com"))
    await auto_marketplace.ai_sales_engine.recommendations.personalized(profile.customer_id)
    await asyncio.sleep(0.05)
    assert len(received) >= 1
