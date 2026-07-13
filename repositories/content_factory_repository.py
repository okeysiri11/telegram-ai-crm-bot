# Content Factory Engine v1 repository.

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.content_factory_engine import CONTENT_TYPES, ContentItem


class ContentFactoryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        content_type: str,
        body: str,
        car_id: uuid.UUID | None = None,
        title: str | None = None,
        version: int = 1,
        metadata: dict | None = None,
        created_by: int | None = None,
        **extra: Any,
    ) -> ContentItem:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")
        if content_type not in CONTENT_TYPES:
            raise ValueError(f"Invalid content_type: {content_type}")

        if car_id is not None:
            result = await self._session.execute(
                select(ContentItem)
                .where(
                    ContentItem.car_id == car_id,
                    ContentItem.content_type == content_type,
                )
                .order_by(ContentItem.version.desc())
                .limit(1)
            )
            latest = result.scalar_one_or_none()
            if latest is not None:
                version = latest.version + 1

        item = ContentItem(
            car_id=car_id,
            content_type=content_type,
            title=title,
            body=body,
            version=version,
            metadata_=metadata,
            created_by=created_by,
        )
        self._session.add(item)
        await self._session.flush()
        return item

    async def get_latest(
        self,
        *,
        car_id: uuid.UUID,
        content_type: str,
    ) -> ContentItem | None:
        result = await self._session.execute(
            select(ContentItem)
            .where(
                ContentItem.car_id == car_id,
                ContentItem.content_type == content_type,
            )
            .order_by(ContentItem.version.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def list_for_car(
        self,
        car_id: uuid.UUID,
        *,
        limit: int = 20,
    ) -> list[ContentItem]:
        result = await self._session.execute(
            select(ContentItem)
            .where(ContentItem.car_id == car_id)
            .order_by(ContentItem.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    @staticmethod
    def snapshot(item: ContentItem) -> dict[str, Any]:
        return {
            "id": str(item.id),
            "car_id": str(item.car_id) if item.car_id else None,
            "content_type": item.content_type,
            "title": item.title,
            "body": item.body,
            "version": item.version,
            "metadata": item.metadata_ or {},
            "created_by": item.created_by,
            "created_at": item.created_at.isoformat(),
        }
