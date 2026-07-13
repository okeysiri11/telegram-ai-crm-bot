# AI Advertising Agent v1 repositories.

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.ai_advertising_agent import (
    ADVERTISING_ACTION_TYPES,
    ADVERTISING_CAMPAIGN_STATUSES,
    ADVERTISING_CHANNELS,
    AdvertisingAgentAction,
    AdvertisingAgentCampaign,
    AdvertisingCampaignStatus,
)


class AdvertisingAgentCampaignRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        tenant_id: uuid.UUID,
        company_id: uuid.UUID,
        name: str,
        channels: list[str],
        budget_total: Decimal = Decimal("0"),
        car_id: uuid.UUID | None = None,
        marketing_campaign_id: uuid.UUID | None = None,
        status: str = AdvertisingCampaignStatus.DRAFT.value,
        daily_budget: Decimal | None = None,
        currency: str = "USD",
        created_by: int | None = None,
        notes: str | None = None,
        metadata: dict | None = None,
        **extra: Any,
    ) -> AdvertisingAgentCampaign:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")
        if status not in ADVERTISING_CAMPAIGN_STATUSES:
            raise ValueError(f"Invalid status: {status}")
        for channel in channels:
            if channel not in ADVERTISING_CHANNELS:
                raise ValueError(f"Invalid channel: {channel}")

        row = AdvertisingAgentCampaign(
            tenant_id=tenant_id,
            company_id=company_id,
            name=name.strip(),
            channels=channels,
            budget_total=budget_total,
            car_id=car_id,
            marketing_campaign_id=marketing_campaign_id,
            status=status,
            daily_budget=daily_budget,
            currency=currency,
            created_by=created_by,
            notes=notes,
            metadata_=metadata,
        )
        self._session.add(row)
        await self._session.flush()
        return row

    async def get_by_id(self, campaign_id: uuid.UUID) -> AdvertisingAgentCampaign | None:
        result = await self._session.execute(
            select(AdvertisingAgentCampaign).where(AdvertisingAgentCampaign.id == campaign_id)
        )
        return result.scalar_one_or_none()

    async def list_by_tenant(
        self,
        tenant_id: uuid.UUID,
        *,
        status: str | None = None,
        limit: int = 100,
    ) -> list[AdvertisingAgentCampaign]:
        stmt = (
            select(AdvertisingAgentCampaign)
            .where(AdvertisingAgentCampaign.tenant_id == tenant_id)
            .order_by(AdvertisingAgentCampaign.created_at.desc())
            .limit(limit)
        )
        if status is not None:
            stmt = stmt.where(AdvertisingAgentCampaign.status == status)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def list_active(self, *, limit: int = 200) -> list[AdvertisingAgentCampaign]:
        result = await self._session.execute(
            select(AdvertisingAgentCampaign)
            .where(AdvertisingAgentCampaign.status == AdvertisingCampaignStatus.ACTIVE.value)
            .order_by(AdvertisingAgentCampaign.created_at.asc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def update_fields(
        self,
        campaign_id: uuid.UUID,
        **fields: Any,
    ) -> AdvertisingAgentCampaign | None:
        row = await self.get_by_id(campaign_id)
        if row is None:
            return None
        allowed = {
            "status",
            "budget_total",
            "budget_allocated",
            "budget_spent",
            "daily_budget",
            "audience_profile",
            "bid_config",
            "ad_creative",
            "performance_metrics",
            "last_monitored_at",
            "notes",
            "metadata_",
        }
        for key, value in fields.items():
            attr = "metadata_" if key == "metadata" else key
            if attr not in allowed:
                raise TypeError(f"Unsupported field: {key}")
            setattr(row, attr, value)
        await self._session.flush()
        return row


class AdvertisingAgentActionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        campaign_id: uuid.UUID,
        tenant_id: uuid.UUID,
        company_id: uuid.UUID,
        action_type: str,
        input_context: dict,
        result: dict,
        confidence_score: Decimal,
        model_version: str,
        summary: str | None = None,
        created_by: int | None = None,
        **extra: Any,
    ) -> AdvertisingAgentAction:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")
        if action_type not in ADVERTISING_ACTION_TYPES:
            raise ValueError(f"Invalid action_type: {action_type}")

        row = AdvertisingAgentAction(
            campaign_id=campaign_id,
            tenant_id=tenant_id,
            company_id=company_id,
            action_type=action_type,
            input_context=input_context,
            result=result,
            confidence_score=confidence_score,
            model_version=model_version,
            summary=summary,
            created_by=created_by,
        )
        self._session.add(row)
        await self._session.flush()
        return row

    async def list_by_campaign(
        self,
        campaign_id: uuid.UUID,
        *,
        action_type: str | None = None,
        limit: int = 50,
    ) -> list[AdvertisingAgentAction]:
        stmt = (
            select(AdvertisingAgentAction)
            .where(AdvertisingAgentAction.campaign_id == campaign_id)
            .order_by(AdvertisingAgentAction.created_at.desc())
            .limit(limit)
        )
        if action_type is not None:
            stmt = stmt.where(AdvertisingAgentAction.action_type == action_type)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
