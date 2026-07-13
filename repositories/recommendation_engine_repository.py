# Recommendation Engine v1 repositories.

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.recommendation_engine import (
    RECOMMENDATION_FEEDBACK_TYPES,
    RECOMMENDATION_TYPES,
    RecommendationFeedback,
    RecommendationHistory,
    RecommendationProfile,
)


class RecommendationProfileRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        tenant_id: uuid.UUID,
        company_id: uuid.UUID,
        budget_min: Decimal | None = None,
        budget_max: Decimal | None = None,
        vehicle_type: str | None = None,
        fuel_type: str | None = None,
        transmission: str | None = None,
        location: str | None = None,
        previous_interactions: list | None = None,
        preferences: dict | None = None,
        sales_lead_id: uuid.UUID | None = None,
        user_id: int | None = None,
        label: str | None = None,
        currency: str = "USD",
        is_active: bool = True,
        created_by: int | None = None,
        metadata: dict | None = None,
        **extra: Any,
    ) -> RecommendationProfile:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")

        row = RecommendationProfile(
            tenant_id=tenant_id,
            company_id=company_id,
            budget_min=budget_min,
            budget_max=budget_max,
            vehicle_type=vehicle_type,
            fuel_type=fuel_type,
            transmission=transmission,
            location=location,
            previous_interactions=previous_interactions,
            preferences=preferences,
            sales_lead_id=sales_lead_id,
            user_id=user_id,
            label=label,
            currency=currency,
            is_active=is_active,
            created_by=created_by,
            metadata_=metadata,
        )
        self._session.add(row)
        await self._session.flush()
        return row

    async def get_by_id(self, profile_id: uuid.UUID) -> RecommendationProfile | None:
        result = await self._session.execute(
            select(RecommendationProfile).where(RecommendationProfile.id == profile_id)
        )
        return result.scalar_one_or_none()

    async def list_by_tenant(
        self,
        tenant_id: uuid.UUID,
        *,
        active_only: bool = True,
        limit: int = 100,
    ) -> list[RecommendationProfile]:
        stmt = (
            select(RecommendationProfile)
            .where(RecommendationProfile.tenant_id == tenant_id)
            .order_by(RecommendationProfile.created_at.desc())
            .limit(limit)
        )
        if active_only:
            stmt = stmt.where(RecommendationProfile.is_active.is_(True))
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update_fields(
        self,
        profile_id: uuid.UUID,
        **fields: Any,
    ) -> RecommendationProfile | None:
        row = await self.get_by_id(profile_id)
        if row is None:
            return None
        allowed = {
            "budget_min",
            "budget_max",
            "vehicle_type",
            "fuel_type",
            "transmission",
            "location",
            "previous_interactions",
            "preferences",
            "label",
            "currency",
            "is_active",
            "metadata_",
        }
        for key, value in fields.items():
            attr = "metadata_" if key == "metadata" else key
            if attr not in allowed:
                raise TypeError(f"Unsupported field: {key}")
            setattr(row, attr, value)
        await self._session.flush()
        return row


class RecommendationHistoryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        profile_id: uuid.UUID,
        tenant_id: uuid.UUID,
        company_id: uuid.UUID,
        recommendation_type: str,
        input_context: dict,
        result: dict,
        confidence_score: Decimal,
        model_version: str,
        entity_type: str | None = None,
        entity_id: uuid.UUID | None = None,
        summary: str | None = None,
        created_by: int | None = None,
        **extra: Any,
    ) -> RecommendationHistory:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")
        if recommendation_type not in RECOMMENDATION_TYPES:
            raise ValueError(f"Invalid recommendation_type: {recommendation_type}")

        row = RecommendationHistory(
            profile_id=profile_id,
            tenant_id=tenant_id,
            company_id=company_id,
            recommendation_type=recommendation_type,
            input_context=input_context,
            result=result,
            confidence_score=confidence_score,
            model_version=model_version,
            entity_type=entity_type,
            entity_id=entity_id,
            summary=summary,
            created_by=created_by,
        )
        self._session.add(row)
        await self._session.flush()
        return row

    async def get_by_id(self, history_id: uuid.UUID) -> RecommendationHistory | None:
        result = await self._session.execute(
            select(RecommendationHistory).where(RecommendationHistory.id == history_id)
        )
        return result.scalar_one_or_none()

    async def list_by_profile(
        self,
        profile_id: uuid.UUID,
        *,
        recommendation_type: str | None = None,
        limit: int = 50,
    ) -> list[RecommendationHistory]:
        stmt = (
            select(RecommendationHistory)
            .where(RecommendationHistory.profile_id == profile_id)
            .order_by(RecommendationHistory.created_at.desc())
            .limit(limit)
        )
        if recommendation_type is not None:
            stmt = stmt.where(RecommendationHistory.recommendation_type == recommendation_type)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())


class RecommendationFeedbackRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        history_id: uuid.UUID,
        profile_id: uuid.UUID,
        tenant_id: uuid.UUID,
        feedback_type: str,
        rating: int | None = None,
        comment: str | None = None,
        created_by: int | None = None,
        **extra: Any,
    ) -> RecommendationFeedback:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")
        if feedback_type not in RECOMMENDATION_FEEDBACK_TYPES:
            raise ValueError(f"Invalid feedback_type: {feedback_type}")
        if rating is not None and not (1 <= rating <= 5):
            raise ValueError("rating must be between 1 and 5")

        row = RecommendationFeedback(
            history_id=history_id,
            profile_id=profile_id,
            tenant_id=tenant_id,
            feedback_type=feedback_type,
            rating=rating,
            comment=comment,
            created_by=created_by,
        )
        self._session.add(row)
        await self._session.flush()
        return row

    async def list_by_profile(
        self,
        profile_id: uuid.UUID,
        *,
        limit: int = 50,
    ) -> list[RecommendationFeedback]:
        result = await self._session.execute(
            select(RecommendationFeedback)
            .where(RecommendationFeedback.profile_id == profile_id)
            .order_by(RecommendationFeedback.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
