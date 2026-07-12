# Settlement Engine v1 — cash, bank, crypto, hybrid multi-step settlement.

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Any

from config import OWNER_ID
from database.models.settlement import (
    Settlement,
    SettlementStatus,
    SettlementStep,
    SettlementStepType,
    SettlementType,
)
from database.session import get_session
from repositories.deal_repository import DealRepository
from repositories.settlement_repository import (
    SettlementRepository,
    SettlementRouteRepository,
    SettlementStatusHistoryRepository,
    SettlementStepRepository,
)
from repositories.user_role_repository import UserRoleRepository

SETTLEMENT_ROLES = frozenset({"OWNER", "ADMIN", "MANAGER", "ACCOUNTANT"})

DEFAULT_HYBRID_STEPS = (
    {"step_type": SettlementStepType.BANK.value, "share": Decimal("0.5")},
    {"step_type": SettlementStepType.CRYPTO.value, "share": Decimal("0.5")},
)

_ACTIVE_STEP_STATUSES = frozenset(
    {
        SettlementStatus.IN_PROGRESS.value,
        SettlementStatus.WAITING_CONFIRMATION.value,
    }
)


class SettlementEngineError(Exception):
    pass


class SettlementEngineV1:
    @staticmethod
    async def user_can_access(user_id: int) -> bool:
        if user_id == OWNER_ID:
            return True
        async with get_session() as session:
            roles = await UserRoleRepository(session).get_user_roles(user_id)
            return any(role.code in SETTLEMENT_ROLES for role in roles)

    @staticmethod
    async def _publish_event(
        event_type: str,
        settlement_id: uuid.UUID,
        payload: dict[str, Any],
    ) -> None:
        try:
            from services import crm_event_bus as bus

            await bus.publish_event(
                event_type,
                "settlement",
                settlement_id,
                payload,
            )
        except Exception:
            pass

    @staticmethod
    async def _record_status(
        session,
        *,
        settlement_id: uuid.UUID,
        to_status: str,
        from_status: str | None = None,
        step_id: uuid.UUID | None = None,
        changed_by: int | None = None,
        notes: str | None = None,
    ) -> None:
        await SettlementStatusHistoryRepository(session).record(
            settlement_id=settlement_id,
            to_status=to_status,
            from_status=from_status,
            step_id=step_id,
            changed_by=changed_by,
            notes=notes,
        )

    @staticmethod
    def _default_steps_for_type(
        settlement_type: str,
        asset: str,
        amount: Decimal,
    ) -> list[dict[str, Any]]:
        if settlement_type == SettlementType.CASH.value:
            return [
                {
                    "step_order": 1,
                    "step_type": SettlementStepType.CASH.value,
                    "asset": asset,
                    "amount": amount,
                }
            ]
        if settlement_type == SettlementType.BANK.value:
            return [
                {
                    "step_order": 1,
                    "step_type": SettlementStepType.BANK.value,
                    "asset": asset,
                    "amount": amount,
                }
            ]
        if settlement_type == SettlementType.CRYPTO.value:
            return [
                {
                    "step_order": 1,
                    "step_type": SettlementStepType.CRYPTO.value,
                    "asset": asset,
                    "amount": amount,
                }
            ]
        steps: list[dict[str, Any]] = []
        for index, part in enumerate(DEFAULT_HYBRID_STEPS, start=1):
            steps.append(
                {
                    "step_order": index,
                    "step_type": part["step_type"],
                    "asset": asset,
                    "amount": (amount * part["share"]).quantize(Decimal("0.00000001")),
                }
            )
        return steps

    @staticmethod
    async def create_settlement(
        actor_id: int,
        *,
        settlement_type: str,
        asset: str,
        amount: Decimal,
        deal_id: uuid.UUID | None = None,
        reference: str | None = None,
        steps: list[dict[str, Any]] | None = None,
    ) -> Settlement:
        if not await SettlementEngineV1.user_can_access(actor_id):
            raise SettlementEngineError("Access denied")

        async with get_session() as session:
            if deal_id is not None:
                deal = await DealRepository(session).get_by_id(deal_id)
                if deal is None:
                    raise SettlementEngineError(f"Deal not found: {deal_id}")

            settlement = await SettlementRepository(session).create(
                settlement_type=settlement_type,
                asset=asset,
                amount=amount,
                deal_id=deal_id,
                reference=reference,
            )

            step_defs = steps or SettlementEngineV1._default_steps_for_type(
                settlement_type,
                asset,
                amount,
            )
            route = await SettlementRouteRepository(session).create(
                settlement_id=settlement.id,
                name=f"{settlement_type} route",
                description=f"Multi-step {settlement_type.lower()} settlement",
                step_count=len(step_defs),
            )

            step_repo = SettlementStepRepository(session)
            for step_def in step_defs:
                await step_repo.create(route_id=route.id, **step_def)

            await SettlementEngineV1._record_status(
                session,
                settlement_id=settlement.id,
                to_status=SettlementStatus.CREATED.value,
                changed_by=actor_id,
                notes="Settlement created",
            )

        await SettlementEngineV1._publish_event(
            "settlement.created",
            settlement.id,
            {
                "settlement_type": settlement_type,
                "asset": asset,
                "amount": str(amount),
                "deal_id": str(deal_id) if deal_id else None,
                "step_count": len(step_defs),
            },
        )
        return settlement

    @staticmethod
    async def start_settlement(
        actor_id: int,
        settlement_id: uuid.UUID,
    ) -> Settlement:
        if not await SettlementEngineV1.user_can_access(actor_id):
            raise SettlementEngineError("Access denied")

        async with get_session() as session:
            settlement = await SettlementRepository(session).get_by_id(settlement_id)
            if settlement is None:
                raise SettlementEngineError(f"Settlement not found: {settlement_id}")
            if settlement.status != SettlementStatus.CREATED.value:
                raise SettlementEngineError(
                    f"Cannot start settlement in status: {settlement.status}"
                )

            old_status = settlement.status
            settlement = await SettlementRepository(session).update_status(
                settlement_id,
                SettlementStatus.IN_PROGRESS.value,
            )

            route = await SettlementRouteRepository(session).get_by_settlement(
                settlement_id
            )
            if route is not None:
                first_step = await SettlementStepRepository(session).next_pending(
                    route.id
                )
                if first_step is not None:
                    await SettlementStepRepository(session).update_status(
                        first_step.id,
                        SettlementStatus.IN_PROGRESS.value,
                    )
                    await SettlementEngineV1._record_status(
                        session,
                        settlement_id=settlement_id,
                        from_status=SettlementStatus.CREATED.value,
                        to_status=SettlementStatus.IN_PROGRESS.value,
                        step_id=first_step.id,
                        changed_by=actor_id,
                        notes=f"Step {first_step.step_order} started",
                    )

            await SettlementEngineV1._record_status(
                session,
                settlement_id=settlement_id,
                from_status=old_status,
                to_status=SettlementStatus.IN_PROGRESS.value,
                changed_by=actor_id,
            )

        await SettlementEngineV1._publish_event(
            "settlement.started",
            settlement_id,
            {"settlement_type": settlement.settlement_type, "asset": settlement.asset},
        )
        return settlement

    @staticmethod
    async def confirm_step(
        actor_id: int,
        step_id: uuid.UUID,
        *,
        external_ref: str | None = None,
    ) -> SettlementStep:
        if not await SettlementEngineV1.user_can_access(actor_id):
            raise SettlementEngineError("Access denied")

        async with get_session() as session:
            step_repo = SettlementStepRepository(session)
            step = await step_repo.get_by_id(step_id)
            if step is None:
                raise SettlementEngineError(f"Step not found: {step_id}")
            if step.status != SettlementStatus.IN_PROGRESS.value:
                raise SettlementEngineError(
                    f"Cannot confirm step in status: {step.status}"
                )

            settlement_id = await step_repo.get_settlement_id(step_id)
            if settlement_id is None:
                raise SettlementEngineError(f"Settlement not found for step: {step_id}")

            old_status = step.status
            step = await step_repo.update_status(
                step_id,
                SettlementStatus.WAITING_CONFIRMATION.value,
                external_ref=external_ref,
            )

            await SettlementRepository(session).update_status(
                settlement_id,
                SettlementStatus.WAITING_CONFIRMATION.value,
            )
            await SettlementEngineV1._record_status(
                session,
                settlement_id=settlement_id,
                from_status=old_status,
                to_status=SettlementStatus.WAITING_CONFIRMATION.value,
                step_id=step_id,
                changed_by=actor_id,
                notes=f"Step {step.step_order} awaiting confirmation",
            )

        return step

    @staticmethod
    async def advance_step(
        actor_id: int,
        step_id: uuid.UUID,
        *,
        external_ref: str | None = None,
    ) -> SettlementStep:
        return await SettlementEngineV1.complete_step(
            actor_id,
            step_id,
            external_ref=external_ref,
        )

    @staticmethod
    async def complete_step(
        actor_id: int,
        step_id: uuid.UUID,
        *,
        external_ref: str | None = None,
    ) -> SettlementStep:
        if not await SettlementEngineV1.user_can_access(actor_id):
            raise SettlementEngineError("Access denied")

        completed_payload: dict[str, Any] | None = None

        async with get_session() as session:
            step_repo = SettlementStepRepository(session)
            step = await step_repo.get_by_id(step_id)
            if step is None:
                raise SettlementEngineError(f"Step not found: {step_id}")
            if step.status not in _ACTIVE_STEP_STATUSES:
                raise SettlementEngineError(
                    f"Cannot complete step in status: {step.status}"
                )

            settlement_id = await step_repo.get_settlement_id(step_id)
            if settlement_id is None:
                raise SettlementEngineError(f"Settlement not found for step: {step_id}")

            old_status = step.status
            step = await step_repo.update_status(
                step_id,
                SettlementStatus.COMPLETED.value,
                external_ref=external_ref,
            )

            await SettlementEngineV1._record_status(
                session,
                settlement_id=settlement_id,
                from_status=old_status,
                to_status=SettlementStatus.COMPLETED.value,
                step_id=step_id,
                changed_by=actor_id,
                notes=f"Step {step.step_order} completed",
            )

            route = await SettlementRouteRepository(session).get_by_settlement(
                settlement_id
            )
            next_step = (
                await step_repo.next_pending(route.id) if route is not None else None
            )

            settlement_repo = SettlementRepository(session)
            if next_step is not None:
                await step_repo.update_status(
                    next_step.id, SettlementStatus.IN_PROGRESS.value
                )
                await settlement_repo.update_status(
                    settlement_id,
                    SettlementStatus.IN_PROGRESS.value,
                )
            else:
                settlement = await settlement_repo.update_status(
                    settlement_id,
                    SettlementStatus.COMPLETED.value,
                )
                await SettlementEngineV1._record_status(
                    session,
                    settlement_id=settlement_id,
                    from_status=SettlementStatus.IN_PROGRESS.value,
                    to_status=SettlementStatus.COMPLETED.value,
                    changed_by=actor_id,
                    notes="All steps completed",
                )
                completed_payload = {
                    "asset": settlement.asset if settlement else step.asset,
                    "amount": str(settlement.amount if settlement else step.amount),
                }

        if completed_payload is not None:
            await SettlementEngineV1._publish_event(
                "settlement.completed",
                settlement_id,
                completed_payload,
            )

        return step

    @staticmethod
    async def fail_settlement(
        actor_id: int,
        settlement_id: uuid.UUID,
        *,
        reason: str | None = None,
        step_id: uuid.UUID | None = None,
    ) -> Settlement:
        if not await SettlementEngineV1.user_can_access(actor_id):
            raise SettlementEngineError("Access denied")

        async with get_session() as session:
            settlement = await SettlementRepository(session).get_by_id(settlement_id)
            if settlement is None:
                raise SettlementEngineError(f"Settlement not found: {settlement_id}")

            old_status = settlement.status
            settlement = await SettlementRepository(session).update_status(
                settlement_id,
                SettlementStatus.FAILED.value,
            )

            if step_id is not None:
                await SettlementStepRepository(session).update_status(
                    step_id, SettlementStatus.FAILED.value
                )

            await SettlementEngineV1._record_status(
                session,
                settlement_id=settlement_id,
                from_status=old_status,
                to_status=SettlementStatus.FAILED.value,
                step_id=step_id,
                changed_by=actor_id,
                notes=reason,
            )

        await SettlementEngineV1._publish_event(
            "settlement.failed",
            settlement_id,
            {"reason": reason, "step_id": str(step_id) if step_id else None},
        )
        return settlement

    @staticmethod
    async def cancel_settlement(
        actor_id: int,
        settlement_id: uuid.UUID,
        *,
        reason: str | None = None,
    ) -> Settlement:
        if not await SettlementEngineV1.user_can_access(actor_id):
            raise SettlementEngineError("Access denied")

        async with get_session() as session:
            settlement = await SettlementRepository(session).get_by_id(settlement_id)
            if settlement is None:
                raise SettlementEngineError(f"Settlement not found: {settlement_id}")
            if settlement.status in {
                SettlementStatus.COMPLETED.value,
                SettlementStatus.FAILED.value,
            }:
                raise SettlementEngineError(
                    f"Cannot cancel settlement in status: {settlement.status}"
                )

            old_status = settlement.status
            settlement = await SettlementRepository(session).update_status(
                settlement_id,
                SettlementStatus.CANCELLED.value,
            )

            await SettlementEngineV1._record_status(
                session,
                settlement_id=settlement_id,
                from_status=old_status,
                to_status=SettlementStatus.CANCELLED.value,
                changed_by=actor_id,
                notes=reason,
            )

        return settlement

    @staticmethod
    async def get_settlement(
        actor_id: int,
        settlement_id: uuid.UUID,
    ) -> dict[str, Any]:
        if not await SettlementEngineV1.user_can_access(actor_id):
            raise SettlementEngineError("Access denied")

        async with get_session() as session:
            settlement = await SettlementRepository(session).get_by_id(settlement_id)
            if settlement is None:
                raise SettlementEngineError(f"Settlement not found: {settlement_id}")

            route = await SettlementRouteRepository(session).get_by_settlement(
                settlement_id
            )
            steps = (
                await SettlementStepRepository(session).list_by_route(route.id)
                if route
                else []
            )
            history = await SettlementStatusHistoryRepository(session).list_by_settlement(
                settlement_id
            )

            return {
                "settlement": {
                    "id": str(settlement.id),
                    "deal_id": str(settlement.deal_id) if settlement.deal_id else None,
                    "settlement_type": settlement.settlement_type,
                    "asset": settlement.asset,
                    "amount": str(settlement.amount),
                    "status": settlement.status,
                    "reference": settlement.reference,
                },
                "route": {
                    "id": str(route.id),
                    "name": route.name,
                    "step_count": route.step_count,
                }
                if route
                else None,
                "steps": [
                    {
                        "id": str(s.id),
                        "step_order": s.step_order,
                        "step_type": s.step_type,
                        "asset": s.asset,
                        "amount": str(s.amount),
                        "status": s.status,
                        "external_ref": s.external_ref,
                    }
                    for s in steps
                ],
                "status_history": [
                    {
                        "from_status": h.from_status,
                        "to_status": h.to_status,
                        "step_id": str(h.step_id) if h.step_id else None,
                        "created_at": h.created_at.isoformat(),
                        "notes": h.notes,
                    }
                    for h in history
                ],
            }
