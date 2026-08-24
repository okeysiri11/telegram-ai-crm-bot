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
from applications.auto_marketplace.crm.tenant import bind_crm_tenant
from applications.auto_marketplace.shared.exceptions import NotFoundError


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
    bind_crm_tenant("default")
    auto_marketplace.reset()
    yield
    auto_marketplace.reset()
    bind_crm_tenant("default")


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
    fetched = await auto_marketplace.crm_engine.customers.get(profile.customer_id)
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
    conversion = await auto_marketplace.crm_engine.pipeline.conversion_analytics()
    assert "leads_total" in conversion
    forecast = await auto_marketplace.crm_engine.pipeline.forecast()
    assert "weighted_pipeline" in forecast


@pytest.mark.asyncio
async def test_tasks_and_reminders():
    task = await auto_marketplace.crm_engine.tasks.create(
        CRMTask(title="Follow up", assigned_agent_id="agent-1")
    )
    assert task.task_id
    completed = await auto_marketplace.crm_engine.tasks.complete(task.task_id)
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


@pytest.mark.asyncio
async def test_memory_backend_tenant_isolation():
    bind_crm_tenant("tenant-alpha")
    lead = await auto_marketplace.crm_engine.leads.create(CRMLead(customer_id="c-iso", notes="alpha-only"))
    bind_crm_tenant("tenant-beta")
    with pytest.raises(NotFoundError):
        await auto_marketplace.crm_engine.leads.get(lead.lead_id)
    bind_crm_tenant("tenant-alpha")
    restored = await auto_marketplace.crm_engine.leads.get(lead.lead_id)
    assert restored.notes == "alpha-only"


@pytest.mark.asyncio
async def test_crm_api_lead_customer_deal_lifecycle(client: TestClient):
    headers = {"Authorization": "Bearer test"}
    created_customer = await client.post(
        "/api/auto/v1/crm/customers",
        json={"first_name": "Ann", "last_name": "Lee", "email": "ann@test.com", "phone": "+1"},
        headers=headers,
    )
    assert created_customer.status == 201
    customer = await created_customer.json()
    customer_id = customer["customer_id"]

    patched_customer = await client.patch(
        f"/api/auto/v1/crm/customers/{customer_id}",
        json={"phone": "+1999"},
        headers=headers,
    )
    assert patched_customer.status == 200
    assert (await patched_customer.json())["phone"] == "+1999"

    listed_customers = await client.get("/api/auto/v1/crm/customers?email=ann@test.com", headers=headers)
    assert listed_customers.status == 200
    assert any(item["customer_id"] == customer_id for item in (await listed_customers.json())["items"])

    created_lead = await client.post(
        "/api/auto/v1/crm/leads",
        json={"customer_id": customer_id, "dealer_id": "d1", "notes": "hot lead"},
        headers=headers,
    )
    assert created_lead.status == 201
    lead = await created_lead.json()
    lead_id = lead["lead_id"]

    got_lead = await client.get(f"/api/auto/v1/crm/leads/{lead_id}", headers=headers)
    assert got_lead.status == 200
    patched_lead = await client.patch(
        f"/api/auto/v1/crm/leads/{lead_id}",
        json={"status": "contacted", "assigned_agent_id": "mgr-1", "notes": "called"},
        headers=headers,
    )
    assert patched_lead.status == 200
    lead_body = await patched_lead.json()
    assert lead_body["status"] == "contacted"
    assert lead_body["assigned_agent_id"] == "mgr-1"

    listed_leads = await client.get(f"/api/auto/v1/crm/leads?status=contacted&customer_id={customer_id}", headers=headers)
    assert listed_leads.status == 200
    assert any(item["lead_id"] == lead_id for item in (await listed_leads.json())["items"])

    converted = await client.post(
        f"/api/auto/v1/crm/leads/{lead_id}/convert",
        json={"amount": 18000},
        headers=headers,
    )
    assert converted.status == 201
    deal = await converted.json()
    deal_id = deal["deal_id"]
    assert deal["customer_id"] == customer_id
    assert deal["stage"] == "qualification"

    again = await client.post(
        f"/api/auto/v1/crm/leads/{lead_id}/convert",
        json={"amount": 99999},
        headers=headers,
    )
    assert again.status == 201
    assert (await again.json())["deal_id"] == deal_id

    got_deal = await client.get(f"/api/auto/v1/crm/deals/{deal_id}", headers=headers)
    assert got_deal.status == 200
    staged = await client.patch(
        f"/api/auto/v1/crm/deals/{deal_id}",
        json={"stage": "proposal"},
        headers=headers,
    )
    assert staged.status == 200
    assert (await staged.json())["stage"] == "proposal"

    pipeline = await client.get("/api/auto/v1/crm/pipeline", headers=headers)
    assert pipeline.status == 200
    stages = (await pipeline.json())["stages"]
    assert any(item["deal_id"] == deal_id for item in stages.get("proposal", []))


@pytest.mark.asyncio
async def test_crm_api_tenant_header_isolation(client: TestClient):
    headers_a = {"Authorization": "Bearer test", "X-Tenant-Id": "web-a"}
    headers_b = {"Authorization": "Bearer test", "X-Tenant-Id": "web-b"}
    created = await client.post(
        "/api/auto/v1/crm/leads",
        json={"notes": "tenant-a-secret", "dealer_id": "d-iso"},
        headers=headers_a,
    )
    assert created.status == 201
    lead_id = (await created.json())["lead_id"]
    hidden = await client.get(f"/api/auto/v1/crm/leads/{lead_id}", headers=headers_b)
    assert hidden.status == 404
    visible = await client.get(f"/api/auto/v1/crm/leads/{lead_id}", headers=headers_a)
    assert visible.status == 200
    assert (await visible.json())["notes"] == "tenant-a-secret"
