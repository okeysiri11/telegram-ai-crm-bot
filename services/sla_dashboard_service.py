# SlaDashboardService — SLA dashboard read API (no business calculations).

from __future__ import annotations

from typing import Any

from database.session import get_session
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
            return await SLARepository(session).get_sla_statistics()


sla_dashboard_service = SlaDashboardService()
