# Dealer Onboarding Flow v1 — session lifecycle, resume, timeout, analytics.

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from database import assign_role
from database.models.dealer_onboarding_engine import (
    OnboardingSessionStatus,
    OnboardingStepName,
    OnboardingStepStatus,
)
from database.session import get_session
from repositories.dealer_onboarding_repository import (
    OnboardingSessionRepository,
    OnboardingStepRepository,
)
from services.rbac_v2 import RbacV2Engine

ONBOARDING_TIMEOUT_HOURS = 72

STEP_LABELS: dict[str, str] = {
    OnboardingStepName.STARTED.value: "Старт",
    OnboardingStepName.AUTOMOTIVE_SELECTED.value: "Выбор Automotive",
    OnboardingStepName.TARIFF_SELECTED.value: "Выбор тарифа",
    OnboardingStepName.PRICING_MODEL_SELECTED.value: "Модель оплаты",
    OnboardingStepName.PAYMENT_CREATED.value: "Оплата",
    OnboardingStepName.RECEIPT_UPLOADED.value: "Загрузка квитанции",
    OnboardingStepName.OWNER_APPROVED.value: "Подтверждение OWNER",
    OnboardingStepName.TENANT_CREATED.value: "Создание tenant",
    OnboardingStepName.ROLE_ASSIGNED.value: "Назначение роли",
    OnboardingStepName.COMPLETED.value: "Активация меню Automotive",
}


class DealerOnboardingEngineError(Exception):
    pass


class DealerOnboardingEngineV1:
    @staticmethod
    def _now() -> datetime:
        return datetime.now(timezone.utc)

    @staticmethod
    def _session_snapshot(row) -> dict[str, Any]:
        return {
            "id": str(row.id),
            "telegram_user_id": row.telegram_user_id,
            "status": row.status,
            "current_step": row.current_step,
            "plan_code": row.plan_code,
            "pricing_model": row.pricing_model,
            "payment_method": row.payment_method,
            "payment_id": str(row.payment_id) if row.payment_id else None,
            "tenant_id": str(row.tenant_id) if row.tenant_id else None,
            "started_at": row.started_at.isoformat(),
            "expires_at": row.expires_at.isoformat(),
            "completed_at": row.completed_at.isoformat() if row.completed_at else None,
            "metadata": row.metadata_ or {},
        }

    @staticmethod
    async def expire_stale_sessions() -> int:
        now = DealerOnboardingEngineV1._now()
        async with get_session() as session:
            return await OnboardingSessionRepository(session).expire_before(now)

    @staticmethod
    async def _ensure_not_expired(row) -> dict[str, Any] | None:
        now = DealerOnboardingEngineV1._now()
        if row.status != OnboardingSessionStatus.ACTIVE.value:
            return DealerOnboardingEngineV1._session_snapshot(row)
        if row.expires_at >= now:
            return DealerOnboardingEngineV1._session_snapshot(row)

        async with get_session() as session:
            repo = OnboardingSessionRepository(session)
            await repo.update_fields(row.id, status=OnboardingSessionStatus.EXPIRED.value)
            step_repo = OnboardingStepRepository(session)
            await step_repo.create(
                session_id=row.id,
                step_name=row.current_step,
                status=OnboardingStepStatus.FAILED.value,
                payload={"reason": "timeout"},
            )
            refreshed = await repo.get_by_id(row.id)
            return DealerOnboardingEngineV1._session_snapshot(refreshed) if refreshed else None

    @staticmethod
    async def get_active_session(telegram_user_id: int) -> dict[str, Any] | None:
        await DealerOnboardingEngineV1.expire_stale_sessions()
        async with get_session() as session:
            row = await OnboardingSessionRepository(session).get_active_for_user(telegram_user_id)
        if row is None:
            return None
        return await DealerOnboardingEngineV1._ensure_not_expired(row)

    @staticmethod
    async def start_session(telegram_user_id: int) -> dict[str, Any]:
        existing = await DealerOnboardingEngineV1.get_active_session(telegram_user_id)
        if existing and existing["status"] == OnboardingSessionStatus.ACTIVE.value:
            return existing

        now = DealerOnboardingEngineV1._now()
        expires_at = now + timedelta(hours=ONBOARDING_TIMEOUT_HOURS)
        async with get_session() as session:
            session_repo = OnboardingSessionRepository(session)
            step_repo = OnboardingStepRepository(session)
            row = await session_repo.create(
                telegram_user_id=telegram_user_id,
                current_step=OnboardingStepName.STARTED.value,
                started_at=now,
                expires_at=expires_at,
            )
            await step_repo.create(
                session_id=row.id,
                step_name=OnboardingStepName.STARTED.value,
                payload={"source": "start"},
            )
            await session.refresh(row)
            return DealerOnboardingEngineV1._session_snapshot(row)

    @staticmethod
    async def record_step(
        session_id: uuid.UUID,
        step_name: str,
        *,
        payload: dict | None = None,
        status: str = OnboardingStepStatus.COMPLETED.value,
        update_current: bool = True,
        **session_fields: Any,
    ) -> dict[str, Any]:
        async with get_session() as session:
            session_repo = OnboardingSessionRepository(session)
            step_repo = OnboardingStepRepository(session)
            row = await session_repo.get_by_id(session_id)
            if row is None:
                raise DealerOnboardingEngineError("Onboarding session not found")
            if row.status != OnboardingSessionStatus.ACTIVE.value:
                raise DealerOnboardingEngineError(f"Session status: {row.status}")

            await step_repo.create(
                session_id=session_id,
                step_name=step_name,
                status=status,
                payload=payload,
            )
            fields = dict(session_fields)
            if update_current:
                fields["current_step"] = step_name
            updated = await session_repo.update_fields(session_id, **fields)
            if updated is None:
                raise DealerOnboardingEngineError("Failed to update session")
            await session.refresh(updated)
            return DealerOnboardingEngineV1._session_snapshot(updated)

    @staticmethod
    async def advance_for_user(
        telegram_user_id: int,
        step_name: str,
        *,
        payload: dict | None = None,
        **session_fields: Any,
    ) -> dict[str, Any] | None:
        active = await DealerOnboardingEngineV1.get_active_session(telegram_user_id)
        if not active or active["status"] != OnboardingSessionStatus.ACTIVE.value:
            return None
        return await DealerOnboardingEngineV1.record_step(
            uuid.UUID(active["id"]),
            step_name,
            payload=payload,
            **session_fields,
        )

    @staticmethod
    async def bind_payment(
        telegram_user_id: int,
        *,
        payment_id: uuid.UUID,
        plan_code: str,
        pricing_model: str,
        payment_method: str,
    ) -> dict[str, Any] | None:
        return await DealerOnboardingEngineV1.advance_for_user(
            telegram_user_id,
            OnboardingStepName.PAYMENT_CREATED.value,
            payload={
                "payment_id": str(payment_id),
                "plan_code": plan_code,
                "pricing_model": pricing_model,
                "payment_method": payment_method,
            },
            payment_id=payment_id,
            plan_code=plan_code,
            pricing_model=pricing_model,
            payment_method=payment_method,
        )

    @staticmethod
    async def get_awaiting_receipt_session(telegram_user_id: int) -> dict[str, Any] | None:
        active = await DealerOnboardingEngineV1.get_active_session(telegram_user_id)
        if not active:
            return None
        if active["current_step"] != OnboardingStepName.PAYMENT_CREATED.value:
            return None
        if not active.get("payment_id"):
            return None
        return active

    @staticmethod
    async def mark_receipt_uploaded(telegram_user_id: int) -> dict[str, Any] | None:
        return await DealerOnboardingEngineV1.advance_for_user(
            telegram_user_id,
            OnboardingStepName.RECEIPT_UPLOADED.value,
        )

    @staticmethod
    async def on_payment_approved(
        *,
        payment_id: uuid.UUID,
        tenant_id: uuid.UUID,
        client_user_id: int,
    ) -> dict[str, Any] | None:
        async with get_session() as session:
            session_repo = OnboardingSessionRepository(session)
            row = await session_repo.get_by_payment_id(payment_id)
            if row is None:
                row = await session_repo.get_active_for_user(client_user_id)
            if row is None:
                return None

        session_id = row.id
        now = DealerOnboardingEngineV1._now()

        await DealerOnboardingEngineV1.record_step(
            session_id,
            OnboardingStepName.OWNER_APPROVED.value,
            payload={"payment_id": str(payment_id), "tenant_id": str(tenant_id)},
            tenant_id=tenant_id,
        )
        await DealerOnboardingEngineV1.record_step(
            session_id,
            OnboardingStepName.TENANT_CREATED.value,
            payload={"tenant_id": str(tenant_id)},
        )

        assign_role(client_user_id, "AUTO_MANAGER")
        await RbacV2Engine.assign_role(client_user_id, "AUTO_OWNER")
        RbacV2Engine.invalidate_cache(client_user_id)

        await DealerOnboardingEngineV1.record_step(
            session_id,
            OnboardingStepName.ROLE_ASSIGNED.value,
            payload={"roles": ["AUTO_MANAGER", "AUTO_OWNER"]},
        )

        async with get_session() as session:
            session_repo = OnboardingSessionRepository(session)
            step_repo = OnboardingStepRepository(session)
            await step_repo.create(
                session_id=session_id,
                step_name=OnboardingStepName.COMPLETED.value,
                payload={"tenant_id": str(tenant_id)},
            )
            updated = await session_repo.update_fields(
                session_id,
                current_step=OnboardingStepName.COMPLETED.value,
                status=OnboardingSessionStatus.COMPLETED.value,
                completed_at=now,
                tenant_id=tenant_id,
            )
            if updated is None:
                return None
            await session.refresh(updated)
            return DealerOnboardingEngineV1._session_snapshot(updated)

    @staticmethod
    def resume_message(session: dict[str, Any]) -> str:
        step = session.get("current_step", OnboardingStepName.STARTED.value)
        label = STEP_LABELS.get(step, step)
        expires_at = session.get("expires_at", "")
        lines = [
            "🚗 Dealer Onboarding",
            "",
            f"Текущий шаг: {label}",
        ]
        if session.get("plan_code"):
            lines.append(f"Тариф: {session['plan_code']}")
        if session.get("pricing_model"):
            lines.append(f"Модель: {session['pricing_model']}")
        if expires_at:
            lines.append(f"Истекает: {expires_at[:16].replace('T', ' ')} UTC")
        if step == OnboardingStepName.RECEIPT_UPLOADED.value:
            lines.append("")
            lines.append("⏳ Ожидаем подтверждения OWNER.")
        elif step == OnboardingStepName.PAYMENT_CREATED.value:
            lines.append("")
            lines.append("📎 Загрузите фото или PDF квитанции об оплате.")
        return "\n".join(lines)

    @staticmethod
    async def get_analytics() -> dict[str, Any]:
        await DealerOnboardingEngineV1.expire_stale_sessions()
        async with get_session() as session:
            session_repo = OnboardingSessionRepository(session)
            step_repo = OnboardingStepRepository(session)
            by_status = await session_repo.count_by_status()
            step_funnel = await step_repo.count_by_step_name()
            durations = await session_repo.count_completed_with_duration()

        total = sum(by_status.values())
        completed = by_status.get(OnboardingSessionStatus.COMPLETED.value, 0)
        active = by_status.get(OnboardingSessionStatus.ACTIVE.value, 0)
        expired = by_status.get(OnboardingSessionStatus.EXPIRED.value, 0)
        avg_hours = round(sum(durations) / len(durations), 2) if durations else None
        completion_rate = round(completed / total * 100, 1) if total else 0.0

        return {
            "total_sessions": total,
            "active_sessions": active,
            "completed_sessions": completed,
            "expired_sessions": expired,
            "completion_rate_pct": completion_rate,
            "avg_completion_hours": avg_hours,
            "by_status": by_status,
            "step_funnel": step_funnel,
            "timeout_hours": ONBOARDING_TIMEOUT_HOURS,
        }

    @staticmethod
    def format_analytics(analytics: dict[str, Any]) -> str:
        lines = [
            "📊 Onboarding Analytics",
            "",
            f"Total sessions: {analytics.get('total_sessions', 0)}",
            f"Active: {analytics.get('active_sessions', 0)}",
            f"Completed: {analytics.get('completed_sessions', 0)}",
            f"Expired: {analytics.get('expired_sessions', 0)}",
            f"Completion rate: {analytics.get('completion_rate_pct', 0)}%",
        ]
        avg = analytics.get("avg_completion_hours")
        if avg is not None:
            lines.append(f"Avg completion: {avg}h")
        funnel = analytics.get("step_funnel") or {}
        if funnel:
            lines.append("")
            lines.append("Step funnel:")
            for step_name in OnboardingStepName:
                count = funnel.get(step_name.value, 0)
                if count:
                    label = STEP_LABELS.get(step_name.value, step_name.value)
                    lines.append(f"• {label}: {count}")
        return "\n".join(lines)
