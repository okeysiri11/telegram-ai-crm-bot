# Lead Automation Engine v1 repository.

from __future__ import annotations

import re
import uuid
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.lead_automation_engine import (
    AUTOMATION_LEAD_SOURCES,
    AUTOMATION_LEAD_STATUSES,
    OPEN_LEAD_STATUSES,
    AutomationLead,
    AutomationLeadStatus,
    LeadSourceEvent,
)


def normalize_phone(phone: str | None) -> str | None:
    if not phone:
        return None
    digits = re.sub(r"\D", "", phone.strip())
    return digits or None


def normalize_email(email: str | None) -> str | None:
    if not email:
        return None
    cleaned = email.strip().lower()
    return cleaned or None


class LeadAutomationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_lead(
        self,
        *,
        customer_name: str,
        source: str,
        phone: str | None = None,
        email: str | None = None,
        telegram_user_id: int | None = None,
        car_id: uuid.UUID | None = None,
        assigned_manager_id: int | None = None,
        score: int = 0,
        status: str = AutomationLeadStatus.NEW.value,
        is_duplicate: bool = False,
        duplicate_of_id: uuid.UUID | None = None,
        external_reference: str | None = None,
        budget: float | int | None = None,
        source_metadata: dict | None = None,
        scoring_factors: dict | None = None,
        notes: str | None = None,
        tenant_id: uuid.UUID | None = None,
        company_id: uuid.UUID | None = None,
        **extra: Any,
    ) -> AutomationLead:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")
        if source not in AUTOMATION_LEAD_SOURCES:
            raise ValueError(f"Invalid source: {source}")
        if status not in AUTOMATION_LEAD_STATUSES:
            raise ValueError(f"Invalid status: {status}")

        lead = AutomationLead(
            customer_name=customer_name.strip(),
            phone=phone,
            phone_normalized=normalize_phone(phone),
            email=email,
            email_normalized=normalize_email(email),
            telegram_user_id=telegram_user_id,
            source=source,
            car_id=car_id,
            assigned_manager_id=assigned_manager_id,
            score=max(0, min(100, score)),
            status=status,
            is_duplicate=is_duplicate,
            duplicate_of_id=duplicate_of_id,
            external_reference=external_reference,
            budget=budget,
            source_metadata=source_metadata or {},
            scoring_factors=scoring_factors or {},
            notes=notes,
            tenant_id=tenant_id,
            company_id=company_id,
        )
        self._session.add(lead)
        await self._session.flush()
        return lead

    async def get_by_id(self, lead_id: uuid.UUID) -> AutomationLead | None:
        result = await self._session.execute(
            select(AutomationLead).where(AutomationLead.id == lead_id)
        )
        return result.scalar_one_or_none()

    async def find_duplicate(
        self,
        *,
        phone: str | None = None,
        email: str | None = None,
        telegram_user_id: int | None = None,
        external_reference: str | None = None,
        source: str | None = None,
    ) -> AutomationLead | None:
        phone_norm = normalize_phone(phone)
        email_norm = normalize_email(email)

        if telegram_user_id is not None:
            result = await self._session.execute(
                select(AutomationLead)
                .where(
                    AutomationLead.telegram_user_id == telegram_user_id,
                    AutomationLead.is_duplicate.is_(False),
                )
                .order_by(AutomationLead.created_at.asc())
                .limit(1)
            )
            match = result.scalar_one_or_none()
            if match is not None:
                return match

        if phone_norm:
            result = await self._session.execute(
                select(AutomationLead)
                .where(
                    AutomationLead.phone_normalized == phone_norm,
                    AutomationLead.is_duplicate.is_(False),
                )
                .order_by(AutomationLead.created_at.asc())
                .limit(1)
            )
            match = result.scalar_one_or_none()
            if match is not None:
                return match

        if email_norm:
            result = await self._session.execute(
                select(AutomationLead)
                .where(
                    AutomationLead.email_normalized == email_norm,
                    AutomationLead.is_duplicate.is_(False),
                )
                .order_by(AutomationLead.created_at.asc())
                .limit(1)
            )
            match = result.scalar_one_or_none()
            if match is not None:
                return match

        if external_reference and source:
            result = await self._session.execute(
                select(AutomationLead)
                .where(
                    AutomationLead.external_reference == external_reference,
                    AutomationLead.source == source,
                    AutomationLead.is_duplicate.is_(False),
                )
                .order_by(AutomationLead.created_at.asc())
                .limit(1)
            )
            return result.scalar_one_or_none()

        return None

    async def list_leads(
        self,
        *,
        tenant_id: uuid.UUID | None = None,
        source: str | None = None,
        status: str | None = None,
        assigned_manager_id: int | None = None,
        min_score: int | None = None,
        limit: int = 50,
    ) -> list[AutomationLead]:
        query = select(AutomationLead).order_by(AutomationLead.created_at.desc())
        if tenant_id is not None:
            query = query.where(AutomationLead.tenant_id == tenant_id)
        if source is not None:
            query = query.where(AutomationLead.source == source)
        if status is not None:
            query = query.where(AutomationLead.status == status)
        if assigned_manager_id is not None:
            query = query.where(AutomationLead.assigned_manager_id == assigned_manager_id)
        if min_score is not None:
            query = query.where(AutomationLead.score >= min_score)
        query = query.limit(limit)
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def count_open_leads(self, manager_id: int) -> int:
        result = await self._session.execute(
            select(func.count())
            .select_from(AutomationLead)
            .where(
                AutomationLead.assigned_manager_id == manager_id,
                AutomationLead.status.in_(OPEN_LEAD_STATUSES),
                AutomationLead.is_duplicate.is_(False),
            )
        )
        return int(result.scalar_one())

    async def create_source_event(
        self,
        *,
        lead_id: uuid.UUID,
        source: str,
        event_type: str,
        payload: dict | None = None,
    ) -> LeadSourceEvent:
        if source not in AUTOMATION_LEAD_SOURCES:
            raise ValueError(f"Invalid source: {source}")

        event = LeadSourceEvent(
            lead_id=lead_id,
            source=source,
            event_type=event_type,
            payload=payload or {},
        )
        self._session.add(event)
        await self._session.flush()
        return event

    async def list_source_events(
        self,
        lead_id: uuid.UUID,
        *,
        limit: int = 50,
    ) -> list[LeadSourceEvent]:
        result = await self._session.execute(
            select(LeadSourceEvent)
            .where(LeadSourceEvent.lead_id == lead_id)
            .order_by(LeadSourceEvent.created_at.asc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def source_stats(self) -> dict[str, int]:
        stats: dict[str, int] = {}
        for source in AUTOMATION_LEAD_SOURCES:
            result = await self._session.execute(
                select(func.count())
                .select_from(AutomationLead)
                .where(
                    AutomationLead.source == source,
                    AutomationLead.is_duplicate.is_(False),
                )
            )
            stats[source] = int(result.scalar_one())
        return stats

    @staticmethod
    def snapshot(lead: AutomationLead) -> dict[str, Any]:
        return {
            "id": str(lead.id),
            "customer_name": lead.customer_name,
            "phone": lead.phone,
            "email": lead.email,
            "telegram_user_id": lead.telegram_user_id,
            "source": lead.source,
            "car_id": str(lead.car_id) if lead.car_id else None,
            "assigned_manager_id": lead.assigned_manager_id,
            "score": lead.score,
            "status": lead.status,
            "is_duplicate": lead.is_duplicate,
            "duplicate_of_id": str(lead.duplicate_of_id) if lead.duplicate_of_id else None,
            "external_reference": lead.external_reference,
            "budget": str(lead.budget) if lead.budget is not None else None,
            "source_metadata": lead.source_metadata or {},
            "scoring_factors": lead.scoring_factors or {},
            "notes": lead.notes,
            "created_at": lead.created_at.isoformat(),
            "updated_at": lead.updated_at.isoformat(),
        }

    @staticmethod
    def event_snapshot(event: LeadSourceEvent) -> dict[str, Any]:
        return {
            "id": str(event.id),
            "lead_id": str(event.lead_id),
            "source": event.source,
            "event_type": event.event_type,
            "payload": event.payload or {},
            "created_at": event.created_at.isoformat(),
        }
