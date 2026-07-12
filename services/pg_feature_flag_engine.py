# Feature Flag Engine v1 — gradual rollout, targeting, and A/B testing.

from __future__ import annotations

import hashlib
import uuid
from typing import Any

from config import OWNER_ID
from database.models.audit_log import AuditAction
from database.models.feature_flag_engine import (
    AssignmentType,
    FeatureFlagStatus,
    FeatureHistoryAction,
)
from database.session import get_session
from repositories.audit_repository import AuditRepository
from repositories.feature_flag_engine_repository import (
    FeatureAssignmentRepository,
    FeatureFlagRepository,
    FeatureHistoryRepository,
)
from repositories.user_role_repository import UserRoleRepository

FEATURE_FLAG_ROLES = frozenset({"OWNER", "ADMIN"})

DEFAULT_FLAGS: tuple[dict[str, Any], ...] = (
    {
        "flag_key": "ai_copilot.enabled",
        "name": "AI Copilot",
        "description": "Automotive AI copilot assistant",
        "enabled": True,
        "rollout_percentage": 100,
    },
    {
        "flag_key": "marketplace.auto_sync",
        "name": "Marketplace Auto Sync",
        "description": "Automatic marketplace inventory sync",
        "enabled": True,
        "rollout_percentage": 50,
    },
    {
        "flag_key": "analytics.advanced_dashboard",
        "name": "Advanced Analytics Dashboard",
        "description": "Enhanced analytics and KPI views",
        "enabled": False,
        "rollout_percentage": 0,
    },
)

_defaults_seeded = False


class FeatureFlagEngineError(Exception):
    pass


class FeatureFlagEngineV1:
    @staticmethod
    async def user_can_access(user_id: int) -> bool:
        if user_id == OWNER_ID:
            return True
        async with get_session() as session:
            roles = await UserRoleRepository(session).get_user_roles(user_id)
            return any(role.code in FEATURE_FLAG_ROLES for role in roles)

    @staticmethod
    def _flag_snapshot(flag) -> dict[str, Any]:
        return {
            "id": str(flag.id),
            "flag_key": flag.flag_key,
            "name": flag.name,
            "description": flag.description,
            "enabled": flag.enabled,
            "rollout_percentage": flag.rollout_percentage,
            "status": flag.status,
            "default_variant": flag.default_variant,
            "config": flag.config or {},
            "created_at": flag.created_at.isoformat(),
            "updated_at": flag.updated_at.isoformat(),
        }

    @staticmethod
    def _assignment_snapshot(assignment) -> dict[str, Any]:
        return {
            "id": str(assignment.id),
            "flag_id": str(assignment.flag_id),
            "assignment_type": assignment.assignment_type,
            "target_key": assignment.target_key,
            "enabled": assignment.enabled,
            "rollout_percentage": assignment.rollout_percentage,
            "variant": assignment.variant,
        }

    @staticmethod
    def _stable_bucket(flag_key: str, subject: str) -> int:
        digest = hashlib.sha256(f"{flag_key}:{subject}".encode()).hexdigest()
        return int(digest[:8], 16) % 100

    @staticmethod
    def _in_rollout(flag_key: str, subject: str, percentage: int) -> bool:
        if percentage >= 100:
            return True
        if percentage <= 0:
            return False
        return FeatureFlagEngineV1._stable_bucket(flag_key, subject) < percentage

    @staticmethod
    async def ensure_default_flags() -> list[dict[str, Any]]:
        global _defaults_seeded
        created: list[dict[str, Any]] = []
        async with get_session() as session:
            repo = FeatureFlagRepository(session)
            hist_repo = FeatureHistoryRepository(session)
            for spec in DEFAULT_FLAGS:
                existing = await repo.get_by_key(spec["flag_key"])
                if existing is not None:
                    continue
                flag = await repo.create(owner_user_id=OWNER_ID, **spec)
                await hist_repo.record(
                    flag_id=flag.id,
                    action=FeatureHistoryAction.CREATED.value,
                    actor_user_id=OWNER_ID,
                    new_value=FeatureFlagEngineV1._flag_snapshot(flag),
                )
                created.append(FeatureFlagEngineV1._flag_snapshot(flag))
            await session.commit()
        if created:
            _defaults_seeded = True
        return created

    @staticmethod
    async def create_flag(
        *,
        actor_id: int,
        flag_key: str,
        name: str,
        description: str | None = None,
        enabled: bool = False,
        rollout_percentage: int = 0,
        default_variant: str = "control",
        config: dict | None = None,
    ) -> dict[str, Any]:
        if not await FeatureFlagEngineV1.user_can_access(actor_id):
            raise FeatureFlagEngineError("Access denied")

        async with get_session() as session:
            repo = FeatureFlagRepository(session)
            if await repo.get_by_key(flag_key) is not None:
                raise FeatureFlagEngineError(f"Flag already exists: {flag_key}")
            flag = await repo.create(
                flag_key=flag_key,
                name=name,
                description=description,
                enabled=enabled,
                rollout_percentage=rollout_percentage,
                default_variant=default_variant,
                config=config,
                owner_user_id=actor_id,
            )
            await FeatureHistoryRepository(session).record(
                flag_id=flag.id,
                action=FeatureHistoryAction.CREATED.value,
                actor_user_id=actor_id,
                new_value=FeatureFlagEngineV1._flag_snapshot(flag),
            )
            await AuditRepository(session).create_log(
                user_id=actor_id,
                entity_type="feature_flag",
                entity_id=str(flag.id),
                action=AuditAction.CREATE.value,
                new_value={"flag_key": flag_key},
            )
            return FeatureFlagEngineV1._flag_snapshot(flag)

    @staticmethod
    async def update_flag(
        *,
        actor_id: int,
        flag_key: str,
        enabled: bool | None = None,
        rollout_percentage: int | None = None,
        status: str | None = None,
        default_variant: str | None = None,
        description: str | None = None,
        config: dict | None = None,
    ) -> dict[str, Any]:
        if not await FeatureFlagEngineV1.user_can_access(actor_id):
            raise FeatureFlagEngineError("Access denied")

        async with get_session() as session:
            repo = FeatureFlagRepository(session)
            flag = await repo.get_by_key(flag_key)
            if flag is None:
                raise FeatureFlagEngineError(f"Flag not found: {flag_key}")

            old_snapshot = FeatureFlagEngineV1._flag_snapshot(flag)
            flag = await repo.update(
                flag,
                enabled=enabled,
                rollout_percentage=rollout_percentage,
                status=status,
                default_variant=default_variant,
                description=description,
                config=config,
            )
            await session.refresh(flag)
            new_snapshot = FeatureFlagEngineV1._flag_snapshot(flag)

            action = FeatureHistoryAction.UPDATED.value
            if enabled is True and not old_snapshot["enabled"]:
                action = FeatureHistoryAction.ENABLED.value
            elif enabled is False and old_snapshot["enabled"]:
                action = FeatureHistoryAction.DISABLED.value
            elif rollout_percentage is not None and rollout_percentage != old_snapshot["rollout_percentage"]:
                action = FeatureHistoryAction.ROLLOUT_CHANGED.value
            elif default_variant is not None and default_variant != old_snapshot["default_variant"]:
                action = FeatureHistoryAction.VARIANT_CHANGED.value

            await FeatureHistoryRepository(session).record(
                flag_id=flag.id,
                action=action,
                actor_user_id=actor_id,
                old_value=old_snapshot,
                new_value=new_snapshot,
            )
            return new_snapshot

    @staticmethod
    async def assign_flag(
        *,
        actor_id: int,
        flag_key: str,
        assignment_type: str,
        target_key: str,
        enabled: bool = True,
        rollout_percentage: int | None = None,
        variant: str | None = None,
        metadata: dict | None = None,
    ) -> dict[str, Any]:
        if not await FeatureFlagEngineV1.user_can_access(actor_id):
            raise FeatureFlagEngineError("Access denied")

        async with get_session() as session:
            flag_repo = FeatureFlagRepository(session)
            assign_repo = FeatureAssignmentRepository(session)
            flag = await flag_repo.get_by_key(flag_key)
            if flag is None:
                raise FeatureFlagEngineError(f"Flag not found: {flag_key}")

            assignment = await assign_repo.upsert(
                flag_id=flag.id,
                assignment_type=assignment_type,
                target_key=target_key,
                enabled=enabled,
                rollout_percentage=rollout_percentage,
                variant=variant,
                metadata=metadata,
            )
            await FeatureHistoryRepository(session).record(
                flag_id=flag.id,
                action=FeatureHistoryAction.ASSIGNED.value,
                actor_user_id=actor_id,
                new_value=FeatureFlagEngineV1._assignment_snapshot(assignment),
            )
            return FeatureFlagEngineV1._assignment_snapshot(assignment)

    @staticmethod
    async def unassign_flag(
        *,
        actor_id: int,
        flag_key: str,
        assignment_type: str,
        target_key: str,
    ) -> bool:
        if not await FeatureFlagEngineV1.user_can_access(actor_id):
            raise FeatureFlagEngineError("Access denied")

        async with get_session() as session:
            flag = await FeatureFlagRepository(session).get_by_key(flag_key)
            if flag is None:
                raise FeatureFlagEngineError(f"Flag not found: {flag_key}")
            removed = await FeatureAssignmentRepository(session).delete(
                flag_id=flag.id,
                assignment_type=assignment_type,
                target_key=target_key,
            )
            if removed:
                await FeatureHistoryRepository(session).record(
                    flag_id=flag.id,
                    action=FeatureHistoryAction.UNASSIGNED.value,
                    actor_user_id=actor_id,
                    old_value={
                        "assignment_type": assignment_type,
                        "target_key": target_key,
                    },
                )
            return removed

    @staticmethod
    async def list_flags(*, actor_id: int) -> list[dict[str, Any]]:
        if not await FeatureFlagEngineV1.user_can_access(actor_id):
            raise FeatureFlagEngineError("Access denied")
        async with get_session() as session:
            flags = await FeatureFlagRepository(session).list_all()
            return [FeatureFlagEngineV1._flag_snapshot(flag) for flag in flags]

    @staticmethod
    async def get_history(
        *,
        actor_id: int,
        flag_key: str,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        if not await FeatureFlagEngineV1.user_can_access(actor_id):
            raise FeatureFlagEngineError("Access denied")
        async with get_session() as session:
            flag = await FeatureFlagRepository(session).get_by_key(flag_key)
            if flag is None:
                raise FeatureFlagEngineError(f"Flag not found: {flag_key}")
            entries = await FeatureHistoryRepository(session).list_for_flag(
                flag.id,
                limit=limit,
            )
            return [
                {
                    "id": str(entry.id),
                    "action": entry.action,
                    "actor_user_id": entry.actor_user_id,
                    "old_value": entry.old_value,
                    "new_value": entry.new_value,
                    "created_at": entry.created_at.isoformat(),
                }
                for entry in entries
            ]

    @staticmethod
    async def resolve_variant(
        *,
        flag_key: str,
        user_id: int | None = None,
        company_id: uuid.UUID | None = None,
        roles: list[str] | None = None,
    ) -> str:
        async with get_session() as session:
            flag = await FeatureFlagRepository(session).get_by_key(flag_key)
            if flag is None or flag.status != FeatureFlagStatus.ACTIVE.value:
                return "control"

            assignments = await FeatureAssignmentRepository(session).list_for_flag(flag.id)
            subject = str(user_id or company_id or "anonymous")

            for assignment in assignments:
                if assignment.assignment_type != AssignmentType.AB_VARIANT.value:
                    continue
                if not assignment.enabled or not assignment.variant:
                    continue
                pct = assignment.rollout_percentage if assignment.rollout_percentage is not None else 50
                variant_subject = f"{assignment.target_key}:{subject}"
                if FeatureFlagEngineV1._in_rollout(flag_key, variant_subject, pct):
                    return assignment.variant

            if user_id is not None:
                for assignment in assignments:
                    if (
                        assignment.assignment_type == AssignmentType.USER.value
                        and assignment.target_key == str(user_id)
                        and assignment.enabled
                        and assignment.variant
                    ):
                        return assignment.variant

            return flag.default_variant

    @staticmethod
    async def is_enabled(
        *,
        flag_key: str,
        user_id: int | None = None,
        company_id: uuid.UUID | None = None,
        roles: list[str] | None = None,
    ) -> bool:
        async with get_session() as session:
            flag = await FeatureFlagRepository(session).get_by_key(flag_key)
            if flag is None:
                return False
            if flag.status == FeatureFlagStatus.ARCHIVED.value:
                return False
            if flag.status == FeatureFlagStatus.PAUSED.value:
                return False

            assignments = await FeatureAssignmentRepository(session).list_for_flag(flag.id)

            if user_id is not None:
                for assignment in assignments:
                    if (
                        assignment.assignment_type == AssignmentType.USER.value
                        and assignment.target_key == str(user_id)
                    ):
                        return assignment.enabled

            if roles:
                for assignment in assignments:
                    if (
                        assignment.assignment_type == AssignmentType.ROLE.value
                        and assignment.target_key in roles
                    ):
                        return assignment.enabled

            if company_id is not None:
                for assignment in assignments:
                    if (
                        assignment.assignment_type == AssignmentType.COMPANY.value
                        and assignment.target_key == str(company_id)
                    ):
                        if assignment.rollout_percentage is not None:
                            return assignment.enabled and FeatureFlagEngineV1._in_rollout(
                                flag_key,
                                str(company_id),
                                assignment.rollout_percentage,
                            )
                        return assignment.enabled

            if not flag.enabled:
                return False

            subject = str(user_id or company_id or "global")
            return FeatureFlagEngineV1._in_rollout(
                flag_key,
                subject,
                flag.rollout_percentage,
            )
