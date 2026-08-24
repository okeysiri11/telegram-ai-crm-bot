"""Sprint 9 — CRM sales intelligence: scoring, temperature, NBA, stale detection."""

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
from applications.auto_marketplace.crm.intelligence import (
    HOT_THRESHOLD,
    STALE_SECONDS,
    WARM_THRESHOLD,
    classify_temperature,
)
from applications.auto_marketplace.crm.models import (
    CRMDeal,
    CRMLead,
    CRMLeadStatus,
    CRMTask,
    CustomerProfile,
    DealStage,
    EmailMessage,
    LeadSource,
    Meeting,
    PhoneCall,
)
from applications.auto_marketplace.crm.persistence import PostgresCRMPersistence, reset_crm_persistence
from applications.auto_marketplace.crm.tenant import bind_crm_tenant
from applications.auto_marketplace.customers.profile_service import CustomerProfileService
from applications.auto_marketplace.deals.service import DealService
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
        "calls": len(await engine.communications.list_calls()),
        "emails": len(await engine.communications.list_emails()),
        "meetings": len(await engine.calendar.list_meetings()),
        "reminders": len(await engine.calendar.list_reminders()),
        "follow_ups": len(await engine.automation.list_follow_ups()),
    }


def test_temperature_thresholds_are_centralized():
    assert classify_temperature(HOT_THRESHOLD, active=True).value == "hot"
    assert classify_temperature(WARM_THRESHOLD, active=True).value == "warm"
    assert classify_temperature(WARM_THRESHOLD - 1, active=True).value == "cold"
    assert classify_temperature(100, active=False).value == "cold"


@pytest.mark.asyncio
async def test_score_is_bounded_deterministic_and_explainable():
    engine = auto_marketplace.crm_engine
    now = time.time()
    lead = await engine.leads.create(CRMLead(source=LeadSource.REFERRAL, vehicle_id="veh-1", notes="score"))
    first = await engine.intelligence.calculate_score(lead_id=lead.lead_id, now=now)
    second = await engine.intelligence.explain_score(lead_id=lead.lead_id, now=now)
    assert 0 <= first["score"] <= 100
    assert first["score"] == second["score"]
    assert first["temperature"] == second["temperature"]
    assert first["factors"] == second["factors"]
    assert first["next_best_action"] == second["next_best_action"]
    assert all("code" in item and "impact" in item and "reason" in item for item in first["factors"])
    assert [item["code"] for item in first["factors"]] == sorted(item["code"] for item in first["factors"])
    stored = await engine.leads.get(lead.lead_id)
    assert stored.status == CRMLeadStatus.NEW
    assert stored.score == lead.score


@pytest.mark.asyncio
async def test_positive_activity_and_overdue_penalties_change_score():
    engine = auto_marketplace.crm_engine
    now = time.time()
    lead = await engine.leads.create(CRMLead(source=LeadSource.WEB, notes="activity"))
    baseline = await engine.intelligence.calculate_score(lead_id=lead.lead_id, now=now)
    await engine.calendar.schedule_meeting(
        Meeting(lead_id=lead.lead_id, title="Showroom", status="completed", completed=True)
    )
    await engine.communications.log_call(PhoneCall(lead_id=lead.lead_id, status="completed"))
    boosted = await engine.intelligence.calculate_score(lead_id=lead.lead_id, now=now)
    assert boosted["score"] > baseline["score"]
    codes = {item["code"] for item in boosted["factors"]}
    assert "completed_meeting" in codes
    assert "completed_call" in codes

    follow = await engine.automation.schedule_follow_up(
        lead_id=lead.lead_id, action_type="call", due_at=now + 3600, idempotency_key="intel-fu"
    )
    scheduled = await engine.intelligence.calculate_score(lead_id=lead.lead_id, now=now)
    await engine.automation.reschedule_follow_up(follow["follow_up_id"], due_at=now - 7200, now=now)
    overdue = await engine.intelligence.calculate_score(lead_id=lead.lead_id, now=now)
    assert overdue["score"] < scheduled["score"]
    assert any(item["code"] == "overdue_follow_up" and item["impact"] < 0 for item in overdue["factors"])

    task_lead = await engine.leads.create(CRMLead(notes="task penalty"))
    before_task = await engine.intelligence.calculate_score(lead_id=task_lead.lead_id, now=now)
    await engine.tasks.create(CRMTask(lead_id=task_lead.lead_id, title="overdue call", due_at=now - 1800))
    after_task = await engine.intelligence.calculate_score(lead_id=task_lead.lead_id, now=now)
    assert after_task["score"] < before_task["score"]
    assert any(item["code"] == "overdue_task" and item["impact"] < 0 for item in after_task["factors"])


@pytest.mark.asyncio
async def test_hot_warm_cold_classification_and_next_best_action():
    engine = auto_marketplace.crm_engine
    now = time.time()
    hot_lead = await engine.leads.create(
        CRMLead(source=LeadSource.REFERRAL, vehicle_id="hot-car", notes="hot")
    )
    await engine.calendar.schedule_meeting(
        Meeting(lead_id=hot_lead.lead_id, title="handover", status="completed", completed=True)
    )
    await engine.communications.log_call(PhoneCall(lead_id=hot_lead.lead_id, status="completed"))
    await engine.automation.schedule_follow_up(
        lead_id=hot_lead.lead_id, action_type="email", due_at=now + 7200, idempotency_key="hot-fu"
    )
    hot = await engine.intelligence.lead_intelligence(hot_lead.lead_id, now=now)
    assert hot["temperature"] == "hot"
    assert hot["score"] >= HOT_THRESHOLD

    warm_lead = await engine.leads.create(CRMLead(source=LeadSource.WEB, vehicle_id="warm-car", notes="warm"))
    await engine.automation.schedule_follow_up(
        lead_id=warm_lead.lead_id, action_type="call", due_at=now + 7200, idempotency_key="warm-fu"
    )
    warm = await engine.intelligence.lead_intelligence(warm_lead.lead_id, now=now)
    assert warm["temperature"] == "warm"
    assert WARM_THRESHOLD <= warm["score"] < HOT_THRESHOLD

    cold_lead = await engine.leads.create(CRMLead(source=LeadSource.WEB, notes="cold"))
    cold = await engine.intelligence.lead_intelligence(cold_lead.lead_id, now=now + 8 * 86400)
    assert cold["temperature"] == "cold"
    assert cold["score"] < WARM_THRESHOLD

    nba_new = await engine.intelligence.next_best_action(lead_id=cold_lead.lead_id, now=now)
    assert nba_new["action"] == "CALL_CUSTOMER"
    assert nba_new["reason"]
    assert nba_new["entity_id"] == cold_lead.lead_id

    overdue_lead = await engine.leads.create(CRMLead(notes="overdue nba"))
    await engine.tasks.create(CRMTask(lead_id=overdue_lead.lead_id, title="do it", due_at=now - 10))
    nba_task = await engine.intelligence.next_best_action(lead_id=overdue_lead.lead_id, now=now)
    assert nba_task["action"] == "COMPLETE_OVERDUE_TASK"
    assert "overdue" in nba_task["reason"].lower()

    deal_lead = await engine.leads.create(CRMLead(notes="pipeline nba"))
    deal = await engine.pipeline.convert_lead_to_deal(deal_lead.lead_id, amount=18000)
    await engine.deals.update_stage(deal.deal_id, DealStage.NEGOTIATION)
    await engine.automation.schedule_follow_up(
        lead_id=deal_lead.lead_id, action_type="call", due_at=now + 5000, idempotency_key="neg-fu"
    )
    nba_deal = await engine.intelligence.next_best_action(deal_id=deal.deal_id, now=now)
    assert nba_deal["action"] == "ADVANCE_PIPELINE"
    assert nba_deal["reason"]
    first = await engine.intelligence.next_best_action(deal_id=deal.deal_id, now=now)
    second = await engine.intelligence.next_best_action(deal_id=deal.deal_id, now=now)
    assert first == second


@pytest.mark.asyncio
async def test_stale_detection_excludes_closed_deals_and_does_not_mutate():
    engine = auto_marketplace.crm_engine
    now = time.time()
    stale_lead = await engine.leads.create(CRMLead(notes="stale"))
    stale_deal = await engine.pipeline.convert_lead_to_deal(stale_lead.lead_id, amount=9000)
    later = now + STALE_SECONDS + 60
    detected = await engine.intelligence.detect_stale(deal_id=stale_deal.deal_id, now=later)
    assert detected["stale"] is True
    assert detected["active"] is True
    assert "no_recent_activity" in detected["reasons"]
    assert "missing_next_action" in detected["reasons"]

    won_lead = await engine.leads.create(CRMLead(notes="won"))
    won = await engine.pipeline.convert_lead_to_deal(won_lead.lead_id, amount=12000)
    closed = await engine.deals.mark_won(won.deal_id)
    assert closed.stage == DealStage.CLOSED_WON
    report = await engine.intelligence.deal_intelligence(won.deal_id, now=later)
    assert report["active"] is False
    assert report["stale"] is False
    assert report["temperature"] == "cold"
    assert report["next_best_action"]["action"] == "NO_ACTION"
    still = await engine.deals.get(won.deal_id)
    assert still.stage == DealStage.CLOSED_WON

    lost_lead = await engine.leads.create(CRMLead(notes="lost"))
    lost = await engine.pipeline.convert_lead_to_deal(lost_lead.lead_id, amount=4000)
    closed_lost = await engine.deals.mark_lost(lost.deal_id, reason="no budget")
    assert closed_lost.stage == DealStage.CLOSED_LOST
    lost_report = await engine.intelligence.deal_intelligence(lost.deal_id, now=later)
    assert lost_report["active"] is False
    assert lost_report["stale"] is False
    assert lost_report["next_best_action"]["action"] == "NO_ACTION"
    assert (await engine.deals.get(lost.deal_id)).stage == DealStage.CLOSED_LOST

    overview = await engine.intelligence.manager_overview(now=later)
    neglected_ids = {item["deal_id"] for item in overview["neglected"]}
    hottest_ids = {item["deal_id"] for item in overview["hottest"]}
    assert stale_deal.deal_id in neglected_ids
    assert won.deal_id not in neglected_ids
    assert lost.deal_id not in neglected_ids
    assert won.deal_id not in hottest_ids
    assert lost.deal_id not in hottest_ids


@pytest.mark.asyncio
async def test_manager_intelligence_orders_hottest_and_reads_are_side_effect_free():
    engine = auto_marketplace.crm_engine
    now = time.time()
    hotter = await engine.leads.create(CRMLead(source=LeadSource.REFERRAL, vehicle_id="a", notes="hotter"))
    cooler = await engine.leads.create(CRMLead(source=LeadSource.REFERRAL, vehicle_id="b", notes="cooler"))
    await engine.calendar.schedule_meeting(
        Meeting(lead_id=hotter.lead_id, title="done", status="completed", completed=True)
    )
    await engine.communications.log_call(PhoneCall(lead_id=hotter.lead_id, status="completed"))
    await engine.communications.log_email(EmailMessage(lead_id=hotter.lead_id, status="sent"))
    await engine.automation.schedule_follow_up(
        lead_id=hotter.lead_id, action_type="call", due_at=now + 4000, idempotency_key="mgr-a"
    )
    await engine.calendar.schedule_meeting(
        Meeting(lead_id=cooler.lead_id, title="also done", status="completed", completed=True)
    )
    await engine.automation.schedule_follow_up(
        lead_id=cooler.lead_id, action_type="call", due_at=now + 4000, idempotency_key="mgr-b"
    )
    before = await _counts(engine)
    first = await engine.intelligence.manager_overview(now=now)
    second = await engine.intelligence.manager_overview(now=now)
    after = await _counts(engine)
    assert before == after
    assert first["hottest"] == second["hottest"]
    assert first["temperatures"] == second["temperatures"]
    hottest_ids = [item["entity_id"] for item in first["hottest"]]
    assert hotter.lead_id in hottest_ids
    assert hottest_ids.index(hotter.lead_id) < hottest_ids.index(cooler.lead_id)
    assert first["temperatures"]["hot"] >= 2
    assert "overdue_follow_ups" in first
    assert "recommended_actions" in first
    again = await engine.intelligence.lead_intelligence(hotter.lead_id, now=now)
    twice = await engine.intelligence.lead_intelligence(hotter.lead_id, now=now)
    assert again == twice
    assert await _counts(engine) == before


@pytest.mark.asyncio
async def test_intelligence_api_auth_tenant_isolation_and_no_side_effects(client: TestClient):
    unauth = await client.get("/api/auto/v1/crm/intelligence")
    assert unauth.status == 401
    missing_lead = await client.get("/api/auto/v1/crm/leads/missing/intelligence")
    assert missing_lead.status == 401

    created = await client.post("/api/auto/v1/crm/leads", json={"notes": "api intel", "source": "web"}, headers=AUTH)
    assert created.status == 201
    lead_id = (await created.json())["lead_id"]
    before = await client.get("/api/auto/v1/crm/metrics", headers=AUTH)
    before_body = await before.json()
    first = await client.get(f"/api/auto/v1/crm/leads/{lead_id}/intelligence", headers=AUTH)
    assert first.status == 200
    payload = await first.json()
    assert 0 <= payload["score"] <= 100
    assert payload["temperature"] in {"hot", "warm", "cold"}
    assert payload["next_best_action"]["action"]
    second = await client.get(f"/api/auto/v1/crm/leads/{lead_id}/intelligence", headers=AUTH)
    assert await second.json() == payload
    after = await client.get("/api/auto/v1/crm/metrics", headers=AUTH)
    after_body = await after.json()
    for key in ("leads", "deals", "tasks", "activities", "calls", "emails", "meetings", "reminders"):
        assert after_body[key] == before_body[key]

    overview = await client.get("/api/auto/v1/crm/intelligence", headers=AUTH)
    assert overview.status == 200
    board = await overview.json()
    assert "hottest" in board
    assert "neglected" in board
    assert "temperatures" in board

    headers_a = {**AUTH, "X-Tenant-Id": "intel-a"}
    headers_b = {**AUTH, "X-Tenant-Id": "intel-b"}
    lead_a = await client.post("/api/auto/v1/crm/leads", json={"notes": "tenant a", "source": "referral"}, headers=headers_a)
    lead_a_id = (await lead_a.json())["lead_id"]
    deal_a = await client.post(
        f"/api/auto/v1/crm/leads/{lead_a_id}/convert",
        json={"amount": 15000},
        headers=headers_a,
    )
    assert deal_a.status == 201, await deal_a.text()
    deal_a_id = (await deal_a.json())["deal_id"]
    hidden_lead = await client.get(f"/api/auto/v1/crm/leads/{lead_a_id}/intelligence", headers=headers_b)
    assert hidden_lead.status == 404
    hidden_deal = await client.get(f"/api/auto/v1/crm/deals/{deal_a_id}/intelligence", headers=headers_b)
    assert hidden_deal.status == 404
    board_b = await client.get("/api/auto/v1/crm/intelligence", headers=headers_b)
    body_b = await board_b.json()
    assert all(item.get("lead_id") != lead_a_id for item in body_b["hottest"])
    assert all(item.get("deal_id") != deal_a_id for item in body_b["neglected"])
    assert all(item.get("entity_id") not in {lead_a_id, deal_a_id} for item in body_b.get("recommended_actions", []))
    visible = await client.get(f"/api/auto/v1/crm/leads/{lead_a_id}/intelligence", headers=headers_a)
    assert visible.status == 200


@pytest.mark.asyncio
async def test_postgres_intelligence_restart_and_tenant_isolation(postgres_crm_mode):
    await _ensure_postgres_tables()
    suffix = uuid.uuid4().hex[:12]
    tenant_a = f"intel-a-{suffix}"
    tenant_b = f"intel-b-{suffix}"
    now = time.time()

    bind_crm_tenant(tenant_a)
    engine = _stack(PostgresCRMPersistence())
    lead = await engine.leads.create(
        CRMLead(source=LeadSource.REFERRAL, vehicle_id=f"v-{suffix}", notes=f"intel-{suffix}")
    )
    await engine.calendar.schedule_meeting(
        Meeting(lead_id=lead.lead_id, title="persist", status="completed", completed=True)
    )
    await engine.automation.schedule_follow_up(
        lead_id=lead.lead_id, action_type="call", due_at=now + 2400, source="intel", idempotency_key=f"pg-{suffix}"
    )
    first = await engine.intelligence.lead_intelligence(lead.lead_id, now=now)
    assert 0 <= first["score"] <= 100

    bind_crm_tenant(tenant_b)
    other = _stack(PostgresCRMPersistence())
    with pytest.raises(NotFoundError):
        await other.intelligence.lead_intelligence(lead.lead_id, now=now)
    other_board = await other.intelligence.manager_overview(now=now)
    assert all(item.get("lead_id") != lead.lead_id for item in other_board["hottest"])

    from database.session import shutdown_db

    await shutdown_db()
    reset_crm_persistence()
    bind_crm_tenant(tenant_a)
    restored = _stack(PostgresCRMPersistence())
    loaded = await restored.intelligence.lead_intelligence(lead.lead_id, now=now)
    assert loaded["score"] == first["score"]
    assert loaded["temperature"] == first["temperature"]
    assert loaded["factors"] == first["factors"]
    assert loaded["next_best_action"] == first["next_best_action"]
    assert loaded["stale"] == first["stale"]
