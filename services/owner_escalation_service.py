# OwnerEscalationService — level-4 platform owner escalation (EventBus-only side effects).

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from database.session import get_session
from events.event_bus import publish
from events.owner_events import OwnerEscalationEvent
from repositories.escalation_repository import EscalationRepository
from repositories.owner_repository import OwnerRepository
from repositories.sla_repository import SLARepository

logger = logging.getLogger(__name__)


class OwnerEscalationService:
    @staticmethod
    def _now() -> datetime:
        return datetime.now(timezone.utc)

    @staticmethod
    async def check_overdue_requests(*, limit: int = 50) -> dict[str, Any]:
        if not OwnerRepository.is_enabled():
            return {"acted": 0, "skipped": True, "reason": "owner_escalation_disabled"}

        now = OwnerEscalationService._now()
        acted = 0
        details: list[dict[str, Any]] = []

        async with get_session() as session:
            owner_repo = OwnerRepository(session)
            rows = await owner_repo.lock_owner_escalation_candidates(now=now, limit=limit)

            for row in rows:
                if row.completed_at is not None:
                    continue

                context = await EscalationRepository(session).load_request_context(row.request_id)
                if context is None:
                    logger.warning(
                        "owner_escalation_missing_context",
                        extra={"request_id": str(row.request_id)},
                    )
                    continue

                escalated = await OwnerEscalationService.escalate_request(
                    row,
                    context=context,
                    session=session,
                    now=now,
                )
                if not escalated:
                    continue

                acted += 1
                details.append(
                    {
                        "request_id": str(row.request_id),
                        "request_number": context.request_number,
                        "minutes_overdue": owner_repo.minutes_overdue_since_completion(row, now),
                    }
                )

        return {"acted": acted, "details": details, "checked_at": now.isoformat()}

    @staticmethod
    async def escalate_request(
        row,
        *,
        context,
        session,
        now: datetime | None = None,
    ) -> bool:
        now = now or OwnerEscalationService._now()
        owner_repo = OwnerRepository(session)

        if row.completed_at is not None or row.owner_escalated:
            return False

        marked = await owner_repo.mark_owner_escalated(row, escalated_at=now)
        if not marked:
            return False

        config = OwnerRepository.owner_config()
        minutes_overdue = OwnerRepository.minutes_overdue_since_completion(row, now)
        manager_name = await SLARepository(session)._resolve_manager_name(
            manager_uuid=context.manager_uuid,
            telegram_id=row.manager_id,
        )

        await publish(
            OwnerEscalationEvent(
                request_id=context.request_id,
                request_number=context.request_number,
                vertical=context.vertical,
                request_type=context.request_type,
                manager_id=context.manager_uuid,
                manager_telegram_id=context.manager_telegram_id,
                manager_name=manager_name,
                owner_id=str(config["telegram_id"]) if config["telegram_id"] else None,
                owner_name=str(config["name"]),
                minutes_overdue=minutes_overdue,
                reason="Exceeded maximum escalation threshold",
                escalation_level=4,
                completion_deadline=row.completion_deadline.isoformat(),
                trigger="owner_escalation_level_4",
            ),
            wait=True,
        )
        return True

    @staticmethod
    async def notify_owner(event: OwnerEscalationEvent) -> bool:
        from services.notification_service import notification_service

        config = OwnerRepository.owner_config()
        owner_tid = config.get("telegram_id")
        if owner_tid is None:
            logger.warning("owner_notification_skipped_no_owner_config")
            return False

        manager_label = event.manager_name or event.manager_id or "—"
        text = (
            "🚨 OWNER ESCALATION\n\n"
            f"Request:\n{event.request_number}\n\n"
            f"Vertical:\n{event.vertical.upper()}\n\n"
            f"Assigned manager:\n{manager_label}\n\n"
            f"Overdue:\n{event.minutes_overdue} minutes\n\n"
            f"Reason:\n{event.reason}"
        )

        await notification_service.notify_managers_new_request(
            vertical=event.vertical,
            request_number=event.request_number,
            client_name="",
            product=text,
            manager_telegram_id=int(owner_tid),
        )

        async with get_session() as session:
            await OwnerRepository(session).mark_owner_notification_sent(event.request_id)
        return True

    @staticmethod
    async def get_owner_escalated(*, limit: int = 100) -> list[dict[str, Any]]:
        async with get_session() as session:
            return await OwnerRepository(session).get_owner_escalated_requests(limit=limit)

    @staticmethod
    async def get_owner_escalation_kpi() -> dict[str, int]:
        async with get_session() as session:
            return await OwnerRepository(session).get_owner_escalation_kpi()


owner_escalation_service = OwnerEscalationService()
