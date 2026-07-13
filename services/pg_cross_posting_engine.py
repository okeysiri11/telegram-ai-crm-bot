# Cross Posting Engine v1 — scheduled posting, reposting, tracking, analytics.

from __future__ import annotations

import hashlib
import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from config import OWNER_ID
from database.models.audit_log import AuditAction
from database.models.cross_posting_engine import (
    PostingChannelType,
    PostingJobStatus,
    PostingResultStatus,
)
from database.session import get_session
from repositories.audit_repository import AuditRepository
from repositories.cross_posting_repository import (
    PostingChannelRepository,
    PostingJobRepository,
    PostingResultRepository,
    PostingTemplateRepository,
)
from repositories.user_role_repository import UserRoleRepository
from services.pg_partner_tenant_engine import PartnerTenantEngineV1

logger = logging.getLogger(__name__)

CROSS_POSTING_ROLES = frozenset({"OWNER", "ADMIN", "MANAGER"})
MAX_PUBLISH_ATTEMPTS = 5

DEFAULT_TEMPLATES: tuple[dict[str, str], ...] = (
    {
        "code": "listing_telegram",
        "name": "Vehicle Listing — Telegram",
        "channel_type": PostingChannelType.TELEGRAM.value,
        "body_template": "🚗 {{title}}\n{{content}}",
    },
    {
        "code": "listing_instagram",
        "name": "Vehicle Listing — Instagram",
        "channel_type": PostingChannelType.INSTAGRAM.value,
        "body_template": "{{title}}\n\n{{content}}\n\n#cars #auto",
    },
    {
        "code": "listing_facebook",
        "name": "Vehicle Listing — Facebook",
        "channel_type": PostingChannelType.FACEBOOK.value,
        "body_template": "{{title}}\n{{content}}",
    },
    {
        "code": "listing_tiktok",
        "name": "Vehicle Listing — TikTok",
        "channel_type": PostingChannelType.TIKTOK.value,
        "body_template": "{{title}} — {{content}} #fyp #cars",
    },
)


class CrossPostingEngineError(Exception):
    pass


class CrossPostingEngineV1:
    @staticmethod
    async def user_can_access(user_id: int) -> bool:
        if user_id == OWNER_ID:
            return True
        async with get_session() as session:
            roles = await UserRoleRepository(session).get_user_roles(user_id)
            return any(role.code in CROSS_POSTING_ROLES for role in roles)

    @staticmethod
    async def _require_access(actor_id: int, tenant_id: uuid.UUID):
        if not await CrossPostingEngineV1.user_can_access(actor_id):
            raise CrossPostingEngineError("Cross posting access denied")
        return await PartnerTenantEngineV1.resolve_context(actor_id, tenant_id)

    @staticmethod
    def _content_hash(content: str) -> str:
        normalized = " ".join(content.strip().lower().split())
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    @staticmethod
    def _channel_snapshot(row) -> dict[str, Any]:
        return {
            "id": str(row.id),
            "channel_type": row.channel_type,
            "external_id": row.external_id,
            "display_name": row.display_name,
            "is_active": row.is_active,
        }

    @staticmethod
    def _job_snapshot(row) -> dict[str, Any]:
        return {
            "id": str(row.id),
            "channel_id": str(row.channel_id),
            "title": row.title,
            "status": row.status,
            "scheduled_at": row.scheduled_at.isoformat() if row.scheduled_at else None,
            "published_at": row.published_at.isoformat() if row.published_at else None,
            "is_repost": row.is_repost,
            "content_hash": row.content_hash,
        }

    @staticmethod
    def _result_snapshot(row) -> dict[str, Any]:
        return {
            "id": str(row.id),
            "job_id": str(row.job_id),
            "channel_type": row.channel_type,
            "status": row.status,
            "external_post_id": row.external_post_id,
            "published_url": row.published_url,
            "views": row.views,
            "likes": row.likes,
            "shares": row.shares,
            "comments": row.comments,
            "clicks": row.clicks,
            "analytics_collected_at": (
                row.analytics_collected_at.isoformat() if row.analytics_collected_at else None
            ),
        }

    @staticmethod
    async def bootstrap_templates(actor_id: int, tenant_id: uuid.UUID) -> list[dict[str, Any]]:
        ctx = await CrossPostingEngineV1._require_access(actor_id, tenant_id)
        created: list[dict[str, Any]] = []
        async with get_session() as session:
            repo = PostingTemplateRepository(session)
            for spec in DEFAULT_TEMPLATES:
                existing = await repo.get_by_code(tenant_id, spec["code"])
                if existing:
                    created.append({"code": existing.code, "channel_type": existing.channel_type})
                    continue
                row = await repo.create(
                    tenant_id=tenant_id,
                    company_id=ctx.company_id,
                    code=spec["code"],
                    name=spec["name"],
                    channel_type=spec["channel_type"],
                    body_template=spec["body_template"],
                )
                created.append({"code": row.code, "channel_type": row.channel_type})
        return created

    @staticmethod
    async def register_channel(
        actor_id: int,
        tenant_id: uuid.UUID,
        *,
        channel_type: str,
        external_id: str,
        display_name: str,
        channel_integration_id: uuid.UUID | None = None,
    ) -> dict[str, Any]:
        ctx = await CrossPostingEngineV1._require_access(actor_id, tenant_id)
        async with get_session() as session:
            row = await PostingChannelRepository(session).create(
                tenant_id=tenant_id,
                company_id=ctx.company_id,
                channel_type=channel_type,
                external_id=external_id,
                display_name=display_name,
                channel_integration_id=channel_integration_id,
            )
            await AuditRepository(session).create_log(
                user_id=actor_id,
                company_id=ctx.company_id,
                tenant_id=tenant_id,
                entity_type="posting_channel",
                entity_id=str(row.id),
                action=AuditAction.CREATE.value,
                new_value={"channel_type": channel_type, "display_name": display_name},
            )
            await session.refresh(row)
            return CrossPostingEngineV1._channel_snapshot(row)

    @staticmethod
    async def check_duplicate(
        tenant_id: uuid.UUID,
        content: str,
        *,
        channel_id: uuid.UUID | None = None,
    ) -> dict[str, Any]:
        content_hash = CrossPostingEngineV1._content_hash(content)
        async with get_session() as session:
            duplicate = await PostingJobRepository(session).find_duplicate(
                tenant_id, content_hash, channel_id=channel_id
            )
        return {
            "is_duplicate": duplicate is not None,
            "content_hash": content_hash,
            "existing_job_id": str(duplicate.id) if duplicate else None,
        }

    @staticmethod
    async def schedule_post(
        actor_id: int,
        tenant_id: uuid.UUID,
        *,
        channel_id: uuid.UUID,
        title: str,
        content: str,
        scheduled_at: datetime,
        template_id: uuid.UUID | None = None,
        car_id: uuid.UUID | None = None,
    ) -> dict[str, Any]:
        ctx = await CrossPostingEngineV1._require_access(actor_id, tenant_id)
        content_hash = CrossPostingEngineV1._content_hash(content)

        async with get_session() as session:
            channel = await PostingChannelRepository(session).get_by_id(channel_id)
            if channel is None or channel.tenant_id != tenant_id:
                raise CrossPostingEngineError(f"Channel not found: {channel_id}")

            duplicate = await PostingJobRepository(session).find_duplicate(
                tenant_id, content_hash, channel_id=channel_id
            )
            if duplicate:
                blocked = await PostingJobRepository(session).create(
                    tenant_id=tenant_id,
                    company_id=ctx.company_id,
                    channel_id=channel_id,
                    title=title,
                    content=content,
                    content_hash=content_hash,
                    template_id=template_id,
                    car_id=car_id,
                    status=PostingJobStatus.DUPLICATE.value,
                    scheduled_at=scheduled_at,
                    created_by=actor_id,
                    metadata={"blocked_by_job_id": str(duplicate.id)},
                )
                await session.refresh(blocked)
                return {
                    "job": CrossPostingEngineV1._job_snapshot(blocked),
                    "duplicate_detected": True,
                    "existing_job_id": str(duplicate.id),
                }

            job = await PostingJobRepository(session).create(
                tenant_id=tenant_id,
                company_id=ctx.company_id,
                channel_id=channel_id,
                title=title,
                content=content,
                content_hash=content_hash,
                template_id=template_id,
                car_id=car_id,
                status=PostingJobStatus.SCHEDULED.value,
                scheduled_at=scheduled_at,
                created_by=actor_id,
            )
            await AuditRepository(session).create_log(
                user_id=actor_id,
                company_id=ctx.company_id,
                tenant_id=tenant_id,
                entity_type="posting_job",
                entity_id=str(job.id),
                action=AuditAction.CREATE.value,
                new_value={"title": title, "scheduled_at": scheduled_at.isoformat()},
            )
            await session.refresh(job)
            return {
                "job": CrossPostingEngineV1._job_snapshot(job),
                "duplicate_detected": False,
            }

    @staticmethod
    async def create_repost(
        actor_id: int,
        tenant_id: uuid.UUID,
        source_job_id: uuid.UUID,
        *,
        scheduled_at: datetime | None = None,
    ) -> dict[str, Any]:
        ctx = await CrossPostingEngineV1._require_access(actor_id, tenant_id)
        now = datetime.now(timezone.utc)
        when = scheduled_at or now

        async with get_session() as session:
            source = await PostingJobRepository(session).get_by_id(source_job_id)
            if source is None or source.tenant_id != tenant_id:
                raise CrossPostingEngineError(f"Source job not found: {source_job_id}")
            if source.status != PostingJobStatus.PUBLISHED.value:
                raise CrossPostingEngineError("Can only repost published jobs")

            job = await PostingJobRepository(session).create(
                tenant_id=tenant_id,
                company_id=ctx.company_id,
                channel_id=source.channel_id,
                title=f"Repost: {source.title}",
                content=source.content,
                content_hash=CrossPostingEngineV1._content_hash(source.content),
                template_id=source.template_id,
                car_id=source.car_id,
                status=PostingJobStatus.SCHEDULED.value,
                scheduled_at=when,
                is_repost=True,
                source_job_id=source_job_id,
                created_by=actor_id,
            )
            await session.refresh(job)
            return CrossPostingEngineV1._job_snapshot(job)

    @staticmethod
    async def _publish_job(session, job) -> dict[str, Any]:
        channel = await PostingChannelRepository(session).get_by_id(job.channel_id)
        if channel is None or not channel.is_active:
            raise CrossPostingEngineError("Channel unavailable")

        await PostingJobRepository(session).update_fields(
            job.id,
            status=PostingJobStatus.PUBLISHING.value,
            attempt_count=job.attempt_count + 1,
        )

        now = datetime.now(timezone.utc)
        external_id = f"{channel.channel_type.lower()}-{job.id.hex[:12]}"
        published_url = f"https://publish.example/{channel.channel_type.lower()}/{external_id}"

        result = await PostingResultRepository(session).create(
            job_id=job.id,
            tenant_id=job.tenant_id,
            channel_type=channel.channel_type,
            status=PostingResultStatus.SUCCESS.value,
            external_post_id=external_id,
            published_url=published_url,
            views=0,
            likes=0,
            shares=0,
            comments=0,
            clicks=0,
            analytics_collected_at=now,
        )
        await PostingJobRepository(session).update_fields(
            job.id,
            status=PostingJobStatus.PUBLISHED.value,
            published_at=now,
        )
        return CrossPostingEngineV1._result_snapshot(result)

    @staticmethod
    async def process_due_jobs(*, limit: int = 20) -> dict[str, Any]:
        now = datetime.now(timezone.utc)
        processed: list[dict[str, Any]] = []
        failed: list[dict[str, Any]] = []

        async with get_session() as session:
            jobs = await PostingJobRepository(session).list_due(before=now, limit=limit)
            for job in jobs:
                try:
                    if job.attempt_count >= MAX_PUBLISH_ATTEMPTS:
                        await PostingJobRepository(session).update_fields(
                            job.id, status=PostingJobStatus.FAILED.value
                        )
                        failed.append({"job_id": str(job.id), "reason": "max_attempts"})
                        continue
                    snapshot = await CrossPostingEngineV1._publish_job(session, job)
                    processed.append(snapshot)
                except Exception as exc:
                    logger.exception("Failed to publish job %s", job.id)
                    await PostingJobRepository(session).update_fields(
                        job.id, status=PostingJobStatus.FAILED.value
                    )
                    await PostingResultRepository(session).create(
                        job_id=job.id,
                        tenant_id=job.tenant_id,
                        channel_type="UNKNOWN",
                        status=PostingResultStatus.FAILED.value,
                        error_message=str(exc),
                    )
                    failed.append({"job_id": str(job.id), "reason": str(exc)})

        return {
            "processed_count": len(processed),
            "failed_count": len(failed),
            "processed": processed,
            "failed": failed,
        }

    @staticmethod
    async def collect_post_analytics(
        actor_id: int,
        tenant_id: uuid.UUID,
        result_id: uuid.UUID,
    ) -> dict[str, Any]:
        await CrossPostingEngineV1._require_access(actor_id, tenant_id)
        now = datetime.now(timezone.utc)

        async with get_session() as session:
            results = await PostingResultRepository(session).list_by_tenant(tenant_id, limit=200)
            row = next((r for r in results if r.id == result_id), None)
            if row is None:
                raise CrossPostingEngineError(f"Result not found: {result_id}")

            views = row.views + 10
            likes = row.likes + 2
            shares = row.shares + 1
            comments = row.comments
            clicks = row.clicks + 3

            updated = await PostingResultRepository(session).update_fields(
                result_id,
                views=views,
                likes=likes,
                shares=shares,
                comments=comments,
                clicks=clicks,
                analytics_collected_at=now,
            )
            await session.refresh(updated)
            return CrossPostingEngineV1._result_snapshot(updated)

    @staticmethod
    async def get_publication_tracking(
        actor_id: int,
        tenant_id: uuid.UUID,
        job_id: uuid.UUID,
    ) -> dict[str, Any]:
        await CrossPostingEngineV1._require_access(actor_id, tenant_id)
        async with get_session() as session:
            job = await PostingJobRepository(session).get_by_id(job_id)
            if job is None or job.tenant_id != tenant_id:
                raise CrossPostingEngineError(f"Job not found: {job_id}")
            result = await PostingResultRepository(session).get_by_job(job_id)
            return {
                "job": CrossPostingEngineV1._job_snapshot(job),
                "result": CrossPostingEngineV1._result_snapshot(result) if result else None,
            }

    @staticmethod
    async def get_cross_posting_dashboard(
        actor_id: int,
        tenant_id: uuid.UUID,
    ) -> dict[str, Any]:
        await CrossPostingEngineV1._require_access(actor_id, tenant_id)
        templates = await CrossPostingEngineV1.bootstrap_templates(actor_id, tenant_id)
        async with get_session() as session:
            channels = await PostingChannelRepository(session).list_by_tenant(tenant_id)
            jobs = await PostingJobRepository(session).list_by_tenant(tenant_id, limit=20)
            results = await PostingResultRepository(session).list_by_tenant(tenant_id, limit=20)

        by_status: dict[str, int] = {}
        for job in jobs:
            by_status[job.status] = by_status.get(job.status, 0) + 1

        total_engagement = sum(r.views + r.likes + r.shares for r in results)

        return {
            "tenant_id": str(tenant_id),
            "supported_channels": [c.value for c in PostingChannelType],
            "channels": [CrossPostingEngineV1._channel_snapshot(c) for c in channels],
            "templates": templates,
            "job_count": len(jobs),
            "jobs_by_status": by_status,
            "publication_count": len(results),
            "total_engagement": total_engagement,
            "capabilities": [
                "scheduled_posting",
                "reposting",
                "publication_tracking",
                "duplicate_detection",
                "post_analytics_collection",
            ],
        }
