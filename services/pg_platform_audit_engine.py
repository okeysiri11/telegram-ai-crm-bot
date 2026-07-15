# Platform audit engine — write to audit_log table.

from __future__ import annotations

import logging
import uuid
from typing import Any

from database.models.platform_audit_log import PlatformAuditEvent, PlatformAuditLog
from database.session import get_session

logger = logging.getLogger(__name__)


class PlatformAuditEngineV1:
    @staticmethod
    async def log(
        *,
        event_type: str,
        entity_type: str,
        entity_id: str | uuid.UUID,
        user_id: int | None = None,
        payload: dict[str, Any] | None = None,
    ) -> str | None:
        try:
            async with get_session() as session:
                row = PlatformAuditLog(
                    event_type=event_type,
                    entity_type=entity_type,
                    entity_id=str(entity_id),
                    user_id=user_id,
                    payload=payload or {},
                )
                session.add(row)
                await session.flush()
                return str(row.id)
        except Exception:
            logger.warning(
                "audit_log write failed event=%s entity=%s:%s",
                event_type,
                entity_type,
                entity_id,
                exc_info=True,
            )
            return None

    @staticmethod
    async def lead_created(entity_id: str, user_id: int | None = None, **payload: Any) -> None:
        await PlatformAuditEngineV1.log(
            event_type=PlatformAuditEvent.LEAD_CREATED.value,
            entity_type="client_request",
            entity_id=entity_id,
            user_id=user_id,
            payload=payload,
        )

    @staticmethod
    async def status_changed(entity_id: str, user_id: int | None = None, **payload: Any) -> None:
        await PlatformAuditEngineV1.log(
            event_type=PlatformAuditEvent.STATUS_CHANGED.value,
            entity_type="client_request",
            entity_id=entity_id,
            user_id=user_id,
            payload=payload,
        )

    @staticmethod
    async def manager_assigned(entity_id: str, user_id: int | None = None, **payload: Any) -> None:
        await PlatformAuditEngineV1.log(
            event_type=PlatformAuditEvent.MANAGER_ASSIGNED.value,
            entity_type="client_request",
            entity_id=entity_id,
            user_id=user_id,
            payload=payload,
        )

    @staticmethod
    async def ai_action(entity_id: str, user_id: int | None = None, **payload: Any) -> None:
        await PlatformAuditEngineV1.log(
            event_type=PlatformAuditEvent.AI_ACTION.value,
            entity_type="ai_manager",
            entity_id=entity_id,
            user_id=user_id,
            payload=payload,
        )
