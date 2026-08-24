"""Sprint 7 — Auto Marketplace CRM end-to-end lifecycle + workflow integrity."""

from __future__ import annotations

import time
import uuid

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.auto_marketplace import auto_marketplace
from applications.auto_marketplace.activities.service import ActivityService
from applications.auto_marketplace.api.register import register_auto_marketplace_routes
from applications.auto_marketplace.calendar.service import CalendarService
from applications.auto_marketplace.communications.service import CommunicationService
from applications.auto_marketplace.crm.engine import CRMEngine
from applications.auto_marketplace.crm.metrics import crm_metrics
from applications.auto_marketplace.crm.models import (
    CRMDeal,
    CRMLead,
    CRMTask,
    CustomerProfile,
    DealStage,
    EmailMessage,
    InteractionType,
    LeadSource,
    Meeting,
    PhoneCall,
    Reminder,
    TaskStatus,
)
from applications.auto_marketplace.crm.persistence import (
    PostgresCRMPersistence,
    reset_crm_persistence,
)
from applications.auto_marketplace.crm.tenant import bind_crm_tenant
from applications.auto_marketplace.customers.profile_service import CustomerProfileService
from applications.auto_marketplace.deals.service import DealService
from applications.auto_marketplace.leads.service import LeadService
from applications.auto_marketplace.sales_pipeline.service import SalesPipelineEngine
from applications.auto_marketplace.shared.exceptions import NotFoundError, ValidationError
from applications.auto_marketplace.shared.store import marketplace_store
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


async def _run_lifecycle(engine: CRMEngine, *, suffix: str, amount: float = 18400.0) -> dict[str, str]:
    lead = await engine.leads.create(
        CRMLead(
            notes=f"Walk-in {suffix}",
            dealer_id="d-life",
            source=LeadSource.WEB,
            assigned_agent_id="agt-life",
            metadata={"intake_key": f"intake-{suffix}", "utm_source": "globefly", "channel": "web"},
        )
    )
    reused = await engine.leads.create(
        CRMLead(notes="duplicate intake", metadata={"intake_key": f"intake-{suffix}"})
    )
    assert reused.lead_id == lead.lead_id
    assert lead.created_at > 0
    assert lead.metadata.get("utm_source") == "globefly"

    deal = await engine.pipeline.convert_lead_to_deal(lead.lead_id, amount=amount, agent_id="agt-life")
    again = await engine.pipeline.convert_lead_to_deal(lead.lead_id, amount=1)
    assert again.deal_id == deal.deal_id
    restored_lead = await engine.leads.get(lead.lead_id)
    assert restored_lead.status.value == "converted"
    assert restored_lead.customer_id == deal.customer_id

    moved = await engine.pipeline.set_stage(deal.deal_id, DealStage.PROPOSAL)
    assert moved.stage == DealStage.PROPOSAL
    view = await engine.pipeline.pipeline_view()
    assert any(item["deal_id"] == deal.deal_id for item in view["stages"].get("proposal", []))

    task = await engine.tasks.create(
        CRMTask(
            title=f"Call {suffix}",
            customer_id=deal.customer_id,
            lead_id=lead.lead_id,
            deal_id=deal.deal_id,
            assigned_agent_id="agt-life",
            due_at=time.time() - 30,
        )
    )
    await engine.tasks.update(task.task_id, description="ring twice")
    completed_task = await engine.tasks.complete(task.task_id)
    assert completed_task.status == TaskStatus.COMPLETED

    call = await engine.communications.log_call(
        PhoneCall(customer_id=deal.customer_id, lead_id=lead.lead_id, deal_id=deal.deal_id, direction="inbound", notes=suffix)
    )
    email = await engine.communications.log_email(
        EmailMessage(customer_id=deal.customer_id, lead_id=lead.lead_id, deal_id=deal.deal_id, subject=f"quote-{suffix}")
    )
    meeting = await engine.calendar.schedule_meeting(
        Meeting(customer_id=deal.customer_id, lead_id=lead.lead_id, deal_id=deal.deal_id, title=f"Drive {suffix}")
    )
    reminder = await engine.calendar.create_reminder(
        Reminder(
            customer_id=deal.customer_id,
            lead_id=lead.lead_id,
            deal_id=deal.deal_id,
            message=f"ping-{suffix}",
            trigger_at=time.time() - 10,
        )
    )
    await engine.calendar.update_reminder(reminder.reminder_id, message=f"ping-{suffix}-upd")
    await engine.calendar.complete_reminder(reminder.reminder_id)

    board = await engine.follow_up()
    assert "overdue_tasks" in board
    assert "overdue_reminders" in board
    assert "recent_activities" in board

    won = await engine.deals.mark_won(deal.deal_id, amount=amount)
    assert won.stage == DealStage.CLOSED_WON
    assert won.win is True
    same = await engine.deals.mark_won(deal.deal_id, amount=1)
    assert same.deal_id == won.deal_id
    assert same.amount == amount
    with pytest.raises(ValidationError):
        await engine.deals.mark_lost(deal.deal_id, reason="too late")
    with pytest.raises(ValidationError):
        await engine.deals.update_stage(deal.deal_id, DealStage.PROSPECT)

    types = {item.interaction_type for item in await engine.activities.list_activities(deal_id=deal.deal_id)}
    assert InteractionType.LEAD_CONVERTED in {
        item.interaction_type for item in await engine.activities.list_activities(lead_id=lead.lead_id)
    }
    assert InteractionType.CALL in types or InteractionType.CALL in {
        item.interaction_type for item in await engine.activities.list_activities(customer_id=deal.customer_id)
    }
    timeline = await engine.activities.customer_timeline(deal.customer_id)
    assert any(item.get("call_id") == call.call_id for item in timeline.get("calls", []))
    assert any(item.get("activity_type") == "call" for item in timeline.get("items", []))

    converted_events = await engine.activities.list_activities(
        lead_id=lead.lead_id, activity_type=InteractionType.LEAD_CONVERTED
    )
    assert len(converted_events) == 1

    return {
        "lead_id": lead.lead_id,
        "customer_id": deal.customer_id,
        "deal_id": deal.deal_id,
        "task_id": task.task_id,
        "call_id": call.call_id,
        "email_id": email.email_id,
        "meeting_id": meeting.meeting_id,
        "reminder_id": reminder.reminder_id,
    }


@pytest.mark.asyncio
async def test_authenticated_intake_source_timestamps_and_idempotency(client: TestClient):
    unauth = await client.post("/api/auto/v1/crm/leads", json={"source": "web", "notes": "nope"})
    assert unauth.status == 401

    payload = {
        "source": "web",
        "notes": "showroom walk-in",
        "dealer_id": "d-7",
        "assigned_agent_id": "agt-7",
        "utm_source": "globefly",
        "utm_campaign": "sprint7",
        "channel": "web",
        "intake_key": "intake-s7-api",
    }
    first = await client.post("/api/auto/v1/crm/leads", json=payload, headers=AUTH)
    assert first.status == 201, await first.text()
    body = await first.json()
    assert body["source"] == "web"
    assert body["created_at"] > 0
    assert body["assigned_agent_id"] == "agt-7"
    assert body["metadata"]["utm_source"] == "globefly"
    assert body["metadata"]["utm_campaign"] == "sprint7"
    assert body["lead_id"]

    second = await client.post("/api/auto/v1/crm/leads", json=payload, headers=AUTH)
    assert second.status == 201
    assert (await second.json())["lead_id"] == body["lead_id"]

    fetched = await client.get(f"/api/auto/v1/crm/leads/{body['lead_id']}", headers=AUTH)
    assert fetched.status == 200
    listed = await client.get("/api/auto/v1/crm/leads", headers=AUTH)
    assert listed.status == 200
    assert any(item["lead_id"] == body["lead_id"] for item in (await listed.json())["items"])


@pytest.mark.asyncio
async def test_memory_lifecycle_conversion_pipeline_tasks_comms_closure():
    engine = auto_marketplace.crm_engine
    ids = await _run_lifecycle(engine, suffix="mem")
    metrics = await engine.metrics()
    persist = engine.leads._records()
    assert metrics["leads"] == await persist.count_leads()
    assert metrics["customers"] == await persist.count_customers()
    assert metrics["deals"] == await persist.count_deals()
    assert metrics["tasks"] == await persist.count_tasks()
    assert metrics["calls"] == await persist.count_calls()
    assert metrics["emails"] == await persist.count_emails()
    assert metrics["meetings"] == await persist.count_meetings()
    assert metrics["reminders"] == await persist.count_reminders()
    assert metrics["opportunities"] == metrics["deals"]
    assert metrics["deals_by_stage"].get("closed_won", 0) >= 1
    assert metrics["conversion"]["deals_won"] >= 1
    lost = await engine.deals.create(CRMDeal(customer_id=ids["customer_id"], amount=500))
    closed = await engine.deals.mark_lost(lost.deal_id, reason="budget")
    assert closed.stage == DealStage.CLOSED_LOST
    assert closed.win is False
    with pytest.raises(ValidationError):
        await engine.deals.mark_won(lost.deal_id)
    assert not hasattr(marketplace_store, "crm_leads")
    assert not hasattr(marketplace_store, "crm_deals")


@pytest.mark.asyncio
async def test_invalid_stage_and_closed_deal_rejected_via_api(client: TestClient):
    created = await client.post("/api/auto/v1/crm/leads", json={"notes": "stage rules"}, headers=AUTH)
    lead_id = (await created.json())["lead_id"]
    converted = await client.post(f"/api/auto/v1/crm/leads/{lead_id}/convert", json={"amount": 9000}, headers=AUTH)
    assert converted.status == 201
    deal_id = (await converted.json())["deal_id"]
    bad = await client.patch(f"/api/auto/v1/crm/deals/{deal_id}", json={"stage": "not-a-stage"}, headers=AUTH)
    assert bad.status == 400
    moved = await client.patch(f"/api/auto/v1/crm/deals/{deal_id}", json={"stage": "negotiation"}, headers=AUTH)
    assert moved.status == 200
    priced = await client.patch(f"/api/auto/v1/crm/deals/{deal_id}", json={"amount": 9100}, headers=AUTH)
    assert priced.status == 200
    won = await client.patch(f"/api/auto/v1/crm/deals/{deal_id}", json={"stage": "closed_won"}, headers=AUTH)
    assert won.status == 200, await won.text()
    body = await won.json()
    assert body["stage"] == "closed_won"
    assert body["win"] is True
    again = await client.patch(f"/api/auto/v1/crm/deals/{deal_id}", json={"stage": "closed_won"}, headers=AUTH)
    assert again.status == 200
    assert (await again.json())["amount"] == 9100
    reopen = await client.patch(f"/api/auto/v1/crm/deals/{deal_id}", json={"stage": "prospect"}, headers=AUTH)
    assert reopen.status == 400
    lose = await client.patch(f"/api/auto/v1/crm/deals/{deal_id}", json={"stage": "closed_lost"}, headers=AUTH)
    assert lose.status == 400


@pytest.mark.asyncio
async def test_api_full_lifecycle_contract_metrics_follow_up_and_gate(client: TestClient):
    lead_resp = await client.post(
        "/api/auto/v1/crm/leads",
        json={"notes": "api lifecycle", "source": "phone", "utm_source": "call-center", "intake_key": "api-life-1"},
        headers=AUTH,
    )
    assert lead_resp.status == 201
    lead_id = (await lead_resp.json())["lead_id"]
    convert = await client.post(f"/api/auto/v1/crm/leads/{lead_id}/convert", json={"amount": 15000}, headers=AUTH)
    assert convert.status == 201
    deal = await convert.json()
    deal_id = deal["deal_id"]
    customer_id = deal["customer_id"]
    convert_again = await client.post(f"/api/auto/v1/crm/leads/{lead_id}/convert", json={"amount": 2}, headers=AUTH)
    assert (await convert_again.json())["deal_id"] == deal_id

    task_resp = await client.post(
        "/api/auto/v1/crm/tasks",
        json={"title": "Prep paperwork", "customer_id": customer_id, "lead_id": lead_id, "deal_id": deal_id},
        headers=AUTH,
    )
    assert task_resp.status == 201
    task_id = (await task_resp.json())["task_id"]
    patched = await client.patch(f"/api/auto/v1/crm/tasks/{task_id}", json={"description": "docs"}, headers=AUTH)
    assert patched.status == 200
    listed_tasks = await client.get("/api/auto/v1/crm/tasks?status=pending", headers=AUTH)
    assert any(item["task_id"] == task_id for item in (await listed_tasks.json())["items"])
    completed = await client.post(f"/api/auto/v1/crm/tasks/{task_id}/complete", json={}, headers=AUTH)
    assert (await completed.json())["status"] == "completed"

    call = await client.post(
        "/api/auto/v1/crm/activities/calls",
        json={"customer_id": customer_id, "lead_id": lead_id, "deal_id": deal_id, "direction": "outbound"},
        headers=AUTH,
    )
    assert call.status == 201
    email = await client.post(
        "/api/auto/v1/crm/activities/emails",
        json={"customer_id": customer_id, "subject": "quote", "status": "logged"},
        headers=AUTH,
    )
    assert email.status == 201
    meeting = await client.post(
        "/api/auto/v1/crm/calendar/meetings",
        json={"customer_id": customer_id, "deal_id": deal_id, "title": "handover"},
        headers=AUTH,
    )
    assert meeting.status == 201
    reminder = await client.post(
        "/api/auto/v1/crm/reminders",
        json={"customer_id": customer_id, "deal_id": deal_id, "message": "follow", "remind_at": time.time() - 8},
        headers=AUTH,
    )
    assert reminder.status == 201, await reminder.text()
    reminder_id = (await reminder.json())["reminder_id"]
    await client.patch(f"/api/auto/v1/crm/reminders/{reminder_id}", json={"message": "follow-upd"}, headers=AUTH)
    done = await client.post(f"/api/auto/v1/crm/reminders/{reminder_id}/complete", json={}, headers=AUTH)
    assert done.status == 200

    timeline = await client.get(f"/api/auto/v1/crm/customers/{customer_id}/timeline", headers=AUTH)
    assert timeline.status == 200
    items = (await timeline.json())["items"]
    assert any(item.get("activity_type") == "lead_converted" for item in items)
    assert any(item.get("activity_type") == "call" for item in items)

    follow = await client.get("/api/auto/v1/crm/follow-up", headers=AUTH)
    assert follow.status == 200
    board = await follow.json()
    assert "overdue_tasks" in board
    assert "upcoming_reminders" in board or "overdue_reminders" in board

    pipeline = await client.get("/api/auto/v1/crm/pipeline", headers=AUTH)
    assert pipeline.status == 200
    priced = await client.patch(f"/api/auto/v1/crm/deals/{deal_id}", json={"amount": 14900}, headers=AUTH)
    assert priced.status == 200
    won = await client.patch(f"/api/auto/v1/crm/deals/{deal_id}", json={"stage": "closed_won"}, headers=AUTH)
    assert won.status == 200, await won.text()
    assert (await won.json())["stage"] == "closed_won"
    metrics = await client.get("/api/auto/v1/crm/metrics", headers=AUTH)
    assert metrics.status == 200
    counts = await metrics.json()
    assert counts["leads"] >= 1
    assert counts["deals"] >= 1
    assert counts["customers"] >= 1
    assert counts["tasks"] >= 1
    assert counts["calls"] >= 1
    assert counts["emails"] >= 1
    assert counts["meetings"] >= 1
    assert counts["reminders"] >= 1
    assert counts["deals_by_stage"].get("closed_won", 0) >= 1

    for method, path, payload in (
        ("POST", "/api/auto/v1/crm/leads", {"source": "web"}),
        ("POST", f"/api/auto/v1/crm/leads/{lead_id}/convert", {"amount": 1}),
        ("POST", f"/api/auto/v1/crm/deals/{deal_id}/win", {"amount": 1}),
        ("POST", "/api/auto/v1/crm/tasks", {"title": "x"}),
        ("POST", "/api/auto/v1/crm/activities/calls", {"direction": "inbound"}),
        ("POST", "/api/auto/v1/crm/reminders", {"message": "x"}),
        ("POST", "/api/auto/v1/crm/requests", {"buyer_id": "b1"}),
    ):
        resp = await client.request(method, path, json=payload)
        assert resp.status == 401, await resp.text()


@pytest.mark.asyncio
async def test_api_cross_tenant_lifecycle_isolation(client: TestClient):
    headers_a = {**AUTH, "X-Tenant-Id": "life-a"}
    headers_b = {**AUTH, "X-Tenant-Id": "life-b"}
    lead = await client.post("/api/auto/v1/crm/leads", json={"notes": "tenant-a"}, headers=headers_a)
    lead_id = (await lead.json())["lead_id"]
    converted = await client.post(f"/api/auto/v1/crm/leads/{lead_id}/convert", json={"amount": 4000}, headers=headers_a)
    deal_id = (await converted.json())["deal_id"]
    customer_id = (await converted.json())["customer_id"]
    task = await client.post(
        "/api/auto/v1/crm/tasks",
        json={"title": "a-only", "deal_id": deal_id, "customer_id": customer_id},
        headers=headers_a,
    )
    task_id = (await task.json())["task_id"]
    call = await client.post("/api/auto/v1/crm/activities/calls", json={"deal_id": deal_id, "notes": "secret"}, headers=headers_a)
    call_id = (await call.json())["call_id"]
    reminder = await client.post("/api/auto/v1/crm/reminders", json={"message": "secret", "deal_id": deal_id}, headers=headers_a)
    reminder_id = (await reminder.json())["reminder_id"]

    assert (await client.get(f"/api/auto/v1/crm/leads/{lead_id}", headers=headers_b)).status == 404
    assert (await client.get(f"/api/auto/v1/crm/deals/{deal_id}", headers=headers_b)).status == 404
    assert (await client.get(f"/api/auto/v1/crm/customers/{customer_id}", headers=headers_b)).status == 404
    assert (await client.get(f"/api/auto/v1/crm/tasks/{task_id}", headers=headers_b)).status == 404
    assert (await client.get(f"/api/auto/v1/crm/calls/{call_id}", headers=headers_b)).status == 404
    assert (await client.get(f"/api/auto/v1/crm/reminders/{reminder_id}", headers=headers_b)).status == 404
    assert (await client.patch(f"/api/auto/v1/crm/deals/{deal_id}", json={"stage": "proposal"}, headers=headers_b)).status == 404
    assert (await client.post(f"/api/auto/v1/crm/deals/{deal_id}/advance", json={}, headers=headers_b)).status == 404
    assert (await client.delete(f"/api/auto/v1/crm/tasks/{task_id}", headers=headers_b)).status == 404
    listed = await client.get("/api/auto/v1/crm/deals", headers=headers_b)
    assert all(item["deal_id"] != deal_id for item in (await listed.json())["items"])


@pytest.mark.asyncio
async def test_postgres_full_lifecycle_restart_metrics_and_isolation(postgres_crm_mode):
    await _ensure_postgres_tables()
    suffix = uuid.uuid4().hex[:12]
    tenant_a = f"life-a-{suffix}"
    tenant_b = f"life-b-{suffix}"

    bind_crm_tenant(tenant_a)
    engine = _stack(PostgresCRMPersistence())
    ids = await _run_lifecycle(engine, suffix=suffix)
    before = await crm_metrics.collect(tenant_a)
    assert before["leads"] == 1
    assert before["customers"] == 1
    assert before["deals"] == 1
    assert before["tasks"] == 1
    assert before["calls"] == 1
    assert before["emails"] == 1
    assert before["meetings"] == 1
    assert before["reminders"] == 1
    assert before["opportunities"] == before["deals"]
    assert before["deals_by_stage"].get("closed_won") == 1
    persist = engine.leads._records()
    assert before["leads"] == await persist.count_leads()
    assert before["activities"] == await persist.count_activities()

    bind_crm_tenant(tenant_b)
    other = _stack(PostgresCRMPersistence())
    other_lead = await other.leads.create(CRMLead(notes=f"b-{suffix}"))
    with pytest.raises(NotFoundError):
        await other.leads.get(ids["lead_id"])
    with pytest.raises(NotFoundError):
        await other.deals.get(ids["deal_id"])
    with pytest.raises(NotFoundError):
        await other.customers.get(ids["customer_id"])
    with pytest.raises(NotFoundError):
        await other.tasks.get(ids["task_id"])
    with pytest.raises(NotFoundError):
        await other.communications.get_call(ids["call_id"])
    with pytest.raises(NotFoundError):
        await other.calendar.get_reminder(ids["reminder_id"])
    with pytest.raises(NotFoundError):
        await other.pipeline.set_stage(ids["deal_id"], DealStage.NEGOTIATION)
    assert all(item.deal_id != ids["deal_id"] for item in await other.deals.list_deals())
    b_metrics = await crm_metrics.collect(tenant_b)
    assert b_metrics["leads"] == 1
    assert b_metrics["deals"] == 0

    from database.session import shutdown_db

    await shutdown_db()
    reset_crm_persistence()
    bind_crm_tenant(tenant_a)
    restored = _stack(PostgresCRMPersistence())
    lead = await restored.leads.get(ids["lead_id"])
    customer = await restored.customers.get(ids["customer_id"])
    deal = await restored.deals.get(ids["deal_id"])
    task = await restored.tasks.get(ids["task_id"])
    call = await restored.communications.get_call(ids["call_id"])
    email = await restored.communications.get_email(ids["email_id"])
    meeting = await restored.calendar.get_meeting(ids["meeting_id"])
    reminder = await restored.calendar.get_reminder(ids["reminder_id"])
    assert lead.status.value == "converted"
    assert lead.customer_id == ids["customer_id"]
    assert lead.metadata.get("converted_deal_id") == ids["deal_id"]
    assert lead.metadata.get("utm_source") == "globefly"
    assert customer.preferences.get("source_lead_id") == ids["lead_id"]
    assert deal.stage == DealStage.CLOSED_WON
    assert deal.customer_id == ids["customer_id"]
    assert task.status == TaskStatus.COMPLETED
    assert task.deal_id == ids["deal_id"]
    assert call.notes == suffix
    assert email.subject == f"quote-{suffix}"
    assert meeting.title == f"Drive {suffix}"
    assert reminder.status == "completed"
    view = await restored.pipeline.pipeline_view()
    assert any(item["deal_id"] == ids["deal_id"] for item in view["stages"].get("closed_won", []))
    third = await restored.pipeline.convert_lead_to_deal(ids["lead_id"], amount=99)
    assert third.deal_id == ids["deal_id"]
    after = await crm_metrics.collect(tenant_a)
    assert after["leads"] == before["leads"]
    assert after["deals"] == before["deals"]
    assert after["tasks"] == before["tasks"]
    assert after["calls"] == before["calls"]
    assert after["reminders"] == before["reminders"]
    assert after["deals_by_stage"].get("closed_won") == 1

    bind_crm_tenant(tenant_b)
    restored_b = _stack(PostgresCRMPersistence())
    assert (await restored_b.leads.get(other_lead.lead_id)).notes == f"b-{suffix}"
    with pytest.raises(NotFoundError):
        await restored_b.deals.get(ids["deal_id"])
