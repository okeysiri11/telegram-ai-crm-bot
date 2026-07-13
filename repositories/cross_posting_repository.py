# Cross Posting Engine v1 repositories.

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.cross_posting_engine import (
    POSTING_CHANNEL_TYPES,
    POSTING_JOB_STATUSES,
    POSTING_RESULT_STATUSES,
    PostingChannel,
    PostingJob,
    PostingJobStatus,
    PostingResult,
    PostingTemplate,
)


class PostingChannelRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        tenant_id: uuid.UUID,
        company_id: uuid.UUID,
        channel_type: str,
        external_id: str,
        display_name: str,
        channel_integration_id: uuid.UUID | None = None,
        is_active: bool = True,
        metadata: dict | None = None,
        **extra: Any,
    ) -> PostingChannel:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")
        if channel_type not in POSTING_CHANNEL_TYPES:
            raise ValueError(f"Invalid channel_type: {channel_type}")

        row = PostingChannel(
            tenant_id=tenant_id,
            company_id=company_id,
            channel_type=channel_type,
            external_id=external_id,
            display_name=display_name,
            channel_integration_id=channel_integration_id,
            is_active=is_active,
            metadata_=metadata,
        )
        self._session.add(row)
        await self._session.flush()
        return row

    async def get_by_id(self, channel_id: uuid.UUID) -> PostingChannel | None:
        result = await self._session.execute(
            select(PostingChannel).where(PostingChannel.id == channel_id)
        )
        return result.scalar_one_or_none()

    async def list_by_tenant(
        self,
        tenant_id: uuid.UUID,
        *,
        active_only: bool = False,
        limit: int = 50,
    ) -> list[PostingChannel]:
        stmt = (
            select(PostingChannel)
            .where(PostingChannel.tenant_id == tenant_id)
            .order_by(PostingChannel.display_name.asc())
            .limit(limit)
        )
        if active_only:
            stmt = stmt.where(PostingChannel.is_active.is_(True))
        result = await self._session.execute(stmt)
        return list(result.scalars().all())


class PostingTemplateRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        tenant_id: uuid.UUID,
        company_id: uuid.UUID,
        code: str,
        name: str,
        channel_type: str,
        body_template: str,
        default_variables: dict | None = None,
        is_active: bool = True,
        **extra: Any,
    ) -> PostingTemplate:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")

        row = PostingTemplate(
            tenant_id=tenant_id,
            company_id=company_id,
            code=code,
            name=name,
            channel_type=channel_type,
            body_template=body_template,
            default_variables=default_variables,
            is_active=is_active,
        )
        self._session.add(row)
        await self._session.flush()
        return row

    async def get_by_code(self, tenant_id: uuid.UUID, code: str) -> PostingTemplate | None:
        result = await self._session.execute(
            select(PostingTemplate).where(
                PostingTemplate.tenant_id == tenant_id,
                PostingTemplate.code == code,
            )
        )
        return result.scalar_one_or_none()

    async def list_by_tenant(self, tenant_id: uuid.UUID, *, limit: int = 50) -> list[PostingTemplate]:
        result = await self._session.execute(
            select(PostingTemplate)
            .where(PostingTemplate.tenant_id == tenant_id)
            .order_by(PostingTemplate.code.asc())
            .limit(limit)
        )
        return list(result.scalars().all())


class PostingJobRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        tenant_id: uuid.UUID,
        company_id: uuid.UUID,
        channel_id: uuid.UUID,
        title: str,
        content: str,
        content_hash: str,
        template_id: uuid.UUID | None = None,
        car_id: uuid.UUID | None = None,
        status: str = PostingJobStatus.DRAFT.value,
        scheduled_at: datetime | None = None,
        is_repost: bool = False,
        source_job_id: uuid.UUID | None = None,
        created_by: int | None = None,
        metadata: dict | None = None,
        **extra: Any,
    ) -> PostingJob:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")
        if status not in POSTING_JOB_STATUSES:
            raise ValueError(f"Invalid status: {status}")

        row = PostingJob(
            tenant_id=tenant_id,
            company_id=company_id,
            channel_id=channel_id,
            title=title,
            content=content,
            content_hash=content_hash,
            template_id=template_id,
            car_id=car_id,
            status=status,
            scheduled_at=scheduled_at,
            is_repost=is_repost,
            source_job_id=source_job_id,
            created_by=created_by,
            metadata_=metadata,
        )
        self._session.add(row)
        await self._session.flush()
        return row

    async def get_by_id(self, job_id: uuid.UUID) -> PostingJob | None:
        result = await self._session.execute(
            select(PostingJob).where(PostingJob.id == job_id)
        )
        return result.scalar_one_or_none()

    async def find_duplicate(
        self,
        tenant_id: uuid.UUID,
        content_hash: str,
        *,
        channel_id: uuid.UUID | None = None,
    ) -> PostingJob | None:
        stmt = select(PostingJob).where(
            PostingJob.tenant_id == tenant_id,
            PostingJob.content_hash == content_hash,
            PostingJob.status.in_([
                PostingJobStatus.SCHEDULED.value,
                PostingJobStatus.PUBLISHING.value,
                PostingJobStatus.PUBLISHED.value,
            ]),
        )
        if channel_id is not None:
            stmt = stmt.where(PostingJob.channel_id == channel_id)
        result = await self._session.execute(stmt.limit(1))
        return result.scalar_one_or_none()

    async def list_due(
        self,
        *,
        before: datetime,
        limit: int = 20,
    ) -> list[PostingJob]:
        result = await self._session.execute(
            select(PostingJob)
            .where(
                PostingJob.status == PostingJobStatus.SCHEDULED.value,
                PostingJob.scheduled_at.is_not(None),
                PostingJob.scheduled_at <= before,
            )
            .order_by(PostingJob.scheduled_at.asc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def list_by_tenant(
        self,
        tenant_id: uuid.UUID,
        *,
        status: str | None = None,
        limit: int = 50,
    ) -> list[PostingJob]:
        stmt = (
            select(PostingJob)
            .where(PostingJob.tenant_id == tenant_id)
            .order_by(PostingJob.created_at.desc())
            .limit(limit)
        )
        if status is not None:
            stmt = stmt.where(PostingJob.status == status)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update_fields(self, job_id: uuid.UUID, **fields: Any) -> PostingJob | None:
        row = await self.get_by_id(job_id)
        if row is None:
            return None
        allowed = {
            "status",
            "scheduled_at",
            "published_at",
            "attempt_count",
            "metadata_",
        }
        for key, value in fields.items():
            attr = "metadata_" if key == "metadata" else key
            if attr not in allowed:
                raise TypeError(f"Unsupported field: {key}")
            setattr(row, attr, value)
        await self._session.flush()
        return row


class PostingResultRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        job_id: uuid.UUID,
        tenant_id: uuid.UUID,
        channel_type: str,
        status: str,
        external_post_id: str | None = None,
        published_url: str | None = None,
        error_message: str | None = None,
        views: int = 0,
        likes: int = 0,
        shares: int = 0,
        comments: int = 0,
        clicks: int = 0,
        analytics_collected_at: datetime | None = None,
        metadata: dict | None = None,
        **extra: Any,
    ) -> PostingResult:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")
        if status not in POSTING_RESULT_STATUSES:
            raise ValueError(f"Invalid status: {status}")

        row = PostingResult(
            job_id=job_id,
            tenant_id=tenant_id,
            channel_type=channel_type,
            status=status,
            external_post_id=external_post_id,
            published_url=published_url,
            error_message=error_message,
            views=views,
            likes=likes,
            shares=shares,
            comments=comments,
            clicks=clicks,
            analytics_collected_at=analytics_collected_at,
            metadata_=metadata,
        )
        self._session.add(row)
        await self._session.flush()
        return row

    async def get_by_job(self, job_id: uuid.UUID) -> PostingResult | None:
        result = await self._session.execute(
            select(PostingResult).where(PostingResult.job_id == job_id)
        )
        return result.scalar_one_or_none()

    async def list_by_tenant(
        self,
        tenant_id: uuid.UUID,
        *,
        limit: int = 50,
    ) -> list[PostingResult]:
        result = await self._session.execute(
            select(PostingResult)
            .where(PostingResult.tenant_id == tenant_id)
            .order_by(PostingResult.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def update_fields(self, result_id: uuid.UUID, **fields: Any) -> PostingResult | None:
        result = await self._session.execute(
            select(PostingResult).where(PostingResult.id == result_id)
        )
        row = result.scalar_one_or_none()
        if row is None:
            return None
        allowed = {
            "status",
            "external_post_id",
            "published_url",
            "error_message",
            "views",
            "likes",
            "shares",
            "comments",
            "clicks",
            "analytics_collected_at",
            "metadata_",
        }
        for key, value in fields.items():
            attr = "metadata_" if key == "metadata" else key
            if attr not in allowed:
                raise TypeError(f"Unsupported field: {key}")
            setattr(row, attr, value)
        await self._session.flush()
        return row
