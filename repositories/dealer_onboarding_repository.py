# Dealer Onboarding Flow v1 repositories.

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.dealer_onboarding_engine import (
    ONBOARDING_SESSION_STATUSES,
    ONBOARDING_STEP_NAMES,
    ONBOARDING_STEP_STATUSES,
    OnboardingSession,
    OnboardingSessionStatus,
    OnboardingStep,
    OnboardingStepStatus,
)


class OnboardingSessionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        telegram_user_id: int,
        current_step: str,
        started_at: datetime,
        expires_at: datetime,
        metadata: dict | None = None,
    ) -> OnboardingSession:
        row = OnboardingSession(
            telegram_user_id=telegram_user_id,
            status=OnboardingSessionStatus.ACTIVE.value,
            current_step=current_step,
            started_at=started_at,
            expires_at=expires_at,
            metadata_=metadata,
        )
        self._session.add(row)
        await self._session.flush()
        return row

    async def get_by_id(self, session_id: uuid.UUID) -> OnboardingSession | None:
        result = await self._session.execute(
            select(OnboardingSession).where(OnboardingSession.id == session_id)
        )
        return result.scalar_one_or_none()

    async def get_active_for_user(self, telegram_user_id: int) -> OnboardingSession | None:
        result = await self._session.execute(
            select(OnboardingSession)
            .where(
                OnboardingSession.telegram_user_id == telegram_user_id,
                OnboardingSession.status == OnboardingSessionStatus.ACTIVE.value,
            )
            .order_by(OnboardingSession.started_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_by_payment_id(self, payment_id: uuid.UUID) -> OnboardingSession | None:
        result = await self._session.execute(
            select(OnboardingSession).where(OnboardingSession.payment_id == payment_id)
        )
        return result.scalar_one_or_none()

    async def update_fields(
        self,
        session_id: uuid.UUID,
        **fields: Any,
    ) -> OnboardingSession | None:
        if "metadata" in fields:
            fields["metadata_"] = fields.pop("metadata")
        if "status" in fields and fields["status"] not in ONBOARDING_SESSION_STATUSES:
            raise ValueError(f"Invalid status: {fields['status']}")
        if "current_step" in fields and fields["current_step"] not in ONBOARDING_STEP_NAMES:
            raise ValueError(f"Invalid step: {fields['current_step']}")

        await self._session.execute(
            update(OnboardingSession)
            .where(OnboardingSession.id == session_id)
            .values(**fields)
        )
        await self._session.flush()
        return await self.get_by_id(session_id)

    async def expire_before(self, cutoff: datetime) -> int:
        result = await self._session.execute(
            update(OnboardingSession)
            .where(
                OnboardingSession.status == OnboardingSessionStatus.ACTIVE.value,
                OnboardingSession.expires_at < cutoff,
            )
            .values(status=OnboardingSessionStatus.EXPIRED.value)
        )
        return int(result.rowcount or 0)

    async def count_by_status(self) -> dict[str, int]:
        result = await self._session.execute(
            select(OnboardingSession.status, func.count())
            .group_by(OnboardingSession.status)
        )
        return {status: count for status, count in result.all()}

    async def count_completed_with_duration(self) -> list[float]:
        result = await self._session.execute(
            select(OnboardingSession.started_at, OnboardingSession.completed_at).where(
                OnboardingSession.status == OnboardingSessionStatus.COMPLETED.value,
                OnboardingSession.completed_at.is_not(None),
            )
        )
        durations: list[float] = []
        for started_at, completed_at in result.all():
            if started_at and completed_at:
                durations.append((completed_at - started_at).total_seconds() / 3600)
        return durations


class OnboardingStepRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        session_id: uuid.UUID,
        step_name: str,
        status: str = OnboardingStepStatus.COMPLETED.value,
        payload: dict | None = None,
    ) -> OnboardingStep:
        if step_name not in ONBOARDING_STEP_NAMES:
            raise ValueError(f"Invalid step_name: {step_name}")
        if status not in ONBOARDING_STEP_STATUSES:
            raise ValueError(f"Invalid status: {status}")

        row = OnboardingStep(
            session_id=session_id,
            step_name=step_name,
            status=status,
            payload=payload,
        )
        self._session.add(row)
        await self._session.flush()
        return row

    async def count_by_step_name(self) -> dict[str, int]:
        result = await self._session.execute(
            select(OnboardingStep.step_name, func.count())
            .where(OnboardingStep.status == OnboardingStepStatus.COMPLETED.value)
            .group_by(OnboardingStep.step_name)
        )
        return {step_name: count for step_name, count in result.all()}

    async def list_for_session(self, session_id: uuid.UUID) -> list[OnboardingStep]:
        result = await self._session.execute(
            select(OnboardingStep)
            .where(OnboardingStep.session_id == session_id)
            .order_by(OnboardingStep.created_at.asc())
        )
        return list(result.scalars().all())
