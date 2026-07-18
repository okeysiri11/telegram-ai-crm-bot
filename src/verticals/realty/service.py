# Realty vertical service.

from __future__ import annotations

from typing import Any

from platform_legacy import legacy
from src.platform.layers.base_service import BaseService
from src.verticals import get_vertical


class RealtyVerticalService(BaseService):
    vertical = get_vertical("realty")

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
        return await legacy.crm.ingest_lead_from_deep_link(
            telegram_user_id=telegram_user_id,
            vertical=cls.vertical.code,
            **fields,
        )
