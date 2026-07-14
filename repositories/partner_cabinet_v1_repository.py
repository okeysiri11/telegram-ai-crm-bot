# Partner Cabinet v1 repository.

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.automotive_partner_integration import AutomotiveRegistryPartner
from database.models.deal_engine_v1 import DEAL_ENGINE_V1_TERMINAL_STATUSES, DealEngineV1Deal
from database.models.partner_cabinet_v1 import (
    PartnerCabinetCommissionStatus,
    PartnerCabinetV1Commission,
    PartnerCabinetV1Profile,
)


class PartnerCabinetV1Repository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_profile_by_telegram(self, telegram_user_id: int) -> PartnerCabinetV1Profile | None:
        result = await self._session.execute(
            select(PartnerCabinetV1Profile).where(
                PartnerCabinetV1Profile.telegram_user_id == telegram_user_id
            )
        )
        return result.scalar_one_or_none()

    async def get_profile_by_partner(self, partner_id: uuid.UUID) -> PartnerCabinetV1Profile | None:
        result = await self._session.execute(
            select(PartnerCabinetV1Profile).where(
                PartnerCabinetV1Profile.partner_id == partner_id
            )
        )
        return result.scalar_one_or_none()

    async def get_partner(self, partner_id: uuid.UUID) -> AutomotiveRegistryPartner | None:
        result = await self._session.execute(
            select(AutomotiveRegistryPartner).where(AutomotiveRegistryPartner.id == partner_id)
        )
        return result.scalar_one_or_none()

    async def get_partner_by_code(self, code: str) -> AutomotiveRegistryPartner | None:
        result = await self._session.execute(
            select(AutomotiveRegistryPartner).where(AutomotiveRegistryPartner.code == code)
        )
        return result.scalar_one_or_none()

    async def list_profiles(self, *, include_blocked: bool = True) -> list[PartnerCabinetV1Profile]:
        stmt = select(PartnerCabinetV1Profile).order_by(PartnerCabinetV1Profile.cabinet_role)
        if not include_blocked:
            stmt = stmt.where(PartnerCabinetV1Profile.is_blocked.is_(False))
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update_profile(self, profile_id: uuid.UUID, **fields) -> PartnerCabinetV1Profile | None:
        result = await self._session.execute(
            select(PartnerCabinetV1Profile).where(PartnerCabinetV1Profile.id == profile_id)
        )
        row = result.scalar_one_or_none()
        if row is None:
            return None
        for key, value in fields.items():
            setattr(row, key, value)
        await self._session.flush()
        return row

    async def count_deals(
        self,
        partner_id: uuid.UUID,
        *,
        active_only: bool = False,
        completed_only: bool = False,
    ) -> int:
        stmt = select(func.count()).select_from(DealEngineV1Deal).where(
            DealEngineV1Deal.partner_id == partner_id
        )
        if active_only:
            stmt = stmt.where(DealEngineV1Deal.status.not_in(tuple(DEAL_ENGINE_V1_TERMINAL_STATUSES)))
        if completed_only:
            stmt = stmt.where(DealEngineV1Deal.status == "COMPLETED")
        result = await self._session.execute(stmt)
        return int(result.scalar_one())

    async def list_recent_deals(
        self,
        partner_id: uuid.UUID,
        *,
        limit: int = 5,
    ) -> list[DealEngineV1Deal]:
        result = await self._session.execute(
            select(DealEngineV1Deal)
            .where(DealEngineV1Deal.partner_id == partner_id)
            .order_by(DealEngineV1Deal.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def sum_commissions(
        self,
        partner_id: uuid.UUID,
        *,
        status: str | None = None,
    ) -> Decimal:
        stmt = select(func.coalesce(func.sum(PartnerCabinetV1Commission.amount), 0)).where(
            PartnerCabinetV1Commission.partner_id == partner_id
        )
        if status:
            stmt = stmt.where(PartnerCabinetV1Commission.status == status)
        result = await self._session.execute(stmt)
        return Decimal(result.scalar_one())

    async def list_pending_commissions(
        self,
        *,
        limit: int = 20,
    ) -> list[PartnerCabinetV1Commission]:
        result = await self._session.execute(
            select(PartnerCabinetV1Commission)
            .where(
                PartnerCabinetV1Commission.status.in_(
                    (
                        PartnerCabinetCommissionStatus.ACCRUED.value,
                        PartnerCabinetCommissionStatus.PENDING.value,
                    )
                )
            )
            .order_by(PartnerCabinetV1Commission.created_at.asc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_commission(self, commission_id: uuid.UUID) -> PartnerCabinetV1Commission | None:
        result = await self._session.execute(
            select(PartnerCabinetV1Commission).where(PartnerCabinetV1Commission.id == commission_id)
        )
        return result.scalar_one_or_none()

    async def create_commission(self, **fields) -> PartnerCabinetV1Commission:
        row = PartnerCabinetV1Commission(**fields)
        self._session.add(row)
        await self._session.flush()
        return row

    async def get_commission_by_revenue(
        self,
        revenue_entry_id: uuid.UUID,
    ) -> PartnerCabinetV1Commission | None:
        result = await self._session.execute(
            select(PartnerCabinetV1Commission).where(
                PartnerCabinetV1Commission.revenue_entry_id == revenue_entry_id
            )
        )
        return result.scalar_one_or_none()

    async def update_commission(
        self,
        commission_id: uuid.UUID,
        **fields,
    ) -> PartnerCabinetV1Commission | None:
        row = await self.get_commission(commission_id)
        if row is None:
            return None
        for key, value in fields.items():
            setattr(row, key, value)
        await self._session.flush()
        return row

    async def link_telegram(
        self,
        partner_id: uuid.UUID,
        telegram_user_id: int,
    ) -> PartnerCabinetV1Profile | None:
        profile = await self.get_profile_by_partner(partner_id)
        if profile is None:
            return None
        profile.telegram_user_id = telegram_user_id
        await self._session.flush()
        return profile
