"""Sprint 8 — CRM automation engine, durable follow-ups, priority, and manager queue."""

from __future__ import annotations

import time
import uuid
from datetime import datetime, timezone

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.auto_marketplace import auto_marketplace
from applications.auto_marketplace.activities.service import ActivityService
from applications.auto_marketplace.api.register import register_auto_marketplace_routes
from applications.auto_marketplace.calendar.service import CalendarService
from applications.auto_marketplace.crm.automation import (
    FollowUpActionStatus,
    calculate_priority,
    classify_follow_up_status,
    parse_utc_timestamp,
)
from applications.auto_marketplace.crm.engine import CRMEngine
from applications.auto_marketplace.crm.models import (
    CRMLead,
    CRMLeadStatus,
    DealStage,
    InteractionType,
    Reminder,
    TaskPriority,
)
from applications.auto_marketplace.crm.persistence import PostgresCRMPersistence, reset_crm_persistence
from applications.auto_marketplace.crm.tenant import bind_crm_tenant
from applications.auto_marketplace.customers.profile_service import CustomerProfileService
from applications.auto_marketplace.deals.service import DealService
from applications.auto_marketplace.leads.service import LeadService
from applications.auto_marketplace.sales_pipeline.service import SalesPipelineEngine
from applications.auto_marketplace.shared.exceptions import NotFoundError, ValidationError
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
        tasks=TaskService(persistence=persist),
        calendar=CalendarService(persistence=persist),
    )


def test_priority_engine_is_deterministic():
    now = 1_700_000_000.0
    assert calculate_priority(now=now, due_at=now + 86400) == TaskPriority.LOW
    assert calculate_priority(now=now, due_at=now + 60) == TaskPriority.NORMAL
    assert calculate_priority(now=now, due_at=now - 7200) == TaskPriority.HIGH
    assert calculate_priority(now=now, due_at=now - 2 * 86400) == TaskPriority.HIGH
    assert calculate_priority(now=now, due_at=now - 8 * 86400) == TaskPriority.URGENT
    assert calculate_priority(now=now, due_at=now + 86400, deal_stage=DealStage.APPROVAL) == TaskPriority.URGENT
    assert calculate_priority(now=now, due_at=now - 10, lead_status=CRMLeadStatus.NEW) == TaskPriority.HIGH
    assert calculate_priority(now=now, due_at=now + 86400, explicit=TaskPriority.HIGH) == TaskPriority.HIGH


def test_utc_timestamp_parsing_and_status_classification():
    ts = parse_utc_timestamp("2026-08-24T12:00:00Z")
    assert ts == datetime(2026, 8, 24, 12, tzinfo=timezone.utc).timestamp()
    naive = parse_utc_timestamp("2026-08-24T12:00:00")
    assert naive == ts
    reminder = Reminder(trigger_at=ts, status="pending")
    assert classify_follow_up_status(reminder, now=ts + 1) == FollowUpActionStatus.OVERDUE
    assert classify_follow_up_status(reminder, now=ts - 10) == FollowUpActionStatus.DUE
    assert classify_follow_up_status(reminder, now=ts - 7200) == FollowUpActionStatus.UPCOMING


@pytest.mark.asyncio
async def test_follow_up_schedule_reschedule_complete_cancel_and_due():
    engine = auto_marketplace.crm_engine
    lead = await engine.leads.create(CRMLead(notes="hot buyer"))
    now = time.time()
    scheduled = await engine.automation.schedule_follow_up(
        lead_id=lead.lead_id,
        action_type="call",
        due_at=now - 120,
        source="test",
        idempotency_key="fu-call-1",
    )
    again = await engine.automation.schedule_follow_up(
        lead_id=lead.lead_id,
        action_type="call",
        due_at=now + 999,
        idempotency_key="fu-call-1",
    )
    assert again["follow_up_id"] == scheduled["follow_up_id"]
    assert scheduled["status"] == "overdue"
    due = await engine.automation.get_due_follow_ups(now=now)
    overdue = await engine.automation.get_overdue_follow_ups(now=now)
    assert any(item["follow_up_id"] == scheduled["follow_up_id"] for item in due)
    assert any(item["follow_up_id"] == scheduled["follow_up_id"] for item in overdue)

    later = now + 7200
    moved = await engine.automation.reschedule_follow_up(scheduled["follow_up_id"], due_at=later, now=now)
    assert moved["status"] == "upcoming"
    nxt = await engine.automation.next_action(lead_id=lead.lead_id, now=now)
    assert nxt is not None
    assert nxt["next_action_type"] == "call"
    assert nxt["next_action_at"] == later
    restored_lead = await engine.leads.get(lead.lead_id)
    assert restored_lead.metadata["next_action"]["follow_up_id"] == scheduled["follow_up_id"]

    completed = await engine.automation.complete_follow_up(scheduled["follow_up_id"], now=now)
    assert completed["status"] == "completed"
    same = await engine.automation.complete_follow_up(scheduled["follow_up_id"], now=now)
    assert same["follow_up_id"] == completed["follow_up_id"]

    other = await engine.automation.schedule_follow_up(
        lead_id=lead.lead_id, action_type="email", due_at=now + 10, source="test"
    )
    cancelled = await engine.automation.cancel_follow_up(other["follow_up_id"], now=now)
    assert cancelled["status"] == "cancelled"


@pytest.mark.asyncio
async def test_automation_idempotency_timeline_and_closed_safety():
    engine = auto_marketplace.crm_engine
    lead = await engine.leads.create(CRMLead(notes="pipeline"))
    now = time.time()
    follow = await engine.automation.schedule_follow_up(
        lead_id=lead.lead_id, action_type="task", due_at=now - 30, source="automation"
    )
    first = await engine.automation.evaluate_due_actions(now=now)
    second = await engine.automation.evaluate_due_actions(now=now)
    assert first["tasks_created"] == 1
    assert second["tasks_created"] == 0
    tasks = await engine.tasks.list_tasks(lead_id=lead.lead_id)
    assert len(tasks) == 1
    assert tasks[0].metadata.get("automation_reminder_id") == follow["follow_up_id"]

    types = {item.interaction_type for item in await engine.activities.list_activities(lead_id=lead.lead_id)}
    assert InteractionType.FOLLOW_UP_SCHEDULED in types
    assert InteractionType.AUTOMATION_TASK_CREATED in types
    scheduled_events = await engine.activities.list_activities(
        lead_id=lead.lead_id, activity_type=InteractionType.FOLLOW_UP_SCHEDULED
    )
    auto_events = await engine.activities.list_activities(
        lead_id=lead.lead_id, activity_type=InteractionType.AUTOMATION_TASK_CREATED
    )
    assert len(scheduled_events) == 1
    assert len(auto_events) == 1

    deal = await engine.pipeline.convert_lead_to_deal(lead.lead_id, amount=8000)
    await engine.deals.mark_won(deal.deal_id)
    with pytest.raises(ValidationError):
        await engine.automation.schedule_follow_up(lead_id=lead.lead_id, action_type="call", due_at=now + 60)

    open_follow = await engine.automation.schedule_follow_up(
        lead_id=(await engine.leads.create(CRMLead(notes="still open"))).lead_id,
        action_type="call",
        due_at=now - 5,
    )
    closed_lead = await engine.leads.create(CRMLead(notes="will lose"))
    pending = await engine.automation.schedule_follow_up(
        lead_id=closed_lead.lead_id, action_type="email", due_at=now - 5
    )
    await engine.leads.set_status(closed_lead.lead_id, CRMLeadStatus.LOST)
    result = await engine.automation.evaluate_due_actions(now=now)
    assert result["cancelled_closed"] >= 1
    cancelled = await engine.automation.get_follow_up(pending["follow_up_id"], now=now)
    assert cancelled["status"] == "cancelled"
    still = await engine.automation.get_follow_up(open_follow["follow_up_id"], now=now)
    assert still["status"] in {"due", "overdue"}


@pytest.mark.asyncio
async def test_manager_queue_orders_urgent_overdue_first():
    engine = auto_marketplace.crm_engine
    now = time.time()
    lead = await engine.leads.create(CRMLead(notes="queue"))
    await engine.automation.schedule_follow_up(
        lead_id=lead.lead_id, action_type="email", due_at=now + 8000, idempotency_key="q-up", source="test"
    )
    await engine.automation.schedule_follow_up(
        lead_id=lead.lead_id, action_type="meeting", due_at=now + 30, idempotency_key="q-due", source="test"
    )
    await engine.automation.schedule_follow_up(
        lead_id=lead.lead_id, action_type="call", due_at=now - 4000, idempotency_key="q-high", source="test"
    )
    await engine.automation.schedule_follow_up(
        lead_id=lead.lead_id,
        action_type="reminder",
        due_at=now - 8 * 86400,
        idempotency_key="q-urgent",
        source="test",
    )
    queue = await engine.automation.get_action_queue(now=now)
    assert queue["items"][0]["status"] == "overdue"
    assert queue["items"][0]["priority"] == "urgent"
    assert queue["items"][0]["action_type"] == "reminder"
    assert "overdue_seconds" in queue["items"][0]
    assert {item["entity_type"] for item in queue["items"]} == {"follow_up"}


@pytest.mark.asyncio
async def test_automation_api_security_queue_and_tenant_isolation(client: TestClient):
    unauth = await client.post("/api/auto/v1/crm/follow-ups", json={"action_type": "call"})
    assert unauth.status == 401
    unauth_eval = await client.post("/api/auto/v1/crm/automation/evaluate", json={})
    assert unauth_eval.status == 401

    lead = await client.post("/api/auto/v1/crm/leads", json={"notes": "api fu"}, headers=AUTH)
    lead_id = (await lead.json())["lead_id"]
    now = time.time()
    created = await client.post(
        "/api/auto/v1/crm/follow-ups",
        json={"lead_id": lead_id, "action_type": "call", "due_at": now - 20, "source": "api"},
        headers=AUTH,
    )
    assert created.status == 201, await created.text()
    follow_id = (await created.json())["follow_up_id"]
    listed = await client.get("/api/auto/v1/crm/follow-ups?overdue=true", headers=AUTH)
    assert listed.status == 200
    assert any(item["follow_up_id"] == follow_id for item in (await listed.json())["items"])
    due = await client.get("/api/auto/v1/crm/follow-ups?due=true", headers=AUTH)
    assert due.status == 200
    moved = await client.patch(
        f"/api/auto/v1/crm/follow-ups/{follow_id}",
        json={"due_at": datetime.fromtimestamp(now + 90, tz=timezone.utc).isoformat()},
        headers=AUTH,
    )
    assert moved.status == 200
    evaluated = await client.post("/api/auto/v1/crm/automation/evaluate", json={}, headers=AUTH)
    assert evaluated.status == 200
    queue = await client.get("/api/auto/v1/crm/automation/queue", headers=AUTH)
    assert queue.status == 200
    body = await queue.json()
    assert "items" in body
    nxt = await client.get(f"/api/auto/v1/crm/leads/{lead_id}/next-action", headers=AUTH)
    assert nxt.status == 200
    payload = await nxt.json()
    assert "next_best_action" in payload
    assert "next_action" in payload

    headers_a = {**AUTH, "X-Tenant-Id": "auto-a"}
    headers_b = {**AUTH, "X-Tenant-Id": "auto-b"}
    lead_a = await client.post("/api/auto/v1/crm/leads", json={"notes": "tenant a"}, headers=headers_a)
    lead_a_id = (await lead_a.json())["lead_id"]
    owned = await client.post(
        "/api/auto/v1/crm/follow-ups",
        json={"lead_id": lead_a_id, "action_type": "email", "due_at": now - 15},
        headers=headers_a,
    )
    assert owned.status == 201
    owned_id = (await owned.json())["follow_up_id"]
    hidden = await client.get(f"/api/auto/v1/crm/follow-ups/{owned_id}", headers=headers_b)
    assert hidden.status == 404
    mutate = await client.patch(
        f"/api/auto/v1/crm/follow-ups/{owned_id}", json={"due_at": now + 10}, headers=headers_b
    )
    assert mutate.status == 404
    queue_b = await client.get("/api/auto/v1/crm/automation/queue", headers=headers_b)
    assert all(item["follow_up_id"] != owned_id for item in (await queue_b.json())["items"])
    eval_b = await client.post("/api/auto/v1/crm/automation/evaluate", json={}, headers=headers_b)
    assert eval_b.status == 200
    still = await client.get(f"/api/auto/v1/crm/follow-ups/{owned_id}", headers=headers_a)
    assert still.status == 200
    done = await client.post(f"/api/auto/v1/crm/follow-ups/{follow_id}/complete", json={}, headers=AUTH)
    assert done.status == 200
    cancel = await client.post(f"/api/auto/v1/crm/follow-ups/{owned_id}/cancel", json={}, headers=headers_a)
    assert cancel.status == 200


@pytest.mark.asyncio
async def test_postgres_follow_up_restart_and_tenant_isolation(postgres_crm_mode):
    await _ensure_postgres_tables()
    suffix = uuid.uuid4().hex[:12]
    tenant_a = f"auto-a-{suffix}"
    tenant_b = f"auto-b-{suffix}"
    now = time.time()

    bind_crm_tenant(tenant_a)
    engine = _stack(PostgresCRMPersistence())
    lead = await engine.leads.create(CRMLead(notes=f"auto-{suffix}"))
    scheduled = await engine.automation.schedule_follow_up(
        lead_id=lead.lead_id,
        action_type="call",
        due_at=now - 45,
        source="postgres",
        idempotency_key=f"pg-{suffix}",
    )
    await engine.automation.evaluate_due_actions(now=now)
    first_tasks = await engine.tasks.list_tasks(lead_id=lead.lead_id)
    assert len(first_tasks) == 1

    bind_crm_tenant(tenant_b)
    other = _stack(PostgresCRMPersistence())
    with pytest.raises(NotFoundError):
        await other.automation.get_follow_up(scheduled["follow_up_id"])
    other_lead = await other.leads.create(CRMLead(notes=f"b-{suffix}"))
    await other.automation.evaluate_due_actions(now=now)
    assert await other.tasks.list_tasks(lead_id=lead.lead_id) == []
    await other.automation.schedule_follow_up(lead_id=other_lead.lead_id, action_type="email", due_at=now + 50)

    from database.session import shutdown_db

    await shutdown_db()
    reset_crm_persistence()
    bind_crm_tenant(tenant_a)
    restored = _stack(PostgresCRMPersistence())
    loaded = await restored.automation.get_follow_up(scheduled["follow_up_id"], now=now)
    assert loaded["action_type"] == "call"
    assert loaded["source"] == "postgres"
    assert loaded["status"] == "overdue"
    nxt = await restored.automation.next_action(lead_id=lead.lead_id, now=now)
    assert nxt is not None
    assert nxt["follow_up_id"] == scheduled["follow_up_id"]
    again = await restored.automation.evaluate_due_actions(now=now)
    assert again["tasks_created"] == 0
    tasks = await restored.tasks.list_tasks(lead_id=lead.lead_id)
    assert len(tasks) == 1
    third = await restored.automation.schedule_follow_up(
        lead_id=lead.lead_id,
        action_type="call",
        due_at=now + 10,
        idempotency_key=f"pg-{suffix}",
    )
    assert third["follow_up_id"] == scheduled["follow_up_id"]
    bind_crm_tenant(tenant_b)
    restored_b = _stack(PostgresCRMPersistence())
    with pytest.raises(NotFoundError):
        await restored_b.automation.get_follow_up(scheduled["follow_up_id"])
