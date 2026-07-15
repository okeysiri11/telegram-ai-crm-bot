# Lead SLA monitoring for client_requests CRM.

from __future__ import annotations

import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select

from database.models.lead_sla import LeadSlaRecord
from database.session import get_session

logger = logging.getLogger(__name__)

# SLA thresholds (seconds) — configurable via env
SLA_ASSIGNMENT_SEC = int(os.getenv("SLA_ASSIGNMENT_SEC", str(15 * 60)))
SLA_FIRST_RESPONSE_SEC = int(os.getenv("SLA_FIRST_RESPONSE_SEC", str(30 * 60)))
SLA_CLOSE_SEC = int(os.getenv("SLA_CLOSE_SEC", str(72 * 3600)))


class LeadSlaEngineV1:
    @staticmethod
    def _now() -> datetime:
        return datetime.now(timezone.utc)

    @staticmethod
    async def on_lead_created(
        *,
        client_request_id: uuid.UUID,
        request_number: str,
        manager_telegram_id: int | None = None,
    ) -> dict[str, Any]:
        async with get_session() as session:
            existing = (
                await session.execute(
                    select(LeadSlaRecord).where(
                        LeadSlaRecord.client_request_id == client_request_id
                    )
                )
            ).scalar_one_or_none()
            if existing:
                return LeadSlaEngineV1._snap(existing)

            row = LeadSlaRecord(
                client_request_id=client_request_id,
                request_number=request_number,
                created_at_lead=LeadSlaEngineV1._now(),
                manager_telegram_id=manager_telegram_id,
                priority="MEDIUM",
            )
            session.add(row)
            await session.flush()
            return LeadSlaEngineV1._snap(row)

    @staticmethod
    async def on_assigned(
        *,
        request_number: str,
        manager_telegram_id: int | None = None,
    ) -> dict[str, Any] | None:
        async with get_session() as session:
            row = (
                await session.execute(
                    select(LeadSlaRecord).where(LeadSlaRecord.request_number == request_number)
                )
            ).scalar_one_or_none()
            if row is None:
                return None
            now = LeadSlaEngineV1._now()
            row.assigned_at = now
            if row.created_at_lead:
                row.time_to_assignment_sec = int((now - row.created_at_lead).total_seconds())
            if manager_telegram_id:
                row.manager_telegram_id = manager_telegram_id
            await session.flush()
            snap = LeadSlaEngineV1._snap(row)

        await LeadSlaEngineV1._check_and_alert(snap)
        return snap

    @staticmethod
    async def on_first_response(request_number: str) -> dict[str, Any] | None:
        async with get_session() as session:
            row = (
                await session.execute(
                    select(LeadSlaRecord).where(LeadSlaRecord.request_number == request_number)
                )
            ).scalar_one_or_none()
            if row is None:
                return None
            if row.first_response_at:
                return LeadSlaEngineV1._snap(row)
            now = LeadSlaEngineV1._now()
            row.first_response_at = now
            base = row.assigned_at or row.created_at_lead
            if base:
                row.time_to_first_response_sec = int((now - base).total_seconds())
            await session.flush()
            snap = LeadSlaEngineV1._snap(row)
        await LeadSlaEngineV1._check_and_alert(snap)
        return snap

    @staticmethod
    async def on_closed(request_number: str) -> dict[str, Any] | None:
        async with get_session() as session:
            row = (
                await session.execute(
                    select(LeadSlaRecord).where(LeadSlaRecord.request_number == request_number)
                )
            ).scalar_one_or_none()
            if row is None:
                return None
            now = LeadSlaEngineV1._now()
            row.closed_at = now
            if row.created_at_lead:
                row.time_to_close_sec = int((now - row.created_at_lead).total_seconds())
            await session.flush()
            return LeadSlaEngineV1._snap(row)

    @staticmethod
    async def raise_priority(request_number: str, priority: str = "HIGH") -> None:
        async with get_session() as session:
            row = (
                await session.execute(
                    select(LeadSlaRecord).where(LeadSlaRecord.request_number == request_number)
                )
            ).scalar_one_or_none()
            if row is None:
                return
            row.priority = priority
            row.sla_breached = True
            await session.flush()

    @staticmethod
    async def _check_and_alert(snap: dict[str, Any]) -> None:
        breached = False
        reasons: list[str] = []
        tta = snap.get("time_to_assignment_sec")
        ttr = snap.get("time_to_first_response_sec")
        if tta is not None and tta > SLA_ASSIGNMENT_SEC:
            breached = True
            reasons.append(f"assignment {tta}s > {SLA_ASSIGNMENT_SEC}s")
        if ttr is not None and ttr > SLA_FIRST_RESPONSE_SEC:
            breached = True
            reasons.append(f"first_response {ttr}s > {SLA_FIRST_RESPONSE_SEC}s")

        if not breached:
            return

        await LeadSlaEngineV1.raise_priority(snap["request_number"], "HIGH")
        from services.pg_platform_audit_engine import PlatformAuditEngineV1
        from services.notification_center import NotificationCenterV1

        await PlatformAuditEngineV1.log(
            event_type="SLA_VIOLATION",
            entity_type="client_request",
            entity_id=snap["request_number"],
            payload={"reasons": reasons, **snap},
        )
        text = (
            f"⚠ SLA exceeded for {snap['request_number']}\n"
            + "\n".join(f"• {r}" for r in reasons)
        )
        await NotificationCenterV1.notify_managers_and_owner(text)

    @staticmethod
    def _snap(row: LeadSlaRecord) -> dict[str, Any]:
        return {
            "id": str(row.id),
            "client_request_id": str(row.client_request_id),
            "request_number": row.request_number,
            "time_to_assignment_sec": row.time_to_assignment_sec,
            "time_to_first_response_sec": row.time_to_first_response_sec,
            "time_to_close_sec": row.time_to_close_sec,
            "priority": row.priority,
            "sla_breached": row.sla_breached,
            "escalation_level": row.escalation_level,
        }
