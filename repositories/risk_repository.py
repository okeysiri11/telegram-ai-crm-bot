# Risk Engine v1 repositories — PostgreSQL async data access.

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.risk import (
    BlockedOperation,
    ExposureLimit,
    RiskDecision,
    RiskDecisionResult,
    RiskEvaluationType,
    RiskEvent,
    RiskEventStatus,
    RiskExposureScope,
    RiskLevel,
    RiskRule,
    RiskRuleType,
)


class RiskRuleRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        rule_code: str,
        rule_type: str,
        risk_level: str = RiskLevel.MEDIUM.value,
        threshold: Decimal | None = None,
        config: dict | None = None,
        description: str | None = None,
        is_active: bool = True,
        **extra: Any,
    ) -> RiskRule:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")
        if rule_type not in {t.value for t in RiskRuleType}:
            raise ValueError(f"Invalid rule_type: {rule_type}")

        rule = RiskRule(
            rule_code=rule_code,
            rule_type=rule_type,
            risk_level=risk_level,
            threshold=threshold,
            config=config,
            description=description,
            is_active=is_active,
        )
        self._session.add(rule)
        await self._session.flush()
        return rule

    async def get_by_code(self, rule_code: str) -> RiskRule | None:
        result = await self._session.execute(
            select(RiskRule).where(RiskRule.rule_code == rule_code)
        )
        return result.scalar_one_or_none()

    async def list_active(self, rule_type: str | None = None) -> list[RiskRule]:
        query = select(RiskRule).where(RiskRule.is_active.is_(True))
        if rule_type is not None:
            query = query.where(RiskRule.rule_type == rule_type)
        result = await self._session.execute(query.order_by(RiskRule.rule_code.asc()))
        return list(result.scalars().all())


class RiskEventRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        event_type: str,
        risk_level: str,
        message: str,
        rule_id: uuid.UUID | None = None,
        deal_id: uuid.UUID | None = None,
        partner_id: uuid.UUID | None = None,
        source_type: str | None = None,
        source_id: str | None = None,
        details: dict | None = None,
        **extra: Any,
    ) -> RiskEvent:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")

        event = RiskEvent(
            rule_id=rule_id,
            event_type=event_type,
            risk_level=risk_level,
            message=message,
            deal_id=deal_id,
            partner_id=partner_id,
            source_type=source_type,
            source_id=source_id,
            details=details,
        )
        self._session.add(event)
        await self._session.flush()
        return event

    async def resolve(self, event_id: uuid.UUID) -> RiskEvent | None:
        result = await self._session.execute(
            select(RiskEvent).where(RiskEvent.id == event_id)
        )
        event = result.scalar_one_or_none()
        if event is None:
            return None
        event.status = RiskEventStatus.RESOLVED.value
        await self._session.flush()
        return event

    async def list_open(
        self,
        *,
        deal_id: uuid.UUID | None = None,
        partner_id: uuid.UUID | None = None,
    ) -> list[RiskEvent]:
        query = select(RiskEvent).where(
            RiskEvent.status == RiskEventStatus.OPEN.value
        )
        if deal_id is not None:
            query = query.where(RiskEvent.deal_id == deal_id)
        if partner_id is not None:
            query = query.where(RiskEvent.partner_id == partner_id)
        result = await self._session.execute(query.order_by(RiskEvent.created_at.desc()))
        return list(result.scalars().all())


class RiskDecisionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        evaluation_type: str,
        risk_level: str,
        decision: str,
        checks: list[dict[str, Any]] | None = None,
        deal_id: uuid.UUID | None = None,
        partner_id: uuid.UUID | None = None,
        asset: str | None = None,
        amount: Decimal | None = None,
        decided_by: int | None = None,
        notes: str | None = None,
        **extra: Any,
    ) -> RiskDecision:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")
        if evaluation_type not in {t.value for t in RiskEvaluationType}:
            raise ValueError(f"Invalid evaluation_type: {evaluation_type}")
        if decision not in {d.value for d in RiskDecisionResult}:
            raise ValueError(f"Invalid decision: {decision}")

        record = RiskDecision(
            evaluation_type=evaluation_type,
            risk_level=risk_level,
            decision=decision,
            checks=checks,
            deal_id=deal_id,
            partner_id=partner_id,
            asset=asset,
            amount=amount,
            decided_by=decided_by,
            notes=notes,
        )
        self._session.add(record)
        await self._session.flush()
        return record

    async def get_by_id(self, decision_id: uuid.UUID) -> RiskDecision | None:
        result = await self._session.execute(
            select(RiskDecision).where(RiskDecision.id == decision_id)
        )
        return result.scalar_one_or_none()

    async def apply_override(
        self,
        decision_id: uuid.UUID,
        *,
        override_by: int,
        override_reason: str,
    ) -> RiskDecision | None:
        decision = await self.get_by_id(decision_id)
        if decision is None:
            return None
        decision.decision = RiskDecisionResult.APPROVED.value
        decision.override_by = override_by
        decision.override_reason = override_reason
        decision.overridden_at = datetime.now(timezone.utc)
        await self._session.flush()
        return decision


class BlockedOperationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        decision_id: uuid.UUID,
        operation_type: str,
        subject_type: str,
        subject_id: str,
        reason: str,
        rule_code: str | None = None,
        **extra: Any,
    ) -> BlockedOperation:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")

        blocked = BlockedOperation(
            decision_id=decision_id,
            operation_type=operation_type,
            subject_type=subject_type,
            subject_id=subject_id,
            reason=reason,
            rule_code=rule_code,
        )
        self._session.add(blocked)
        await self._session.flush()
        return blocked

    async def resolve_for_decision(self, decision_id: uuid.UUID) -> int:
        result = await self._session.execute(
            select(BlockedOperation).where(
                BlockedOperation.decision_id == decision_id,
                BlockedOperation.is_active.is_(True),
            )
        )
        count = 0
        now = datetime.now(timezone.utc)
        for blocked in result.scalars().all():
            blocked.is_active = False
            blocked.resolved_at = now
            count += 1
        if count:
            await self._session.flush()
        return count

    async def list_active(
        self,
        *,
        subject_type: str | None = None,
        subject_id: str | None = None,
    ) -> list[BlockedOperation]:
        query = select(BlockedOperation).where(BlockedOperation.is_active.is_(True))
        if subject_type is not None:
            query = query.where(BlockedOperation.subject_type == subject_type)
        if subject_id is not None:
            query = query.where(BlockedOperation.subject_id == subject_id)
        result = await self._session.execute(query.order_by(BlockedOperation.created_at.desc()))
        return list(result.scalars().all())


class ExposureLimitRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        scope: str,
        max_exposure: Decimal,
        scope_key: str | None = None,
        asset: str | None = None,
        current_exposure: Decimal = Decimal("0"),
        description: str | None = None,
        is_active: bool = True,
        **extra: Any,
    ) -> ExposureLimit:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")
        if scope not in {s.value for s in RiskExposureScope}:
            raise ValueError(f"Invalid scope: {scope}")

        limit = ExposureLimit(
            scope=scope,
            scope_key=scope_key,
            asset=asset,
            max_exposure=max_exposure,
            current_exposure=current_exposure,
            description=description,
            is_active=is_active,
        )
        self._session.add(limit)
        await self._session.flush()
        return limit

    async def get_matching(
        self,
        *,
        scope: str,
        scope_key: str | None = None,
        asset: str | None = None,
    ) -> ExposureLimit | None:
        query = select(ExposureLimit).where(
            ExposureLimit.scope == scope,
            ExposureLimit.is_active.is_(True),
        )
        if scope_key is not None:
            query = query.where(ExposureLimit.scope_key == scope_key)
        if asset is not None:
            query = query.where(
                (ExposureLimit.asset == asset) | (ExposureLimit.asset.is_(None))
            )
        result = await self._session.execute(query.limit(1))
        return result.scalar_one_or_none()

    async def list_active(self) -> list[ExposureLimit]:
        result = await self._session.execute(
            select(ExposureLimit)
            .where(ExposureLimit.is_active.is_(True))
            .order_by(ExposureLimit.scope.asc(), ExposureLimit.scope_key.asc())
        )
        return list(result.scalars().all())
