"""Sprint 10 — CRM sales execution: priority, SLA, escalation, manager queue."""

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
from applications.auto_marketplace.crm.automation import DUE_WINDOW_SECONDS
from applications.auto_marketplace.crm.engine import CRMEngine
from applications.auto_marketplace.crm.execution import (
    SLA_BREACH_SECONDS,
    SLAStatus,
    classify_priority,
    classify_sla,
)
from applications.auto_marketplace.crm.intelligence import HOT_THRESHOLD, STALE_SECONDS
from applications.auto_marketplace.crm.models import (
    CRMLead,
    CRMTask,
    DealStage,
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
        "leads": len(await engine.leads.list_leads()),
        "deals": len(await engine.deals.list_deals()),
        "tasks": len(await engine.tasks.list_tasks()),
        "activities": len(await engine.activities.list_activities()),
        "follow_ups": len(await engine.automation.list_follow_ups()),
    }


async def _hot_lead(engine: CRMEngine, *, now: float, suffix: str = "hot") -> CRMLead:
    lead = await engine.leads.create(
        CRMLead(
            source=LeadSource.REFERRAL,
            vehicle_id=f"veh-{suffix}",
            notes=suffix,
            assigned_agent_id="agt-hot",
        )
    )
    await engine.calendar.schedule_meeting(
        Meeting(lead_id=lead.lead_id, title="done", status="completed", completed=True)
    )
    await engine.communications.log_call(PhoneCall(lead_id=lead.lead_id, status="completed"))
    await engine.automation.schedule_follow_up(
        lead_id=lead.lead_id, action_type="call", due_at=now + 7200, idempotency_key=f"hot-{suffix}"
    )
    return lead


def test_sla_classification_is_deterministic():
    now = 1_800_000_000.0
    assert classify_sla(now=now, due_at=now + 7200, stale=False, last_activity_age=0).value == "on_time"
    assert classify_sla(now=now, due_at=now + 60, stale=False, last_activity_age=0).value == "due_soon"
    assert now + 60 <= now + DUE_WINDOW_SECONDS
    assert classify_sla(now=now, due_at=now - 120, stale=False, last_activity_age=0).value == "overdue"
    assert classify_sla(now=now, due_at=now - SLA_BREACH_SECONDS - 1, stale=False, last_activity_age=0).value == "breached"
    assert classify_sla(now=now, due_at=None, stale=True, last_activity_age=STALE_SECONDS).value == "breached"
    first = classify_sla(now=now, due_at=now - 10, stale=False, last_activity_age=0)
    second = classify_sla(now=now, due_at=now - 10, stale=False, last_activity_age=0)
    assert first == second == SLAStatus.OVERDUE


def test_priority_labels_are_explainable():
    assert classify_priority(80, sla=SLAStatus.ON_TIME, reasons=["HOT_LEAD", "HIGH_SCORE"]).value == "critical"
    assert classify_priority(10, sla=SLAStatus.BREACHED, reasons=["SLA_BREACHED", "HOT_LEAD"]).value == "critical"
    assert classify_priority(10, sla=SLAStatus.BREACHED, reasons=["SLA_BREACHED"]).value == "high"
    assert classify_priority(25, sla=SLAStatus.ON_TIME, reasons=["DEAL_REQUIRES_ACTION"]).value == "medium"


@pytest.mark.asyncio
async def test_priority_reason_codes_and_nba_automation_integration():
    engine = auto_marketplace.crm_engine
    now = time.time()
    lead = await _hot_lead(engine, now=now, suffix="codes")
    intel = await engine.intelligence.lead_intelligence(lead.lead_id, now=now)
    assert intel["temperature"] == "hot"
    assert intel["score"] >= HOT_THRESHOLD
    nxt = await engine.automation.next_action(lead_id=lead.lead_id, now=now)
    assert nxt is not None
    follow = await engine.automation.reschedule_follow_up(nxt["follow_up_id"], due_at=now - 1800, now=now)
    item = await engine.execution.evaluate(lead_id=lead.lead_id, now=now)
    assert "FOLLOW_UP_OVERDUE" in item["reason_codes"]
    assert "HOT_LEAD" in item["reason_codes"]
    assert "HIGH_SCORE" in item["reason_codes"]
    assert item["recommended_action"] == (await engine.intelligence.next_best_action(lead_id=lead.lead_id, now=now))["action"]
    assert item["due_at"] == follow["due_at"] or item["due_at"] is not None
    assert item["sla_status"] == "overdue"
    assert item["overdue"] is True
    assert item["escalation_level"] == "manager"
    assert "FOLLOW_UP_OVERDUE" in item["escalation_reasons"]
    assert item["owner_id"] == "agt-hot"
    again = await engine.execution.evaluate(lead_id=lead.lead_id, now=now)
    assert again == item

    task_lead = await engine.leads.create(CRMLead(notes="task-overdue", assigned_agent_id="agt-task"))
    await engine.tasks.create(CRMTask(lead_id=task_lead.lead_id, title="late", due_at=now - 90))
    task_item = await engine.execution.evaluate(lead_id=task_lead.lead_id, now=now)
    assert "TASK_OVERDUE" in task_item["reason_codes"]
    assert task_item["recommended_action"] == "COMPLETE_OVERDUE_TASK"
    assert task_item["sla_status"] in {"overdue", "breached"}


@pytest.mark.asyncio
async def test_sla_states_on_crm_follow_ups():
    engine = auto_marketplace.crm_engine
    now = time.time()
    on_time = await engine.leads.create(CRMLead(notes="on-time"))
    await engine.automation.schedule_follow_up(
        lead_id=on_time.lead_id, action_type="email", due_at=now + 7200, idempotency_key="sla-on"
    )
    due_soon = await engine.leads.create(CRMLead(notes="due-soon"))
    await engine.automation.schedule_follow_up(
        lead_id=due_soon.lead_id, action_type="email", due_at=now + 90, idempotency_key="sla-soon"
    )
    overdue = await engine.leads.create(CRMLead(notes="overdue"))
    await engine.automation.schedule_follow_up(
        lead_id=overdue.lead_id, action_type="call", due_at=now - 300, idempotency_key="sla-over"
    )
    breached = await engine.leads.create(CRMLead(notes="breached"))
    await engine.automation.schedule_follow_up(
        lead_id=breached.lead_id, action_type="call", due_at=now - SLA_BREACH_SECONDS - 10, idempotency_key="sla-br"
    )
    assert (await engine.execution.evaluate(lead_id=on_time.lead_id, now=now))["sla_status"] == "on_time"
    assert (await engine.execution.evaluate(lead_id=due_soon.lead_id, now=now))["sla_status"] == "due_soon"
    over = await engine.execution.evaluate(lead_id=overdue.lead_id, now=now)
    assert over["sla_status"] == "overdue"
    assert over["escalation_level"] in {"attention", "manager", "critical"}
    br = await engine.execution.evaluate(lead_id=breached.lead_id, now=now)
    assert br["sla_status"] == "breached"
    assert "SLA_BREACHED" in br["reason_codes"]
    assert br["escalation_level"] in {"manager", "critical"}


@pytest.mark.asyncio
async def test_manager_queue_ordering_filters_and_closed_deal_safety():
    engine = auto_marketplace.crm_engine
    now = time.time()
    hot = await _hot_lead(engine, now=now, suffix="queue")
    nxt = await engine.automation.next_action(lead_id=hot.lead_id, now=now)
    assert nxt is not None
    await engine.automation.reschedule_follow_up(nxt["follow_up_id"], due_at=now - SLA_BREACH_SECONDS - 50, now=now)
    quiet = await engine.leads.create(CRMLead(notes="quiet", assigned_agent_id="agt-quiet"))
    await engine.automation.schedule_follow_up(
        lead_id=quiet.lead_id, action_type="email", due_at=now + 8000, idempotency_key="quiet-fu"
    )
    stale_lead = await engine.leads.create(CRMLead(notes="stale-deal"))
    stale_deal = await engine.pipeline.convert_lead_to_deal(stale_lead.lead_id, amount=22000)
    later = now + STALE_SECONDS + 120
    won_lead = await engine.leads.create(CRMLead(notes="won"))
    won = await engine.pipeline.convert_lead_to_deal(won_lead.lead_id, amount=5000)
    closed = await engine.deals.mark_won(won.deal_id)
    assert closed.stage == DealStage.CLOSED_WON

    before = await _counts(engine)
    first = await engine.execution.queue(now=now)
    second = await engine.execution.queue(now=now)
    assert first["items"] == second["items"]
    assert first["summary"] == second["summary"]
    assert await _counts(engine) == before
    ids = [item["entity_id"] for item in first["items"]]
    assert hot.lead_id in ids
    assert won.deal_id not in ids
    assert won_lead.lead_id not in ids
    assert quiet.lead_id in ids
    assert ids.index(hot.lead_id) < ids.index(quiet.lead_id)
    hot_item = next(item for item in first["items"] if item["entity_id"] == hot.lead_id)
    assert hot_item["escalation_level"] in {"manager", "critical"}
    assert hot_item["priority"] in {"high", "critical"}
    assert hot_item["sla_status"] == "breached"

    owned = await engine.execution.queue(now=now, owner="agt-hot")
    assert owned["items"]
    assert all(item["owner_id"] == "agt-hot" for item in owned["items"])
    overdue = await engine.execution.queue(now=now, overdue=True)
    assert overdue["items"]
    assert all(item["overdue"] is True for item in overdue["items"])
    breached = await engine.execution.queue(now=now, sla_status="breached")
    assert all(item["sla_status"] == "breached" for item in breached["items"])
    leads_only = await engine.execution.queue(now=now, entity_type="lead")
    assert all(item["entity_type"] == "lead" for item in leads_only["items"])
    hot_only = await engine.execution.queue(now=now, temperature="hot")
    assert all(item["temperature"] == "hot" for item in hot_only["items"])
    crit = await engine.execution.queue(now=now, escalation_level=hot_item["escalation_level"])
    assert all(item["escalation_level"] == hot_item["escalation_level"] for item in crit["items"])

    closed_exec = await engine.execution.deal_execution(won.deal_id, now=now)
    assert closed_exec["active"] is False
    assert closed_exec["overdue"] is False
    assert closed_exec["recommended_action"] == "NO_ACTION"
    assert closed_exec["escalation_level"] == "none"
    assert (await engine.deals.get(won.deal_id)).stage == DealStage.CLOSED_WON
    stale_item = await engine.execution.deal_execution(stale_deal.deal_id, now=later)
    assert stale_item["stale"] is True
    assert "STALE_OPPORTUNITY" in stale_item["reason_codes"]
    later_q = await engine.execution.queue(now=later)
    assert later_q["summary"]["stale_opportunities"] >= 1
    assert first["summary"]["overdue"] >= 1


@pytest.mark.asyncio
async def test_execution_api_auth_tenant_isolation_and_dashboard(client: TestClient):
    unauth = await client.get("/api/auto/v1/crm/execution")
    assert unauth.status == 401
    unauth_q = await client.get("/api/auto/v1/crm/execution/queue")
    assert unauth_q.status == 401
    unauth_l = await client.get("/api/auto/v1/crm/leads/missing/execution")
    assert unauth_l.status == 401

    created = await client.post(
        "/api/auto/v1/crm/leads",
        json={"notes": "exec-api", "source": "web", "assigned_agent_id": "agt-api"},
        headers=AUTH,
    )
    assert created.status == 201
    lead_id = (await created.json())["lead_id"]
    before = await client.get("/api/auto/v1/crm/metrics", headers=AUTH)
    before_body = await before.json()
    detail = await client.get(f"/api/auto/v1/crm/leads/{lead_id}/execution", headers=AUTH)
    assert detail.status == 200
    payload = await detail.json()
    assert payload["recommended_action"]
    assert payload["sla_status"] in {"on_time", "due_soon", "overdue", "breached"}
    again = await client.get(f"/api/auto/v1/crm/leads/{lead_id}/execution", headers=AUTH)
    second = await again.json()
    payload.pop("derived_at")
    second.pop("derived_at")
    assert second == payload
    after = await client.get("/api/auto/v1/crm/metrics", headers=AUTH)
    after_body = await after.json()
    for key in ("leads", "deals", "tasks", "activities", "reminders"):
        assert after_body[key] == before_body[key]
    summary = await client.get("/api/auto/v1/crm/execution", headers=AUTH)
    assert summary.status == 200
    board = await summary.json()
    assert "overdue" in board
    assert "sla_breaches" in board
    queue = await client.get("/api/auto/v1/crm/execution/queue?overdue=true", headers=AUTH)
    assert queue.status == 200
    body = await queue.json()
    assert "items" in body
    assert "summary" in body

    headers_a = {**AUTH, "X-Tenant-Id": "exec-a"}
    headers_b = {**AUTH, "X-Tenant-Id": "exec-b"}
    lead_a = await client.post("/api/auto/v1/crm/leads", json={"notes": "tenant-a", "source": "referral"}, headers=headers_a)
    lead_a_id = (await lead_a.json())["lead_id"]
    hidden = await client.get(f"/api/auto/v1/crm/leads/{lead_a_id}/execution", headers=headers_b)
    assert hidden.status == 404
    queue_b = await client.get("/api/auto/v1/crm/execution/queue", headers=headers_b)
    assert all(item.get("lead_id") != lead_a_id for item in (await queue_b.json())["items"])
    sum_b = await client.get("/api/auto/v1/crm/execution", headers=headers_b)
    visible = await client.get(f"/api/auto/v1/crm/leads/{lead_a_id}/execution", headers=headers_a)
    assert visible.status == 200
    assert (await visible.json())["tenant_id"] == "exec-a"
    assert (await sum_b.json())["tenant_id"] == "exec-b"
    dash = await executive_dashboard_service.get_dashboard(DashboardRole.SALES_MANAGER)
    types = {item["type"] for item in dash.widgets}
    assert "sales_execution" in types
    assert "sales_intelligence" in types


@pytest.mark.asyncio
async def test_postgres_execution_restart_and_tenant_isolation(postgres_crm_mode):
    await _ensure_postgres_tables()
    suffix = uuid.uuid4().hex[:12]
    tenant_a = f"exec-a-{suffix}"
    tenant_b = f"exec-b-{suffix}"
    now = time.time()

    bind_crm_tenant(tenant_a)
    engine = _stack(PostgresCRMPersistence())
    lead = await engine.leads.create(
        CRMLead(source=LeadSource.REFERRAL, vehicle_id=f"v-{suffix}", notes=f"exec-{suffix}", assigned_agent_id="agt-a")
    )
    await engine.automation.schedule_follow_up(
        lead_id=lead.lead_id,
        action_type="call",
        due_at=now - 400,
        source="exec",
        idempotency_key=f"pg-{suffix}",
    )
    first = await engine.execution.evaluate(lead_id=lead.lead_id, now=now)
    queue_a = await engine.execution.queue(now=now)
    assert first["tenant_id"] == tenant_a
    assert any(item["lead_id"] == lead.lead_id for item in queue_a["items"])

    bind_crm_tenant(tenant_b)
    other = _stack(PostgresCRMPersistence())
    with pytest.raises(NotFoundError):
        await other.execution.lead_execution(lead.lead_id, now=now)
    other_queue = await other.execution.queue(now=now)
    assert all(item.get("lead_id") != lead.lead_id for item in other_queue["items"])
    other_sum = await other.execution.summary(now=now)
    assert other_sum["tenant_id"] == tenant_b

    from database.session import shutdown_db

    await shutdown_db()
    reset_crm_persistence()
    bind_crm_tenant(tenant_a)
    restored = _stack(PostgresCRMPersistence())
    loaded = await restored.execution.evaluate(lead_id=lead.lead_id, now=now)
    assert loaded["priority"] == first["priority"]
    assert loaded["sla_status"] == first["sla_status"]
    assert loaded["escalation_level"] == first["escalation_level"]
    assert loaded["reason_codes"] == first["reason_codes"]
    assert loaded["recommended_action"] == first["recommended_action"]
    restored_queue = await restored.execution.queue(now=now)
    restored_ids = [item["execution_id"] for item in restored_queue["items"]]
    original_ids = [item["execution_id"] for item in queue_a["items"]]
    assert restored_ids == original_ids
    assert restored_queue["summary"] == queue_a["summary"]
