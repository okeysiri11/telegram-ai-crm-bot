# Auto vertical service — delegates to legacy pg_* engines.

from __future__ import annotations

import uuid
from typing import Any

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
        from services.pg_auto_client_request_engine import AutoClientRequestEngineV1

        return await AutoClientRequestEngineV1.get_request_summary(request_number)

    @classmethod
    async def list_new_client_requests(cls, *, limit: int = 10) -> list[dict[str, Any]]:
        from services.pg_auto_client_request_engine import AutoClientRequestEngineV1

        return await AutoClientRequestEngineV1.list_new_request_summaries(limit=limit)

    @classmethod
    async def record_vin_intake(
        cls,
        *,
        vin: str,
        car_id: uuid.UUID,
        created_by: int,
    ) -> None:
        from services.pg_vin_engine import VinEngineV1

        await VinEngineV1.record_car_intake(vin=vin, car_id=car_id, created_by=created_by)

    @classmethod
    async def resolve_default_tenant_id(cls) -> uuid.UUID | None:
        from services.pg_partner_tenant_engine import PartnerTenantEngineV1

        return await PartnerTenantEngineV1.get_default_tenant_id()
