# Automotive Treasury Engine v1 repositories.

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.automotive_treasury_engine import (
    AutomotiveDealerRateHistory,
    AutomotiveDealerRateSheet,
)


class AutomotiveTreasuryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_active_sheet(
        self,
        *,
        tenant_id: uuid.UUID | None = None,
    ) -> AutomotiveDealerRateSheet | None:
        stmt = (
            select(AutomotiveDealerRateSheet)
            .where(AutomotiveDealerRateSheet.is_active.is_(True))
            .order_by(AutomotiveDealerRateSheet.source_updated_at.desc())
            .limit(1)
        )
        if tenant_id is None:
            stmt = stmt.where(AutomotiveDealerRateSheet.tenant_id.is_(None))
        else:
            stmt = stmt.where(AutomotiveDealerRateSheet.tenant_id == tenant_id)
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        if row is not None or tenant_id is None:
            return row
        result = await self._session.execute(
            select(AutomotiveDealerRateSheet)
            .where(
                AutomotiveDealerRateSheet.is_active.is_(True),
                AutomotiveDealerRateSheet.tenant_id.is_(None),
            )
            .order_by(AutomotiveDealerRateSheet.source_updated_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def deactivate_sheets(
        self,
        *,
        tenant_id: uuid.UUID | None = None,
    ) -> int:
        stmt = (
            update(AutomotiveDealerRateSheet)
            .where(AutomotiveDealerRateSheet.is_active.is_(True))
            .values(is_active=False)
        )
        if tenant_id is None:
            stmt = stmt.where(AutomotiveDealerRateSheet.tenant_id.is_(None))
        else:
            stmt = stmt.where(AutomotiveDealerRateSheet.tenant_id == tenant_id)
        result = await self._session.execute(stmt)
        return int(result.rowcount or 0)

    async def upsert_active_sheet(
        self,
        *,
        tenant_id: uuid.UUID | None,
        rates: dict[str, Decimal],
        source_updated_at: datetime,
        source_channel_id: str | None = None,
        source_message_id: int | None = None,
        source_text: str | None = None,
        updated_by_user_id: int | None = None,
    ) -> AutomotiveDealerRateSheet:
        await self.deactivate_sheets(tenant_id=tenant_id)
        row = AutomotiveDealerRateSheet(
            tenant_id=tenant_id,
            is_active=True,
            usd_buy=rates["USD_BUY"],
            usd_sell=rates["USD_SELL"],
            eur_buy=rates["EUR_BUY"],
            eur_sell=rates["EUR_SELL"],
            usdt_buy=rates["USDT_BUY"],
            usdt_sell=rates["USDT_SELL"],
            usd_white_premium=rates.get("USD_WHITE_PREMIUM"),
            usd_blue_premium=rates.get("USD_BLUE_PREMIUM"),
            source_channel_id=source_channel_id,
            source_message_id=source_message_id,
            source_text=source_text,
            source_updated_at=source_updated_at,
            updated_by_user_id=updated_by_user_id,
        )
        self._session.add(row)
        await self._session.flush()
        return row

    async def record_history(
        self,
        *,
        tenant_id: uuid.UUID | None,
        rates: dict[str, Any],
        source_updated_at: datetime,
        source_channel_id: str | None = None,
        source_message_id: int | None = None,
        source_text: str | None = None,
        updated_by_user_id: int | None = None,
    ) -> AutomotiveDealerRateHistory:
        row = AutomotiveDealerRateHistory(
            tenant_id=tenant_id,
            rates=rates,
            source_channel_id=source_channel_id,
            source_message_id=source_message_id,
            source_text=source_text,
            source_updated_at=source_updated_at,
            updated_by_user_id=updated_by_user_id,
        )
        self._session.add(row)
        await self._session.flush()
        return row
