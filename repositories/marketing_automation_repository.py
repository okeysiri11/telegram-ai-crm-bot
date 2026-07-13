# Marketing Automation Engine v1 repository.

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.marketing_automation_engine import (
    AUTOMATION_CAMPAIGN_STATUSES,
    AUTOMATION_CHANNELS,
    AutomationCampaign,
    AutomationCampaignStatus,
    ProcessedMedia,
    RepostRule,
    SCHEDULED_POST_STATUSES,
    ScheduledPost,
    ScheduledPostStatus,
)


class AutomationCampaignRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        name: str,
        description: str | None = None,
        car_id: uuid.UUID | None = None,
        auto_marketing_campaign_id: uuid.UUID | None = None,
        status: str = AutomationCampaignStatus.DRAFT.value,
        channels: list[str] | None = None,
        metrics: dict | None = None,
        settings: dict | None = None,
        owner_user_id: int | None = None,
        **extra: Any,
    ) -> AutomationCampaign:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")
        if status not in AUTOMATION_CAMPAIGN_STATUSES:
            raise ValueError(f"Invalid status: {status}")

        campaign = AutomationCampaign(
            name=name,
            description=description,
            car_id=car_id,
            auto_marketing_campaign_id=auto_marketing_campaign_id,
            status=status,
            channels=channels or [],
            metrics=metrics or {},
            settings=settings or {},
            owner_user_id=owner_user_id,
        )
        self._session.add(campaign)
        await self._session.flush()
        return campaign

    async def get_by_id(self, campaign_id: uuid.UUID) -> AutomationCampaign | None:
        result = await self._session.execute(
            select(AutomationCampaign).where(AutomationCampaign.id == campaign_id)
        )
        return result.scalar_one_or_none()

    async def list_campaigns(
        self,
        *,
        status: str | None = None,
        limit: int = 50,
    ) -> list[AutomationCampaign]:
        query = select(AutomationCampaign).order_by(AutomationCampaign.created_at.desc())
        if status is not None:
            query = query.where(AutomationCampaign.status == status)
        query = query.limit(limit)
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def increment_metric(
        self,
        campaign_id: uuid.UUID,
        metric: str,
        *,
        channel: str | None = None,
        delta: int = 1,
    ) -> AutomationCampaign | None:
        campaign = await self.get_by_id(campaign_id)
        if campaign is None:
            return None
        metrics = dict(campaign.metrics or {})
        metrics[metric] = metrics.get(metric, 0) + delta
        if channel:
            by_channel = dict(metrics.get("by_channel", {}))
            channel_metrics = dict(by_channel.get(channel, {}))
            channel_metrics[metric] = channel_metrics.get(metric, 0) + delta
            by_channel[channel] = channel_metrics
            metrics["by_channel"] = by_channel
        campaign.metrics = metrics
        await self._session.flush()
        return campaign


class RepostRuleRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        name: str,
        channels: list[str],
        interval_hours: int = 24,
        max_reposts: int = 3,
        campaign_id: uuid.UUID | None = None,
        source_content: str | None = None,
        source_media_path: str | None = None,
        car_id: uuid.UUID | None = None,
        watermark_enabled: bool = True,
        optimize_images: bool = True,
        is_active: bool = True,
        next_repost_at: datetime | None = None,
        created_by: int | None = None,
        **extra: Any,
    ) -> RepostRule:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")
        for channel in channels:
            if channel not in AUTOMATION_CHANNELS:
                raise ValueError(f"Invalid channel: {channel}")

        rule = RepostRule(
            campaign_id=campaign_id,
            name=name,
            source_content=source_content,
            source_media_path=source_media_path,
            car_id=car_id,
            channels=channels,
            interval_hours=interval_hours,
            max_reposts=max_reposts,
            watermark_enabled=watermark_enabled,
            optimize_images=optimize_images,
            is_active=is_active,
            next_repost_at=next_repost_at,
            created_by=created_by,
        )
        self._session.add(rule)
        await self._session.flush()
        return rule

    async def get_by_id(self, rule_id: uuid.UUID) -> RepostRule | None:
        result = await self._session.execute(
            select(RepostRule).where(RepostRule.id == rule_id)
        )
        return result.scalar_one_or_none()

    async def list_due(
        self,
        *,
        now: datetime | None = None,
        limit: int = 20,
    ) -> list[RepostRule]:
        due_at = now or datetime.now(timezone.utc)
        result = await self._session.execute(
            select(RepostRule)
            .where(
                RepostRule.is_active.is_(True),
                RepostRule.repost_count < RepostRule.max_reposts,
                RepostRule.next_repost_at.is_not(None),
                RepostRule.next_repost_at <= due_at,
            )
            .order_by(RepostRule.next_repost_at.asc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def mark_reposted(
        self,
        rule: RepostRule,
        *,
        now: datetime | None = None,
    ) -> RepostRule:
        current = now or datetime.now(timezone.utc)
        rule.repost_count += 1
        rule.last_reposted_at = current
        if rule.repost_count >= rule.max_reposts:
            rule.is_active = False
            rule.next_repost_at = None
        else:
            rule.next_repost_at = current + timedelta(hours=rule.interval_hours)
        await self._session.flush()
        return rule


class ScheduledPostRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        channel: str,
        content: str,
        scheduled_at: datetime,
        campaign_id: uuid.UUID | None = None,
        car_id: uuid.UUID | None = None,
        repost_rule_id: uuid.UUID | None = None,
        hashtags: list[str] | None = None,
        source_media_path: str | None = None,
        status: str = ScheduledPostStatus.SCHEDULED.value,
        repost_generation: int = 0,
        target_config: dict | None = None,
        created_by: int | None = None,
        **extra: Any,
    ) -> ScheduledPost:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")
        if channel not in AUTOMATION_CHANNELS:
            raise ValueError(f"Invalid channel: {channel}")
        if status not in SCHEDULED_POST_STATUSES:
            raise ValueError(f"Invalid status: {status}")

        post = ScheduledPost(
            campaign_id=campaign_id,
            car_id=car_id,
            repost_rule_id=repost_rule_id,
            channel=channel,
            content=content,
            hashtags=hashtags or [],
            source_media_path=source_media_path,
            scheduled_at=scheduled_at,
            status=status,
            repost_generation=repost_generation,
            target_config=target_config or {},
            created_by=created_by,
        )
        self._session.add(post)
        await self._session.flush()
        return post

    async def get_by_id(self, post_id: uuid.UUID) -> ScheduledPost | None:
        result = await self._session.execute(
            select(ScheduledPost).where(ScheduledPost.id == post_id)
        )
        return result.scalar_one_or_none()

    async def list_due(
        self,
        *,
        now: datetime | None = None,
        limit: int = 20,
    ) -> list[ScheduledPost]:
        due_at = now or datetime.now(timezone.utc)
        result = await self._session.execute(
            select(ScheduledPost)
            .where(
                ScheduledPost.status == ScheduledPostStatus.SCHEDULED.value,
                ScheduledPost.scheduled_at <= due_at,
            )
            .order_by(ScheduledPost.scheduled_at.asc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def update_post(
        self,
        post: ScheduledPost,
        **fields: Any,
    ) -> ScheduledPost:
        allowed = {
            "processed_media_path",
            "hashtags",
            "content",
            "status",
            "publication_id",
            "processing_metadata",
            "error_message",
            "published_at",
        }
        unknown = set(fields) - allowed
        if unknown:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(unknown))}")
        for key, value in fields.items():
            setattr(post, key, value)
        await self._session.flush()
        return post

    async def count_by_status(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for status in SCHEDULED_POST_STATUSES:
            result = await self._session.execute(
                select(func.count())
                .select_from(ScheduledPost)
                .where(ScheduledPost.status == status)
            )
            counts[status] = int(result.scalar_one())
        return counts


class ProcessedMediaRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        original_path: str,
        processed_path: str,
        scheduled_post_id: uuid.UUID | None = None,
        watermark_applied: bool = False,
        optimized: bool = False,
        original_size_bytes: int | None = None,
        processed_size_bytes: int | None = None,
        metadata: dict | None = None,
        **extra: Any,
    ) -> ProcessedMedia:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")

        asset = ProcessedMedia(
            scheduled_post_id=scheduled_post_id,
            original_path=original_path,
            processed_path=processed_path,
            watermark_applied=watermark_applied,
            optimized=optimized,
            original_size_bytes=original_size_bytes,
            processed_size_bytes=processed_size_bytes,
            metadata_=metadata,
        )
        self._session.add(asset)
        await self._session.flush()
        return asset
