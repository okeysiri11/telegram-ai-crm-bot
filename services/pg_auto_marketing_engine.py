# Auto Marketing Engine v1 — campaigns, templates, media, and multi-channel publishing.

from __future__ import annotations

import logging
import re
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError

from config import BOT_TOKEN, MARKETING_TELEGRAM_CHANNEL_ID, OWNER_ID
from database.models.audit_log import AuditAction
from database.models.auto_marketing_engine import (
    CampaignStatus,
    MarketingChannel,
    PublicationStatus,
)
from database.session import get_session
from repositories.audit_repository import AuditRepository
from repositories.auto_marketing_repository import (
    MarketingCampaignRepository,
    MarketingMediaRepository,
    MarketingPostTemplateRepository,
    MarketingPublicationRepository,
)
from repositories.car_repository import CarRepository
from repositories.user_role_repository import UserRoleRepository

logger = logging.getLogger(__name__)

MARKETING_ROLES = frozenset({"OWNER", "ADMIN", "MANAGER"})
MEDIA_STORAGE_ROOT = Path(__file__).resolve().parent.parent / "storage" / "marketing"
MAX_PUBLISH_ATTEMPTS = 5

DEFAULT_TEMPLATES: tuple[dict[str, Any], ...] = (
    {
        "code": "car_listing_telegram",
        "name": "Car Listing — Telegram",
        "channel": MarketingChannel.TELEGRAM.value,
        "body_template": (
            "🚗 {{year}} {{make}} {{model}}\n"
            "VIN: {{vin}}\n"
            "Цена: {{sale_price}}\n"
            "{{description}}"
        ),
        "default_variables": {"description": "Связь в личные сообщения."},
    },
    {
        "code": "car_listing_instagram",
        "name": "Car Listing — Instagram",
        "channel": MarketingChannel.INSTAGRAM.value,
        "body_template": (
            "{{year}} {{make}} {{model}} ✨\n"
            "VIN {{vin}} | {{sale_price}}\n"
            "{{description}}\n"
            "#auto #cars #forsale"
        ),
        "default_variables": {"description": "DM for details."},
    },
    {
        "code": "car_listing_facebook",
        "name": "Car Listing — Facebook",
        "channel": MarketingChannel.FACEBOOK.value,
        "body_template": (
            "For sale: {{year}} {{make}} {{model}}\n"
            "VIN: {{vin}}\n"
            "Price: {{sale_price}}\n"
            "{{description}}"
        ),
        "default_variables": {"description": "Message us to schedule a viewing."},
    },
    {
        "code": "car_listing_tiktok",
        "name": "Car Listing — TikTok",
        "channel": MarketingChannel.TIKTOK.value,
        "body_template": (
            "{{year}} {{make}} {{model}} 🔥\n"
            "{{sale_price}} | VIN {{vin}}\n"
            "{{description}}"
        ),
        "default_variables": {"description": "Link in bio."},
    },
)

_templates_seeded = False
_TEMPLATE_VAR_PATTERN = re.compile(r"\{\{\s*([a-zA-Z0-9_]+)\s*\}\}")


class AutoMarketingEngineError(Exception):
    pass


class AutoMarketingEngineV1:
    @staticmethod
    async def user_can_access(user_id: int) -> bool:
        if user_id == OWNER_ID:
            return True
        async with get_session() as session:
            roles = await UserRoleRepository(session).get_user_roles(user_id)
            return any(role.code in MARKETING_ROLES for role in roles)

    @staticmethod
    def _campaign_snapshot(campaign) -> dict[str, Any]:
        return {
            "id": str(campaign.id),
            "name": campaign.name,
            "description": campaign.description,
            "car_id": str(campaign.car_id) if campaign.car_id else None,
            "status": campaign.status,
            "channels": campaign.channels or [],
            "metrics": campaign.metrics or {},
            "owner_user_id": campaign.owner_user_id,
            "started_at": campaign.started_at.isoformat() if campaign.started_at else None,
            "ended_at": campaign.ended_at.isoformat() if campaign.ended_at else None,
            "created_at": campaign.created_at.isoformat(),
            "updated_at": campaign.updated_at.isoformat(),
        }

    @staticmethod
    def _template_snapshot(template) -> dict[str, Any]:
        return {
            "id": str(template.id),
            "code": template.code,
            "name": template.name,
            "channel": template.channel,
            "body_template": template.body_template,
            "default_variables": template.default_variables or {},
            "is_active": template.is_active,
            "description": template.description,
        }

    @staticmethod
    def _media_snapshot(asset) -> dict[str, Any]:
        return {
            "id": str(asset.id),
            "campaign_id": str(asset.campaign_id) if asset.campaign_id else None,
            "car_id": str(asset.car_id) if asset.car_id else None,
            "file_name": asset.file_name,
            "storage_path": asset.storage_path,
            "media_type": asset.media_type,
            "telegram_file_id": asset.telegram_file_id,
            "public_url": asset.public_url,
            "metadata": asset.metadata_ or {},
            "uploaded_by": asset.uploaded_by,
            "created_at": asset.created_at.isoformat(),
        }

    @staticmethod
    def _publication_snapshot(publication) -> dict[str, Any]:
        return {
            "id": str(publication.id),
            "campaign_id": str(publication.campaign_id) if publication.campaign_id else None,
            "car_id": str(publication.car_id) if publication.car_id else None,
            "template_id": str(publication.template_id) if publication.template_id else None,
            "channel": publication.channel,
            "content": publication.content,
            "media_asset_ids": publication.media_asset_ids or [],
            "status": publication.status,
            "scheduled_at": publication.scheduled_at.isoformat()
            if publication.scheduled_at
            else None,
            "published_at": publication.published_at.isoformat()
            if publication.published_at
            else None,
            "target_config": publication.target_config or {},
            "external_post_id": publication.external_post_id,
            "error_message": publication.error_message,
            "attempt_count": publication.attempt_count,
            "created_by": publication.created_by,
            "created_at": publication.created_at.isoformat(),
        }

    @staticmethod
    def render_template(body: str, variables: dict[str, Any]) -> str:
        def replace(match: re.Match[str]) -> str:
            key = match.group(1)
            value = variables.get(key, "")
            return "" if value is None else str(value)

        return _TEMPLATE_VAR_PATTERN.sub(replace, body).strip()

    @staticmethod
    def _car_variables(car) -> dict[str, Any]:
        return {
            "vin": car.vin,
            "make": car.make,
            "model": car.model,
            "year": car.year,
            "color": car.color or "",
            "mileage": car.mileage or "",
            "sale_price": str(car.sale_price) if car.sale_price is not None else "—",
            "purchase_price": str(car.purchase_price) if car.purchase_price is not None else "—",
            "status": car.status,
        }

    @staticmethod
    async def ensure_default_templates() -> list[dict[str, Any]]:
        global _templates_seeded
        created: list[dict[str, Any]] = []

        async with get_session() as session:
            repo = MarketingPostTemplateRepository(session)
            for spec in DEFAULT_TEMPLATES:
                existing = await repo.get_by_code(spec["code"])
                if existing is not None:
                    continue
                template = await repo.create(**spec)
                created.append(AutoMarketingEngineV1._template_snapshot(template))

        _templates_seeded = True
        return created

    @staticmethod
    async def create_campaign(
        actor_id: int,
        *,
        name: str,
        description: str | None = None,
        car_id: uuid.UUID | None = None,
        channels: list[str] | None = None,
        activate: bool = False,
    ) -> dict[str, Any]:
        if not await AutoMarketingEngineV1.user_can_access(actor_id):
            raise AutoMarketingEngineError("Access denied")

        channel_list = channels or [c.value for c in MarketingChannel]
        for channel in channel_list:
            if channel not in {c.value for c in MarketingChannel}:
                raise AutoMarketingEngineError(f"Invalid channel: {channel}")

        async with get_session() as session:
            if car_id is not None:
                car = await CarRepository(session).get_car(car_id)
                if car is None:
                    raise AutoMarketingEngineError(f"Car not found: {car_id}")

            campaign = await MarketingCampaignRepository(session).create(
                name=name,
                description=description,
                car_id=car_id,
                channels=channel_list,
                owner_user_id=actor_id,
                status=CampaignStatus.ACTIVE.value if activate else CampaignStatus.DRAFT.value,
                started_at=datetime.now(timezone.utc) if activate else None,
            )
            await AuditRepository(session).create_log(
                user_id=actor_id,
                entity_type="marketing_campaign",
                entity_id=str(campaign.id),
                action=AuditAction.CREATE.value,
                new_value={"name": name, "channels": channel_list},
            )
            return AutoMarketingEngineV1._campaign_snapshot(campaign)

    @staticmethod
    async def list_campaigns(
        actor_id: int,
        *,
        status: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        if not await AutoMarketingEngineV1.user_can_access(actor_id):
            raise AutoMarketingEngineError("Access denied")

        async with get_session() as session:
            campaigns = await MarketingCampaignRepository(session).list_campaigns(
                status=status,
                limit=limit,
            )
            return [AutoMarketingEngineV1._campaign_snapshot(c) for c in campaigns]

    @staticmethod
    async def get_campaign(
        actor_id: int,
        campaign_id: uuid.UUID,
    ) -> dict[str, Any]:
        if not await AutoMarketingEngineV1.user_can_access(actor_id):
            raise AutoMarketingEngineError("Access denied")

        async with get_session() as session:
            campaign = await MarketingCampaignRepository(session).get_by_id(campaign_id)
            if campaign is None:
                raise AutoMarketingEngineError(f"Campaign not found: {campaign_id}")
            return AutoMarketingEngineV1._campaign_snapshot(campaign)

    @staticmethod
    async def list_templates(
        actor_id: int,
        *,
        channel: str | None = None,
    ) -> list[dict[str, Any]]:
        if not await AutoMarketingEngineV1.user_can_access(actor_id):
            raise AutoMarketingEngineError("Access denied")

        await AutoMarketingEngineV1.ensure_default_templates()

        async with get_session() as session:
            templates = await MarketingPostTemplateRepository(session).list_templates(
                channel=channel,
            )
            return [AutoMarketingEngineV1._template_snapshot(t) for t in templates]

    @staticmethod
    async def store_media(
        actor_id: int,
        *,
        file_name: str,
        content: bytes,
        media_type: str,
        campaign_id: uuid.UUID | None = None,
        car_id: uuid.UUID | None = None,
        telegram_file_id: str | None = None,
        public_url: str | None = None,
        metadata: dict | None = None,
    ) -> dict[str, Any]:
        if not await AutoMarketingEngineV1.user_can_access(actor_id):
            raise AutoMarketingEngineError("Access denied")

        MEDIA_STORAGE_ROOT.mkdir(parents=True, exist_ok=True)
        safe_name = re.sub(r"[^\w.\-]", "_", file_name) or "asset.bin"
        asset_id = uuid.uuid4()
        relative_path = f"{asset_id}/{safe_name}"
        absolute_path = MEDIA_STORAGE_ROOT / relative_path
        absolute_path.parent.mkdir(parents=True, exist_ok=True)
        absolute_path.write_bytes(content)

        async with get_session() as session:
            asset = await MarketingMediaRepository(session).create(
                file_name=safe_name,
                storage_path=str(relative_path),
                media_type=media_type,
                campaign_id=campaign_id,
                car_id=car_id,
                telegram_file_id=telegram_file_id,
                public_url=public_url,
                metadata=metadata,
                uploaded_by=actor_id,
            )
            await AuditRepository(session).create_log(
                user_id=actor_id,
                entity_type="marketing_media",
                entity_id=str(asset.id),
                action=AuditAction.CREATE.value,
                new_value={"file_name": safe_name, "media_type": media_type},
            )
            return AutoMarketingEngineV1._media_snapshot(asset)

    @staticmethod
    async def queue_publication(
        actor_id: int,
        *,
        channel: str,
        content: str,
        campaign_id: uuid.UUID | None = None,
        car_id: uuid.UUID | None = None,
        template_code: str | None = None,
        variables: dict[str, Any] | None = None,
        media_asset_ids: list[str] | None = None,
        scheduled_at: datetime | None = None,
        target_config: dict | None = None,
    ) -> dict[str, Any]:
        if not await AutoMarketingEngineV1.user_can_access(actor_id):
            raise AutoMarketingEngineError("Access denied")

        await AutoMarketingEngineV1.ensure_default_templates()

        rendered_content = content
        template_id = None

        async with get_session() as session:
            if template_code:
                template = await MarketingPostTemplateRepository(session).get_by_code(
                    template_code
                )
                if template is None:
                    raise AutoMarketingEngineError(f"Template not found: {template_code}")
                merged = dict(template.default_variables or {})
                if variables:
                    merged.update(variables)
                if car_id is not None:
                    car = await CarRepository(session).get_car(car_id)
                    if car is not None:
                        merged.update(AutoMarketingEngineV1._car_variables(car))
                rendered_content = AutoMarketingEngineV1.render_template(
                    template.body_template,
                    merged,
                )
                template_id = template.id

            status = (
                PublicationStatus.SCHEDULED.value
                if scheduled_at and scheduled_at > datetime.now(timezone.utc)
                else PublicationStatus.QUEUED.value
            )

            publication = await MarketingPublicationRepository(session).create(
                channel=channel,
                content=rendered_content,
                campaign_id=campaign_id,
                car_id=car_id,
                template_id=template_id,
                media_asset_ids=media_asset_ids,
                status=status,
                scheduled_at=scheduled_at,
                target_config=target_config,
                created_by=actor_id,
            )

            if campaign_id is not None:
                await MarketingCampaignRepository(session).increment_channel_metric(
                    campaign_id,
                    channel,
                    "queued",
                )

            await AuditRepository(session).create_log(
                user_id=actor_id,
                entity_type="marketing_publication",
                entity_id=str(publication.id),
                action=AuditAction.CREATE.value,
                new_value={"channel": channel, "status": status},
            )
            return AutoMarketingEngineV1._publication_snapshot(publication)

    @staticmethod
    async def schedule_car_campaign(
        actor_id: int,
        *,
        car_id: uuid.UUID,
        channels: list[str] | None = None,
        scheduled_at: datetime | None = None,
        campaign_name: str | None = None,
        target_config: dict | None = None,
    ) -> dict[str, Any]:
        """Create a campaign and queue publications for all requested channels."""
        if not await AutoMarketingEngineV1.user_can_access(actor_id):
            raise AutoMarketingEngineError("Access denied")

        channel_list = channels or [c.value for c in MarketingChannel]
        async with get_session() as session:
            car = await CarRepository(session).get_car(car_id)
            if car is None:
                raise AutoMarketingEngineError(f"Car not found: {car_id}")

        name = campaign_name or f"{car.year} {car.make} {car.model}"
        campaign = await AutoMarketingEngineV1.create_campaign(
            actor_id,
            name=name,
            car_id=car_id,
            channels=channel_list,
            activate=True,
        )

        publications: list[dict[str, Any]] = []
        template_map = {
            MarketingChannel.TELEGRAM.value: "car_listing_telegram",
            MarketingChannel.INSTAGRAM.value: "car_listing_instagram",
            MarketingChannel.FACEBOOK.value: "car_listing_facebook",
            MarketingChannel.TIKTOK.value: "car_listing_tiktok",
        }

        for channel in channel_list:
            pub = await AutoMarketingEngineV1.queue_publication(
                actor_id,
                channel=channel,
                content="",
                campaign_id=uuid.UUID(campaign["id"]),
                car_id=car_id,
                template_code=template_map.get(channel),
                scheduled_at=scheduled_at,
                target_config=target_config,
            )
            publications.append(pub)

        return {
            "campaign": campaign,
            "publications": publications,
        }

    @staticmethod
    async def get_queue_stats(actor_id: int) -> dict[str, Any]:
        if not await AutoMarketingEngineV1.user_can_access(actor_id):
            raise AutoMarketingEngineError("Access denied")

        async with get_session() as session:
            repo = MarketingPublicationRepository(session)
            return {
                "by_channel": await repo.queue_stats_by_channel(),
                "by_status": await repo.count_by_status(),
            }

    @staticmethod
    async def _publish_telegram(
        publication,
        media_assets: list,
    ) -> str:
        channel_id = (publication.target_config or {}).get("channel_id")
        if not channel_id:
            channel_id = MARKETING_TELEGRAM_CHANNEL_ID
        if not channel_id:
            raise AutoMarketingEngineError(
                "Telegram channel not configured (set MARKETING_TELEGRAM_CHANNEL_ID)"
            )
        if not BOT_TOKEN:
            raise AutoMarketingEngineError("BOT_TOKEN not configured")

        bot = Bot(token=BOT_TOKEN)
        try:
            photos = [a for a in media_assets if a.media_type == "photo"]
            if photos:
                first = photos[0]
                if first.telegram_file_id:
                    message = await bot.send_photo(
                        chat_id=channel_id,
                        photo=first.telegram_file_id,
                        caption=publication.content[:1024],
                    )
                elif first.public_url:
                    message = await bot.send_photo(
                        chat_id=channel_id,
                        photo=first.public_url,
                        caption=publication.content[:1024],
                    )
                else:
                    file_path = MEDIA_STORAGE_ROOT / first.storage_path
                    if file_path.exists():
                        message = await bot.send_photo(
                            chat_id=channel_id,
                            photo=file_path.read_bytes(),
                            caption=publication.content[:1024],
                        )
                    else:
                        message = await bot.send_message(
                            chat_id=channel_id,
                            text=publication.content[:4096],
                        )
            else:
                message = await bot.send_message(
                    chat_id=channel_id,
                    text=publication.content[:4096],
                )
            return str(message.message_id)
        except TelegramAPIError as exc:
            raise AutoMarketingEngineError(f"Telegram API error: {exc}") from exc
        finally:
            await bot.session.close()

    @staticmethod
    async def _publish_social_queue(
        publication,
        *,
        connector_name: str,
    ) -> str:
        """v1 queue processor — records external reference for connector handoff."""
        external_id = f"{connector_name}_{publication.id}"
        logger.info(
            "Queued %s publication %s for external connector",
            connector_name,
            publication.id,
        )
        return external_id

    @staticmethod
    async def process_due_publications(
        *,
        limit: int = 20,
    ) -> dict[str, Any]:
        """Publication scheduler — processes due queue items across all channels."""
        await AutoMarketingEngineV1.ensure_default_templates()

        processed = 0
        published = 0
        failed = 0
        results: list[dict[str, Any]] = []

        async with get_session() as session:
            pub_repo = MarketingPublicationRepository(session)
            media_repo = MarketingMediaRepository(session)
            campaign_repo = MarketingCampaignRepository(session)

            due = await pub_repo.list_due(limit=limit)

            for publication in due:
                if publication.attempt_count >= MAX_PUBLISH_ATTEMPTS:
                    await pub_repo.mark_failed(
                        publication,
                        "Max publish attempts exceeded",
                    )
                    failed += 1
                    continue

                await pub_repo.mark_publishing(publication)
                processed += 1

                media_assets = []
                for asset_id_str in publication.media_asset_ids or []:
                    try:
                        asset = await media_repo.get_by_id(uuid.UUID(asset_id_str))
                    except ValueError:
                        asset = None
                    if asset is not None:
                        media_assets.append(asset)

                try:
                    if publication.channel == MarketingChannel.TELEGRAM.value:
                        external_id = await AutoMarketingEngineV1._publish_telegram(
                            publication,
                            media_assets,
                        )
                    elif publication.channel == MarketingChannel.INSTAGRAM.value:
                        external_id = await AutoMarketingEngineV1._publish_social_queue(
                            publication,
                            connector_name="instagram",
                        )
                    elif publication.channel == MarketingChannel.FACEBOOK.value:
                        external_id = await AutoMarketingEngineV1._publish_social_queue(
                            publication,
                            connector_name="facebook",
                        )
                    elif publication.channel == MarketingChannel.TIKTOK.value:
                        external_id = await AutoMarketingEngineV1._publish_social_queue(
                            publication,
                            connector_name="tiktok",
                        )
                    else:
                        raise AutoMarketingEngineError(
                            f"Unsupported channel: {publication.channel}"
                        )

                    await pub_repo.mark_published(
                        publication,
                        external_post_id=external_id,
                    )
                    if publication.campaign_id is not None:
                        await campaign_repo.increment_channel_metric(
                            publication.campaign_id,
                            publication.channel,
                            "published",
                        )
                    published += 1
                    results.append({
                        "id": str(publication.id),
                        "channel": publication.channel,
                        "status": PublicationStatus.PUBLISHED.value,
                        "external_post_id": external_id,
                    })
                except AutoMarketingEngineError as exc:
                    await pub_repo.mark_failed(publication, str(exc))
                    if publication.campaign_id is not None:
                        await campaign_repo.increment_channel_metric(
                            publication.campaign_id,
                            publication.channel,
                            "failed",
                        )
                    failed += 1
                    results.append({
                        "id": str(publication.id),
                        "channel": publication.channel,
                        "status": PublicationStatus.FAILED.value,
                        "error": str(exc),
                    })

        return {
            "processed": processed,
            "published": published,
            "failed": failed,
            "results": results,
        }
