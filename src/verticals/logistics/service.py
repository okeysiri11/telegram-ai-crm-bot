# Logistics vertical service.

from __future__ import annotations

from typing import Any

from src.platform.layers.base_service import BaseService
from src.verticals import get_vertical


class LogisticsVerticalService(BaseService):
    vertical = get_vertical("logistics")

    @classmethod
    async def health(cls) -> dict[str, Any]:
        return {
            "vertical": cls.vertical.code,
            "maturity": cls.vertical.maturity,
            "scaffold": True,
            "capabilities": list(cls.vertical.capabilities),
        }

    @classmethod
    async def ingest_lead(
        cls,
        *,
        telegram_user_id: int,
        **fields: Any,
    ) -> dict[str, Any]:
        from services.pg_lead_engine import LeadEngineV1

        return await LeadEngineV1.ingest_from_deep_link(
            telegram_user_id=telegram_user_id,
            vertical=cls.vertical.code,
            **fields,
        )
