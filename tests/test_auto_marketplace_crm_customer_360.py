"""Sprint 11 — CRM Customer 360, unified timeline, relationship intelligence."""

from __future__ import annotations

import time
import uuid

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.auto_marketplace import auto_marketplace
from applications.auto_marketplace.activities.service import ActivityService
from applications.auto_marketplace.api.register import register_auto_marketplace_routes
from applications.auto_marketplace.business_intelligence.models import DashboardRole
from applications.auto_marketplace.calendar.service import CalendarService
from applications.auto_marketplace.communications.service import CommunicationService
from applications.auto_marketplace.crm.customer_360 import classify_relationship
from applications.auto_marketplace.crm.engine import CRMEngine
from applications.auto_marketplace.crm.models import (
    CRMLead,
    CRMTask,
    CustomerProfile,
    DealStage,
    Interaction,
    InteractionType,
    LeadSource,
    Meeting,
    PhoneCall,
)
from applications.auto_marketplace.crm.persistence import PostgresCRMPersistence, reset_crm_persistence
from applications.auto_marketplace.crm.tenant import bind_crm_tenant
from applications.auto_marketplace.customers.profile_service import CustomerProfileService
from applications.auto_marketplace.deals.service import DealService
from applications.auto_marketplace.executive_dashboard.service import executive_dashboard_service
from applications.auto_marketplace.leads.service import LeadService
from applications.auto_marketplace.sales_pipeline.service import SalesPipelineEngine
from applications.auto_marketplace.shared.exceptions import NotFoundError
from applications.auto_marketplace.tasks.service import TaskService
from tests.test_auto_marketplace_crm_postgres import _ensure_postgres_tables

AUTH = {"Authorization": "Bearer test"}


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


@pytest.fixture
async def postgres_crm_mode(monkeypatch):
    monkeypatch.setenv("AUTO_CRM_PERSISTENCE", "postgres")
    reset_crm_persistence()
    from database.session import shutdown_db

    await shutdown_db()
    yield
    await shutdown_db()
    monkeypatch.setenv("AUTO_CRM_PERSISTENCE", "memory")
    reset_crm_persistence()


def _stack(persist: PostgresCRMPersistence) -> CRMEngine:
    customers = CustomerProfileService(persistence=persist)
    leads = LeadService(persistence=persist)
    deals = DealService(persistence=persist)
    return CRMEngine(
        customers=customers,
        leads=leads,
        deals=deals,
        pipeline=SalesPipelineEngine(leads=leads, deals=deals, persistence=persist),
        activities=ActivityService(persistence=persist),
        communications=CommunicationService(persistence=persist),
        tasks=TaskService(persistence=persist),
        calendar=CalendarService(persistence=persist),
    )


async def _counts(engine: CRMEngine) -> dict[str, int]:
    return {
        "customers": len(await engine.customers.list_profiles()),
        "leads": len(await engine.leads.list_leads()),
        "deals": len(await engine.deals.list_deals()),
        "tasks": len(await engine.tasks.list_tasks()),
        "activities": len(await engine.activities.list_activities()),
        "follow_ups": len(await engine.automation.list_follow_ups()),
    }


def test_relationship_thresholds_are_centralized():
    assert classify_relationship(75).value == "strong"
    assert classify_relationship(55).value == "healthy"
    assert classify_relationship(35).value == "attention"
    assert classify_relationship(34).value == "at_risk"


@pytest.mark.asyncio
async def test_customer_360_minimal_and_open_closed_deals():
    engine = auto_marketplace.crm_engine
    now = time.time()
    bare = await engine.customers.create(CustomerProfile(first_name="Mina", email="mina@test.com"))
    empty = await engine.customer_360.get_360(bare.customer_id, now=now)
    assert empty["customer_id"] == bare.customer_id
    assert empty["identity"]["email"] == "mina@test.com"
    assert empty["open_opportunities"] == []
    assert empty["closed_opportunities"] == []
    assert isinstance(empty["timeline"], list)
    assert empty["relationship_health"] in {"strong", "healthy", "attention", "at_risk"}
    assert empty["next_best_action"]["action"] == "NO_ACTION"

    customer = await engine.customers.create(
        CustomerProfile(first_name="Omar", email="omar@test.com", owner_agent_id="agt-360")
    )
    lead = await engine.leads.create(
        CRMLead(
            customer_id=customer.customer_id,
            source=LeadSource.REFERRAL,
            vehicle_id="veh-360",
            assigned_agent_id="agt-360",
        )
    )
    deal = await engine.pipeline.convert_lead_to_deal(lead.lead_id, amount=18000)
    await engine.calendar.schedule_meeting(
        Meeting(
            customer_id=customer.customer_id,
            lead_id=lead.lead_id,
            deal_id=deal.deal_id,
            title="handover",
            status="completed",
            completed=True,
        )
    )
    await engine.communications.log_call(
        PhoneCall(customer_id=customer.customer_id, lead_id=lead.lead_id, status="completed")
    )
    await engine.automation.schedule_follow_up(
        lead_id=lead.lead_id,
        customer_id=customer.customer_id,
        action_type="call",
        due_at=now + 7200,
        idempotency_key="c360-open",
    )
    opened = await engine.customer_360.get_360(customer.customer_id, now=now)
    assert opened["open_opportunities"]
    assert opened["deal_value"] == 18000
    assert opened["owner_id"]
    assert any(item["event_type"] in {"lead_created", "opportunity_created", "communication"} for item in opened["timeline"])
    intel = await engine.intelligence.lead_intelligence(lead.lead_id, now=now)
    exec_item = await engine.execution.evaluate(lead_id=lead.lead_id, now=now)
    assert opened["lead_temperature"] == intel["temperature"]
    assert opened["next_best_action"]["action"] == exec_item["recommended_action"]
    assert opened["sla_status"] == exec_item["sla_status"]

    won_customer = await engine.customers.create(CustomerProfile(email="won@test.com"))
    won_lead = await engine.leads.create(CRMLead(customer_id=won_customer.customer_id, notes="win"))
    won_deal = await engine.pipeline.convert_lead_to_deal(won_lead.lead_id, amount=5000)
    await engine.deals.mark_won(won_deal.deal_id)
    closed = await engine.customer_360.get_360(won_customer.customer_id, now=now)
    assert closed["closed_opportunities"]
    assert closed["open_opportunities"] == []
    assert any(item["event_type"] == "deal_won" for item in closed["timeline"])
    assert (await engine.deals.get(won_deal.deal_id)).stage == DealStage.CLOSED_WON


@pytest.mark.asyncio
async def test_timeline_ordering_tie_break_relationship_and_signals():
    engine = auto_marketplace.crm_engine
    now = time.time()
    customer = await engine.customers.create(CustomerProfile(email="tie@test.com", first_name="Tie"))
    stamp = now - 10
    first = await engine.activities.record(
        Interaction(
            customer_id=customer.customer_id,
            interaction_type=InteractionType.NOTE,
            subject="alpha",
            body="a",
            created_at=stamp,
            idempotency_key="note-a",
        )
    )
    second = await engine.activities.record(
        Interaction(
            customer_id=customer.customer_id,
            interaction_type=InteractionType.NOTE,
            subject="beta",
            body="b",
            created_at=stamp,
            idempotency_key="note-b",
        )
    )
    timeline = await engine.customer_360.timeline(customer.customer_id)
    same_ts = [item for item in timeline if item["occurred_at"] == stamp]
    assert len(same_ts) == 2
    ordered = sorted(same_ts, key=lambda item: (-item["occurred_at"], item["event_type"], item["event_id"]))
    assert same_ts == ordered
    assert {first.interaction_id, second.interaction_id} == {item["event_id"] for item in same_ts}

    lead = await engine.leads.create(CRMLead(customer_id=customer.customer_id, notes="signals"))
    await engine.tasks.create(
        CRMTask(customer_id=customer.customer_id, lead_id=lead.lead_id, title="late", due_at=now - 90)
    )
    await engine.automation.schedule_follow_up(
        lead_id=lead.lead_id,
        customer_id=customer.customer_id,
        action_type="call",
        due_at=now - 400,
        idempotency_key="c360-over",
    )
    report = await engine.customer_360.get_360(customer.customer_id, now=now)
    codes = [item["code"] for item in report["attention_signals"]]
    assert len(codes) == len(set(codes))
    assert "FOLLOW_UP_OVERDUE" in codes
    assert report["relationship_explanation"]
    assert report["relationship_reason_codes"]
    again = await engine.customer_360.get_360(customer.customer_id, now=now)
    assert again["relationship_health"] == report["relationship_health"]
    assert again["relationship_score"] == report["relationship_score"]
    assert again["attention_signals"] == report["attention_signals"]
    assert again["timeline"] == report["timeline"]
    before = await _counts(engine)
    await engine.customer_360.get_360(customer.customer_id, now=now)
    assert await _counts(engine) == before


@pytest.mark.asyncio
async def test_customer_360_api_auth_tenant_and_dashboard(client: TestClient):
    unauth = await client.get("/api/auto/v1/crm/customers/missing/360")
    assert unauth.status == 401
    created = await client.post(
        "/api/auto/v1/crm/customers",
        json={"first_name": "Api", "email": "api360@test.com"},
        headers=AUTH,
    )
    assert created.status == 201, await created.text()
    customer_id = (await created.json())["customer_id"]
    before = await client.get("/api/auto/v1/crm/metrics", headers=AUTH)
    before_body = await before.json()
    first = await client.get(f"/api/auto/v1/crm/customers/{customer_id}/360", headers=AUTH)
    assert first.status == 200
    payload = await first.json()
    assert payload["customer_id"] == customer_id
    assert "timeline" in payload
    assert "relationship_health" in payload
    second = await client.get(f"/api/auto/v1/crm/customers/{customer_id}/360", headers=AUTH)
    body = await second.json()
    payload.pop("derived_at", None)
    body.pop("derived_at", None)
    assert body == payload
    after = await client.get("/api/auto/v1/crm/metrics", headers=AUTH)
    after_body = await after.json()
    for key in ("customers", "leads", "deals", "tasks", "activities", "reminders"):
        assert after_body[key] == before_body[key]

    headers_a = {**AUTH, "X-Tenant-Id": "c360-a"}
    headers_b = {**AUTH, "X-Tenant-Id": "c360-b"}
    cust_a = await client.post("/api/auto/v1/crm/customers", json={"email": "a360@test.com"}, headers=headers_a)
    cust_a_id = (await cust_a.json())["customer_id"]
    hidden = await client.get(f"/api/auto/v1/crm/customers/{cust_a_id}/360", headers=headers_b)
    assert hidden.status == 404
    visible = await client.get(f"/api/auto/v1/crm/customers/{cust_a_id}/360", headers=headers_a)
    assert visible.status == 200
    assert (await visible.json())["tenant_id"] == "c360-a"
    dash = await executive_dashboard_service.get_dashboard(DashboardRole.SALES_MANAGER)
    types = {item["type"] for item in dash.widgets}
    assert "customer_360" in types
    assert "sales_execution" in types


@pytest.mark.asyncio
async def test_postgres_customer_360_restart_and_tenant_isolation(postgres_crm_mode):
    await _ensure_postgres_tables()
    suffix = uuid.uuid4().hex[:12]
    tenant_a = f"c360-a-{suffix}"
    tenant_b = f"c360-b-{suffix}"
    now = time.time()

    bind_crm_tenant(tenant_a)
    engine = _stack(PostgresCRMPersistence())
    customer = await engine.customers.create(CustomerProfile(email=f"pg-{suffix}@test.com", first_name="Persist"))
    lead = await engine.leads.create(CRMLead(customer_id=customer.customer_id, notes=f"360-{suffix}"))
    await engine.pipeline.convert_lead_to_deal(lead.lead_id, amount=12000)
    await engine.automation.schedule_follow_up(
        lead_id=lead.lead_id,
        customer_id=customer.customer_id,
        action_type="email",
        due_at=now + 4000,
        idempotency_key=f"pg360-{suffix}",
    )
    first = await engine.customer_360.get_360(customer.customer_id, now=now)
    assert first["tenant_id"] == tenant_a
    assert first["open_opportunities"]

    bind_crm_tenant(tenant_b)
    other = _stack(PostgresCRMPersistence())
    with pytest.raises(NotFoundError):
        await other.customer_360.get_360(customer.customer_id, now=now)

    from database.session import shutdown_db

    await shutdown_db()
    reset_crm_persistence()
    bind_crm_tenant(tenant_a)
    restored = _stack(PostgresCRMPersistence())
    loaded = await restored.customer_360.get_360(customer.customer_id, now=now)
    assert loaded["relationship_health"] == first["relationship_health"]
    assert loaded["relationship_score"] == first["relationship_score"]
    assert loaded["attention_signals"] == first["attention_signals"]
    assert [item["event_id"] for item in loaded["timeline"]] == [item["event_id"] for item in first["timeline"]]
    assert loaded["next_best_action"] == first["next_best_action"]
    assert loaded["sla_status"] == first["sla_status"]
    assert loaded["open_opportunities"][0]["amount"] == first["open_opportunities"][0]["amount"]
