# SlaDashboardService — SLA dashboard read API (no business calculations).

from __future__ import annotations

from typing import Any

from database.session import get_session
from repositories.owner_repository import OwnerRepository
from repositories.sla_repository import SLARepository


class SlaDashboardService:
    @staticmethod
    async def get_overdue(*, limit: int = 100) -> list[dict[str, Any]]:
        async with get_session() as session:
            return await SLARepository(session).get_overdue_requests(limit=limit)

    @staticmethod
    async def get_at_risk(*, limit: int = 100) -> list[dict[str, Any]]:
        async with get_session() as session:
            return await SLARepository(session).get_risk_requests(limit=limit)

    @staticmethod
    async def get_statistics() -> dict[str, Any]:
        async with get_session() as session:
            stats = await SLARepository(session).get_sla_statistics()
            owner_kpi = await OwnerRepository(session).get_owner_escalation_kpi()
        stats.update(owner_kpi)
        return stats

    @staticmethod
    async def get_owner_escalated(*, limit: int = 100) -> list[dict[str, Any]]:
        async with get_session() as session:
            return await SLARepository(session).get_owner_escalated_requests(limit=limit)


sla_dashboard_service = SlaDashboardService()
