# Dealer Portal Engine v1 repositories.

from __future__ import annotations

import uuid
from datetime import date
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.dealer_portal_engine import (
    DealerPortalRecommendation,
    DealerPortalSnapshot,
    RecommendationPriority,
    RecommendationStatus,
)


class DealerPortalSnapshotRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert(
        self,
        *,
        tenant_id: uuid.UUID,
        company_id: uuid.UUID,
        snapshot_date: date,
        widgets: dict,
        sections: dict,
    ) -> DealerPortalSnapshot:
        result = await self._session.execute(
            select(DealerPortalSnapshot).where(
                DealerPortalSnapshot.tenant_id == tenant_id,
                DealerPortalSnapshot.snapshot_date == snapshot_date,
            )
        )
        existing = result.scalar_one_or_none()
        if existing is not None:
            existing.widgets = widgets
            existing.sections = sections
            await self._session.flush()
            return existing

        row = DealerPortalSnapshot(
            tenant_id=tenant_id,
            company_id=company_id,
            snapshot_date=snapshot_date,
            widgets=widgets,
            sections=sections,
        )
        self._session.add(row)
        await self._session.flush()
        return row

    async def get_latest(self, tenant_id: uuid.UUID) -> DealerPortalSnapshot | None:
        result = await self._session.execute(
            select(DealerPortalSnapshot)
            .where(DealerPortalSnapshot.tenant_id == tenant_id)
            .order_by(DealerPortalSnapshot.snapshot_date.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()


class DealerPortalRecommendationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        tenant_id: uuid.UUID,
        company_id: uuid.UUID,
        category: str,
        title: str,
        body: str,
        priority: str = RecommendationPriority.MEDIUM.value,
        metadata: dict | None = None,
    ) -> DealerPortalRecommendation:
        row = DealerPortalRecommendation(
            tenant_id=tenant_id,
            company_id=company_id,
            category=category,
            title=title,
            body=body,
            priority=priority,
            metadata_=metadata,
        )
        self._session.add(row)
        await self._session.flush()
        return row

    async def list_active(
        self,
        tenant_id: uuid.UUID,
        *,
        limit: int = 20,
    ) -> list[DealerPortalRecommendation]:
        result = await self._session.execute(
            select(DealerPortalRecommendation)
            .where(
                DealerPortalRecommendation.tenant_id == tenant_id,
                DealerPortalRecommendation.status == RecommendationStatus.ACTIVE.value,
            )
            .order_by(DealerPortalRecommendation.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def dismiss(self, recommendation_id: uuid.UUID) -> DealerPortalRecommendation | None:
        result = await self._session.execute(
            select(DealerPortalRecommendation).where(
                DealerPortalRecommendation.id == recommendation_id
            )
        )
        row = result.scalar_one_or_none()
        if row is None:
            return None
        row.status = RecommendationStatus.DISMISSED.value
        await self._session.flush()
        return row

    async def replace_active(
        self,
        tenant_id: uuid.UUID,
        recommendations: list[dict[str, Any]],
        *,
        company_id: uuid.UUID,
    ) -> list[DealerPortalRecommendation]:
        result = await self._session.execute(
            select(DealerPortalRecommendation).where(
                DealerPortalRecommendation.tenant_id == tenant_id,
                DealerPortalRecommendation.status == RecommendationStatus.ACTIVE.value,
            )
        )
        for row in result.scalars().all():
            row.status = RecommendationStatus.DISMISSED.value

        created: list[DealerPortalRecommendation] = []
        for item in recommendations:
            created.append(
                await self.create(
                    tenant_id=tenant_id,
                    company_id=company_id,
                    category=item["category"],
                    title=item["title"],
                    body=item["body"],
                    priority=item.get("priority", RecommendationPriority.MEDIUM.value),
                    metadata=item.get("metadata"),
                )
            )
        return created
