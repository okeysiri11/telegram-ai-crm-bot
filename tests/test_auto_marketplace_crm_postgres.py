"""Sprint 1 Durable CRM — PostgreSQL restart persistence and tenant isolation."""

from __future__ import annotations

import os
import uuid

import pytest

from applications.auto_marketplace.crm.models import (
    CRMDeal,
    CRMLead,
    CRMLeadStatus,
    CRMTask,
    CustomerProfile,
    DealStage,
    EmailMessage,
    Interaction,
    InteractionType,
    LeadSource,
    Meeting,
    PhoneCall,
    Reminder,
    TaskPriority,
    TaskStatus,
)
from applications.auto_marketplace.activities.service import ActivityService
from applications.auto_marketplace.calendar.service import CalendarService
from applications.auto_marketplace.communications.service import CommunicationService
from applications.auto_marketplace.tasks.service import TaskService
from applications.auto_marketplace.crm.metrics import crm_metrics
from applications.auto_marketplace.crm.persistence import (
    PostgresCRMPersistence,
    crm_persistence_mode,
    get_crm_persistence,
    reset_crm_persistence,
)
from applications.auto_marketplace.crm.tenant import bind_crm_tenant, current_crm_tenant
from applications.auto_marketplace.customers.profile_service import CustomerProfileService
from applications.auto_marketplace.deals.service import DealService
from applications.auto_marketplace.leads.service import LeadService
from applications.auto_marketplace.sales_pipeline.service import SalesPipelineEngine
from applications.auto_marketplace.shared.exceptions import NotFoundError


async def _ensure_postgres_tables() -> None:
    from database.engine import get_engine, is_postgres_configured
    from database.session import shutdown_db
    from sqlalchemy import text

    if not is_postgres_configured():
        pytest.fail("PostgreSQL is not configured; restart persistence cannot be demonstrated")

    await shutdown_db()
    engine = get_engine()
    ddl = [
        """
        CREATE TABLE IF NOT EXISTS auto_marketplace_crm_customers (
            customer_id VARCHAR(64) PRIMARY KEY,
            tenant_id VARCHAR(128) NOT NULL DEFAULT 'default',
            first_name VARCHAR(255) NOT NULL DEFAULT '',
            last_name VARCHAR(255) NOT NULL DEFAULT '',
            email VARCHAR(255) NOT NULL DEFAULT '',
            phone VARCHAR(64) NOT NULL DEFAULT '',
            segment VARCHAR(64) NOT NULL DEFAULT 'standard',
            intent_score FLOAT NOT NULL DEFAULT 0,
            lifetime_value FLOAT NOT NULL DEFAULT 0,
            owner_agent_id VARCHAR(64) NOT NULL DEFAULT '',
            created_ts FLOAT NOT NULL DEFAULT 0,
            payload JSONB NOT NULL DEFAULT '{}'::jsonb,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS auto_marketplace_crm_leads (
            lead_id VARCHAR(64) PRIMARY KEY,
            tenant_id VARCHAR(128) NOT NULL DEFAULT 'default',
            customer_id VARCHAR(64) NOT NULL DEFAULT '',
            vehicle_id VARCHAR(64) NOT NULL DEFAULT '',
            dealer_id VARCHAR(64) NOT NULL DEFAULT '',
            source VARCHAR(64) NOT NULL DEFAULT 'web',
            status VARCHAR(64) NOT NULL DEFAULT 'new',
            score FLOAT NOT NULL DEFAULT 0,
            assigned_agent_id VARCHAR(64) NOT NULL DEFAULT '',
            notes TEXT NOT NULL DEFAULT '',
            created_ts FLOAT NOT NULL DEFAULT 0,
            qualified_at FLOAT NULL,
            payload JSONB NOT NULL DEFAULT '{}'::jsonb,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS auto_marketplace_crm_deals (
            deal_id VARCHAR(64) PRIMARY KEY,
            tenant_id VARCHAR(128) NOT NULL DEFAULT 'default',
            opportunity_id VARCHAR(64) NOT NULL DEFAULT '',
            customer_id VARCHAR(64) NOT NULL DEFAULT '',
            dealer_id VARCHAR(64) NOT NULL DEFAULT '',
            vehicle_id VARCHAR(64) NOT NULL DEFAULT '',
            stage VARCHAR(64) NOT NULL DEFAULT 'prospect',
            amount FLOAT NOT NULL DEFAULT 0,
            probability FLOAT NOT NULL DEFAULT 0.1,
            win BOOLEAN NULL,
            owner_agent_id VARCHAR(64) NOT NULL DEFAULT '',
            created_ts FLOAT NOT NULL DEFAULT 0,
            closed_at FLOAT NULL,
            payload JSONB NOT NULL DEFAULT '{}'::jsonb,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS auto_marketplace_crm_tasks (
            task_id VARCHAR(64) PRIMARY KEY,
            tenant_id VARCHAR(128) NOT NULL DEFAULT 'default',
            title VARCHAR(255) NOT NULL DEFAULT '',
            description TEXT NOT NULL DEFAULT '',
            status VARCHAR(64) NOT NULL DEFAULT 'pending',
            priority VARCHAR(64) NOT NULL DEFAULT 'normal',
            customer_id VARCHAR(64) NOT NULL DEFAULT '',
            lead_id VARCHAR(64) NOT NULL DEFAULT '',
            deal_id VARCHAR(64) NOT NULL DEFAULT '',
            assigned_agent_id VARCHAR(64) NOT NULL DEFAULT '',
            created_by VARCHAR(64) NOT NULL DEFAULT '',
            due_at FLOAT NULL,
            completed_at FLOAT NULL,
            created_ts FLOAT NOT NULL DEFAULT 0,
            payload JSONB NOT NULL DEFAULT '{}'::jsonb,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS auto_marketplace_crm_activities (
            activity_id VARCHAR(64) PRIMARY KEY,
            tenant_id VARCHAR(128) NOT NULL DEFAULT 'default',
            activity_type VARCHAR(64) NOT NULL DEFAULT 'note',
            customer_id VARCHAR(64) NOT NULL DEFAULT '',
            lead_id VARCHAR(64) NOT NULL DEFAULT '',
            deal_id VARCHAR(64) NOT NULL DEFAULT '',
            task_id VARCHAR(64) NOT NULL DEFAULT '',
            agent_id VARCHAR(64) NOT NULL DEFAULT '',
            subject VARCHAR(255) NOT NULL DEFAULT '',
            body TEXT NOT NULL DEFAULT '',
            idempotency_key VARCHAR(255) NOT NULL DEFAULT '',
            created_ts FLOAT NOT NULL DEFAULT 0,
            payload JSONB NOT NULL DEFAULT '{}'::jsonb,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS auto_marketplace_crm_calls (
            call_id VARCHAR(64) PRIMARY KEY,
            tenant_id VARCHAR(128) NOT NULL DEFAULT 'default',
            customer_id VARCHAR(64) NOT NULL DEFAULT '',
            lead_id VARCHAR(64) NOT NULL DEFAULT '',
            deal_id VARCHAR(64) NOT NULL DEFAULT '',
            agent_id VARCHAR(64) NOT NULL DEFAULT '',
            direction VARCHAR(32) NOT NULL DEFAULT 'outbound',
            status VARCHAR(64) NOT NULL DEFAULT 'logged',
            duration_sec INTEGER NOT NULL DEFAULT 0,
            summary TEXT NOT NULL DEFAULT '',
            started_at FLOAT NULL,
            ended_at FLOAT NULL,
            created_ts FLOAT NOT NULL DEFAULT 0,
            payload JSONB NOT NULL DEFAULT '{}'::jsonb,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS auto_marketplace_crm_emails (
            email_id VARCHAR(64) PRIMARY KEY,
            tenant_id VARCHAR(128) NOT NULL DEFAULT 'default',
            customer_id VARCHAR(64) NOT NULL DEFAULT '',
            lead_id VARCHAR(64) NOT NULL DEFAULT '',
            deal_id VARCHAR(64) NOT NULL DEFAULT '',
            agent_id VARCHAR(64) NOT NULL DEFAULT '',
            subject VARCHAR(255) NOT NULL DEFAULT '',
            body TEXT NOT NULL DEFAULT '',
            direction VARCHAR(32) NOT NULL DEFAULT 'outbound',
            status VARCHAR(64) NOT NULL DEFAULT 'logged',
            sender VARCHAR(255) NOT NULL DEFAULT '',
            recipient VARCHAR(255) NOT NULL DEFAULT '',
            created_ts FLOAT NOT NULL DEFAULT 0,
            payload JSONB NOT NULL DEFAULT '{}'::jsonb,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS auto_marketplace_crm_meetings (
            meeting_id VARCHAR(64) PRIMARY KEY,
            tenant_id VARCHAR(128) NOT NULL DEFAULT 'default',
            customer_id VARCHAR(64) NOT NULL DEFAULT '',
            lead_id VARCHAR(64) NOT NULL DEFAULT '',
            deal_id VARCHAR(64) NOT NULL DEFAULT '',
            agent_id VARCHAR(64) NOT NULL DEFAULT '',
            title VARCHAR(255) NOT NULL DEFAULT '',
            description TEXT NOT NULL DEFAULT '',
            scheduled_at FLOAT NOT NULL DEFAULT 0,
            duration_min INTEGER NOT NULL DEFAULT 30,
            location VARCHAR(255) NOT NULL DEFAULT '',
            status VARCHAR(64) NOT NULL DEFAULT 'scheduled',
            completed BOOLEAN NOT NULL DEFAULT FALSE,
            created_ts FLOAT NOT NULL DEFAULT 0,
            payload JSONB NOT NULL DEFAULT '{}'::jsonb,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS auto_marketplace_crm_reminders (
            reminder_id VARCHAR(64) PRIMARY KEY,
            tenant_id VARCHAR(128) NOT NULL DEFAULT 'default',
            task_id VARCHAR(64) NOT NULL DEFAULT '',
            customer_id VARCHAR(64) NOT NULL DEFAULT '',
            lead_id VARCHAR(64) NOT NULL DEFAULT '',
            deal_id VARCHAR(64) NOT NULL DEFAULT '',
            title VARCHAR(255) NOT NULL DEFAULT '',
            message TEXT NOT NULL DEFAULT '',
            assigned_agent_id VARCHAR(64) NOT NULL DEFAULT '',
            trigger_at FLOAT NOT NULL DEFAULT 0,
            status VARCHAR(64) NOT NULL DEFAULT 'pending',
            triggered BOOLEAN NOT NULL DEFAULT FALSE,
            created_ts FLOAT NOT NULL DEFAULT 0,
            payload JSONB NOT NULL DEFAULT '{}'::jsonb,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """,
    ]
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
            for stmt in ddl:
                await conn.execute(text(stmt))
    except Exception as exc:  # noqa: BLE001
        pytest.fail(f"PostgreSQL is unreachable; restart persistence cannot be demonstrated: {exc}")


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


@pytest.mark.asyncio
async def test_production_default_is_postgres(monkeypatch):
    monkeypatch.delenv("AUTO_CRM_PERSISTENCE", raising=False)
    reset_crm_persistence()
    assert crm_persistence_mode() == "postgres"
    assert get_crm_persistence().backend == "postgres"
    monkeypatch.setenv("AUTO_CRM_PERSISTENCE", "memory")
    reset_crm_persistence()


@pytest.mark.asyncio
async def test_leads_deals_customers_survive_engine_restart(postgres_crm_mode):
    await _ensure_postgres_tables()
    suffix = uuid.uuid4().hex[:12]
    tenant = f"restart-{suffix}"
    bind_crm_tenant(tenant)

    leads = LeadService(persistence=PostgresCRMPersistence())
    deals = DealService(persistence=PostgresCRMPersistence())
    customers = CustomerProfileService(persistence=PostgresCRMPersistence())

    profile = await customers.create(
        CustomerProfile(first_name="Durable", last_name="CRM", email=f"durable-{suffix}@example.com")
    )
    lead = await leads.create(CRMLead(customer_id=profile.customer_id, dealer_id="d-restart", notes=f"n-{suffix}"))
    deal = await deals.create(CRMDeal(customer_id=profile.customer_id, dealer_id="d-restart", amount=19999))

    customer_id, lead_id, deal_id = profile.customer_id, lead.lead_id, deal.deal_id

    from database.session import shutdown_db

    await shutdown_db()
    reset_crm_persistence()

    bind_crm_tenant(tenant)
    leads2 = LeadService(persistence=PostgresCRMPersistence())
    deals2 = DealService(persistence=PostgresCRMPersistence())
    customers2 = CustomerProfileService(persistence=PostgresCRMPersistence())

    restored_customer = await customers2.get(customer_id)
    restored_lead = await leads2.get(lead_id)
    restored_deal = await deals2.get(deal_id)

    assert restored_customer.email == f"durable-{suffix}@example.com"
    assert restored_lead.notes == f"n-{suffix}"
    assert restored_deal.amount == 19999

    await customers2.delete(customer_id)
    await leads2.delete(lead_id)
    await deals2.delete(deal_id)


@pytest.mark.asyncio
async def test_tenant_isolation_on_get_and_list(postgres_crm_mode):
    await _ensure_postgres_tables()
    suffix = uuid.uuid4().hex[:12]
    tenant_a = f"tenant-a-{suffix}"
    tenant_b = f"tenant-b-{suffix}"

    persist = PostgresCRMPersistence()
    leads = LeadService(persistence=persist)

    bind_crm_tenant(tenant_a)
    assert current_crm_tenant() == tenant_a
    lead = await leads.create(CRMLead(customer_id="c-a", notes=f"secret-{suffix}"))

    bind_crm_tenant(tenant_b)
    with pytest.raises(NotFoundError):
        await leads.get(lead.lead_id)
    listed_b = await leads.list_leads()
    assert all(item.lead_id != lead.lead_id for item in listed_b)

    bind_crm_tenant(tenant_a)
    owned = await leads.get(lead.lead_id)
    assert owned.notes == f"secret-{suffix}"
    listed_a = await leads.list_leads()
    assert any(item.lead_id == lead.lead_id for item in listed_a)

    await leads.delete(lead.lead_id)


@pytest.mark.asyncio
async def test_lead_customer_deal_lifecycle_survives_restart(postgres_crm_mode):
    await _ensure_postgres_tables()
    suffix = uuid.uuid4().hex[:12]
    tenant = f"life-{suffix}"
    bind_crm_tenant(tenant)
    persist = PostgresCRMPersistence()
    leads = LeadService(persistence=persist)
    deals = DealService(persistence=persist)
    customers = CustomerProfileService(persistence=persist)

    profile = await customers.create(CustomerProfile(first_name="Pat", last_name="Ng", email=f"pat-{suffix}@ex.com"))
    updated_customer = await customers.update(profile.customer_id, phone="+1555")
    assert updated_customer.phone == "+1555"
    lead = await leads.create(
        CRMLead(customer_id=profile.customer_id, dealer_id="d-life", notes="open", source=LeadSource.WEB)
    )
    contacted = await leads.set_status(lead.lead_id, CRMLeadStatus.CONTACTED)
    assigned = await leads.assign(lead.lead_id, "mgr-life")
    assert contacted.status == CRMLeadStatus.CONTACTED
    assert assigned.assigned_agent_id == "mgr-life"
    listed_contacted = await leads.list_leads(status=CRMLeadStatus.CONTACTED, customer_id=profile.customer_id)
    assert any(item.lead_id == lead.lead_id for item in listed_contacted)
    await leads.qualify(lead.lead_id, agent_id="mgr-life")

    pipeline = SalesPipelineEngine(leads=leads, deals=deals, persistence=persist)
    deal = await pipeline.convert_lead_to_deal(lead.lead_id, amount=22000)
    again = await pipeline.convert_lead_to_deal(lead.lead_id, amount=1)
    assert again.deal_id == deal.deal_id
    staged = await deals.update_stage(deal.deal_id, DealStage.PROPOSAL)

    listed_leads = await leads.list_leads(status=CRMLeadStatus.CONVERTED, customer_id=profile.customer_id)
    listed_customers = await customers.list_profiles(email=f"pat-{suffix}@ex.com")
    listed_deals = await deals.list_deals(stage=DealStage.PROPOSAL, customer_id=profile.customer_id)
    assert any(item.lead_id == lead.lead_id for item in listed_leads)
    assert any(item.customer_id == profile.customer_id for item in listed_customers)
    assert any(item.deal_id == staged.deal_id for item in listed_deals)

    ids = (profile.customer_id, lead.lead_id, deal.deal_id)
    from database.session import shutdown_db

    await shutdown_db()
    reset_crm_persistence()
    bind_crm_tenant(tenant)
    persist2 = PostgresCRMPersistence()
    leads2 = LeadService(persistence=persist2)
    deals2 = DealService(persistence=persist2)
    customers2 = CustomerProfileService(persistence=persist2)

    restored_customer = await customers2.get(ids[0])
    restored_lead = await leads2.get(ids[1])
    restored_deal = await deals2.get(ids[2])
    assert restored_customer.phone == "+1555"
    assert restored_customer.email == f"pat-{suffix}@ex.com"
    assert restored_lead.status.value == "converted"
    assert restored_lead.assigned_agent_id == "mgr-life"
    assert restored_lead.metadata.get("converted_deal_id") == ids[2]
    assert restored_deal.stage.value == "proposal"
    assert restored_deal.amount == 22000
    assert restored_deal.customer_id == ids[0]
    listed_after = await leads2.list_leads(customer_id=ids[0])
    assert any(item.lead_id == ids[1] for item in listed_after)

    await customers2.delete(ids[0])
    await leads2.delete(ids[1])
    await deals2.delete(ids[2])


@pytest.mark.asyncio
async def test_tenant_isolation_customers_and_deals(postgres_crm_mode):
    await _ensure_postgres_tables()
    suffix = uuid.uuid4().hex[:12]
    tenant_a = f"iso-a-{suffix}"
    tenant_b = f"iso-b-{suffix}"
    persist = PostgresCRMPersistence()
    customers = CustomerProfileService(persistence=persist)
    deals = DealService(persistence=persist)

    bind_crm_tenant(tenant_a)
    profile = await customers.create(CustomerProfile(email=f"a-{suffix}@ex.com", first_name="A"))
    deal = await deals.create(CRMDeal(customer_id=profile.customer_id, amount=111, dealer_id="d-a"))

    bind_crm_tenant(tenant_b)
    with pytest.raises(NotFoundError):
        await customers.get(profile.customer_id)
    with pytest.raises(NotFoundError):
        await deals.get(deal.deal_id)
    assert all(item.customer_id != profile.customer_id for item in await customers.list_profiles())
    assert all(item.deal_id != deal.deal_id for item in await deals.list_deals())

    bind_crm_tenant(tenant_a)
    assert (await customers.get(profile.customer_id)).email == f"a-{suffix}@ex.com"
    assert (await deals.get(deal.deal_id)).amount == 111

    await deals.delete(deal.deal_id)
    await customers.delete(profile.customer_id)


@pytest.mark.asyncio
async def test_tasks_and_activities_survive_engine_restart(postgres_crm_mode):
    await _ensure_postgres_tables()
    suffix = uuid.uuid4().hex[:12]
    tenant = f"wf-{suffix}"
    bind_crm_tenant(tenant)
    persist = PostgresCRMPersistence()
    tasks = TaskService(persistence=persist)
    activities = ActivityService(persistence=persist)
    customers = CustomerProfileService(persistence=persist)
    leads = LeadService(persistence=persist)
    deals = DealService(persistence=persist)

    profile = await customers.create(CustomerProfile(first_name="Task", last_name="Owner", email=f"task-{suffix}@ex.com"))
    lead = await leads.create(CRMLead(customer_id=profile.customer_id, notes=f"wf-{suffix}"))
    deal = await deals.create(CRMDeal(customer_id=profile.customer_id, amount=9000, stage=DealStage.PROSPECT))
    task = await tasks.create(
        CRMTask(
            title=f"Call {suffix}",
            description="follow up",
            customer_id=profile.customer_id,
            lead_id=lead.lead_id,
            deal_id=deal.deal_id,
            assigned_agent_id="agent-wf",
            priority=TaskPriority.HIGH,
            due_at=1.0,
        )
    )
    await tasks.complete(task.task_id)
    note = await activities.record(
        Interaction(
            customer_id=profile.customer_id,
            lead_id=lead.lead_id,
            deal_id=deal.deal_id,
            interaction_type=InteractionType.NOTE,
            subject="Manual note",
            body=suffix,
        )
    )
    ids = (profile.customer_id, lead.lead_id, deal.deal_id, task.task_id, note.interaction_id)

    from database.session import shutdown_db

    await shutdown_db()
    reset_crm_persistence()
    bind_crm_tenant(tenant)
    persist2 = PostgresCRMPersistence()
    tasks2 = TaskService(persistence=persist2)
    activities2 = ActivityService(persistence=persist2)
    deals2 = DealService(persistence=persist2)

    restored_task = await tasks2.get(ids[3])
    assert restored_task.title == f"Call {suffix}"
    assert restored_task.status == TaskStatus.COMPLETED
    assert restored_task.customer_id == ids[0]
    assert restored_task.lead_id == ids[1]
    assert restored_task.deal_id == ids[2]
    restored_note = await activities2.get_interaction(ids[4])
    assert restored_note.body == suffix
    timeline = await activities2.entity_timeline(customer_id=ids[0])
    assert any(item["activity_id"] == ids[4] for item in timeline)
    restored_deal = await deals2.get(ids[2])
    assert restored_deal.stage == DealStage.PROSPECT

    await tasks2.delete(ids[3])
    await activities2._records().delete_activity(ids[4])
    await deals2.delete(ids[2])


@pytest.mark.asyncio
async def test_pipeline_stage_survives_restart_and_tenant_isolation(postgres_crm_mode):
    await _ensure_postgres_tables()
    suffix = uuid.uuid4().hex[:12]
    tenant_a = f"pipe-a-{suffix}"
    tenant_b = f"pipe-b-{suffix}"
    persist = PostgresCRMPersistence()
    deals = DealService(persistence=persist)
    pipeline = SalesPipelineEngine(deals=deals, persistence=persist)

    bind_crm_tenant(tenant_a)
    deal = await deals.create(CRMDeal(amount=3333, dealer_id="d-pipe"))
    moved = await pipeline.set_stage(deal.deal_id, DealStage.NEGOTIATION)
    assert moved.stage == DealStage.NEGOTIATION
    view_a = await pipeline.pipeline_view()
    assert any(item["deal_id"] == deal.deal_id for item in view_a["stages"].get("negotiation", []))

    bind_crm_tenant(tenant_b)
    view_b = await pipeline.pipeline_view()
    assert all(item["deal_id"] != deal.deal_id for rows in view_b["stages"].values() for item in rows)
    with pytest.raises(NotFoundError):
        await deals.get(deal.deal_id)

    from database.session import shutdown_db

    await shutdown_db()
    reset_crm_persistence()
    bind_crm_tenant(tenant_a)
    persist2 = PostgresCRMPersistence()
    deals2 = DealService(persistence=persist2)
    pipeline2 = SalesPipelineEngine(deals=deals2, persistence=persist2)
    restored = await deals2.get(deal.deal_id)
    assert restored.stage == DealStage.NEGOTIATION
    view2 = await pipeline2.pipeline_view()
    assert any(item["deal_id"] == deal.deal_id for item in view2["stages"].get("negotiation", []))
    await deals2.delete(deal.deal_id)


@pytest.mark.asyncio
async def test_conversion_creates_customer_and_is_idempotent_across_restart(postgres_crm_mode):
    await _ensure_postgres_tables()
    suffix = uuid.uuid4().hex[:12]
    tenant = f"cvt-{suffix}"
    bind_crm_tenant(tenant)
    persist = PostgresCRMPersistence()
    leads = LeadService(persistence=persist)
    deals = DealService(persistence=persist)
    customers = CustomerProfileService(persistence=persist)
    activities = ActivityService(persistence=persist)
    pipeline = SalesPipelineEngine(leads=leads, deals=deals, persistence=persist)

    lead = await leads.create(CRMLead(notes=f"Walk-in {suffix}", dealer_id="d-cvt"))
    assert lead.customer_id == ""
    deal = await pipeline.convert_lead_to_deal(lead.lead_id, amount=15000, agent_id="agt-cvt")
    again = await pipeline.convert_lead_to_deal(lead.lead_id, amount=1)
    assert again.deal_id == deal.deal_id
    assert deal.customer_id
    profiles = await customers.list_profiles()
    assert sum(1 for p in profiles if p.customer_id == deal.customer_id) == 1
    assert sum(1 for d in await deals.list_deals() if d.customer_id == deal.customer_id) == 1
    converted_events = await activities.list_activities(lead_id=lead.lead_id, activity_type=InteractionType.LEAD_CONVERTED)
    assert len(converted_events) == 1

    ids = (lead.lead_id, deal.deal_id, deal.customer_id)
    from database.session import shutdown_db

    await shutdown_db()
    reset_crm_persistence()
    bind_crm_tenant(tenant)
    persist2 = PostgresCRMPersistence()
    leads2 = LeadService(persistence=persist2)
    deals2 = DealService(persistence=persist2)
    customers2 = CustomerProfileService(persistence=persist2)
    pipeline2 = SalesPipelineEngine(leads=leads2, deals=deals2, persistence=persist2)

    restored_lead = await leads2.get(ids[0])
    restored_deal = await deals2.get(ids[1])
    restored_customer = await customers2.get(ids[2])
    assert restored_lead.status == CRMLeadStatus.CONVERTED
    assert restored_lead.metadata.get("converted_deal_id") == ids[1]
    assert restored_lead.metadata.get("converted_customer_id") == ids[2]
    assert restored_lead.customer_id == ids[2]
    assert restored_deal.amount == 15000
    assert restored_customer.preferences.get("source_lead_id") == ids[0]
    third = await pipeline2.convert_lead_to_deal(ids[0], amount=99)
    assert third.deal_id == ids[1]
    assert sum(1 for p in await customers2.list_profiles() if p.customer_id == ids[2]) == 1

    await deals2.delete(ids[1])
    await leads2.delete(ids[0])
    await customers2.delete(ids[2])


@pytest.mark.asyncio
async def test_task_and_activity_tenant_isolation(postgres_crm_mode):
    await _ensure_postgres_tables()
    suffix = uuid.uuid4().hex[:12]
    tenant_a = f"ta-{suffix}"
    tenant_b = f"tb-{suffix}"
    persist = PostgresCRMPersistence()
    tasks = TaskService(persistence=persist)
    activities = ActivityService(persistence=persist)

    bind_crm_tenant(tenant_a)
    task = await tasks.create(CRMTask(title=f"secret-{suffix}", assigned_agent_id="a"))
    note = await activities.record(Interaction(subject="secret", body=suffix, interaction_type=InteractionType.NOTE))

    bind_crm_tenant(tenant_b)
    with pytest.raises(NotFoundError):
        await tasks.get(task.task_id)
    with pytest.raises(NotFoundError):
        await activities.get_interaction(note.interaction_id)
    assert all(item.task_id != task.task_id for item in await tasks.list_tasks())
    assert all(item.interaction_id != note.interaction_id for item in await activities.list_activities())

    bind_crm_tenant(tenant_a)
    assert (await tasks.get(task.task_id)).title == f"secret-{suffix}"
    await tasks.delete(task.task_id)
    await activities._records().delete_activity(note.interaction_id)


@pytest.mark.asyncio
async def test_calls_emails_meetings_reminders_survive_restart(postgres_crm_mode):
    await _ensure_postgres_tables()
    suffix = uuid.uuid4().hex[:12]
    tenant = f"comm-{suffix}"
    bind_crm_tenant(tenant)
    persist = PostgresCRMPersistence()
    comms = CommunicationService(persistence=persist)
    calendar = CalendarService(persistence=persist)
    activities = ActivityService(persistence=persist)
    customers = CustomerProfileService(persistence=persist)
    profile = await customers.create(CustomerProfile(first_name="Comms", last_name="User", email=f"c-{suffix}@ex.com"))

    call = await comms.log_call(PhoneCall(customer_id=profile.customer_id, direction="inbound", duration_sec=42, notes=suffix))
    email = await comms.log_email(EmailMessage(customer_id=profile.customer_id, subject=f"sub-{suffix}", body="hello", status="logged"))
    meeting = await calendar.schedule_meeting(Meeting(customer_id=profile.customer_id, title=f"Meet {suffix}", location="showroom"))
    reminder = await calendar.create_reminder(Reminder(customer_id=profile.customer_id, message=f"ping-{suffix}", trigger_at=1.0))
    ids = (call.call_id, email.email_id, meeting.meeting_id, reminder.reminder_id, profile.customer_id)

    from database.session import shutdown_db

    await shutdown_db()
    reset_crm_persistence()
    bind_crm_tenant(tenant)
    persist2 = PostgresCRMPersistence()
    comms2 = CommunicationService(persistence=persist2)
    calendar2 = CalendarService(persistence=persist2)
    activities2 = ActivityService(persistence=persist2)

    restored_call = await comms2.get_call(ids[0])
    restored_email = await comms2.get_email(ids[1])
    restored_meeting = await calendar2.get_meeting(ids[2])
    restored_reminder = await calendar2.get_reminder(ids[3])
    assert restored_call.duration_sec == 42
    assert restored_email.subject == f"sub-{suffix}"
    assert restored_meeting.title == f"Meet {suffix}"
    assert restored_reminder.message == f"ping-{suffix}"
    timeline = await activities2.customer_timeline(ids[4])
    assert any(item.get("call_id") == ids[0] for item in timeline["calls"])
    assert any(item.get("activity_type") == "call" for item in timeline["items"])

    await comms2.delete_call(ids[0])
    await comms2.delete_email(ids[1])
    await calendar2.delete_meeting(ids[2])
    await calendar2.delete_reminder(ids[3])


@pytest.mark.asyncio
async def test_communications_tenant_isolation(postgres_crm_mode):
    await _ensure_postgres_tables()
    suffix = uuid.uuid4().hex[:12]
    persist = PostgresCRMPersistence()
    comms = CommunicationService(persistence=persist)
    calendar = CalendarService(persistence=persist)
    bind_crm_tenant(f"ca-{suffix}")
    call = await comms.log_call(PhoneCall(direction="outbound", notes="secret"))
    email = await comms.log_email(EmailMessage(subject="secret"))
    meeting = await calendar.schedule_meeting(Meeting(title="secret"))
    reminder = await calendar.create_reminder(Reminder(message="secret", trigger_at=9.0))
    bind_crm_tenant(f"cb-{suffix}")
    with pytest.raises(NotFoundError):
        await comms.get_call(call.call_id)
    with pytest.raises(NotFoundError):
        await comms.get_email(email.email_id)
    with pytest.raises(NotFoundError):
        await calendar.get_meeting(meeting.meeting_id)
    with pytest.raises(NotFoundError):
        await calendar.get_reminder(reminder.reminder_id)


@pytest.mark.asyncio
async def test_opportunity_is_deal_projection_across_restart(postgres_crm_mode):
    await _ensure_postgres_tables()
    suffix = uuid.uuid4().hex[:12]
    tenant = f"opp-{suffix}"
    bind_crm_tenant(tenant)
    persist = PostgresCRMPersistence()
    leads = LeadService(persistence=persist)
    deals = DealService(persistence=persist)
    pipeline = SalesPipelineEngine(leads=leads, deals=deals, persistence=persist)
    lead = await leads.create(CRMLead(notes=f"opp-{suffix}"))
    opp = await pipeline.convert_lead_to_opportunity(lead.lead_id, amount=7700)
    again = await pipeline.convert_lead_to_opportunity(lead.lead_id, amount=1)
    assert again.opportunity_id == opp.opportunity_id
    deal = await pipeline.open_deal_from_opportunity(opp.opportunity_id)
    assert deal.amount == 7700
    assert deal.deal_id == opp.opportunity_id or deal.opportunity_id == opp.opportunity_id

    from database.session import shutdown_db

    await shutdown_db()
    reset_crm_persistence()
    bind_crm_tenant(tenant)
    persist2 = PostgresCRMPersistence()
    leads2 = LeadService(persistence=persist2)
    deals2 = DealService(persistence=persist2)
    pipeline2 = SalesPipelineEngine(leads=leads2, deals=deals2, persistence=persist2)
    restored = await pipeline2.get_opportunity(opp.opportunity_id)
    assert restored.amount == 7700
    bind_crm_tenant(f"other-{suffix}")
    with pytest.raises(NotFoundError):
        await pipeline2.get_opportunity(opp.opportunity_id)
    listed = await pipeline2.list_opportunities()
    assert all(item.opportunity_id != opp.opportunity_id for item in listed)


@pytest.mark.asyncio
async def test_crm_metrics_survive_restart_and_ignore_store_overlays(postgres_crm_mode):
    await _ensure_postgres_tables()
    suffix = uuid.uuid4().hex[:12]
    tenant = f"metrics-{suffix}"
    bind_crm_tenant(tenant)
    persist = PostgresCRMPersistence()
    customers = CustomerProfileService(persistence=persist)
    leads = LeadService(persistence=persist)
    deals = DealService(persistence=persist)
    tasks = TaskService(persistence=persist)
    activities = ActivityService(persistence=persist)
    comms = CommunicationService(persistence=persist)
    calendar = CalendarService(persistence=persist)

    profile = await customers.create(CustomerProfile(first_name="Met", last_name="User", email=f"m-{suffix}@ex.com"))
    await leads.create(CRMLead(customer_id=profile.customer_id, notes=suffix))
    await deals.create(CRMDeal(customer_id=profile.customer_id, amount=3300, opportunity_id=""))
    await tasks.create(CRMTask(title=f"task-{suffix}", customer_id=profile.customer_id))
    await activities.record(Interaction(subject="note", customer_id=profile.customer_id))
    await comms.log_call(PhoneCall(customer_id=profile.customer_id, direction="inbound"))
    await comms.log_email(EmailMessage(customer_id=profile.customer_id, subject=suffix))
    await calendar.schedule_meeting(Meeting(customer_id=profile.customer_id, title=suffix))
    await calendar.create_reminder(Reminder(customer_id=profile.customer_id, message=suffix, trigger_at=2.0))

    before = await crm_metrics.collect(tenant)
    assert before["leads"] == 1
    assert before["customers"] == 1
    assert before["deals"] == 1
    assert before["tasks"] == 1
    assert before["calls"] == 1
    assert before["emails"] == 1
    assert before["meetings"] == 1
    assert before["reminders"] == 1
    assert before["opportunities"] == before["deals"]
    assert before["activities"] >= 1

    from applications.auto_marketplace.shared.store import marketplace_store

    assert not hasattr(marketplace_store, "crm_leads")
    assert not hasattr(marketplace_store, "crm_deals")
    still = await crm_metrics.collect(tenant)
    assert still["leads"] == 1
    assert still["deals"] == 1

    from database.session import shutdown_db

    await shutdown_db()
    reset_crm_persistence()
    bind_crm_tenant(tenant)
    after = await crm_metrics.collect(tenant)
    assert after["leads"] == before["leads"]
    assert after["customers"] == before["customers"]
    assert after["deals"] == before["deals"]
    assert after["tasks"] == before["tasks"]
    assert after["calls"] == before["calls"]
    assert after["emails"] == before["emails"]
    assert after["meetings"] == before["meetings"]
    assert after["reminders"] == before["reminders"]
    assert after["opportunities"] == after["deals"]
    await crm_metrics.refresh(tenant)
    from applications.auto_marketplace import auto_marketplace

    health = auto_marketplace.health()
    assert health["crm_leads"] == 1
    assert health["crm_opportunities"] == 1


@pytest.mark.asyncio
async def test_crm_metrics_tenant_isolation_postgres(postgres_crm_mode):
    await _ensure_postgres_tables()
    suffix = uuid.uuid4().hex[:12]
    persist = PostgresCRMPersistence()
    leads = LeadService(persistence=persist)
    bind_crm_tenant(f"ma-{suffix}")
    await leads.create(CRMLead(notes="alpha"))
    counts_a = await crm_metrics.collect(f"ma-{suffix}")
    counts_b = await crm_metrics.collect(f"mb-{suffix}")
    assert counts_a["leads"] == 1
    assert counts_b["leads"] == 0
    assert counts_b["deals"] == 0
    assert counts_b["calls"] == 0
    assert counts_b["tasks"] == 0
    assert counts_b["activities"] == 0
