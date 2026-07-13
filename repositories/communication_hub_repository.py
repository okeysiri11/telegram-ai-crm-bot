# Communication Hub v1 repositories.

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.communication_hub import (
    HUB_CAMPAIGN_STATUSES,
    HUB_CHANNEL_TYPES,
    HUB_MESSAGE_DIRECTIONS,
    HUB_MESSAGE_STATUSES,
    HUB_SENDER_TYPES,
    CommunicationCampaign,
    CommunicationChannel,
    CommunicationMessage,
    HubCampaignStatus,
    HubChannelType,
    HubMessageDirection,
    HubMessageStatus,
    HubSenderType,
)


class CommunicationChannelRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        tenant_id: uuid.UUID,
        company_id: uuid.UUID,
        channel_type: str,
        external_id: str,
        name: str,
        is_active: bool = True,
        config: dict | None = None,
        metadata: dict | None = None,
        **extra: Any,
    ) -> CommunicationChannel:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")
        if channel_type not in HUB_CHANNEL_TYPES:
            raise ValueError(f"Invalid channel_type: {channel_type}")

        row = CommunicationChannel(
            tenant_id=tenant_id,
            company_id=company_id,
            channel_type=channel_type,
            external_id=external_id,
            name=name,
            is_active=is_active,
            config=config,
            metadata_=metadata,
        )
        self._session.add(row)
        await self._session.flush()
        return row

    async def get_by_id(self, channel_id: uuid.UUID) -> CommunicationChannel | None:
        result = await self._session.execute(
            select(CommunicationChannel).where(CommunicationChannel.id == channel_id)
        )
        return result.scalar_one_or_none()

    async def list_by_tenant(
        self,
        tenant_id: uuid.UUID,
        *,
        active_only: bool = True,
        limit: int = 50,
    ) -> list[CommunicationChannel]:
        stmt = (
            select(CommunicationChannel)
            .where(CommunicationChannel.tenant_id == tenant_id)
            .order_by(CommunicationChannel.created_at.desc())
            .limit(limit)
        )
        if active_only:
            stmt = stmt.where(CommunicationChannel.is_active.is_(True))
        result = await self._session.execute(stmt)
        return list(result.scalars().all())


class CommunicationMessageRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        channel_id: uuid.UUID,
        tenant_id: uuid.UUID,
        company_id: uuid.UUID,
        conversation_id: str,
        direction: str,
        sender_type: str,
        message_text: str,
        sender_id: str | None = None,
        status: str = HubMessageStatus.NEW.value,
        sales_lead_id: uuid.UUID | None = None,
        automation_lead_id: uuid.UUID | None = None,
        assigned_manager_id: int | None = None,
        campaign_id: uuid.UUID | None = None,
        metadata: dict | None = None,
        **extra: Any,
    ) -> CommunicationMessage:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")
        if direction not in HUB_MESSAGE_DIRECTIONS:
            raise ValueError(f"Invalid direction: {direction}")
        if sender_type not in HUB_SENDER_TYPES:
            raise ValueError(f"Invalid sender_type: {sender_type}")
        if status not in HUB_MESSAGE_STATUSES:
            raise ValueError(f"Invalid status: {status}")

        row = CommunicationMessage(
            channel_id=channel_id,
            tenant_id=tenant_id,
            company_id=company_id,
            conversation_id=conversation_id,
            direction=direction,
            sender_type=sender_type,
            message_text=message_text.strip(),
            sender_id=sender_id,
            status=status,
            sales_lead_id=sales_lead_id,
            automation_lead_id=automation_lead_id,
            assigned_manager_id=assigned_manager_id,
            campaign_id=campaign_id,
            metadata_=metadata,
        )
        self._session.add(row)
        await self._session.flush()
        return row

    async def list_inbox(
        self,
        tenant_id: uuid.UUID,
        *,
        status: str | None = None,
        channel_id: uuid.UUID | None = None,
        limit: int = 100,
    ) -> list[CommunicationMessage]:
        stmt = (
            select(CommunicationMessage)
            .where(CommunicationMessage.tenant_id == tenant_id)
            .order_by(CommunicationMessage.created_at.desc())
            .limit(limit)
        )
        if status is not None:
            stmt = stmt.where(CommunicationMessage.status == status)
        if channel_id is not None:
            stmt = stmt.where(CommunicationMessage.channel_id == channel_id)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def list_conversation(
        self,
        tenant_id: uuid.UUID,
        conversation_id: str,
        *,
        limit: int = 100,
    ) -> list[CommunicationMessage]:
        result = await self._session.execute(
            select(CommunicationMessage)
            .where(
                CommunicationMessage.tenant_id == tenant_id,
                CommunicationMessage.conversation_id == conversation_id,
            )
            .order_by(CommunicationMessage.created_at.asc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def update_fields(
        self,
        message_id: uuid.UUID,
        **fields: Any,
    ) -> CommunicationMessage | None:
        result = await self._session.execute(
            select(CommunicationMessage).where(CommunicationMessage.id == message_id)
        )
        row = result.scalar_one_or_none()
        if row is None:
            return None
        allowed = {
            "status",
            "sales_lead_id",
            "automation_lead_id",
            "assigned_manager_id",
            "metadata_",
        }
        for key, value in fields.items():
            attr = "metadata_" if key == "metadata" else key
            if attr not in allowed:
                raise TypeError(f"Unsupported field: {key}")
            setattr(row, attr, value)
        await self._session.flush()
        return row


class CommunicationCampaignRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        tenant_id: uuid.UUID,
        company_id: uuid.UUID,
        name: str,
        channel_types: list[str],
        message_template: str | None = None,
        auto_response_enabled: bool = True,
        routing_rules: dict | None = None,
        status: str = HubCampaignStatus.DRAFT.value,
        starts_at: datetime | None = None,
        ends_at: datetime | None = None,
        created_by: int | None = None,
        metadata: dict | None = None,
        **extra: Any,
    ) -> CommunicationCampaign:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")
        if status not in HUB_CAMPAIGN_STATUSES:
            raise ValueError(f"Invalid status: {status}")
        for ch in channel_types:
            if ch not in HUB_CHANNEL_TYPES:
                raise ValueError(f"Invalid channel type in campaign: {ch}")

        row = CommunicationCampaign(
            tenant_id=tenant_id,
            company_id=company_id,
            name=name,
            channel_types=channel_types,
            message_template=message_template,
            auto_response_enabled=auto_response_enabled,
            routing_rules=routing_rules,
            status=status,
            starts_at=starts_at,
            ends_at=ends_at,
            created_by=created_by,
            metadata_=metadata,
        )
        self._session.add(row)
        await self._session.flush()
        return row

    async def get_by_id(self, campaign_id: uuid.UUID) -> CommunicationCampaign | None:
        result = await self._session.execute(
            select(CommunicationCampaign).where(CommunicationCampaign.id == campaign_id)
        )
        return result.scalar_one_or_none()

    async def list_active_for_channel(
        self,
        tenant_id: uuid.UUID,
        channel_type: str,
        *,
        limit: int = 10,
    ) -> list[CommunicationCampaign]:
        result = await self._session.execute(
            select(CommunicationCampaign)
            .where(
                CommunicationCampaign.tenant_id == tenant_id,
                CommunicationCampaign.status == HubCampaignStatus.ACTIVE.value,
            )
            .order_by(CommunicationCampaign.created_at.desc())
            .limit(limit)
        )
        campaigns = list(result.scalars().all())
        return [c for c in campaigns if channel_type in (c.channel_types or [])]
