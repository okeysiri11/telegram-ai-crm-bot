# Auto vertical service — delegates to legacy via platform_legacy adapters.

from __future__ import annotations

import uuid
from typing import Any

from platform_legacy import legacy
from src.platform.layers.base_service import BaseService
from src.verticals import get_vertical


class AutoVerticalService(BaseService):
    vertical = get_vertical("auto")

    @classmethod
    async def health(cls) -> dict[str, Any]:
        return {
            "vertical": cls.vertical.code,
            "maturity": cls.vertical.maturity,
            "capabilities": list(cls.vertical.capabilities),
        }

    @classmethod
    async def get_client_request(cls, request_number: str) -> dict[str, Any] | None:
        return await legacy.crm.get_auto_request_summary(request_number)

    @classmethod
    async def list_new_client_requests(cls, *, limit: int = 10) -> list[dict[str, Any]]:
        return await legacy.crm.list_new_auto_requests(limit=limit)

    @classmethod
    async def record_vin_intake(
        cls,
        *,
        vin: str,
        car_id: uuid.UUID,
        created_by: int,
    ) -> None:
        await legacy.crm.record_vin_intake(vin=vin, car_id=car_id, created_by=created_by)

    @classmethod
    async def resolve_default_tenant_id(cls) -> uuid.UUID | None:
        return await legacy.crm.get_default_tenant_id()
