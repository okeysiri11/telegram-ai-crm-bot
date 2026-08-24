"""Durable Auto Marketplace CRM metrics — PostgreSQL is the production source of truth.

Synchronous callers (health, foundation dashboards) read a process snapshot.
Async callers refresh that snapshot from CRM persistence. Never use asyncio.run().
"""

from __future__ import annotations

from typing import Any

from applications.auto_marketplace.crm.persistence import get_crm_persistence

_EMPTY: dict[str, Any] = {
    "customers": 0,
    "leads": 0,
    "deals": 0,
    "tasks": 0,
    "activities": 0,
    "calls": 0,
    "emails": 0,
    "meetings": 0,
    "reminders": 0,
    "opportunities": 0,
    "leads_by_status": {},
    "deals_by_stage": {},
    "backend": "",
}


class CRMMetricsService:
    """Tenant-scoped CRM counts derived from CRMPersistence (postgres in production)."""

    def __init__(self) -> None:
        self._cache: dict[str, Any] = dict(_EMPTY)

    def cached(self) -> dict[str, Any]:
        return dict(self._cache)

    def reset(self) -> None:
        self._cache = dict(_EMPTY)

    async def collect(self, tenant_id: str | None = None) -> dict[str, Any]:
        records = get_crm_persistence()
        leads = await records.list_leads(tenant_id)
        deals = await records.list_deals(tenant_id)
        leads_by_status: dict[str, int] = {}
        for lead in leads:
            key = lead.status.value if hasattr(lead.status, "value") else str(lead.status)
            leads_by_status[key] = leads_by_status.get(key, 0) + 1
        deals_by_stage: dict[str, int] = {}
        for deal in deals:
            key = deal.stage.value if hasattr(deal.stage, "value") else str(deal.stage)
            deals_by_stage[key] = deals_by_stage.get(key, 0) + 1
        deal_count = await records.count_deals(tenant_id)
        return {
            "customers": await records.count_customers(tenant_id),
            "leads": await records.count_leads(tenant_id),
            "deals": deal_count,
            "tasks": await records.count_tasks(tenant_id),
            "activities": await records.count_activities(tenant_id),
            "calls": await records.count_calls(tenant_id),
            "emails": await records.count_emails(tenant_id),
            "meetings": await records.count_meetings(tenant_id),
            "reminders": await records.count_reminders(tenant_id),
            "opportunities": deal_count,
            "leads_by_status": leads_by_status,
            "deals_by_stage": deals_by_stage,
            "backend": records.backend,
        }

    async def refresh(self, tenant_id: str | None = None) -> dict[str, Any]:
        snapshot = await self.collect(tenant_id)
        self._cache = dict(snapshot)
        return self.cached()

    async def refresh_for_request(self, request: Any) -> dict[str, Any]:
        from applications.auto_marketplace.crm.tenant import bind_crm_tenant, tenant_from_request

        bind_crm_tenant(tenant_from_request(request))
        return await self.refresh()


crm_metrics = CRMMetricsService()
