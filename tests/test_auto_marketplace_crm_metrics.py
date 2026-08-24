"""Sprint 5 — durable CRM health/count/analytics read paths."""

from __future__ import annotations

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.auto_marketplace import auto_marketplace
from applications.auto_marketplace.api.register import register_auto_marketplace_routes
from applications.auto_marketplace.crm.metrics import crm_metrics
from applications.auto_marketplace.crm.models import (
    CRMDeal,
    CRMLead,
    CRMTask,
    CustomerProfile,
    EmailMessage,
    Interaction,
    Meeting,
    PhoneCall,
    Reminder,
)
from applications.auto_marketplace.crm.tenant import bind_crm_tenant
from applications.auto_marketplace.shared.store import marketplace_store

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


async def _seed_crm() -> None:
    engine = auto_marketplace.crm_engine
    profile = await engine.customers.create(CustomerProfile(first_name="Ada", last_name="Buyer", email="ada@ex.com"))
    await engine.leads.create(CRMLead(customer_id=profile.customer_id, notes="hot"))
    await engine.deals.create(CRMDeal(customer_id=profile.customer_id, amount=4100))
    await engine.tasks.create(CRMTask(title="Call back", customer_id=profile.customer_id))
    await engine.activities.record(Interaction(subject="note", body="hello", customer_id=profile.customer_id))
    await engine.communications.log_call(PhoneCall(customer_id=profile.customer_id, direction="outbound"))
    await engine.communications.log_email(EmailMessage(customer_id=profile.customer_id, subject="quote"))
    await engine.calendar.schedule_meeting(Meeting(customer_id=profile.customer_id, title="showroom"))
    await engine.calendar.create_reminder(Reminder(customer_id=profile.customer_id, message="follow", trigger_at=1.0))


@pytest.mark.asyncio
async def test_durable_metrics_and_health_snapshot():
    assert auto_marketplace.health()["crm_leads"] == 0
    await _seed_crm()
    assert auto_marketplace.health()["crm_leads"] == 0
    snapshot = await crm_metrics.refresh()
    health = auto_marketplace.health()
    assert health["crm_leads"] == 1
    assert health["crm_deals"] == 1
    assert health["crm_customers"] == 1
    assert health["crm_tasks"] == 1
    assert health["crm_activities"] >= 1
    assert health["crm_calls"] == 1
    assert health["crm_emails"] == 1
    assert health["crm_meetings"] == 1
    assert health["crm_reminders"] == 1
    assert health["crm_opportunities"] == health["crm_deals"]
    assert snapshot["opportunities"] == snapshot["deals"]
    metrics = await auto_marketplace.crm_engine.metrics()
    assert metrics["leads"] == 1
    assert metrics["opportunities"] == metrics["deals"]
    analytics = auto_marketplace.analytics.dashboard_metrics()
    assert analytics["leads"] == 1
    assert analytics["deals"] == 1
    assert analytics["calls"] == 1
    workflow = await auto_marketplace.bi_engine.analytics.workflow_analytics()
    assert workflow["calls"] == 1
    assert workflow["opportunities"] == 1
    assert not hasattr(marketplace_store, "opportunities")
    for name in (
        "crm_leads",
        "crm_deals",
        "crm_tasks",
        "customer_profiles",
        "phone_calls",
        "email_messages",
        "meetings",
        "reminders",
        "interactions",
    ):
        assert not hasattr(marketplace_store, name)


@pytest.mark.asyncio
async def test_web_crm_does_not_dual_write_foundation_customers():
    profile = await auto_marketplace.crm_engine.customers.create(
        CustomerProfile(first_name="No", last_name="Shadow", email="noshadow@ex.com", preferences={"make": "Honda"})
    )
    assert marketplace_store.customers.get(profile.customer_id) is None
    recs = await auto_marketplace.recommendations.recommend_for_crm_customer(profile.customer_id)
    assert isinstance(recs, list)


@pytest.mark.asyncio
async def test_metrics_tenant_isolation():
    bind_crm_tenant("tenant-a")
    await auto_marketplace.crm_engine.leads.create(CRMLead(notes="alpha"))
    counts_a = await crm_metrics.collect("tenant-a")
    counts_b = await crm_metrics.collect("tenant-b")
    assert counts_a["leads"] == 1
    assert counts_b["leads"] == 0
    assert counts_a["calls"] == 0
    bind_crm_tenant("tenant-b")
    other = await crm_metrics.refresh()
    assert other["leads"] == 0


@pytest.mark.asyncio
async def test_health_api_is_tenant_scoped(client: TestClient):
    bind_crm_tenant("tenant-a")
    await auto_marketplace.crm_engine.leads.create(CRMLead(notes="visible"))
    resp_a = await client.get("/api/auto/v1/health", headers={"X-Tenant-Id": "tenant-a"})
    assert resp_a.status == 200
    body_a = await resp_a.json()
    assert body_a["crm_leads"] == 1
    resp_b = await client.get("/api/auto/v1/health", headers={"X-Tenant-Id": "tenant-b"})
    assert resp_b.status == 200
    body_b = await resp_b.json()
    assert body_b["crm_leads"] == 0


@pytest.mark.asyncio
async def test_crm_metrics_api_and_analytics_refresh(client: TestClient):
    await _seed_crm()
    metrics = await client.get("/api/auto/v1/crm/metrics", headers=AUTH)
    assert metrics.status == 200
    payload = await metrics.json()
    assert payload["leads"] == 1
    assert payload["opportunities"] == payload["deals"]
    analytics = await client.get("/api/auto/v1/analytics")
    assert analytics.status == 200
    body = await analytics.json()
    assert body["leads"] == 1
    assert body["meetings"] == 1
