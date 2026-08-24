"""Sprint 1 Durable CRM — PostgreSQL restart persistence and tenant isolation."""

from __future__ import annotations

import os
import uuid

import pytest

from applications.auto_marketplace.crm.models import CRMDeal, CRMLead, CRMLeadStatus, CustomerProfile, DealStage, LeadSource
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
