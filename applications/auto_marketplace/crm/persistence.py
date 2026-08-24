"""CRM persistence backends — Postgres is the production source of truth.

Set AUTO_CRM_PERSISTENCE=memory only for isolated unit tests. Production and
restart-durability tests leave the variable unset (or set to postgres).
"""

from __future__ import annotations

import os
from typing import Protocol

from applications.auto_marketplace.crm.models import (
    CRMDeal,
    CRMLead,
    CRMLeadStatus,
    CustomerProfile,
    DealStage,
    LeadSource,
)
from applications.auto_marketplace.crm.tenant import current_crm_tenant
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store

_MEMORY_MODES = frozenset({"memory", "mem", "in_memory", "in-memory"})


def crm_persistence_mode() -> str:
    raw = os.environ.get("AUTO_CRM_PERSISTENCE", "").strip().lower()
    if raw in _MEMORY_MODES:
        return "memory"
    return "postgres"


def _lead_from_payload(data: dict) -> CRMLead:
    source_raw = data.get("source", LeadSource.WEB.value)
    status_raw = data.get("status", CRMLeadStatus.NEW.value)
    try:
        source = LeadSource(str(source_raw))
    except ValueError:
        source = LeadSource.WEB
    try:
        status = CRMLeadStatus(str(status_raw))
    except ValueError:
        status = CRMLeadStatus.NEW
    return CRMLead(
        lead_id=str(data.get("lead_id") or ""),
        customer_id=str(data.get("customer_id") or ""),
        vehicle_id=str(data.get("vehicle_id") or ""),
        dealer_id=str(data.get("dealer_id") or ""),
        source=source,
        status=status,
        score=float(data.get("score") or 0.0),
        assigned_agent_id=str(data.get("assigned_agent_id") or ""),
        notes=str(data.get("notes") or ""),
        metadata=dict(data.get("metadata") or {}) if isinstance(data.get("metadata"), dict) else {},
        created_at=float(data.get("created_at") or 0.0),
        qualified_at=float(data["qualified_at"]) if data.get("qualified_at") is not None else None,
    )


def _deal_from_payload(data: dict) -> CRMDeal:
    stage_raw = data.get("stage", DealStage.PROSPECT.value)
    try:
        stage = DealStage(str(stage_raw))
    except ValueError:
        stage = DealStage.PROSPECT
    return CRMDeal(
        deal_id=str(data.get("deal_id") or ""),
        opportunity_id=str(data.get("opportunity_id") or ""),
        customer_id=str(data.get("customer_id") or ""),
        dealer_id=str(data.get("dealer_id") or ""),
        vehicle_id=str(data.get("vehicle_id") or ""),
        stage=stage,
        amount=float(data.get("amount") or 0.0),
        probability=float(data.get("probability") or 0.1),
        win=data.get("win"),
        owner_agent_id=str(data.get("owner_agent_id") or ""),
        created_at=float(data.get("created_at") or 0.0),
        closed_at=float(data["closed_at"]) if data.get("closed_at") is not None else None,
    )


def _customer_from_payload(data: dict) -> CustomerProfile:
    return CustomerProfile(
        customer_id=str(data.get("customer_id") or ""),
        first_name=str(data.get("first_name") or ""),
        last_name=str(data.get("last_name") or ""),
        email=str(data.get("email") or ""),
        phone=str(data.get("phone") or ""),
        segment=str(data.get("segment") or "standard"),
        intent_score=float(data.get("intent_score") or 0.0),
        lifetime_value=float(data.get("lifetime_value") or 0.0),
        preferences=dict(data.get("preferences") or {}) if isinstance(data.get("preferences"), dict) else {},
        tags=list(data.get("tags") or []) if isinstance(data.get("tags"), list) else [],
        owner_agent_id=str(data.get("owner_agent_id") or ""),
        created_at=float(data.get("created_at") or 0.0),
    )


class CRMPersistence(Protocol):
    backend: str

    async def save_customer(self, profile: CustomerProfile, tenant_id: str | None = None) -> CustomerProfile: ...
    async def get_customer(self, customer_id: str, tenant_id: str | None = None) -> CustomerProfile | None: ...
    async def list_customers(self, tenant_id: str | None = None) -> list[CustomerProfile]: ...
    async def delete_customer(self, customer_id: str, tenant_id: str | None = None) -> bool: ...
    async def count_customers(self, tenant_id: str | None = None) -> int: ...

    async def save_lead(self, lead: CRMLead, tenant_id: str | None = None) -> CRMLead: ...
    async def get_lead(self, lead_id: str, tenant_id: str | None = None) -> CRMLead | None: ...
    async def list_leads(self, tenant_id: str | None = None) -> list[CRMLead]: ...
    async def delete_lead(self, lead_id: str, tenant_id: str | None = None) -> bool: ...
    async def count_leads(self, tenant_id: str | None = None) -> int: ...

    async def save_deal(self, deal: CRMDeal, tenant_id: str | None = None) -> CRMDeal: ...
    async def get_deal(self, deal_id: str, tenant_id: str | None = None) -> CRMDeal | None: ...
    async def list_deals(self, tenant_id: str | None = None) -> list[CRMDeal]: ...
    async def delete_deal(self, deal_id: str, tenant_id: str | None = None) -> bool: ...
    async def count_deals(self, tenant_id: str | None = None) -> int: ...


def _tid(tenant_id: str | None) -> str:
    return tenant_id or current_crm_tenant()


class MemoryCRMPersistence:
    """In-process store used only when AUTO_CRM_PERSISTENCE=memory (unit tests)."""

    backend = "memory"

    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self._store = store or marketplace_store
        self._customer_tenants: dict[str, str] = {}
        self._lead_tenants: dict[str, str] = {}
        self._deal_tenants: dict[str, str] = {}

    def _visible(self, entity_id: str, tenant_map: dict[str, str], tenant_id: str) -> bool:
        return tenant_map.get(entity_id, "default") == tenant_id

    async def save_customer(self, profile: CustomerProfile, tenant_id: str | None = None) -> CustomerProfile:
        tid = _tid(tenant_id)
        self._customer_tenants[profile.customer_id] = tid
        return self._store.customer_profiles.save(profile.customer_id, profile)

    async def get_customer(self, customer_id: str, tenant_id: str | None = None) -> CustomerProfile | None:
        tid = _tid(tenant_id)
        profile = self._store.customer_profiles.get(customer_id)
        if profile is None or not self._visible(customer_id, self._customer_tenants, tid):
            return None
        return profile

    async def list_customers(self, tenant_id: str | None = None) -> list[CustomerProfile]:
        tid = _tid(tenant_id)
        return [
            p
            for p in self._store.customer_profiles.list_all()
            if self._visible(p.customer_id, self._customer_tenants, tid)
        ]

    async def delete_customer(self, customer_id: str, tenant_id: str | None = None) -> bool:
        if await self.get_customer(customer_id, tenant_id) is None:
            return False
        self._customer_tenants.pop(customer_id, None)
        return self._store.customer_profiles.delete(customer_id)

    async def count_customers(self, tenant_id: str | None = None) -> int:
        return len(await self.list_customers(tenant_id))

    async def save_lead(self, lead: CRMLead, tenant_id: str | None = None) -> CRMLead:
        tid = _tid(tenant_id)
        self._lead_tenants[lead.lead_id] = tid
        return self._store.crm_leads.save(lead.lead_id, lead)

    async def get_lead(self, lead_id: str, tenant_id: str | None = None) -> CRMLead | None:
        tid = _tid(tenant_id)
        lead = self._store.crm_leads.get(lead_id)
        if lead is None or not self._visible(lead_id, self._lead_tenants, tid):
            return None
        return lead

    async def list_leads(self, tenant_id: str | None = None) -> list[CRMLead]:
        tid = _tid(tenant_id)
        return [lead for lead in self._store.crm_leads.list_all() if self._visible(lead.lead_id, self._lead_tenants, tid)]

    async def delete_lead(self, lead_id: str, tenant_id: str | None = None) -> bool:
        if await self.get_lead(lead_id, tenant_id) is None:
            return False
        self._lead_tenants.pop(lead_id, None)
        return self._store.crm_leads.delete(lead_id)

    async def count_leads(self, tenant_id: str | None = None) -> int:
        return len(await self.list_leads(tenant_id))

    async def save_deal(self, deal: CRMDeal, tenant_id: str | None = None) -> CRMDeal:
        tid = _tid(tenant_id)
        self._deal_tenants[deal.deal_id] = tid
        return self._store.crm_deals.save(deal.deal_id, deal)

    async def get_deal(self, deal_id: str, tenant_id: str | None = None) -> CRMDeal | None:
        tid = _tid(tenant_id)
        deal = self._store.crm_deals.get(deal_id)
        if deal is None or not self._visible(deal_id, self._deal_tenants, tid):
            return None
        return deal

    async def list_deals(self, tenant_id: str | None = None) -> list[CRMDeal]:
        tid = _tid(tenant_id)
        return [d for d in self._store.crm_deals.list_all() if self._visible(d.deal_id, self._deal_tenants, tid)]

    async def delete_deal(self, deal_id: str, tenant_id: str | None = None) -> bool:
        if await self.get_deal(deal_id, tenant_id) is None:
            return False
        self._deal_tenants.pop(deal_id, None)
        return self._store.crm_deals.delete(deal_id)

    async def count_deals(self, tenant_id: str | None = None) -> int:
        return len(await self.list_deals(tenant_id))


class PostgresCRMPersistence:
    """Production backend: PostgreSQL is the durable source of truth."""

    backend = "postgres"

    async def save_customer(self, profile: CustomerProfile, tenant_id: str | None = None) -> CustomerProfile:
        from database.session import get_session
        from repositories.auto_marketplace_crm_repository import AutoMarketplaceCrmRepository

        tid = _tid(tenant_id)
        async with get_session() as session:
            repo = AutoMarketplaceCrmRepository(session)
            await repo.upsert_customer(tid, profile.to_dict())
        return profile

    async def get_customer(self, customer_id: str, tenant_id: str | None = None) -> CustomerProfile | None:
        from database.session import get_session
        from repositories.auto_marketplace_crm_repository import AutoMarketplaceCrmRepository

        tid = _tid(tenant_id)
        async with get_session() as session:
            repo = AutoMarketplaceCrmRepository(session)
            data = await repo.get_customer(tid, customer_id)
        return _customer_from_payload(data) if data else None

    async def list_customers(self, tenant_id: str | None = None) -> list[CustomerProfile]:
        from database.session import get_session
        from repositories.auto_marketplace_crm_repository import AutoMarketplaceCrmRepository

        tid = _tid(tenant_id)
        async with get_session() as session:
            repo = AutoMarketplaceCrmRepository(session)
            rows = await repo.list_customers(tid)
        return [_customer_from_payload(row) for row in rows]

    async def delete_customer(self, customer_id: str, tenant_id: str | None = None) -> bool:
        from database.session import get_session
        from repositories.auto_marketplace_crm_repository import AutoMarketplaceCrmRepository

        tid = _tid(tenant_id)
        async with get_session() as session:
            repo = AutoMarketplaceCrmRepository(session)
            return await repo.delete_customer(tid, customer_id)

    async def count_customers(self, tenant_id: str | None = None) -> int:
        from database.session import get_session
        from repositories.auto_marketplace_crm_repository import AutoMarketplaceCrmRepository

        tid = _tid(tenant_id)
        async with get_session() as session:
            repo = AutoMarketplaceCrmRepository(session)
            return await repo.count_customers(tid)

    async def save_lead(self, lead: CRMLead, tenant_id: str | None = None) -> CRMLead:
        from database.session import get_session
        from repositories.auto_marketplace_crm_repository import AutoMarketplaceCrmRepository

        tid = _tid(tenant_id)
        async with get_session() as session:
            repo = AutoMarketplaceCrmRepository(session)
            await repo.upsert_lead(tid, lead.to_dict())
        return lead

    async def get_lead(self, lead_id: str, tenant_id: str | None = None) -> CRMLead | None:
        from database.session import get_session
        from repositories.auto_marketplace_crm_repository import AutoMarketplaceCrmRepository

        tid = _tid(tenant_id)
        async with get_session() as session:
            repo = AutoMarketplaceCrmRepository(session)
            data = await repo.get_lead(tid, lead_id)
        return _lead_from_payload(data) if data else None

    async def list_leads(self, tenant_id: str | None = None) -> list[CRMLead]:
        from database.session import get_session
        from repositories.auto_marketplace_crm_repository import AutoMarketplaceCrmRepository

        tid = _tid(tenant_id)
        async with get_session() as session:
            repo = AutoMarketplaceCrmRepository(session)
            rows = await repo.list_leads(tid)
        return [_lead_from_payload(row) for row in rows]

    async def delete_lead(self, lead_id: str, tenant_id: str | None = None) -> bool:
        from database.session import get_session
        from repositories.auto_marketplace_crm_repository import AutoMarketplaceCrmRepository

        tid = _tid(tenant_id)
        async with get_session() as session:
            repo = AutoMarketplaceCrmRepository(session)
            return await repo.delete_lead(tid, lead_id)

    async def count_leads(self, tenant_id: str | None = None) -> int:
        from database.session import get_session
        from repositories.auto_marketplace_crm_repository import AutoMarketplaceCrmRepository

        tid = _tid(tenant_id)
        async with get_session() as session:
            repo = AutoMarketplaceCrmRepository(session)
            return await repo.count_leads(tid)

    async def save_deal(self, deal: CRMDeal, tenant_id: str | None = None) -> CRMDeal:
        from database.session import get_session
        from repositories.auto_marketplace_crm_repository import AutoMarketplaceCrmRepository

        tid = _tid(tenant_id)
        async with get_session() as session:
            repo = AutoMarketplaceCrmRepository(session)
            await repo.upsert_deal(tid, deal.to_dict())
        return deal

    async def get_deal(self, deal_id: str, tenant_id: str | None = None) -> CRMDeal | None:
        from database.session import get_session
        from repositories.auto_marketplace_crm_repository import AutoMarketplaceCrmRepository

        tid = _tid(tenant_id)
        async with get_session() as session:
            repo = AutoMarketplaceCrmRepository(session)
            data = await repo.get_deal(tid, deal_id)
        return _deal_from_payload(data) if data else None

    async def list_deals(self, tenant_id: str | None = None) -> list[CRMDeal]:
        from database.session import get_session
        from repositories.auto_marketplace_crm_repository import AutoMarketplaceCrmRepository

        tid = _tid(tenant_id)
        async with get_session() as session:
            repo = AutoMarketplaceCrmRepository(session)
            rows = await repo.list_deals(tid)
        return [_deal_from_payload(row) for row in rows]

    async def delete_deal(self, deal_id: str, tenant_id: str | None = None) -> bool:
        from database.session import get_session
        from repositories.auto_marketplace_crm_repository import AutoMarketplaceCrmRepository

        tid = _tid(tenant_id)
        async with get_session() as session:
            repo = AutoMarketplaceCrmRepository(session)
            return await repo.delete_deal(tid, deal_id)

    async def count_deals(self, tenant_id: str | None = None) -> int:
        from database.session import get_session
        from repositories.auto_marketplace_crm_repository import AutoMarketplaceCrmRepository

        tid = _tid(tenant_id)
        async with get_session() as session:
            repo = AutoMarketplaceCrmRepository(session)
            return await repo.count_deals(tid)


_persist: CRMPersistence | None = None


def get_crm_persistence() -> CRMPersistence:
    global _persist
    mode = crm_persistence_mode()
    if _persist is not None and _persist.backend == mode:
        return _persist
    if mode == "memory":
        _persist = MemoryCRMPersistence()
    else:
        _persist = PostgresCRMPersistence()
    return _persist


def reset_crm_persistence() -> None:
    """Drop the cached backend so tests can switch memory/postgres."""
    global _persist
    _persist = None
