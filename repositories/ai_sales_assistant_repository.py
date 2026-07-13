# AI Sales Assistant v1 repository.

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.ai_sales_assistant import (
    SALES_HANDOFF_STATUSES,
    SALES_MEETING_STATUSES,
    SALES_MESSAGE_ROLES,
    SALES_SESSION_STATUSES,
    SalesAssistantHandoff,
    SalesAssistantMeeting,
    SalesAssistantMessage,
    SalesAssistantSession,
    SalesHandoffStatus,
    SalesMeetingStatus,
    SalesSessionStatus,
)


class SalesAssistantRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_or_create_session(
        self,
        *,
        telegram_user_id: int,
        lead_id: uuid.UUID | None = None,
    ) -> SalesAssistantSession:
        result = await self._session.execute(
            select(SalesAssistantSession)
            .where(
                SalesAssistantSession.telegram_user_id == telegram_user_id,
                SalesAssistantSession.status.not_in([
                    SalesSessionStatus.CLOSED.value,
                    SalesSessionStatus.TRANSFERRED.value,
                ]),
            )
            .order_by(SalesAssistantSession.created_at.desc())
            .limit(1)
        )
        existing = result.scalar_one_or_none()
        if existing is not None:
            if lead_id is not None and existing.lead_id is None:
                existing.lead_id = lead_id
                await self._session.flush()
            return existing

        session = SalesAssistantSession(
            telegram_user_id=telegram_user_id,
            lead_id=lead_id,
            status=SalesSessionStatus.ACTIVE.value,
            contact_data={},
            context={},
        )
        self._session.add(session)
        await self._session.flush()
        return session

    async def get_session(self, session_id: uuid.UUID) -> SalesAssistantSession | None:
        result = await self._session.execute(
            select(SalesAssistantSession).where(SalesAssistantSession.id == session_id)
        )
        return result.scalar_one_or_none()

    async def update_session(
        self,
        session: SalesAssistantSession,
        **fields: Any,
    ) -> SalesAssistantSession:
        allowed = {
            "lead_id",
            "car_id",
            "status",
            "contact_data",
            "financing_data",
            "scheduling_data",
            "context",
            "assigned_manager_id",
            "last_intent",
            "message_count",
        }
        unknown = set(fields) - allowed
        if unknown:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(unknown))}")
        for key, value in fields.items():
            setattr(session, key, value)
        await self._session.flush()
        return session

    async def add_message(
        self,
        *,
        session_id: uuid.UUID,
        role: str,
        content: str,
        intent: str | None = None,
        metadata: dict | None = None,
    ) -> SalesAssistantMessage:
        if role not in SALES_MESSAGE_ROLES:
            raise ValueError(f"Invalid role: {role}")

        message = SalesAssistantMessage(
            session_id=session_id,
            role=role,
            content=content,
            intent=intent,
            metadata_=metadata,
        )
        self._session.add(message)
        await self._session.flush()
        return message

    async def list_messages(
        self,
        session_id: uuid.UUID,
        *,
        limit: int = 30,
    ) -> list[SalesAssistantMessage]:
        result = await self._session.execute(
            select(SalesAssistantMessage)
            .where(SalesAssistantMessage.session_id == session_id)
            .order_by(SalesAssistantMessage.created_at.asc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def create_meeting(
        self,
        *,
        session_id: uuid.UUID,
        scheduled_at: datetime,
        title: str,
        notes: str | None = None,
        calendar_event_id: int | None = None,
        status: str = SalesMeetingStatus.SCHEDULED.value,
    ) -> SalesAssistantMeeting:
        if status not in SALES_MEETING_STATUSES:
            raise ValueError(f"Invalid status: {status}")

        meeting = SalesAssistantMeeting(
            session_id=session_id,
            scheduled_at=scheduled_at,
            title=title,
            notes=notes,
            calendar_event_id=calendar_event_id,
            status=status,
        )
        self._session.add(meeting)
        await self._session.flush()
        return meeting

    async def create_handoff(
        self,
        *,
        session_id: uuid.UUID,
        manager_id: int,
        reason: str | None = None,
        status: str = SalesHandoffStatus.PENDING.value,
    ) -> SalesAssistantHandoff:
        if status not in SALES_HANDOFF_STATUSES:
            raise ValueError(f"Invalid status: {status}")

        handoff = SalesAssistantHandoff(
            session_id=session_id,
            manager_id=manager_id,
            reason=reason,
            status=status,
            transferred_at=datetime.now(timezone.utc),
        )
        self._session.add(handoff)
        await self._session.flush()
        return handoff

    @staticmethod
    def session_snapshot(session: SalesAssistantSession) -> dict[str, Any]:
        return {
            "id": str(session.id),
            "telegram_user_id": session.telegram_user_id,
            "lead_id": str(session.lead_id) if session.lead_id else None,
            "car_id": str(session.car_id) if session.car_id else None,
            "status": session.status,
            "contact_data": session.contact_data or {},
            "financing_data": session.financing_data or {},
            "scheduling_data": session.scheduling_data or {},
            "context": session.context or {},
            "assigned_manager_id": session.assigned_manager_id,
            "last_intent": session.last_intent,
            "message_count": session.message_count,
            "created_at": session.created_at.isoformat(),
            "updated_at": session.updated_at.isoformat(),
        }
