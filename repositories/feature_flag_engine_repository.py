# Feature Flag Engine v1 repositories.

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.feature_flag_engine import (
    AssignmentType,
    FeatureAssignment,
    FeatureFlag,
    FeatureFlagStatus,
    FeatureHistory,
    FeatureHistoryAction,
)


class FeatureFlagRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        flag_key: str,
        name: str,
        description: str | None = None,
        enabled: bool = False,
        rollout_percentage: int = 0,
        status: str = FeatureFlagStatus.ACTIVE.value,
        default_variant: str = "control",
        config: dict | None = None,
        owner_user_id: int | None = None,
        **extra: Any,
    ) -> FeatureFlag:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")
        if status not in {s.value for s in FeatureFlagStatus}:
            raise ValueError(f"Invalid status: {status}")
        if not 0 <= rollout_percentage <= 100:
            raise ValueError("rollout_percentage must be 0-100")

        flag = FeatureFlag(
            flag_key=flag_key,
            name=name,
            description=description,
            enabled=enabled,
            rollout_percentage=rollout_percentage,
            status=status,
            default_variant=default_variant,
            config=config,
            owner_user_id=owner_user_id,
        )
        self._session.add(flag)
        await self._session.flush()
        return flag

    async def get_by_id(self, flag_id: uuid.UUID) -> FeatureFlag | None:
        result = await self._session.execute(
            select(FeatureFlag).where(FeatureFlag.id == flag_id)
        )
        return result.scalar_one_or_none()

    async def get_by_key(self, flag_key: str) -> FeatureFlag | None:
        result = await self._session.execute(
            select(FeatureFlag).where(FeatureFlag.flag_key == flag_key)
        )
        return result.scalar_one_or_none()

    async def list_all(self, *, include_archived: bool = False) -> list[FeatureFlag]:
        query = select(FeatureFlag)
        if not include_archived:
            query = query.where(FeatureFlag.status != FeatureFlagStatus.ARCHIVED.value)
        result = await self._session.execute(query.order_by(FeatureFlag.flag_key.asc()))
        return list(result.scalars().all())

    async def update(
        self,
        flag: FeatureFlag,
        *,
        enabled: bool | None = None,
        rollout_percentage: int | None = None,
        status: str | None = None,
        default_variant: str | None = None,
        description: str | None = None,
        config: dict | None = None,
    ) -> FeatureFlag:
        if enabled is not None:
            flag.enabled = enabled
        if rollout_percentage is not None:
            if not 0 <= rollout_percentage <= 100:
                raise ValueError("rollout_percentage must be 0-100")
            flag.rollout_percentage = rollout_percentage
        if status is not None:
            flag.status = status
        if default_variant is not None:
            flag.default_variant = default_variant
        if description is not None:
            flag.description = description
        if config is not None:
            flag.config = config
        await self._session.flush()
        return flag


class FeatureAssignmentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert(
        self,
        *,
        flag_id: uuid.UUID,
        assignment_type: str,
        target_key: str,
        enabled: bool = True,
        rollout_percentage: int | None = None,
        variant: str | None = None,
        metadata: dict | None = None,
        **extra: Any,
    ) -> FeatureAssignment:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")
        if assignment_type not in {t.value for t in AssignmentType}:
            raise ValueError(f"Invalid assignment_type: {assignment_type}")

        result = await self._session.execute(
            select(FeatureAssignment).where(
                FeatureAssignment.flag_id == flag_id,
                FeatureAssignment.assignment_type == assignment_type,
                FeatureAssignment.target_key == target_key,
            )
        )
        assignment = result.scalar_one_or_none()
        if assignment is None:
            assignment = FeatureAssignment(
                flag_id=flag_id,
                assignment_type=assignment_type,
                target_key=target_key,
                enabled=enabled,
                rollout_percentage=rollout_percentage,
                variant=variant,
                metadata_=metadata,
            )
            self._session.add(assignment)
        else:
            assignment.enabled = enabled
            assignment.rollout_percentage = rollout_percentage
            assignment.variant = variant
            assignment.metadata_ = metadata
        await self._session.flush()
        return assignment

    async def list_for_flag(self, flag_id: uuid.UUID) -> list[FeatureAssignment]:
        result = await self._session.execute(
            select(FeatureAssignment)
            .where(FeatureAssignment.flag_id == flag_id)
            .order_by(FeatureAssignment.assignment_type.asc())
        )
        return list(result.scalars().all())

    async def delete(
        self,
        *,
        flag_id: uuid.UUID,
        assignment_type: str,
        target_key: str,
    ) -> bool:
        result = await self._session.execute(
            select(FeatureAssignment).where(
                FeatureAssignment.flag_id == flag_id,
                FeatureAssignment.assignment_type == assignment_type,
                FeatureAssignment.target_key == target_key,
            )
        )
        assignment = result.scalar_one_or_none()
        if assignment is None:
            return False
        await self._session.delete(assignment)
        await self._session.flush()
        return True


class FeatureHistoryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def record(
        self,
        *,
        flag_id: uuid.UUID,
        action: str,
        actor_user_id: int | None = None,
        old_value: dict | None = None,
        new_value: dict | None = None,
        **extra: Any,
    ) -> FeatureHistory:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")
        if action not in {a.value for a in FeatureHistoryAction}:
            raise ValueError(f"Invalid action: {action}")

        entry = FeatureHistory(
            flag_id=flag_id,
            action=action,
            actor_user_id=actor_user_id,
            old_value=old_value,
            new_value=new_value,
        )
        self._session.add(entry)
        await self._session.flush()
        return entry

    async def list_for_flag(
        self,
        flag_id: uuid.UUID,
        *,
        limit: int = 50,
    ) -> list[FeatureHistory]:
        result = await self._session.execute(
            select(FeatureHistory)
            .where(FeatureHistory.flag_id == flag_id)
            .order_by(FeatureHistory.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
