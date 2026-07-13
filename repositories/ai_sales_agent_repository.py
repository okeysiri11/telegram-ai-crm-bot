# AI Sales Agent v1 repositories.

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.ai_sales_agent import (
    SALES_CONVERSATION_DIRECTIONS,
    SALES_LEAD_SOURCES,
    SALES_LEAD_STATUSES,
    SALES_OFFER_STATUSES,
    CustomerPreference,
    SalesConversation,
    SalesConversationDirection,
    SalesLead,
    SalesLeadSource,
    SalesLeadStatus,
    SalesOffer,
    SalesOfferStatus,
)


class SalesAgentLeadRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        tenant_id: uuid.UUID,
        company_id: uuid.UUID,
        source: str = SalesLeadSource.MANUAL.value,
        status: str = SalesLeadStatus.NEW.value,
        customer_name: str | None = None,
        customer_phone: str | None = None,
        customer_email: str | None = None,
        automation_lead_id: uuid.UUID | None = None,
        marketplace_listing_id: uuid.UUID | None = None,
        assigned_manager_id: int | None = None,
        intent: str | None = None,
        budget_min: Decimal | None = None,
        budget_max: Decimal | None = None,
        currency: str = "USD",
        notes: str | None = None,
        next_follow_up_at: datetime | None = None,
        created_by: int | None = None,
        metadata: dict | None = None,
        **extra: Any,
    ) -> SalesLead:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")
        if source not in SALES_LEAD_SOURCES:
            raise ValueError(f"Invalid source: {source}")
        if status not in SALES_LEAD_STATUSES:
            raise ValueError(f"Invalid status: {status}")

        row = SalesLead(
            tenant_id=tenant_id,
            company_id=company_id,
            source=source,
            status=status,
            customer_name=customer_name,
            customer_phone=customer_phone,
            customer_email=customer_email,
            automation_lead_id=automation_lead_id,
            marketplace_listing_id=marketplace_listing_id,
            assigned_manager_id=assigned_manager_id,
            intent=intent,
            budget_min=budget_min,
            budget_max=budget_max,
            currency=currency,
            notes=notes,
            next_follow_up_at=next_follow_up_at,
            created_by=created_by,
            metadata_=metadata,
        )
        self._session.add(row)
        await self._session.flush()
        return row

    async def get_by_id(self, lead_id: uuid.UUID) -> SalesLead | None:
        result = await self._session.execute(
            select(SalesLead).where(SalesLead.id == lead_id)
        )
        return result.scalar_one_or_none()

    async def list_by_tenant(
        self,
        tenant_id: uuid.UUID,
        *,
        status: str | None = None,
        limit: int = 100,
    ) -> list[SalesLead]:
        stmt = (
            select(SalesLead)
            .where(SalesLead.tenant_id == tenant_id)
            .order_by(SalesLead.created_at.desc())
            .limit(limit)
        )
        if status is not None:
            stmt = stmt.where(SalesLead.status == status)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def list_due_for_follow_up(
        self,
        tenant_id: uuid.UUID,
        *,
        before: datetime,
        limit: int = 100,
    ) -> list[SalesLead]:
        active_statuses = {
            SalesLeadStatus.NEW.value,
            SalesLeadStatus.QUALIFIED.value,
            SalesLeadStatus.NEGOTIATION.value,
            SalesLeadStatus.OFFER_SENT.value,
            SalesLeadStatus.WAITING_CUSTOMER.value,
        }
        result = await self._session.execute(
            select(SalesLead)
            .where(
                SalesLead.tenant_id == tenant_id,
                SalesLead.status.in_(active_statuses),
                SalesLead.next_follow_up_at.is_not(None),
                SalesLead.next_follow_up_at <= before,
            )
            .order_by(SalesLead.next_follow_up_at.asc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def update_fields(self, lead_id: uuid.UUID, **fields: Any) -> SalesLead | None:
        row = await self.get_by_id(lead_id)
        if row is None:
            return None
        allowed = {
            "status",
            "intent",
            "qualification_score",
            "budget_min",
            "budget_max",
            "recommended_car_id",
            "assigned_manager_id",
            "last_contact_at",
            "next_follow_up_at",
            "notes",
            "metadata_",
            "customer_name",
            "customer_phone",
            "customer_email",
        }
        for key, value in fields.items():
            attr = "metadata_" if key == "metadata" else key
            if attr not in allowed:
                raise TypeError(f"Unsupported field: {key}")
            setattr(row, attr, value)
        await self._session.flush()
        return row


class SalesAgentConversationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        sales_lead_id: uuid.UUID,
        tenant_id: uuid.UUID,
        company_id: uuid.UUID,
        channel: str,
        message_text: str,
        direction: str = SalesConversationDirection.INBOUND.value,
        intent_detected: str | None = None,
        sentiment: str | None = None,
        ai_summary: str | None = None,
        created_by: int | None = None,
        **extra: Any,
    ) -> SalesConversation:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")
        if direction not in SALES_CONVERSATION_DIRECTIONS:
            raise ValueError(f"Invalid direction: {direction}")

        row = SalesConversation(
            sales_lead_id=sales_lead_id,
            tenant_id=tenant_id,
            company_id=company_id,
            channel=channel,
            message_text=message_text.strip(),
            direction=direction,
            intent_detected=intent_detected,
            sentiment=sentiment,
            ai_summary=ai_summary,
            created_by=created_by,
        )
        self._session.add(row)
        await self._session.flush()
        return row

    async def list_by_lead(
        self,
        sales_lead_id: uuid.UUID,
        *,
        limit: int = 50,
    ) -> list[SalesConversation]:
        result = await self._session.execute(
            select(SalesConversation)
            .where(SalesConversation.sales_lead_id == sales_lead_id)
            .order_by(SalesConversation.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())


class SalesAgentOfferRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        sales_lead_id: uuid.UUID,
        tenant_id: uuid.UUID,
        company_id: uuid.UUID,
        car_id: uuid.UUID,
        offer_price: Decimal,
        discount_amount: Decimal = Decimal("0"),
        currency: str = "USD",
        status: str = SalesOfferStatus.DRAFT.value,
        document_id: uuid.UUID | None = None,
        valid_until: datetime | None = None,
        terms: dict | None = None,
        notes: str | None = None,
        created_by: int | None = None,
        **extra: Any,
    ) -> SalesOffer:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")
        if status not in SALES_OFFER_STATUSES:
            raise ValueError(f"Invalid status: {status}")

        row = SalesOffer(
            sales_lead_id=sales_lead_id,
            tenant_id=tenant_id,
            company_id=company_id,
            car_id=car_id,
            offer_price=offer_price,
            discount_amount=discount_amount,
            currency=currency,
            status=status,
            document_id=document_id,
            valid_until=valid_until,
            terms=terms,
            notes=notes,
            created_by=created_by,
        )
        self._session.add(row)
        await self._session.flush()
        return row

    async def get_by_id(self, offer_id: uuid.UUID) -> SalesOffer | None:
        result = await self._session.execute(
            select(SalesOffer).where(SalesOffer.id == offer_id)
        )
        return result.scalar_one_or_none()

    async def list_by_lead(
        self,
        sales_lead_id: uuid.UUID,
        *,
        limit: int = 20,
    ) -> list[SalesOffer]:
        result = await self._session.execute(
            select(SalesOffer)
            .where(SalesOffer.sales_lead_id == sales_lead_id)
            .order_by(SalesOffer.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def update_fields(self, offer_id: uuid.UUID, **fields: Any) -> SalesOffer | None:
        row = await self.get_by_id(offer_id)
        if row is None:
            return None
        allowed = {"status", "document_id", "valid_until", "terms", "notes"}
        for key, value in fields.items():
            if key not in allowed:
                raise TypeError(f"Unsupported field: {key}")
            setattr(row, key, value)
        await self._session.flush()
        return row


class SalesAgentCustomerPreferenceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert(
        self,
        *,
        sales_lead_id: uuid.UUID,
        tenant_id: uuid.UUID,
        preferred_makes: list[str] | None = None,
        preferred_models: list[str] | None = None,
        body_types: list[str] | None = None,
        min_year: int | None = None,
        max_year: int | None = None,
        max_mileage: int | None = None,
        budget_min: Decimal | None = None,
        budget_max: Decimal | None = None,
        fuel_type: str | None = None,
        transmission: str | None = None,
        notes: str | None = None,
        metadata: dict | None = None,
        **extra: Any,
    ) -> CustomerPreference:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")

        result = await self._session.execute(
            select(CustomerPreference).where(CustomerPreference.sales_lead_id == sales_lead_id)
        )
        row = result.scalar_one_or_none()
        if row is None:
            row = CustomerPreference(
                sales_lead_id=sales_lead_id,
                tenant_id=tenant_id,
                preferred_makes=preferred_makes,
                preferred_models=preferred_models,
                body_types=body_types,
                min_year=min_year,
                max_year=max_year,
                max_mileage=max_mileage,
                budget_min=budget_min,
                budget_max=budget_max,
                fuel_type=fuel_type,
                transmission=transmission,
                notes=notes,
                metadata_=metadata,
            )
            self._session.add(row)
        else:
            updates = {
                "preferred_makes": preferred_makes,
                "preferred_models": preferred_models,
                "body_types": body_types,
                "min_year": min_year,
                "max_year": max_year,
                "max_mileage": max_mileage,
                "budget_min": budget_min,
                "budget_max": budget_max,
                "fuel_type": fuel_type,
                "transmission": transmission,
                "notes": notes,
                "metadata_": metadata,
            }
            for key, value in updates.items():
                if value is not None:
                    setattr(row, key, value)
        await self._session.flush()
        return row

    async def get_by_lead(self, sales_lead_id: uuid.UUID) -> CustomerPreference | None:
        result = await self._session.execute(
            select(CustomerPreference).where(CustomerPreference.sales_lead_id == sales_lead_id)
        )
        return result.scalar_one_or_none()
