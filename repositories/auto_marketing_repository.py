# Auto Marketing Engine v1 repository.

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.auto_marketing_engine import (
    CAMPAIGN_STATUSES,
    MARKETING_CHANNELS,
    MEDIA_TYPES,
    PUBLICATION_STATUSES,
    MarketingCampaign,
    MarketingMediaAsset,
    MarketingPostTemplate,
    MarketingPublication,
    PublicationStatus,
)


class MarketingCampaignRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        name: str,
        description: str | None = None,
        car_id: uuid.UUID | None = None,
        status: str = "draft",
        channels: list[str] | None = None,
        metrics: dict | None = None,
        owner_user_id: int | None = None,
        started_at: datetime | None = None,
        **extra: Any,
    ) -> MarketingCampaign:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")
        if status not in CAMPAIGN_STATUSES:
            raise ValueError(f"Invalid status: {status}")

        campaign = MarketingCampaign(
            name=name,
            description=description,
            car_id=car_id,
            status=status,
            channels=channels or [],
            metrics=metrics or {},
            owner_user_id=owner_user_id,
            started_at=started_at,
        )
        self._session.add(campaign)
        await self._session.flush()
        return campaign

    async def get_by_id(self, campaign_id: uuid.UUID) -> MarketingCampaign | None:
        result = await self._session.execute(
            select(MarketingCampaign).where(MarketingCampaign.id == campaign_id)
        )
        return result.scalar_one_or_none()

    async def list_campaigns(
        self,
        *,
        status: str | None = None,
        owner_user_id: int | None = None,
        limit: int = 50,
    ) -> list[MarketingCampaign]:
        query = select(MarketingCampaign).order_by(MarketingCampaign.created_at.desc())
        if status is not None:
            query = query.where(MarketingCampaign.status == status)
        if owner_user_id is not None:
            query = query.where(MarketingCampaign.owner_user_id == owner_user_id)
        query = query.limit(limit)
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def update_status(
        self,
        campaign_id: uuid.UUID,
        status: str,
        *,
        ended_at: datetime | None = None,
    ) -> MarketingCampaign | None:
        if status not in CAMPAIGN_STATUSES:
            raise ValueError(f"Invalid status: {status}")
        campaign = await self.get_by_id(campaign_id)
        if campaign is None:
            return None
        campaign.status = status
        if ended_at is not None:
            campaign.ended_at = ended_at
        await self._session.flush()
        return campaign

    async def update_metrics(
        self,
        campaign_id: uuid.UUID,
        metrics: dict[str, Any],
    ) -> MarketingCampaign | None:
        campaign = await self.get_by_id(campaign_id)
        if campaign is None:
            return None
        current = dict(campaign.metrics or {})
        current.update(metrics)
        campaign.metrics = current
        await self._session.flush()
        return campaign

    async def increment_channel_metric(
        self,
        campaign_id: uuid.UUID,
        channel: str,
        metric: str,
        delta: int = 1,
    ) -> MarketingCampaign | None:
        campaign = await self.get_by_id(campaign_id)
        if campaign is None:
            return None
        metrics = dict(campaign.metrics or {})
        channel_metrics = dict(metrics.get(channel, {}))
        channel_metrics[metric] = channel_metrics.get(metric, 0) + delta
        metrics[channel] = channel_metrics
        campaign.metrics = metrics
        await self._session.flush()
        return campaign


class MarketingPostTemplateRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        code: str,
        name: str,
        channel: str,
        body_template: str,
        default_variables: dict | None = None,
        is_active: bool = True,
        description: str | None = None,
        **extra: Any,
    ) -> MarketingPostTemplate:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")
        if channel not in MARKETING_CHANNELS:
            raise ValueError(f"Invalid channel: {channel}")

        template = MarketingPostTemplate(
            code=code,
            name=name,
            channel=channel,
            body_template=body_template,
            default_variables=default_variables or {},
            is_active=is_active,
            description=description,
        )
        self._session.add(template)
        await self._session.flush()
        return template

    async def get_by_code(self, code: str) -> MarketingPostTemplate | None:
        result = await self._session.execute(
            select(MarketingPostTemplate).where(MarketingPostTemplate.code == code)
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, template_id: uuid.UUID) -> MarketingPostTemplate | None:
        result = await self._session.execute(
            select(MarketingPostTemplate).where(MarketingPostTemplate.id == template_id)
        )
        return result.scalar_one_or_none()

    async def list_templates(
        self,
        *,
        channel: str | None = None,
        active_only: bool = True,
        limit: int = 100,
    ) -> list[MarketingPostTemplate]:
        query = select(MarketingPostTemplate).order_by(MarketingPostTemplate.code.asc())
        if channel is not None:
            query = query.where(MarketingPostTemplate.channel == channel)
        if active_only:
            query = query.where(MarketingPostTemplate.is_active.is_(True))
        query = query.limit(limit)
        result = await self._session.execute(query)
        return list(result.scalars().all())


class MarketingMediaRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        file_name: str,
        storage_path: str,
        media_type: str,
        campaign_id: uuid.UUID | None = None,
        car_id: uuid.UUID | None = None,
        telegram_file_id: str | None = None,
        public_url: str | None = None,
        metadata: dict | None = None,
        uploaded_by: int | None = None,
        **extra: Any,
    ) -> MarketingMediaAsset:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")
        if media_type not in MEDIA_TYPES:
            raise ValueError(f"Invalid media_type: {media_type}")

        asset = MarketingMediaAsset(
            campaign_id=campaign_id,
            car_id=car_id,
            file_name=file_name,
            storage_path=storage_path,
            media_type=media_type,
            telegram_file_id=telegram_file_id,
            public_url=public_url,
            metadata_=metadata,
            uploaded_by=uploaded_by,
        )
        self._session.add(asset)
        await self._session.flush()
        return asset

    async def get_by_id(self, asset_id: uuid.UUID) -> MarketingMediaAsset | None:
        result = await self._session.execute(
            select(MarketingMediaAsset).where(MarketingMediaAsset.id == asset_id)
        )
        return result.scalar_one_or_none()

    async def list_for_campaign(
        self,
        campaign_id: uuid.UUID,
        *,
        limit: int = 50,
    ) -> list[MarketingMediaAsset]:
        result = await self._session.execute(
            select(MarketingMediaAsset)
            .where(MarketingMediaAsset.campaign_id == campaign_id)
            .order_by(MarketingMediaAsset.created_at.asc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def list_for_car(
        self,
        car_id: uuid.UUID,
        *,
        limit: int = 50,
    ) -> list[MarketingMediaAsset]:
        result = await self._session.execute(
            select(MarketingMediaAsset)
            .where(MarketingMediaAsset.car_id == car_id)
            .order_by(MarketingMediaAsset.created_at.asc())
            .limit(limit)
        )
        return list(result.scalars().all())


class MarketingPublicationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        channel: str,
        content: str,
        campaign_id: uuid.UUID | None = None,
        car_id: uuid.UUID | None = None,
        template_id: uuid.UUID | None = None,
        media_asset_ids: list[str] | None = None,
        status: str = PublicationStatus.QUEUED.value,
        scheduled_at: datetime | None = None,
        target_config: dict | None = None,
        created_by: int | None = None,
        **extra: Any,
    ) -> MarketingPublication:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")
        if channel not in MARKETING_CHANNELS:
            raise ValueError(f"Invalid channel: {channel}")
        if status not in PUBLICATION_STATUSES:
            raise ValueError(f"Invalid status: {status}")

        publication = MarketingPublication(
            campaign_id=campaign_id,
            car_id=car_id,
            template_id=template_id,
            channel=channel,
            content=content,
            media_asset_ids=media_asset_ids or [],
            status=status,
            scheduled_at=scheduled_at,
            target_config=target_config or {},
            created_by=created_by,
        )
        self._session.add(publication)
        await self._session.flush()
        return publication

    async def get_by_id(self, publication_id: uuid.UUID) -> MarketingPublication | None:
        result = await self._session.execute(
            select(MarketingPublication).where(MarketingPublication.id == publication_id)
        )
        return result.scalar_one_or_none()

    async def list_due(
        self,
        *,
        now: datetime | None = None,
        limit: int = 50,
    ) -> list[MarketingPublication]:
        due_at = now or datetime.now(timezone.utc)
        result = await self._session.execute(
            select(MarketingPublication)
            .where(
                MarketingPublication.status.in_([
                    PublicationStatus.QUEUED.value,
                    PublicationStatus.SCHEDULED.value,
                ]),
                (
                    (MarketingPublication.scheduled_at.is_(None))
                    | (MarketingPublication.scheduled_at <= due_at)
                ),
            )
            .order_by(MarketingPublication.scheduled_at.asc().nullsfirst())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def list_by_channel(
        self,
        channel: str,
        *,
        status: str | None = None,
        limit: int = 50,
    ) -> list[MarketingPublication]:
        query = (
            select(MarketingPublication)
            .where(MarketingPublication.channel == channel)
            .order_by(MarketingPublication.created_at.desc())
        )
        if status is not None:
            query = query.where(MarketingPublication.status == status)
        query = query.limit(limit)
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def list_for_campaign(
        self,
        campaign_id: uuid.UUID,
        *,
        limit: int = 100,
    ) -> list[MarketingPublication]:
        result = await self._session.execute(
            select(MarketingPublication)
            .where(MarketingPublication.campaign_id == campaign_id)
            .order_by(MarketingPublication.created_at.asc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def mark_publishing(self, publication: MarketingPublication) -> MarketingPublication:
        publication.status = PublicationStatus.PUBLISHING.value
        publication.attempt_count += 1
        await self._session.flush()
        return publication

    async def mark_published(
        self,
        publication: MarketingPublication,
        *,
        external_post_id: str | None = None,
    ) -> MarketingPublication:
        publication.status = PublicationStatus.PUBLISHED.value
        publication.published_at = datetime.now(timezone.utc)
        publication.external_post_id = external_post_id
        publication.error_message = None
        await self._session.flush()
        return publication

    async def mark_failed(
        self,
        publication: MarketingPublication,
        error_message: str,
    ) -> MarketingPublication:
        publication.status = PublicationStatus.FAILED.value
        publication.error_message = error_message[:2000]
        await self._session.flush()
        return publication

    async def count_by_status(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for status in PUBLICATION_STATUSES:
            result = await self._session.execute(
                select(MarketingPublication).where(MarketingPublication.status == status)
            )
            counts[status] = len(list(result.scalars().all()))
        return counts

    async def queue_stats_by_channel(self) -> dict[str, dict[str, int]]:
        stats: dict[str, dict[str, int]] = {}
        for channel in MARKETING_CHANNELS:
            channel_stats: dict[str, int] = {}
            for status in PUBLICATION_STATUSES:
                result = await self._session.execute(
                    select(MarketingPublication).where(
                        MarketingPublication.channel == channel,
                        MarketingPublication.status == status,
                    )
                )
                channel_stats[status] = len(list(result.scalars().all()))
            stats[channel] = channel_stats
        return stats
