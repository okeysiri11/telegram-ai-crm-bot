"""Sprint 12 — CRM manager command center, pipeline forecasting, team performance."""

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
from applications.auto_marketplace.crm.engine import CRMEngine
from applications.auto_marketplace.crm.intelligence import STALE_SECONDS
from applications.auto_marketplace.crm.manager_intelligence import (
    CURRENCY_UNSPECIFIED,
    STAGE_BASE_PROBABILITY,
    add_money,
    clamp_probability,
    classify_deal_risk,
    classify_forecast_category,
    classify_workload,
    deal_currency,
    forecast_probability,
    money_payload,
)
from applications.auto_marketplace.crm.models import (
    CRMDeal,
    CRMLead,
    CRMTask,
    CustomerProfile,
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
        "customers": len(await engine.customers.list_profiles()),
        "leads": len(await engine.leads.list_leads()),
        "deals": len(await engine.deals.list_deals()),
        "tasks": len(await engine.tasks.list_tasks()),
        "activities": len(await engine.activities.list_activities()),
        "follow_ups": len(await engine.automation.list_follow_ups()),
    }


async def _open_deal(
    engine: CRMEngine,
    *,
    notes: str,
    amount: float,
    owner: str = "agt-a",
    stage: DealStage = DealStage.QUALIFICATION,
) -> CRMDeal:
    lead = await engine.leads.create(CRMLead(notes=notes, assigned_agent_id=owner, source=LeadSource.WEB))
    deal = await engine.pipeline.convert_lead_to_deal(lead.lead_id, amount=amount, agent_id=owner)
    if stage != deal.stage:
        deal = await engine.deals.update_stage(deal.deal_id, stage)
    return deal


def test_forecast_rules_are_centralized_deterministic_and_explainable():
    assert STAGE_BASE_PROBABILITY[DealStage.PROSPECT] == 0.10
    assert STAGE_BASE_PROBABILITY[DealStage.CLOSED_WON] == 1.0
    assert STAGE_BASE_PROBABILITY[DealStage.CLOSED_LOST] == 0.0
    assert clamp_probability(-1) == 0.0
    assert clamp_probability(2) == 1.0
    first = forecast_probability(
        stage=DealStage.PROPOSAL,
        score=80,
        temperature="hot",
        relationship_health="healthy",
        stale=False,
        sla_status="on_time",
        escalation_level="none",
        follow_up_overdue=False,
        hot_no_action=False,
    )
    second = forecast_probability(
        stage=DealStage.PROPOSAL,
        score=80,
        temperature="hot",
        relationship_health="healthy",
        stale=False,
        sla_status="on_time",
        escalation_level="none",
        follow_up_overdue=False,
        hot_no_action=False,
    )
    assert first == second
    assert 0.0 <= first["forecast_probability"] <= 1.0
    assert "STAGE_PROPOSAL" in first["reason_codes"]
    assert first["explanation"]
    won = forecast_probability(
        stage=DealStage.CLOSED_WON,
        score=10,
        temperature="cold",
        relationship_health="at_risk",
        stale=True,
        sla_status="breached",
        escalation_level="critical",
        follow_up_overdue=True,
        hot_no_action=True,
    )
    lost = forecast_probability(
        stage=DealStage.CLOSED_LOST,
        score=90,
        temperature="hot",
        relationship_health="strong",
        stale=False,
        sla_status="on_time",
        escalation_level="none",
        follow_up_overdue=False,
        hot_no_action=False,
    )
    assert won["forecast_probability"] == 1.0
    assert lost["forecast_probability"] == 0.0
    category = classify_forecast_category(stage=DealStage.APPROVAL, probability=0.9, risk_level="low", stale=False)
    assert category["forecast_category"] == "commit"
    at_risk = classify_forecast_category(stage=DealStage.APPROVAL, probability=0.9, risk_level="critical", stale=True)
    assert at_risk["forecast_category"] == "at_risk"
    risk = classify_deal_risk(
        stale=True,
        follow_up_overdue=True,
        task_overdue=False,
        sla_status="breached",
        escalation_level="manager",
        relationship_health="at_risk",
        hot_no_action=True,
        high_value_neglected=True,
        no_recent_contact=True,
    )
    assert risk["risk_level"] == "critical"
    assert "STALE_DEAL" in risk["risk_flags"]
    assert risk["explanation"]
    again = classify_deal_risk(
        stale=True,
        follow_up_overdue=True,
        task_overdue=False,
        sla_status="breached",
        escalation_level="manager",
        relationship_health="at_risk",
        hot_no_action=True,
        high_value_neglected=True,
        no_recent_contact=True,
    )
    assert risk == again
    load = classify_workload(
        open_deals=1,
        high_priority_items=0,
        overdue_follow_ups=0,
        overdue_tasks=0,
        sla_at_risk=0,
        sla_breaches=0,
        escalations=0,
        high_risk_deals=0,
    )
    assert load["workload_level"] == "normal"
    heavy = classify_workload(
        open_deals=8,
        high_priority_items=4,
        overdue_follow_ups=3,
        overdue_tasks=2,
        sla_at_risk=2,
        sla_breaches=2,
        escalations=2,
        high_risk_deals=3,
    )
    assert heavy["workload_level"] == "critical"
    assert heavy["reason_codes"]


def test_multi_currency_totals_are_not_silently_combined():
    assert deal_currency(CRMDeal()) == CURRENCY_UNSPECIFIED
    buckets: dict[str, float] = {}
    add_money(buckets, "usd", 100)
    add_money(buckets, "eur", 50)
    payload = money_payload(buckets)
    assert payload["mixed_currencies"] is True
    assert payload["canonical_total"] is None
    assert payload["by_currency"]["usd"] == 100
    assert payload["by_currency"]["eur"] == 50
    assert payload["by_currency"]["usd"] + payload["by_currency"]["eur"] != payload["canonical_total"]


@pytest.mark.asyncio
async def test_pipeline_snapshot_empty_single_multiple_and_closed_states():
    engine = auto_marketplace.crm_engine
    now = time.time()
    empty = await engine.manager.pipeline_snapshot(now=now)
    assert empty["items"] == []
    assert empty["total"] == 0
    assert empty["currency"] == CURRENCY_UNSPECIFIED

    zero = await _open_deal(engine, notes="zero", amount=0, owner="agt-a")
    missing = await engine.deals.create(CRMDeal(owner_agent_id="agt-a", stage=DealStage.PROSPECT))
    open_deal = await _open_deal(engine, notes="open", amount=10000, owner="agt-a", stage=DealStage.PROPOSAL)
    won_src = await _open_deal(engine, notes="won", amount=8000, owner="agt-b")
    won = await engine.deals.mark_won(won_src.deal_id, amount=8000)
    lost_src = await _open_deal(engine, notes="lost", amount=4000, owner="agt-b")
    lost = await engine.deals.mark_lost(lost_src.deal_id)

    before = await _counts(engine)
    snap = await engine.manager.pipeline_snapshot(now=now, limit=50)
    after = await _counts(engine)
    assert after == before
    assert snap["total"] == 5
    by_id = {item["deal_id"]: item for item in snap["items"]}
    assert by_id[zero.deal_id]["deal_value"] == 0
    assert by_id[zero.deal_id]["weighted_value"] == 0
    assert by_id[missing.deal_id]["deal_value"] == 0
    assert by_id[missing.deal_id]["weighted_value"] == 0
    assert 0 <= by_id[open_deal.deal_id]["forecast_probability"] <= 1
    assert by_id[open_deal.deal_id]["weighted_value"] == round(
        by_id[open_deal.deal_id]["deal_value"] * by_id[open_deal.deal_id]["forecast_probability"], 2
    )
    assert by_id[open_deal.deal_id]["forecast_explanation"]
    assert by_id[won.deal_id]["forecast_probability"] == 1.0
    assert by_id[won.deal_id]["weighted_value"] == 0
    assert by_id[won.deal_id]["forecast_category"] == "closed_won"
    assert by_id[lost.deal_id]["forecast_probability"] == 0.0
    assert by_id[lost.deal_id]["forecast_category"] == "closed_lost"
    assert by_id[lost.deal_id]["active"] is False

    forecast = await engine.manager.forecast(now=now)
    assert forecast["open_deal_count"] == 3
    assert forecast["won_deal_count"] == 1
    assert forecast["lost_deal_count"] == 1
    assert forecast["won_value"]["canonical_total"] == 8000
    assert forecast["lost_value"]["canonical_total"] == 4000
    assert forecast["weighted_pipeline"]["mixed_currencies"] is False
    page = await engine.manager.pipeline_snapshot(now=now, limit=2, offset=0)
    page2 = await engine.manager.pipeline_snapshot(now=now, limit=2, offset=2)
    assert len(page["items"]) == 2
    assert len(page2["items"]) == 2
    assert page["items"][0]["deal_id"] != page2["items"][0]["deal_id"]


@pytest.mark.asyncio
async def test_forecast_risk_team_actions_and_rankings_are_deterministic():
    engine = auto_marketplace.crm_engine
    now = time.time()
    approval = await _open_deal(engine, notes="commit", amount=50000, owner="agt-a", stage=DealStage.APPROVAL)
    await engine.communications.log_call(PhoneCall(deal_id=approval.deal_id, status="completed"))
    await engine.calendar.schedule_meeting(
        Meeting(deal_id=approval.deal_id, title="close", status="completed", completed=True)
    )
    twin_a = await engine.deals.create(
        CRMDeal(amount=12000, owner_agent_id="agt-tie", stage=DealStage.PROPOSAL, deal_id="deal-aaa")
    )
    twin_b = await engine.deals.create(
        CRMDeal(amount=12000, owner_agent_id="agt-tie", stage=DealStage.PROPOSAL, deal_id="deal-bbb")
    )
    stale_lead = await engine.leads.create(CRMLead(notes="stale", assigned_agent_id="agt-risk"))
    stale = await engine.pipeline.convert_lead_to_deal(stale_lead.lead_id, amount=30000, agent_id="agt-risk")
    later = now + STALE_SECONDS + 60
    await engine.automation.schedule_follow_up(
        lead_id=stale_lead.lead_id,
        deal_id=stale.deal_id,
        action_type="call",
        due_at=later - 4000,
        idempotency_key="stale-fu",
    )
    await engine.tasks.create(CRMTask(deal_id=stale.deal_id, title="late", due_at=later - 90))

    first = await engine.manager.command_center(now=later)
    second = await engine.manager.command_center(now=later)
    first.pop("generated_at", None)
    second.pop("generated_at", None)
    first["pipeline_changes"].pop("generated_at", None)
    second["pipeline_changes"].pop("generated_at", None)
    assert first == second

    by_id = {item["deal_id"]: item for item in (await engine.manager.pipeline_snapshot(now=later, limit=50))["items"]}
    assert by_id[stale.deal_id]["stale"] is True
    assert by_id[stale.deal_id]["risk_level"] in {"high", "critical"}
    assert "STALE_DEAL" in by_id[stale.deal_id]["risk_flags"]
    assert by_id[stale.deal_id]["forecast_category"] == "at_risk"
    assert by_id[stale.deal_id]["risk_explanation"]
    nba = await engine.intelligence.next_best_action(deal_id=stale.deal_id, now=later)
    exec_item = await engine.execution.deal_execution(stale.deal_id, now=later)
    assert by_id[stale.deal_id]["next_best_action"] == nba["action"]
    assert by_id[stale.deal_id]["sla_status"] == exec_item["sla_status"]
    assert by_id[stale.deal_id]["escalation_status"] == exec_item["escalation_level"]

    tops = first["top_opportunities"]
    assert tops
    ids = [item["deal_id"] for item in tops]
    assert ids == sorted(ids, key=lambda deal_id: (-by_id[deal_id]["weighted_value"], -by_id[deal_id]["forecast_probability"], -by_id[deal_id]["deal_value"], deal_id))
    ranked = engine.manager._top_opportunities(list(by_id.values()), limit=10)
    tie_ids = [item["deal_id"] for item in ranked if item["deal_id"] in {twin_a.deal_id, twin_b.deal_id}]
    assert tie_ids == sorted(tie_ids)
    risks = first["top_risks"]
    assert risks[0]["deal_id"] == stale.deal_id or risks[0]["risk_level"] in {"high", "critical"}
    risk_ids = [item["deal_id"] for item in risks]
    assert risk_ids == sorted(
        risk_ids,
        key=lambda deal_id: (
            -{"critical": 3, "high": 2, "medium": 1, "low": 0}[by_id[deal_id]["risk_level"]],
            -by_id[deal_id]["deal_value"],
            deal_id,
        ),
    )

    actions = first["action_center"]["items"]
    keys = [item["item"] for item in actions]
    assert len(keys) == len(set(keys))
    assert all(item["source_engine"] in {"sales_execution", "deal_risk"} for item in actions)

    team = first["team_performance"]
    assert team["targets"] is None
    owners = {row["owner_id"]: row for row in team["owners"]}
    assert "agt-risk" in owners
    assert owners["agt-risk"]["workload"]["workload_level"] in {"normal", "elevated", "high", "critical"}
    assert owners["agt-risk"]["workload"]["explanation"]
    assert owners["agt-risk"]["stale_deals"] >= 1
    revenue = first["revenue_intelligence"]
    assert revenue["closed_won_revenue"]["canonical_total"] in (0, None) or revenue["closed_won_revenue"]["by_currency"]
    assert first["pipeline_changes"]["capability"] == "limited_by_existing_history"
    assert "forecast_category_changed" in first["pipeline_changes"]["unsupported_events"]
    change_types = {item["change_type"] for item in first["pipeline_changes"]["items"]}
    assert "deal_created" in change_types

    filtered = await engine.manager.pipeline_snapshot(now=later, owner="agt-risk", risk_level=by_id[stale.deal_id]["risk_level"])
    assert filtered["items"]
    assert all(item["owner_id"] == "agt-risk" for item in filtered["items"])


@pytest.mark.asyncio
async def test_command_center_reuses_sprints_8_11_and_does_not_mutate():
    engine = auto_marketplace.crm_engine
    now = time.time()
    customer = await engine.customers.create(CustomerProfile(first_name="Pat", email="pat@test.com"))
    lead = await engine.leads.create(
        CRMLead(customer_id=customer.customer_id, notes="360-link", assigned_agent_id="agt-360", source=LeadSource.REFERRAL)
    )
    deal = await engine.pipeline.convert_lead_to_deal(lead.lead_id, amount=18000, agent_id="agt-360")
    await engine.automation.schedule_follow_up(
        lead_id=lead.lead_id,
        customer_id=customer.customer_id,
        deal_id=deal.deal_id,
        action_type="email",
        due_at=now - 500,
        idempotency_key="mgr-fu",
    )
    view = await engine.customer_360.get_360(customer.customer_id, now=now)
    before = await _counts(engine)
    center = await engine.manager.command_center(now=now)
    after = await _counts(engine)
    assert after == before
    snap = (await engine.manager.pipeline_snapshot(now=now))["items"][0]
    assert snap["customer_id"] == customer.customer_id
    assert snap["relationship_health"] in {"strong", "healthy", "attention", "at_risk"}
    assert view["relationship_health"] in {"strong", "healthy", "attention", "at_risk"}
    assert snap["next_best_action"]
    flags = snap["risk_flags"]
    assert "FOLLOW_UP_OVERDUE" in flags or any(
        item["reason_codes"] and "FOLLOW_UP_OVERDUE" in (item.get("reason_codes") or [])
        for item in center["action_center"]["items"]
    )
    again_360 = await engine.customer_360.get_360(customer.customer_id, now=now)
    assert again_360["customer_id"] == view["customer_id"]
    assert again_360["relationship_health"] == view["relationship_health"]


@pytest.mark.asyncio
async def test_manager_api_auth_filters_tenant_dashboard_and_idempotency(client: TestClient):
    for path in (
        "/api/auto/v1/crm/manager/command-center",
        "/api/auto/v1/crm/manager/pipeline",
        "/api/auto/v1/crm/manager/forecast",
        "/api/auto/v1/crm/manager/team-performance",
    ):
        unauth = await client.get(path)
        assert unauth.status == 401, path

    created = await client.post(
        "/api/auto/v1/crm/leads",
        json={"notes": "mgr-api", "source": "web", "assigned_agent_id": "agt-api"},
        headers=AUTH,
    )
    assert created.status == 201
    lead_id = (await created.json())["lead_id"]
    converted = await client.post(f"/api/auto/v1/crm/leads/{lead_id}/convert", json={"amount": 9000}, headers=AUTH)
    assert converted.status in {200, 201}, await converted.text()
    before = await client.get("/api/auto/v1/crm/metrics", headers=AUTH)
    before_body = await before.json()
    first = await client.get("/api/auto/v1/crm/manager/command-center", headers=AUTH)
    assert first.status == 200
    payload = await first.json()
    assert "pipeline_summary" in payload
    assert "action_center" in payload
    second = await client.get("/api/auto/v1/crm/manager/command-center", headers=AUTH)
    body = await second.json()
    payload.pop("generated_at", None)
    body.pop("generated_at", None)
    payload.get("pipeline_changes", {}).pop("generated_at", None)
    body.get("pipeline_changes", {}).pop("generated_at", None)
    assert body == payload
    pipe = await client.get("/api/auto/v1/crm/manager/pipeline?limit=10&offset=0", headers=AUTH)
    assert pipe.status == 200
    pipe_body = await pipe.json()
    assert pipe_body["limit"] == 10
    assert "items" in pipe_body
    forecast = await client.get("/api/auto/v1/crm/manager/forecast", headers=AUTH)
    assert forecast.status == 200
    team = await client.get("/api/auto/v1/crm/manager/team-performance", headers=AUTH)
    assert team.status == 200
    team_body = await team.json()
    assert team_body["targets"] is None
    filtered = await client.get("/api/auto/v1/crm/manager/pipeline?owner=agt-api", headers=AUTH)
    assert filtered.status == 200
    after = await client.get("/api/auto/v1/crm/metrics", headers=AUTH)
    after_body = await after.json()
    for key in ("customers", "leads", "deals", "tasks", "activities", "reminders"):
        assert after_body[key] == before_body[key]

    headers_a = {**AUTH, "X-Tenant-Id": "mgr-a"}
    headers_b = {**AUTH, "X-Tenant-Id": "mgr-b"}
    lead_a = await client.post(
        "/api/auto/v1/crm/leads",
        json={"notes": "tenant-a", "source": "web", "assigned_agent_id": "agt-a"},
        headers=headers_a,
    )
    lead_a_id = (await lead_a.json())["lead_id"]
    conv_a = await client.post(f"/api/auto/v1/crm/leads/{lead_a_id}/convert", json={"amount": 15000}, headers=headers_a)
    assert conv_a.status in {200, 201}
    hidden = await client.get("/api/auto/v1/crm/manager/pipeline", headers=headers_b)
    hidden_body = await hidden.json()
    assert hidden_body["total"] == 0
    visible = await client.get("/api/auto/v1/crm/manager/pipeline", headers=headers_a)
    visible_body = await visible.json()
    assert visible_body["total"] >= 1
    assert visible_body["tenant_id"] == "mgr-a"

    dash = await executive_dashboard_service.get_dashboard(DashboardRole.SALES_MANAGER)
    types = {item["type"] for item in dash.widgets}
    assert "pipeline_forecast" in types
    forecast_widget = next(item for item in dash.widgets if item["type"] == "pipeline_forecast")
    assert "weighted_forecast" in forecast_widget["data"]
    assert "commit_forecast" in forecast_widget["data"]


@pytest.mark.asyncio
async def test_postgres_manager_forecast_restart_and_tenant_isolation(postgres_crm_mode):
    await _ensure_postgres_tables()
    suffix = uuid.uuid4().hex[:12]
    tenant_a = f"mgr-a-{suffix}"
    tenant_b = f"mgr-b-{suffix}"
    now = time.time()

    bind_crm_tenant(tenant_a)
    engine = _stack(PostgresCRMPersistence())
    lead = await engine.leads.create(CRMLead(notes=f"mgr-{suffix}", assigned_agent_id="agt-pg"))
    deal = await engine.pipeline.convert_lead_to_deal(lead.lead_id, amount=21000, agent_id="agt-pg")
    first = await engine.manager.forecast(now=now)
    snap = await engine.manager.pipeline_snapshot(now=now)
    assert first["tenant_id"] == tenant_a
    assert snap["items"][0]["deal_id"] == deal.deal_id

    bind_crm_tenant(tenant_b)
    other = _stack(PostgresCRMPersistence())
    isolated = await other.manager.pipeline_snapshot(now=now)
    assert isolated["total"] == 0
    with pytest.raises(NotFoundError):
        await other.deals.get(deal.deal_id)

    from database.session import shutdown_db

    await shutdown_db()
    reset_crm_persistence()
    bind_crm_tenant(tenant_a)
    restored = _stack(PostgresCRMPersistence())
    loaded = await restored.manager.forecast(now=now)
    loaded_snap = await restored.manager.pipeline_snapshot(now=now)
    assert loaded["open_deal_count"] == first["open_deal_count"]
    assert loaded["weighted_pipeline"] == first["weighted_pipeline"]
    assert loaded_snap["items"][0]["forecast_probability"] == snap["items"][0]["forecast_probability"]
    assert loaded_snap["items"][0]["forecast_category"] == snap["items"][0]["forecast_category"]
    assert loaded_snap["items"][0]["risk_level"] == snap["items"][0]["risk_level"]
    assert loaded_snap["items"][0]["weighted_value"] == snap["items"][0]["weighted_value"]
