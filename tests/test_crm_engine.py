"""Tests — CRM & Sales Pipeline Engine (Sprint 6.3)."""

from __future__ import annotations

import asyncio

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.auto_marketplace import auto_marketplace
from applications.auto_marketplace.api.register import register_auto_marketplace_routes
from applications.auto_marketplace.crm.models import CRMDeal, CRMLead, CRMTask, CustomerProfile, DealStage, LeadSource
from applications.auto_marketplace.crm.security import crm_security


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


def test_crm_security_roles():
    assert crm_security.authorize("owner", "crm.delete")
    assert crm_security.authorize("sales_agent", "leads.write")
    assert not crm_security.authorize("customer", "leads.manage")


@pytest.mark.asyncio
async def test_customer_profile_crud():
    profile = await auto_marketplace.crm_engine.customers.create(
        CustomerProfile(first_name="John", last_name="Doe", email="john@example.com", phone="+1234")
    )
    assert profile.segment in {"cold", "warm", "hot", "vip", "standard"}
    fetched = auto_marketplace.crm_engine.customers.get(profile.customer_id)
    assert fetched.email == "john@example.com"


@pytest.mark.asyncio
async def test_lead_scoring_and_qualification():
    customer = await auto_marketplace.crm_engine.customers.create(
        CustomerProfile(first_name="Jane", email="jane@example.com")
    )
    lead = await auto_marketplace.crm_engine.leads.create(
        CRMLead(customer_id=customer.customer_id, vehicle_id="v1", dealer_id="d1", source=LeadSource.WEB),
        customer,
    )
    assert lead.score > 0
    qualified = await auto_marketplace.crm_engine.pipeline.qualify_lead(lead.lead_id, agent_id="agent-1")
    assert qualified.status.value == "qualified"


@pytest.mark.asyncio
async def test_sales_pipeline_deal_lifecycle():
    deal = await auto_marketplace.crm_engine.deals.create(
        CRMDeal(customer_id="c1", dealer_id="d1", vehicle_id="v1", amount=30000)
    )
    assert deal.probability > 0
    advanced = await auto_marketplace.crm_engine.pipeline.advance_stage(deal.deal_id)
    assert advanced.stage != DealStage.PROSPECT
    won = await auto_marketplace.crm_engine.deals.mark_won(deal.deal_id, amount=29500)
    assert won.stage == DealStage.CLOSED_WON


@pytest.mark.asyncio
async def test_pipeline_analytics():
    await auto_marketplace.crm_engine.leads.create(CRMLead(customer_id="c1", dealer_id="d1"))
    conversion = auto_marketplace.crm_engine.pipeline.conversion_analytics()
    assert "leads_total" in conversion
    forecast = auto_marketplace.crm_engine.pipeline.forecast()
    assert "weighted_pipeline" in forecast


@pytest.mark.asyncio
async def test_tasks_and_reminders():
    task = await auto_marketplace.crm_engine.tasks.create(
        CRMTask(title="Follow up", customer_id="c1", assigned_agent_id="agent-1")
    )
    assert task.task_id
    completed = auto_marketplace.crm_engine.tasks.complete(task.task_id)
    assert completed.status.value == "completed"


@pytest.mark.asyncio
async def test_ai_next_best_action():
    lead = await auto_marketplace.crm_engine.leads.create(CRMLead(customer_id="c1", source=LeadSource.WEB))
    action = await auto_marketplace.crm_engine.ai.next_best_action(lead)
    assert "action" in action


@pytest.mark.asyncio
async def test_crm_api_create_lead(client: TestClient):
    resp = await client.post(
        "/api/auto/v1/crm/customers",
        json={"first_name": "Api", "last_name": "User", "email": "api@test.com"},
        headers={"Authorization": "Bearer test"},
    )
    assert resp.status == 201
    customer = await resp.json()

    resp = await client.post(
        "/api/auto/v1/crm/leads",
        json={"customer_id": customer["customer_id"], "dealer_id": "d1", "vehicle_id": "v1"},
        headers={"Authorization": "Bearer test"},
    )
    assert resp.status == 201
    data = await resp.json()
    assert "next_best_action" in data


@pytest.mark.asyncio
async def test_crm_pipeline_api(client: TestClient):
    resp = await client.get(
        "/api/auto/v1/crm/pipeline",
        headers={"Authorization": "Bearer test"},
    )
    assert resp.status == 200


@pytest.mark.asyncio
async def test_lead_created_event():
    received: list = []

    from events import subscribe

    subscribe("LeadCreatedEvent", lambda e: received.append(e))
    await auto_marketplace.crm_engine.leads.create(CRMLead(customer_id="c1"))
    await asyncio.sleep(0.05)
    assert len(received) >= 1
