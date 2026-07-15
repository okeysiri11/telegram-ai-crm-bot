# Escalation engine — remind / reassign when manager is silent.

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select

from database.models.lead_sla import LeadSlaRecord
from database.session import get_session

logger = logging.getLogger(__name__)

ESCALATION_STEPS = (
    (int(os.getenv("ESCALATION_REMIND_SEC", "300")), 1),      # 5 min
    (int(os.getenv("ESCALATION_REPEAT_SEC", "900")), 2),      # 15 min
    (int(os.getenv("ESCALATION_REASSIGN_SEC", "1800")), 3),   # 30 min
    (int(os.getenv("ESCALATION_OWNER_SEC", "3600")), 4),      # 60 min
)


class EscalationEngineV1:
    @staticmethod
    async def process_pending() -> dict[str, Any]:
        """Scan open SLA records and escalate according to thresholds."""
        now = datetime.now(timezone.utc)
        acted = 0
        details: list[dict[str, Any]] = []

        async with get_session() as session:
            rows = list(
                (
                    await session.execute(
                        select(LeadSlaRecord).where(
                            LeadSlaRecord.closed_at.is_(None),
                            LeadSlaRecord.first_response_at.is_(None),
                        )
                    )
                ).scalars().all()
            )

            for row in rows:
                base = row.assigned_at or row.created_at_lead
                if base is None:
                    continue
                elapsed = int((now - base).total_seconds())
                target_level = 0
                for threshold, level in ESCALATION_STEPS:
                    if elapsed >= threshold:
                        target_level = level

                if target_level <= row.escalation_level:
                    continue

                previous = row.escalation_level
                row.escalation_level = target_level
                await session.flush()
                acted += 1
                info = {
                    "request_number": row.request_number,
                    "from_level": previous,
                    "to_level": target_level,
                    "elapsed_sec": elapsed,
                }
                details.append(info)

        for info in details:
            await EscalationEngineV1._apply_level(info)

        return {"acted": acted, "details": details}

    @staticmethod
    async def _apply_level(info: dict[str, Any]) -> None:
        from services.notification_center import NotificationCenterV1
        from services.pg_platform_audit_engine import PlatformAuditEngineV1

        level = info["to_level"]
        req = info["request_number"]
        await PlatformAuditEngineV1.log(
            event_type="ESCALATION",
            entity_type="client_request",
            entity_id=req,
            payload=info,
        )

        if level == 1:
            await NotificationCenterV1.notify_managers(
                f"⏰ Reminder: lead {req} waiting for response (5+ min)"
            )
        elif level == 2:
            await NotificationCenterV1.notify_managers(
                f"⏰ Repeat: lead {req} still unanswered (15+ min)"
            )
        elif level == 3:
            await EscalationEngineV1._reassign(req)
            await NotificationCenterV1.notify_managers(
                f"🔄 Lead {req} reassigned after 30+ min without response"
            )
        elif level >= 4:
            await NotificationCenterV1.notify_owner(
                f"🚨 Escalation: lead {req} unanswered for 60+ minutes"
            )

    @staticmethod
    async def _reassign(request_number: str) -> None:
        try:
            from services.pg_auto_client_request_engine import AutoClientRequestEngineV1
            from services.pg_client_request_crm_engine import ClientRequestCrmEngineV1

            manager_info = await AutoClientRequestEngineV1.find_auto_manager()
            if manager_info is None:
                return
            manager_uuid, _, _ = manager_info
            await ClientRequestCrmEngineV1.assign_manager(request_number, manager_uuid)
        except Exception:
            logger.warning("Escalation reassign failed for %s", request_number, exc_info=True)
