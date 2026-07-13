# Marketing Automation Engine v1 — scheduled posting, reposts, media pipeline.

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from config import OWNER_ID
from database.models.audit_log import AuditAction
from database.models.marketing_automation_engine import (
    AutomationCampaignStatus,
    AutomationChannel,
    ScheduledPostStatus,
)
from database.session import get_session
from repositories.audit_repository import AuditRepository
from repositories.car_repository import CarRepository
from repositories.marketing_automation_repository import (
    AutomationCampaignRepository,
    ProcessedMediaRepository,
    RepostRuleRepository,
    ScheduledPostRepository,
)
from repositories.user_role_repository import UserRoleRepository
from services.marketing_media_processor import (
    MEDIA_ROOT,
    generate_hashtags,
    process_media,
)

MARKETING_AUTOMATION_ROLES = frozenset({"OWNER", "ADMIN", "MANAGER"})


class MarketingAutomationEngineError(Exception):
    pass


class MarketingAutomationEngineV1:
    @staticmethod
    async def user_can_access(user_id: int) -> bool:
        if user_id == OWNER_ID:
            return True
        async with get_session() as session:
            roles = await UserRoleRepository(session).get_user_roles(user_id)
            return any(role.code in MARKETING_AUTOMATION_ROLES for role in roles)

    @staticmethod
    def _campaign_snapshot(campaign) -> dict[str, Any]:
        return {
            "id": str(campaign.id),
            "name": campaign.name,
            "description": campaign.description,
            "car_id": str(campaign.car_id) if campaign.car_id else None,
            "auto_marketing_campaign_id": (
                str(campaign.auto_marketing_campaign_id)
                if campaign.auto_marketing_campaign_id
                else None
            ),
            "status": campaign.status,
            "channels": campaign.channels or [],
            "metrics": campaign.metrics or {},
            "settings": campaign.settings or {},
            "owner_user_id": campaign.owner_user_id,
            "created_at": campaign.created_at.isoformat(),
            "updated_at": campaign.updated_at.isoformat(),
        }

    @staticmethod
    def _repost_rule_snapshot(rule) -> dict[str, Any]:
        return {
            "id": str(rule.id),
            "campaign_id": str(rule.campaign_id) if rule.campaign_id else None,
            "name": rule.name,
            "channels": rule.channels or [],
            "interval_hours": rule.interval_hours,
            "max_reposts": rule.max_reposts,
            "repost_count": rule.repost_count,
            "watermark_enabled": rule.watermark_enabled,
            "optimize_images": rule.optimize_images,
            "is_active": rule.is_active,
            "next_repost_at": rule.next_repost_at.isoformat() if rule.next_repost_at else None,
            "last_reposted_at": rule.last_reposted_at.isoformat() if rule.last_reposted_at else None,
            "car_id": str(rule.car_id) if rule.car_id else None,
        }

    @staticmethod
    def _scheduled_post_snapshot(post) -> dict[str, Any]:
        return {
            "id": str(post.id),
            "campaign_id": str(post.campaign_id) if post.campaign_id else None,
            "car_id": str(post.car_id) if post.car_id else None,
            "repost_rule_id": str(post.repost_rule_id) if post.repost_rule_id else None,
            "channel": post.channel,
            "content": post.content,
            "hashtags": post.hashtags or [],
            "source_media_path": post.source_media_path,
            "processed_media_path": post.processed_media_path,
            "scheduled_at": post.scheduled_at.isoformat(),
            "status": post.status,
            "publication_id": str(post.publication_id) if post.publication_id else None,
            "repost_generation": post.repost_generation,
            "processing_metadata": post.processing_metadata or {},
            "error_message": post.error_message,
            "published_at": post.published_at.isoformat() if post.published_at else None,
            "created_at": post.created_at.isoformat(),
        }

    @staticmethod
    async def create_campaign(
        actor_id: int,
        *,
        name: str,
        description: str | None = None,
        car_id: uuid.UUID | None = None,
        channels: list[str] | None = None,
        settings: dict | None = None,
        activate: bool = False,
    ) -> dict[str, Any]:
        if not await MarketingAutomationEngineV1.user_can_access(actor_id):
            raise MarketingAutomationEngineError("Access denied")

        channel_list = channels or [c.value for c in AutomationChannel]
        default_settings = {
            "watermark_enabled": True,
            "optimize_images": True,
            "auto_hashtags": True,
        }
        if settings:
            default_settings.update(settings)

        async with get_session() as session:
            if car_id is not None:
                car = await CarRepository(session).get_car(car_id)
                if car is None:
                    raise MarketingAutomationEngineError(f"Car not found: {car_id}")

            campaign = await AutomationCampaignRepository(session).create(
                name=name,
                description=description,
                car_id=car_id,
                channels=channel_list,
                settings=default_settings,
                owner_user_id=actor_id,
                status=(
                    AutomationCampaignStatus.ACTIVE.value
                    if activate
                    else AutomationCampaignStatus.DRAFT.value
                ),
            )
            await AuditRepository(session).create_log(
                user_id=actor_id,
                entity_type="marketing_automation_campaign",
                entity_id=str(campaign.id),
                action=AuditAction.CREATE.value,
                new_value={"name": name, "channels": channel_list},
            )
            return MarketingAutomationEngineV1._campaign_snapshot(campaign)

    @staticmethod
    async def get_campaign(actor_id: int, campaign_id: uuid.UUID) -> dict[str, Any]:
        if not await MarketingAutomationEngineV1.user_can_access(actor_id):
            raise MarketingAutomationEngineError("Access denied")

        async with get_session() as session:
            campaign = await AutomationCampaignRepository(session).get_by_id(campaign_id)
            if campaign is None:
                raise MarketingAutomationEngineError(f"Campaign not found: {campaign_id}")
            return MarketingAutomationEngineV1._campaign_snapshot(campaign)

    @staticmethod
    async def list_campaigns(
        actor_id: int,
        *,
        status: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        if not await MarketingAutomationEngineV1.user_can_access(actor_id):
            raise MarketingAutomationEngineError("Access denied")

        async with get_session() as session:
            campaigns = await AutomationCampaignRepository(session).list_campaigns(
                status=status,
                limit=limit,
            )
            return [
                MarketingAutomationEngineV1._campaign_snapshot(c)
                for c in campaigns
            ]

    @staticmethod
    async def create_repost_rule(
        actor_id: int,
        *,
        name: str,
        channels: list[str],
        source_content: str,
        interval_hours: int = 24,
        max_reposts: int = 3,
        campaign_id: uuid.UUID | None = None,
        source_media_path: str | None = None,
        car_id: uuid.UUID | None = None,
        watermark_enabled: bool = True,
        optimize_images: bool = True,
        start_at: datetime | None = None,
    ) -> dict[str, Any]:
        if not await MarketingAutomationEngineV1.user_can_access(actor_id):
            raise MarketingAutomationEngineError("Access denied")

        next_repost = start_at or (datetime.now(timezone.utc) + timedelta(hours=interval_hours))

        async with get_session() as session:
            rule = await RepostRuleRepository(session).create(
                name=name,
                channels=channels,
                source_content=source_content,
                source_media_path=source_media_path,
                car_id=car_id,
                campaign_id=campaign_id,
                interval_hours=interval_hours,
                max_reposts=max_reposts,
                watermark_enabled=watermark_enabled,
                optimize_images=optimize_images,
                next_repost_at=next_repost,
                created_by=actor_id,
            )
            if campaign_id is not None:
                await AutomationCampaignRepository(session).increment_metric(
                    campaign_id,
                    "repost_rules",
                )
            return MarketingAutomationEngineV1._repost_rule_snapshot(rule)

    @staticmethod
    async def schedule_post(
        actor_id: int,
        *,
        channel: str,
        content: str,
        scheduled_at: datetime,
        campaign_id: uuid.UUID | None = None,
        car_id: uuid.UUID | None = None,
        source_media_path: str | None = None,
        hashtags: list[str] | None = None,
        target_config: dict | None = None,
        repost_rule_id: uuid.UUID | None = None,
        repost_generation: int = 0,
    ) -> dict[str, Any]:
        if not await MarketingAutomationEngineV1.user_can_access(actor_id):
            raise MarketingAutomationEngineError("Access denied")

        async with get_session() as session:
            post = await ScheduledPostRepository(session).create(
                channel=channel,
                content=content,
                scheduled_at=scheduled_at,
                campaign_id=campaign_id,
                car_id=car_id,
                source_media_path=source_media_path,
                hashtags=hashtags,
                target_config=target_config,
                repost_rule_id=repost_rule_id,
                repost_generation=repost_generation,
                created_by=actor_id,
            )
            if campaign_id is not None:
                await AutomationCampaignRepository(session).increment_metric(
                    campaign_id,
                    "scheduled",
                    channel=channel,
                )
            await AuditRepository(session).create_log(
                user_id=actor_id,
                entity_type="marketing_automation_post",
                entity_id=str(post.id),
                action=AuditAction.CREATE.value,
                new_value={"channel": channel, "scheduled_at": scheduled_at.isoformat()},
            )
            return MarketingAutomationEngineV1._scheduled_post_snapshot(post)

    @staticmethod
    async def schedule_multi_channel(
        actor_id: int,
        *,
        content: str,
        scheduled_at: datetime,
        channels: list[str] | None = None,
        campaign_id: uuid.UUID | None = None,
        car_id: uuid.UUID | None = None,
        source_media_path: str | None = None,
    ) -> list[dict[str, Any]]:
        channel_list = channels or [c.value for c in AutomationChannel]
        posts: list[dict[str, Any]] = []
        for channel in channel_list:
            post = await MarketingAutomationEngineV1.schedule_post(
                actor_id,
                channel=channel,
                content=content,
                scheduled_at=scheduled_at,
                campaign_id=campaign_id,
                car_id=car_id,
                source_media_path=source_media_path,
            )
            posts.append(post)
        return posts

    @staticmethod
    async def _prepare_post_content(
        session,
        post,
        *,
        campaign_settings: dict | None = None,
    ) -> tuple[str, list[str], str | None, dict[str, Any]]:
        settings = campaign_settings or {}
        watermark_enabled = settings.get("watermark_enabled", True)
        optimize_enabled = settings.get("optimize_images", True)
        auto_hashtags = settings.get("auto_hashtags", True)

        make = model = None
        year = None
        if post.car_id is not None:
            car = await CarRepository(session).get_car(post.car_id)
            if car is not None:
                make, model, year = car.make, car.model, car.year

        hashtags = list(post.hashtags or [])
        if auto_hashtags and not hashtags:
            hashtags = generate_hashtags(
                channel=post.channel,
                make=make,
                model=model,
                year=year,
            )

        processed_path = post.processed_media_path
        processing_meta: dict[str, Any] = {}

        if post.source_media_path:
            processed_path, processing_meta = process_media(
                post.source_media_path,
                watermark_enabled=watermark_enabled,
                optimize_enabled=optimize_enabled,
            )
            await ProcessedMediaRepository(session).create(
                scheduled_post_id=post.id,
                original_path=post.source_media_path,
                processed_path=processed_path,
                watermark_applied=processing_meta.get("watermark_applied", False),
                optimized=processing_meta.get("optimized", False),
                original_size_bytes=processing_meta.get("original_size_bytes"),
                processed_size_bytes=processing_meta.get("processed_size_bytes"),
                metadata=processing_meta,
            )

        hashtag_line = " ".join(hashtags)
        final_content = post.content.strip()
        if hashtag_line and hashtag_line not in final_content:
            final_content = f"{final_content}\n\n{hashtag_line}".strip()

        return final_content, hashtags, processed_path, processing_meta

    @staticmethod
    async def process_due_scheduled_posts(*, limit: int = 20) -> dict[str, Any]:
        from services.pg_auto_marketing_engine import AutoMarketingEngineV1

        processed = 0
        published = 0
        failed = 0
        results: list[dict[str, Any]] = []

        async with get_session() as session:
            post_repo = ScheduledPostRepository(session)
            campaign_repo = AutomationCampaignRepository(session)
            due_posts = await post_repo.list_due(limit=limit)

            for post in due_posts:
                processed += 1
                await post_repo.update_post(post, status=ScheduledPostStatus.PROCESSING.value)

                campaign_settings: dict = {}
                if post.campaign_id is not None:
                    campaign = await campaign_repo.get_by_id(post.campaign_id)
                    if campaign is not None:
                        campaign_settings = campaign.settings or {}

                try:
                    final_content, hashtags, processed_path, processing_meta = (
                        await MarketingAutomationEngineV1._prepare_post_content(
                            session,
                            post,
                            campaign_settings=campaign_settings,
                        )
                    )

                    media_asset_ids: list[str] = []
                    if processed_path:
                        media_bytes = (MEDIA_ROOT / processed_path).read_bytes()
                        asset = await AutoMarketingEngineV1.store_media(
                            OWNER_ID,
                            file_name=Path(processed_path).name,
                            content=media_bytes,
                            media_type="photo",
                            campaign_id=None,
                            car_id=post.car_id,
                        )
                        media_asset_ids = [asset["id"]]

                    publication = await AutoMarketingEngineV1.queue_publication(
                        OWNER_ID,
                        channel=post.channel,
                        content=final_content,
                        campaign_id=None,
                        car_id=post.car_id,
                        media_asset_ids=media_asset_ids,
                        scheduled_at=None,
                        target_config=post.target_config,
                    )

                    await post_repo.update_post(
                        post,
                        content=final_content,
                        hashtags=hashtags,
                        processed_media_path=processed_path,
                        processing_metadata=processing_meta,
                        publication_id=uuid.UUID(publication["id"]),
                        status=ScheduledPostStatus.QUEUED.value,
                    )

                    publish_result = await AutoMarketingEngineV1.process_due_publications(limit=5)
                    if publish_result.get("published", 0) > 0:
                        await post_repo.update_post(
                            post,
                            status=ScheduledPostStatus.PUBLISHED.value,
                            published_at=datetime.now(timezone.utc),
                        )
                        published += 1
                        if post.campaign_id is not None:
                            await campaign_repo.increment_metric(
                                post.campaign_id,
                                "published",
                                channel=post.channel,
                            )
                    else:
                        failed += 1
                        await post_repo.update_post(
                            post,
                            status=ScheduledPostStatus.FAILED.value,
                            error_message="Publication queue processing failed",
                        )

                    results.append({
                        "id": str(post.id),
                        "channel": post.channel,
                        "status": post.status,
                        "hashtags": hashtags,
                    })
                except Exception as exc:
                    failed += 1
                    await post_repo.update_post(
                        post,
                        status=ScheduledPostStatus.FAILED.value,
                        error_message=str(exc)[:2000],
                    )
                    if post.campaign_id is not None:
                        await campaign_repo.increment_metric(
                            post.campaign_id,
                            "failed",
                            channel=post.channel,
                        )
                    results.append({
                        "id": str(post.id),
                        "channel": post.channel,
                        "status": ScheduledPostStatus.FAILED.value,
                        "error": str(exc),
                    })

        return {
            "processed": processed,
            "published": published,
            "failed": failed,
            "results": results,
        }

    @staticmethod
    async def process_repost_rules(*, limit: int = 10) -> dict[str, Any]:
        created = 0
        results: list[dict[str, Any]] = []

        async with get_session() as session:
            rule_repo = RepostRuleRepository(session)
            post_repo = ScheduledPostRepository(session)
            campaign_repo = AutomationCampaignRepository(session)
            due_rules = await rule_repo.list_due(limit=limit)

            for rule in due_rules:
                generation = rule.repost_count + 1
                for channel in rule.channels or []:
                    post = await post_repo.create(
                        channel=channel,
                        content=rule.source_content or "",
                        scheduled_at=datetime.now(timezone.utc),
                        campaign_id=rule.campaign_id,
                        car_id=rule.car_id,
                        source_media_path=rule.source_media_path,
                        repost_rule_id=rule.id,
                        repost_generation=generation,
                        created_by=rule.created_by,
                    )
                    created += 1
                    if rule.campaign_id is not None:
                        await campaign_repo.increment_metric(
                            rule.campaign_id,
                            "reposted",
                            channel=channel,
                        )
                    results.append({
                        "rule_id": str(rule.id),
                        "post_id": str(post.id),
                        "channel": channel,
                        "generation": generation,
                    })

                await rule_repo.mark_reposted(rule)

        return {"created": created, "results": results}

    @staticmethod
    async def run_automation_cycle(*, post_limit: int = 20, repost_limit: int = 10) -> dict[str, Any]:
        posts = await MarketingAutomationEngineV1.process_due_scheduled_posts(limit=post_limit)
        reposts = await MarketingAutomationEngineV1.process_repost_rules(limit=repost_limit)
        return {"scheduled_posts": posts, "reposts": reposts}

    @staticmethod
    async def get_tracking_stats(actor_id: int) -> dict[str, Any]:
        if not await MarketingAutomationEngineV1.user_can_access(actor_id):
            raise MarketingAutomationEngineError("Access denied")

        async with get_session() as session:
            campaigns = await AutomationCampaignRepository(session).list_campaigns(limit=100)
            post_counts = await ScheduledPostRepository(session).count_by_status()
            return {
                "campaigns": [
                    MarketingAutomationEngineV1._campaign_snapshot(c)
                    for c in campaigns
                ],
                "scheduled_posts_by_status": post_counts,
                "totals": {
                    "campaigns": len(campaigns),
                    "scheduled": post_counts.get(ScheduledPostStatus.SCHEDULED.value, 0),
                    "published": post_counts.get(ScheduledPostStatus.PUBLISHED.value, 0),
                    "failed": post_counts.get(ScheduledPostStatus.FAILED.value, 0),
                },
            }

    @staticmethod
    async def store_source_media(
        actor_id: int,
        *,
        file_name: str,
        content: bytes,
    ) -> str:
        if not await MarketingAutomationEngineV1.user_can_access(actor_id):
            raise MarketingAutomationEngineError("Access denied")

        MEDIA_ROOT.mkdir(parents=True, exist_ok=True)
        safe_name = file_name.replace("/", "_").replace("\\", "_") or "upload.jpg"
        relative = f"uploads/{uuid.uuid4()}_{safe_name}"
        path = MEDIA_ROOT / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return relative
