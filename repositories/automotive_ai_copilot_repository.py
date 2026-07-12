# Automotive AI Copilot v1 repositories.

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.automotive_ai_copilot import (
    AiDecision,
    AiFeedback,
    AiPrediction,
    AiRecommendation,
    DecisionStatus,
    FeedbackRating,
    PredictionType,
    RecommendationType,
)


class AiRecommendationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        recommendation_type: str,
        title: str,
        summary: str,
        confidence_score: Decimal,
        model_version: str,
        vehicle_id: uuid.UUID | None = None,
        entity_type: str | None = None,
        entity_id: str | None = None,
        recommended_value: Decimal | None = None,
        currency: str | None = None,
        input_context: dict | None = None,
        created_by: int | None = None,
        **extra: Any,
    ) -> AiRecommendation:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")
        if recommendation_type not in {t.value for t in RecommendationType}:
            raise ValueError(f"Invalid recommendation_type: {recommendation_type}")

        rec = AiRecommendation(
            recommendation_type=recommendation_type,
            title=title,
            summary=summary,
            confidence_score=confidence_score,
            model_version=model_version,
            vehicle_id=vehicle_id,
            entity_type=entity_type,
            entity_id=entity_id,
            recommended_value=recommended_value,
            currency=currency,
            input_context=input_context,
            created_by=created_by,
        )
        self._session.add(rec)
        await self._session.flush()
        return rec

    async def get_by_id(self, recommendation_id: uuid.UUID) -> AiRecommendation | None:
        result = await self._session.execute(
            select(AiRecommendation).where(AiRecommendation.id == recommendation_id)
        )
        return result.scalar_one_or_none()

    async def list_by_vehicle(
        self,
        vehicle_id: uuid.UUID,
        *,
        limit: int = 50,
    ) -> list[AiRecommendation]:
        result = await self._session.execute(
            select(AiRecommendation)
            .where(AiRecommendation.vehicle_id == vehicle_id)
            .order_by(AiRecommendation.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def list_by_type(
        self,
        recommendation_type: str,
        *,
        limit: int = 50,
    ) -> list[AiRecommendation]:
        result = await self._session.execute(
            select(AiRecommendation)
            .where(AiRecommendation.recommendation_type == recommendation_type)
            .order_by(AiRecommendation.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def list_history(
        self,
        *,
        model_version: str | None = None,
        limit: int = 100,
    ) -> list[AiRecommendation]:
        query = select(AiRecommendation)
        if model_version:
            query = query.where(AiRecommendation.model_version == model_version)
        result = await self._session.execute(
            query.order_by(AiRecommendation.created_at.desc()).limit(limit)
        )
        return list(result.scalars().all())


class AiPredictionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        prediction_type: str,
        predicted_value: Decimal,
        unit: str,
        confidence_score: Decimal,
        model_version: str,
        vehicle_id: uuid.UUID | None = None,
        entity_type: str | None = None,
        entity_id: str | None = None,
        valid_until: datetime | None = None,
        metadata: dict | None = None,
        created_by: int | None = None,
        **extra: Any,
    ) -> AiPrediction:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")
        if prediction_type not in {t.value for t in PredictionType}:
            raise ValueError(f"Invalid prediction_type: {prediction_type}")

        pred = AiPrediction(
            prediction_type=prediction_type,
            predicted_value=predicted_value,
            unit=unit,
            confidence_score=confidence_score,
            model_version=model_version,
            vehicle_id=vehicle_id,
            entity_type=entity_type,
            entity_id=entity_id,
            valid_until=valid_until,
            metadata_=metadata,
            created_by=created_by,
        )
        self._session.add(pred)
        await self._session.flush()
        return pred

    async def get_by_id(self, prediction_id: uuid.UUID) -> AiPrediction | None:
        result = await self._session.execute(
            select(AiPrediction).where(AiPrediction.id == prediction_id)
        )
        return result.scalar_one_or_none()

    async def list_by_vehicle(
        self,
        vehicle_id: uuid.UUID,
        *,
        limit: int = 50,
    ) -> list[AiPrediction]:
        result = await self._session.execute(
            select(AiPrediction)
            .where(AiPrediction.vehicle_id == vehicle_id)
            .order_by(AiPrediction.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def list_by_type(
        self,
        prediction_type: str,
        *,
        limit: int = 50,
    ) -> list[AiPrediction]:
        result = await self._session.execute(
            select(AiPrediction)
            .where(AiPrediction.prediction_type == prediction_type)
            .order_by(AiPrediction.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())


class AiDecisionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        decision_type: str,
        model_version: str,
        recommendation_id: uuid.UUID | None = None,
        prediction_id: uuid.UUID | None = None,
        vehicle_id: uuid.UUID | None = None,
        status: str = DecisionStatus.PENDING.value,
        **extra: Any,
    ) -> AiDecision:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")
        if status not in {s.value for s in DecisionStatus}:
            raise ValueError(f"Invalid status: {status}")

        decision = AiDecision(
            decision_type=decision_type,
            model_version=model_version,
            recommendation_id=recommendation_id,
            prediction_id=prediction_id,
            vehicle_id=vehicle_id,
            status=status,
        )
        self._session.add(decision)
        await self._session.flush()
        return decision

    async def update_status(
        self,
        decision_id: uuid.UUID,
        status: str,
        *,
        decided_by: int | None = None,
        applied_value: Decimal | None = None,
        notes: str | None = None,
    ) -> AiDecision | None:
        result = await self._session.execute(
            select(AiDecision).where(AiDecision.id == decision_id)
        )
        decision = result.scalar_one_or_none()
        if decision is None:
            return None
        if status not in {s.value for s in DecisionStatus}:
            raise ValueError(f"Invalid status: {status}")

        decision.status = status
        decision.decided_by = decided_by
        decision.decided_at = datetime.now(timezone.utc)
        if applied_value is not None:
            decision.applied_value = applied_value
        if notes is not None:
            decision.notes = notes
        decision.updated_at = datetime.now(timezone.utc)
        await self._session.flush()
        return decision

    async def list_by_vehicle(
        self,
        vehicle_id: uuid.UUID,
        *,
        limit: int = 50,
    ) -> list[AiDecision]:
        result = await self._session.execute(
            select(AiDecision)
            .where(AiDecision.vehicle_id == vehicle_id)
            .order_by(AiDecision.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())


class AiFeedbackRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        rating: str,
        model_version: str,
        recommendation_id: uuid.UUID | None = None,
        decision_id: uuid.UUID | None = None,
        comment: str | None = None,
        submitted_by: int | None = None,
    ) -> AiFeedback:
        if rating not in {r.value for r in FeedbackRating}:
            raise ValueError(f"Invalid rating: {rating}")

        feedback = AiFeedback(
            rating=rating,
            model_version=model_version,
            recommendation_id=recommendation_id,
            decision_id=decision_id,
            comment=comment,
            submitted_by=submitted_by,
        )
        self._session.add(feedback)
        await self._session.flush()
        return feedback

    async def list_by_model(
        self,
        model_version: str,
        *,
        limit: int = 100,
    ) -> list[AiFeedback]:
        result = await self._session.execute(
            select(AiFeedback)
            .where(AiFeedback.model_version == model_version)
            .order_by(AiFeedback.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
