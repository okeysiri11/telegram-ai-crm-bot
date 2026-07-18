# EscalationService — SLA breach detection and EventBus-only escalation actions.

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from database.session import get_session
from platform_configuration.config_provider import config_provider
from events.event_bus import publish
from events.request_events import ManagerEscalationEvent, RequestOverdueEvent
from repositories.escalation_repository import EscalationRepository

logger = logging.getLogger(__name__)


def _escalation_level_timers() -> dict[str, int]:
    return config_provider.escalation_timers()


class EscalationService:
    @staticmethod
    def _now() -> datetime:
        return datetime.now(timezone.utc)

    @staticmethod
    def _deadline_level2(row) -> datetime:
        timers = _escalation_level_timers()
        return row.first_response_deadline + timedelta(seconds=timers["level2_after_sec"])

    @staticmethod
    def _deadline_level3(row) -> datetime:
        timers = _escalation_level_timers()
        return row.first_response_deadline + timedelta(
            seconds=timers["level2_after_sec"] + timers["level3_after_sec"]
        )

    @staticmethod
    def _next_escalation_level(row, now: datetime) -> int | None:
        if row.first_response_at is not None or row.completed_at is not None:
            return None
        if row.escalation_level < 1 and now >= row.first_response_deadline:
            return 1
        if row.escalation_level < 2 and now >= EscalationService._deadline_level2(row):
            return 2
        if row.escalation_level < 3 and now >= EscalationService._deadline_level3(row):
            return 3
        return None

    @staticmethod
    async def process_due_escalations(*, limit: int = 50) -> dict[str, Any]:
        """Scan due SLA rows with row locking; publish events idempotently."""
        now = EscalationService._now()
        acted = 0
        details: list[dict[str, Any]] = []

        async with get_session() as session:
            repo = EscalationRepository(session)
            rows = await repo.lock_due_for_escalation(now=now, limit=limit)

            for row in rows:
                next_level = EscalationService._next_escalation_level(row, now)
                if next_level is None:
                    continue

                context = await repo.load_request_context(row.request_id)
                if context is None:
                    logger.warning(
                        "escalation_missing_request_context",
                        extra={"request_id": str(row.request_id)},
                    )
                    continue

                previous_level = row.escalation_level
                overdue_seconds = repo.overdue_seconds(row, now)

                if next_level == 3:
                    reassigned, alternate = await EscalationService._reassign_request(context)
                    if not reassigned:
                        continue
                    await repo.advance_escalation_level(
                        row,
                        new_level=3,
                        manager_telegram_id=int(alternate["telegram_id"]) if alternate else None,
                    )
                else:
                    advanced = await repo.advance_escalation_level(row, new_level=next_level)
                    if not advanced:
                        continue
                    await EscalationService._publish_for_level(
                        next_level,
                        context=context,
                        overdue_seconds=overdue_seconds,
                    )

                acted += 1
                details.append(
                    {
                        "request_id": str(row.request_id),
                        "request_number": context.request_number,
                        "from_level": previous_level,
                        "to_level": next_level,
                        "overdue_seconds": overdue_seconds,
                    }
                )

        return {"acted": acted, "details": details, "checked_at": now.isoformat()}

    @staticmethod
    async def _publish_for_level(
        level: int,
        *,
        context,
        overdue_seconds: int,
    ) -> None:
        if level == 1:
            await publish(
                RequestOverdueEvent(
                    request_id=context.request_id,
                    request_number=context.request_number,
                    vertical=context.vertical,
                    request_type=context.request_type,
                    manager_id=context.manager_uuid,
                    manager_telegram_id=context.manager_telegram_id,
                    overdue_seconds=overdue_seconds,
                    reason="sla_first_response",
                    escalation_level=1,
                ),
                wait=True,
            )
            return

        if level == 2:
            await publish(
                ManagerEscalationEvent(
                    request_id=context.request_id,
                    request_number=context.request_number,
                    vertical=context.vertical,
                    request_type=context.request_type,
                    manager_id=context.manager_uuid,
                    manager_telegram_id=context.manager_telegram_id,
                    client_telegram_id=context.client_telegram_id,
                    escalation_level=2,
                    overdue_seconds=overdue_seconds,
                    reason="sla_manager_escalation",
                ),
                wait=True,
            )

    @staticmethod
    async def _reassign_request(context) -> tuple[bool, dict[str, Any] | None]:
        from services.manager_service import manager_service
        from services.request_service import request_service

        current_uuid = context.manager_uuid
        alternate = await manager_service.resolve_alternate_manager_for_vertical(
            context.vertical,
            exclude_manager_id=current_uuid,
        )
        if alternate is None:
            logger.warning(
                "escalation_reassign_no_alternate_manager",
                extra={"request_id": context.request_id, "vertical": context.vertical},
            )
            return False, None

        new_manager_uuid = alternate["user_id"]
        if current_uuid and str(new_manager_uuid) == str(current_uuid):
            logger.info(
                "escalation_reassign_same_manager_skipped",
                extra={"request_id": context.request_id},
            )
            return False, None

        result = await request_service.reassign_request(context.request_id, new_manager_uuid)
        if result is None:
            logger.warning(
                "escalation_reassign_failed",
                extra={"request_id": context.request_id, "new_manager_id": str(new_manager_uuid)},
            )
            return False, None

        logger.info(
            "escalation_reassigned",
            extra={
                "request_id": context.request_id,
                "previous_manager_id": current_uuid,
                "new_manager_id": str(new_manager_uuid),
            },
        )
        return True, alternate


escalation_service = EscalationService()
