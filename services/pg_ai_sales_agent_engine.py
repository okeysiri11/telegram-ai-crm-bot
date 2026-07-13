# AI Sales Agent v1 — lead qualification, intent, budget, recommendations, offers, follow-ups.

from __future__ import annotations

import re
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from config import OWNER_ID
from database.models.ai_sales_agent import (
    SalesConversationDirection,
    SalesLeadSource,
    SalesLeadStatus,
    SalesOfferStatus,
)
from database.models.audit_log import AuditAction
from database.models.car import CarStatus
from database.models.notification import NotificationChannel, NotificationType
from database.session import get_session
from repositories.ai_sales_agent_repository import (
    SalesAgentConversationRepository,
    SalesAgentCustomerPreferenceRepository,
    SalesAgentLeadRepository,
    SalesAgentOfferRepository,
)
from repositories.audit_repository import AuditRepository
from repositories.notification_repository import NotificationRepository
from repositories.user_role_repository import UserRoleRepository
from services.pg_car_engine import CarEngineV1
from services.pg_dealer_portal_engine import DealerPortalEngineV1
from services.pg_document_engine import DocumentEngineV1
from services.pg_lead_marketplace_engine import LeadMarketplaceEngineV1
from services.pg_partner_tenant_engine import PartnerTenantEngineV1

SALES_AGENT_ROLES = frozenset({"OWNER", "ADMIN", "MANAGER"})
MODEL_VERSION = "ai-sales-agent-v1.0.0"
MONEY = Decimal("0.01")
QUALIFICATION_THRESHOLD = 60
FOLLOW_UP_INTERVAL_DAYS = 3

INTENT_KEYWORDS: dict[str, tuple[str, ...]] = {
    "PURCHASE": (
        "buy", "purchase", "price", "available", "inventory", "interested",
        "купить", "цена", "стоимость", "интересует", "available",
    ),
    "FINANCING": (
        "finance", "loan", "credit", "payment", "down payment", "monthly",
        "кредит", "финанс", "рассроч", "платеж", "взнос",
    ),
    "TRADE_IN": (
        "trade", "trade-in", "exchange", "swap", "обмен", "trade in",
    ),
    "TEST_DRIVE": (
        "test drive", "test-drive", "visit", "see the car", "appointment",
        "тест-драйв", "приехать", "встреч", "запис",
    ),
    "NEGOTIATION": (
        "discount", "deal", "offer", "negotiate", "lower", "best price",
        "скидк", "торг", "предложен", "дешевле",
    ),
    "LOST_INTEREST": (
        "not interested", "cancel", "pass", "too expensive", "changed mind",
        "не интерес", "отказ", "дорого", "передумал",
    ),
}


class AiSalesAgentError(Exception):
    pass


class AiSalesAgentV1:
    @staticmethod
    async def user_can_access(user_id: int) -> bool:
        if user_id == OWNER_ID:
            return True
        async with get_session() as session:
            roles = await UserRoleRepository(session).get_user_roles(user_id)
            return any(role.code in SALES_AGENT_ROLES for role in roles)

    @staticmethod
    async def _require_access(actor_id: int, tenant_id: uuid.UUID):
        if not await AiSalesAgentV1.user_can_access(actor_id):
            raise AiSalesAgentError("Sales agent access denied")
        return await PartnerTenantEngineV1.resolve_context(actor_id, tenant_id)

    @staticmethod
    def _quantize(amount: Decimal) -> Decimal:
        return amount.quantize(MONEY, rounding=ROUND_HALF_UP)

    @staticmethod
    def _lead_snapshot(row) -> dict[str, Any]:
        return {
            "id": str(row.id),
            "tenant_id": str(row.tenant_id),
            "company_id": str(row.company_id),
            "automation_lead_id": (
                str(row.automation_lead_id) if row.automation_lead_id else None
            ),
            "marketplace_listing_id": (
                str(row.marketplace_listing_id) if row.marketplace_listing_id else None
            ),
            "recommended_car_id": (
                str(row.recommended_car_id) if row.recommended_car_id else None
            ),
            "customer_name": row.customer_name,
            "customer_phone": row.customer_phone,
            "customer_email": row.customer_email,
            "source": row.source,
            "status": row.status,
            "intent": row.intent,
            "qualification_score": row.qualification_score,
            "budget_min": str(row.budget_min) if row.budget_min is not None else None,
            "budget_max": str(row.budget_max) if row.budget_max is not None else None,
            "currency": row.currency,
            "assigned_manager_id": row.assigned_manager_id,
            "last_contact_at": (
                row.last_contact_at.isoformat() if row.last_contact_at else None
            ),
            "next_follow_up_at": (
                row.next_follow_up_at.isoformat() if row.next_follow_up_at else None
            ),
            "notes": row.notes,
            "metadata": row.metadata_ or {},
            "created_by": row.created_by,
            "created_at": row.created_at.isoformat(),
        }

    @staticmethod
    def _conversation_snapshot(row) -> dict[str, Any]:
        return {
            "id": str(row.id),
            "sales_lead_id": str(row.sales_lead_id),
            "channel": row.channel,
            "direction": row.direction,
            "message_text": row.message_text,
            "intent_detected": row.intent_detected,
            "sentiment": row.sentiment,
            "ai_summary": row.ai_summary,
            "created_by": row.created_by,
            "created_at": row.created_at.isoformat(),
        }

    @staticmethod
    def _offer_snapshot(row) -> dict[str, Any]:
        return {
            "id": str(row.id),
            "sales_lead_id": str(row.sales_lead_id),
            "car_id": str(row.car_id),
            "document_id": str(row.document_id) if row.document_id else None,
            "offer_price": str(row.offer_price),
            "discount_amount": str(row.discount_amount),
            "currency": row.currency,
            "status": row.status,
            "valid_until": row.valid_until.isoformat() if row.valid_until else None,
            "terms": row.terms or {},
            "notes": row.notes,
            "created_by": row.created_by,
            "created_at": row.created_at.isoformat(),
        }

    @staticmethod
    def _preference_snapshot(row) -> dict[str, Any]:
        return {
            "sales_lead_id": str(row.sales_lead_id),
            "preferred_makes": row.preferred_makes or [],
            "preferred_models": row.preferred_models or [],
            "body_types": row.body_types or [],
            "min_year": row.min_year,
            "max_year": row.max_year,
            "max_mileage": row.max_mileage,
            "budget_min": str(row.budget_min) if row.budget_min is not None else None,
            "budget_max": str(row.budget_max) if row.budget_max is not None else None,
            "fuel_type": row.fuel_type,
            "transmission": row.transmission,
            "notes": row.notes,
            "metadata": row.metadata_ or {},
        }

    @staticmethod
    async def _get_lead_or_raise(session, lead_id: uuid.UUID, tenant_id: uuid.UUID):
        row = await SalesAgentLeadRepository(session).get_by_id(lead_id)
        if row is None or row.tenant_id != tenant_id:
            raise AiSalesAgentError(f"Sales lead not found: {lead_id}")
        return row

    @staticmethod
    def detect_intent_from_text(text: str) -> str:
        lowered = text.lower()
        scores: dict[str, int] = {intent: 0 for intent in INTENT_KEYWORDS}
        for intent, keywords in INTENT_KEYWORDS.items():
            for keyword in keywords:
                if keyword in lowered:
                    scores[intent] += 1
        best = max(scores, key=scores.get)
        if scores[best] > 0:
            return best
        return "GENERAL"

    @staticmethod
    def _parse_budget_from_text(text: str) -> tuple[Decimal | None, Decimal | None]:
        lowered = text.lower().replace(",", "")
        amounts: list[Decimal] = []
        for match in re.finditer(r"\$?\s*(\d+(?:\.\d+)?)\s*k?", lowered):
            raw = match.group(1)
            value = Decimal(raw)
            if "k" in match.group(0) and value < Decimal("1000"):
                value *= Decimal("1000")
            if value >= Decimal("3000"):
                amounts.append(value)
        if not amounts:
            return None, None
        if len(amounts) == 1:
            center = amounts[0]
            return AiSalesAgentV1._quantize(center * Decimal("0.85")), AiSalesAgentV1._quantize(
                center * Decimal("1.15")
            )
        return AiSalesAgentV1._quantize(min(amounts)), AiSalesAgentV1._quantize(max(amounts))

    @staticmethod
    def _score_lead(lead, prefs, conversation_count: int) -> int:
        score = 0
        if lead.customer_name:
            score += 10
        if lead.customer_phone or lead.customer_email:
            score += 20
        if lead.budget_min or lead.budget_max or (prefs and (prefs.budget_min or prefs.budget_max)):
            score += 20
        if prefs and (prefs.preferred_makes or prefs.preferred_models):
            score += 15
        if lead.intent and lead.intent not in {"GENERAL", "LOST_INTEREST"}:
            score += 15
        score += min(20, conversation_count * 5)
        if lead.status == SalesLeadStatus.QUALIFIED.value:
            score += 10
        return min(100, score)

    @staticmethod
    async def create_lead(
        actor_id: int,
        tenant_id: uuid.UUID,
        *,
        customer_name: str | None = None,
        customer_phone: str | None = None,
        customer_email: str | None = None,
        source: str = SalesLeadSource.MANUAL.value,
        automation_lead_id: uuid.UUID | None = None,
        marketplace_listing_id: uuid.UUID | None = None,
        assigned_manager_id: int | None = None,
        notes: str | None = None,
    ) -> dict[str, Any]:
        ctx = await AiSalesAgentV1._require_access(actor_id, tenant_id)
        now = datetime.now(timezone.utc)
        async with get_session() as session:
            row = await SalesAgentLeadRepository(session).create(
                tenant_id=tenant_id,
                company_id=ctx.company_id,
                customer_name=customer_name,
                customer_phone=customer_phone,
                customer_email=customer_email,
                source=source,
                automation_lead_id=automation_lead_id,
                marketplace_listing_id=marketplace_listing_id,
                assigned_manager_id=assigned_manager_id,
                notes=notes,
                next_follow_up_at=now + timedelta(days=FOLLOW_UP_INTERVAL_DAYS),
                created_by=actor_id,
            )
            await AuditRepository(session).create_log(
                user_id=actor_id,
                company_id=ctx.company_id,
                tenant_id=tenant_id,
                entity_type="ai_sales_lead",
                entity_id=str(row.id),
                action=AuditAction.CREATE.value,
                new_value={"source": source, "status": row.status},
            )
            await session.refresh(row)
            return AiSalesAgentV1._lead_snapshot(row)

    @staticmethod
    async def qualify_lead(
        actor_id: int,
        tenant_id: uuid.UUID,
        lead_id: uuid.UUID,
    ) -> dict[str, Any]:
        ctx = await AiSalesAgentV1._require_access(actor_id, tenant_id)
        async with get_session() as session:
            lead = await AiSalesAgentV1._get_lead_or_raise(session, lead_id, tenant_id)
            prefs = await SalesAgentCustomerPreferenceRepository(session).get_by_lead(lead_id)
            conversations = await SalesAgentConversationRepository(session).list_by_lead(lead_id)
            score = AiSalesAgentV1._score_lead(lead, prefs, len(conversations))

            new_status = lead.status
            if score >= QUALIFICATION_THRESHOLD and lead.status == SalesLeadStatus.NEW.value:
                new_status = SalesLeadStatus.QUALIFIED.value
            elif lead.status == SalesLeadStatus.NEW.value and score >= 40:
                new_status = SalesLeadStatus.QUALIFIED.value

            updated = await SalesAgentLeadRepository(session).update_fields(
                lead_id,
                qualification_score=score,
                status=new_status,
            )
            await AuditRepository(session).create_log(
                user_id=actor_id,
                company_id=ctx.company_id,
                tenant_id=tenant_id,
                entity_type="ai_sales_lead",
                entity_id=str(lead_id),
                action=AuditAction.UPDATE.value,
                new_value={"qualification_score": score, "status": new_status},
            )
            await session.refresh(updated)
            return {
                "lead": AiSalesAgentV1._lead_snapshot(updated),
                "qualification": {
                    "score": score,
                    "threshold": QUALIFICATION_THRESHOLD,
                    "qualified": score >= QUALIFICATION_THRESHOLD,
                    "factors": {
                        "has_contact": bool(lead.customer_phone or lead.customer_email),
                        "has_budget": bool(lead.budget_min or lead.budget_max),
                        "conversation_count": len(conversations),
                        "intent": lead.intent,
                    },
                },
            }

    @staticmethod
    async def detect_customer_intent(
        actor_id: int,
        tenant_id: uuid.UUID,
        lead_id: uuid.UUID,
        *,
        message_text: str,
        channel: str = "TELEGRAM",
        direction: str = SalesConversationDirection.INBOUND.value,
    ) -> dict[str, Any]:
        ctx = await AiSalesAgentV1._require_access(actor_id, tenant_id)
        intent = AiSalesAgentV1.detect_intent_from_text(message_text)
        sentiment = "negative" if intent == "LOST_INTEREST" else "positive" if intent == "PURCHASE" else "neutral"
        now = datetime.now(timezone.utc)

        async with get_session() as session:
            lead = await AiSalesAgentV1._get_lead_or_raise(session, lead_id, tenant_id)
            conversation = await SalesAgentConversationRepository(session).create(
                sales_lead_id=lead_id,
                tenant_id=tenant_id,
                company_id=ctx.company_id,
                channel=channel,
                message_text=message_text,
                direction=direction,
                intent_detected=intent,
                sentiment=sentiment,
                ai_summary=f"Detected intent: {intent}",
                created_by=actor_id,
            )

            new_status = lead.status
            if intent == "LOST_INTEREST":
                new_status = SalesLeadStatus.LOST.value
            elif intent == "NEGOTIATION" and lead.status in {
                SalesLeadStatus.QUALIFIED.value,
                SalesLeadStatus.WAITING_CUSTOMER.value,
            }:
                new_status = SalesLeadStatus.NEGOTIATION.value

            await SalesAgentLeadRepository(session).update_fields(
                lead_id,
                intent=intent,
                status=new_status,
                last_contact_at=now,
                next_follow_up_at=now + timedelta(days=FOLLOW_UP_INTERVAL_DAYS),
            )
            await session.refresh(conversation)
            refreshed_lead = await SalesAgentLeadRepository(session).get_by_id(lead_id)
            return {
                "lead": AiSalesAgentV1._lead_snapshot(refreshed_lead),
                "conversation": AiSalesAgentV1._conversation_snapshot(conversation),
                "intent": intent,
                "sentiment": sentiment,
            }

    @staticmethod
    async def estimate_budget(
        actor_id: int,
        tenant_id: uuid.UUID,
        lead_id: uuid.UUID,
        *,
        message_text: str | None = None,
    ) -> dict[str, Any]:
        await AiSalesAgentV1._require_access(actor_id, tenant_id)
        async with get_session() as session:
            lead = await AiSalesAgentV1._get_lead_or_raise(session, lead_id, tenant_id)
            prefs = await SalesAgentCustomerPreferenceRepository(session).get_by_lead(lead_id)

            budget_min = lead.budget_min
            budget_max = lead.budget_max
            source = "existing"

            if message_text:
                parsed_min, parsed_max = AiSalesAgentV1._parse_budget_from_text(message_text)
                if parsed_min and parsed_max:
                    budget_min = parsed_min
                    budget_max = parsed_max
                    source = "conversation"
            elif prefs and prefs.budget_min and prefs.budget_max:
                budget_min = prefs.budget_min
                budget_max = prefs.budget_max
                source = "preferences"
            elif not budget_min and not budget_max:
                budget_min = Decimal("15000")
                budget_max = Decimal("35000")
                source = "default_market_range"

            budget_min = AiSalesAgentV1._quantize(budget_min or Decimal("15000"))
            budget_max = AiSalesAgentV1._quantize(budget_max or Decimal("35000"))

            await SalesAgentLeadRepository(session).update_fields(
                lead_id,
                budget_min=budget_min,
                budget_max=budget_max,
            )
            await SalesAgentCustomerPreferenceRepository(session).upsert(
                sales_lead_id=lead_id,
                tenant_id=tenant_id,
                budget_min=budget_min,
                budget_max=budget_max,
            )
            refreshed = await SalesAgentLeadRepository(session).get_by_id(lead_id)
            return {
                "lead_id": str(lead_id),
                "budget_min": str(budget_min),
                "budget_max": str(budget_max),
                "currency": lead.currency,
                "source": source,
                "lead": AiSalesAgentV1._lead_snapshot(refreshed),
            }

    @staticmethod
    async def recommend_vehicles(
        actor_id: int,
        tenant_id: uuid.UUID,
        lead_id: uuid.UUID,
        *,
        limit: int = 5,
    ) -> dict[str, Any]:
        await AiSalesAgentV1._require_access(actor_id, tenant_id)
        async with get_session() as session:
            lead = await AiSalesAgentV1._get_lead_or_raise(session, lead_id, tenant_id)
            prefs = await SalesAgentCustomerPreferenceRepository(session).get_by_lead(lead_id)

        cars = await CarEngineV1.list_cars(
            actor_id,
            status=CarStatus.READY_FOR_SALE.value,
            limit=100,
        )
        budget_min = lead.budget_min or (prefs.budget_min if prefs else None)
        budget_max = lead.budget_max or (prefs.budget_max if prefs else None)
        preferred_makes = set(m.lower() for m in (prefs.preferred_makes or []) if prefs)
        preferred_models = set(m.lower() for m in (prefs.preferred_models or []) if prefs)

        scored: list[tuple[int, dict[str, Any]]] = []
        for car in cars:
            price = Decimal(str(car.get("sale_price") or car.get("total_cost") or "0"))
            if price <= 0:
                continue
            if budget_max and price > budget_max * Decimal("1.1"):
                continue
            if budget_min and price < budget_min * Decimal("0.7"):
                continue

            score = 50
            make = (car.get("make") or "").lower()
            model = (car.get("model") or "").lower()
            if preferred_makes and make in preferred_makes:
                score += 25
            if preferred_models and any(pm in model for pm in preferred_models):
                score += 20
            if budget_min and budget_max:
                mid = (budget_min + budget_max) / 2
                delta = abs(price - mid) / mid if mid > 0 else Decimal("1")
                score += max(0, 15 - int(delta * 20))
            scored.append((score, car))

        scored.sort(key=lambda item: item[0], reverse=True)
        recommendations = [
            {"match_score": score, **car}
            for score, car in scored[:limit]
        ]

        top_car_id = None
        if recommendations:
            top_car_id = uuid.UUID(recommendations[0]["id"])
            async with get_session() as session:
                await SalesAgentLeadRepository(session).update_fields(
                    lead_id,
                    recommended_car_id=top_car_id,
                )

        return {
            "lead_id": str(lead_id),
            "recommendations": recommendations,
            "count": len(recommendations),
            "top_recommendation_id": str(top_car_id) if top_car_id else None,
            "integration": "car_engine",
        }

    @staticmethod
    async def generate_offer(
        actor_id: int,
        tenant_id: uuid.UUID,
        lead_id: uuid.UUID,
        car_id: uuid.UUID,
        *,
        discount_amount: Decimal | float | int = 0,
        valid_days: int = 7,
        generate_contract: bool = True,
        buyer_name: str | None = None,
    ) -> dict[str, Any]:
        ctx = await AiSalesAgentV1._require_access(actor_id, tenant_id)
        async with get_session() as session:
            lead = await AiSalesAgentV1._get_lead_or_raise(session, lead_id, tenant_id)
            car = await CarEngineV1.get_car(actor_id, car_id)
            list_price = Decimal(str(car.get("sale_price") or car.get("total_cost") or "0"))
            if list_price <= 0:
                raise AiSalesAgentError("Vehicle has no list price for offer generation")

            discount = AiSalesAgentV1._quantize(Decimal(str(discount_amount)))
            offer_price = AiSalesAgentV1._quantize(max(Decimal("0"), list_price - discount))
            valid_until = datetime.now(timezone.utc) + timedelta(days=valid_days)

            document_id = None
            document = None
            if generate_contract:
                try:
                    contract = await DocumentEngineV1.generate_sales_contract(
                        actor_id,
                        buyer_name=buyer_name or lead.customer_name or "Customer",
                        seller_name="Dealer",
                        vehicle_description=f"{car.get('year')} {car.get('make')} {car.get('model')}",
                        vin=car.get("vin") or "",
                        amount=str(offer_price),
                        currency=lead.currency,
                    )
                    document = contract
                    document_id = uuid.UUID(contract["document"]["id"])
                except Exception:
                    document = None
                    document_id = None

            offer = await SalesAgentOfferRepository(session).create(
                sales_lead_id=lead_id,
                tenant_id=tenant_id,
                company_id=ctx.company_id,
                car_id=car_id,
                offer_price=offer_price,
                discount_amount=discount,
                currency=lead.currency,
                status=SalesOfferStatus.SENT.value,
                document_id=document_id,
                valid_until=valid_until,
                terms={
                    "list_price": str(list_price),
                    "valid_days": valid_days,
                    "model_version": MODEL_VERSION,
                },
                created_by=actor_id,
            )
            await SalesAgentLeadRepository(session).update_fields(
                lead_id,
                status=SalesLeadStatus.OFFER_SENT.value,
                recommended_car_id=car_id,
            )
            await AuditRepository(session).create_log(
                user_id=actor_id,
                company_id=ctx.company_id,
                tenant_id=tenant_id,
                entity_type="ai_sales_offer",
                entity_id=str(offer.id),
                action=AuditAction.CREATE.value,
                new_value={"offer_price": str(offer_price), "car_id": str(car_id)},
            )
            await session.refresh(offer)
            return {
                "offer": AiSalesAgentV1._offer_snapshot(offer),
                "lead_status": SalesLeadStatus.OFFER_SENT.value,
                "document": document,
                "integrations": ["car_engine", "document_engine"],
            }

    @staticmethod
    async def process_follow_up_reminders(
        actor_id: int,
        tenant_id: uuid.UUID,
    ) -> dict[str, Any]:
        ctx = await AiSalesAgentV1._require_access(actor_id, tenant_id)
        now = datetime.now(timezone.utc)
        reminders: list[dict[str, Any]] = []

        async with get_session() as session:
            due_leads = await SalesAgentLeadRepository(session).list_due_for_follow_up(
                tenant_id, before=now
            )
            for lead in due_leads:
                recipient = lead.assigned_manager_id or actor_id
                title = f"Follow up: {lead.customer_name or 'Sales lead'}"
                message = (
                    f"Lead {lead.id} ({lead.status}) is due for follow-up. "
                    f"Intent: {lead.intent or 'unknown'}."
                )
                notification = await NotificationRepository(session).create(
                    user_id=recipient,
                    notification_type=NotificationType.SYSTEM_ALERT.value,
                    channel=NotificationChannel.INTERNAL.value,
                    title=title,
                    message=message,
                )
                await SalesAgentLeadRepository(session).update_fields(
                    lead.id,
                    next_follow_up_at=now + timedelta(days=FOLLOW_UP_INTERVAL_DAYS),
                )
                reminders.append({
                    "lead_id": str(lead.id),
                    "notification_id": str(notification.id),
                    "recipient_user_id": recipient,
                    "status": lead.status,
                })

            if reminders:
                await AuditRepository(session).create_log(
                    user_id=actor_id,
                    company_id=ctx.company_id,
                    tenant_id=tenant_id,
                    entity_type="ai_sales_agent",
                    entity_id=str(tenant_id),
                    action=AuditAction.STATUS_CHANGE.value,
                    new_value={"follow_up_reminders_sent": len(reminders)},
                )

        return {
            "reminders_sent": len(reminders),
            "reminders": reminders,
            "integration": "notification_engine",
        }

    @staticmethod
    async def list_leads(
        actor_id: int,
        tenant_id: uuid.UUID,
        *,
        status: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        await AiSalesAgentV1._require_access(actor_id, tenant_id)
        async with get_session() as session:
            rows = await SalesAgentLeadRepository(session).list_by_tenant(
                tenant_id, status=status, limit=limit
            )
            return [AiSalesAgentV1._lead_snapshot(r) for r in rows]

    @staticmethod
    async def get_lead(
        actor_id: int,
        tenant_id: uuid.UUID,
        lead_id: uuid.UUID,
    ) -> dict[str, Any]:
        await AiSalesAgentV1._require_access(actor_id, tenant_id)
        async with get_session() as session:
            lead = await AiSalesAgentV1._get_lead_or_raise(session, lead_id, tenant_id)
            prefs = await SalesAgentCustomerPreferenceRepository(session).get_by_lead(lead_id)
            conversations = await SalesAgentConversationRepository(session).list_by_lead(lead_id)
            offers = await SalesAgentOfferRepository(session).list_by_lead(lead_id)
            return {
                "lead": AiSalesAgentV1._lead_snapshot(lead),
                "preferences": (
                    AiSalesAgentV1._preference_snapshot(prefs) if prefs else None
                ),
                "conversations": [
                    AiSalesAgentV1._conversation_snapshot(c) for c in conversations
                ],
                "offers": [AiSalesAgentV1._offer_snapshot(o) for o in offers],
            }

    @staticmethod
    async def update_lead_status(
        actor_id: int,
        tenant_id: uuid.UUID,
        lead_id: uuid.UUID,
        status: str,
    ) -> dict[str, Any]:
        ctx = await AiSalesAgentV1._require_access(actor_id, tenant_id)
        if status not in {s.value for s in SalesLeadStatus}:
            raise AiSalesAgentError(f"Invalid status: {status}")
        async with get_session() as session:
            await AiSalesAgentV1._get_lead_or_raise(session, lead_id, tenant_id)
            row = await SalesAgentLeadRepository(session).update_fields(lead_id, status=status)
            await AuditRepository(session).create_log(
                user_id=actor_id,
                company_id=ctx.company_id,
                tenant_id=tenant_id,
                entity_type="ai_sales_lead",
                entity_id=str(lead_id),
                action=AuditAction.STATUS_CHANGE.value,
                new_value={"status": status},
            )
            await session.refresh(row)
            return AiSalesAgentV1._lead_snapshot(row)

    @staticmethod
    async def get_agent_dashboard(
        actor_id: int,
        tenant_id: uuid.UUID,
    ) -> dict[str, Any]:
        await AiSalesAgentV1._require_access(actor_id, tenant_id)
        leads = await AiSalesAgentV1.list_leads(actor_id, tenant_id, limit=200)
        by_status: dict[str, int] = {}
        for lead in leads:
            by_status[lead["status"]] = by_status.get(lead["status"], 0) + 1

        portal_leads = await DealerPortalEngineV1.get_active_leads(actor_id, tenant_id)
        marketplace_listings = await LeadMarketplaceEngineV1.list_listings(
            actor_id, tenant_id, limit=10
        )
        inventory = await CarEngineV1.list_cars(
            actor_id, status=CarStatus.READY_FOR_SALE.value, limit=20
        )

        return {
            "tenant_id": str(tenant_id),
            "lead_count": len(leads),
            "leads_by_status": by_status,
            "statuses": [s.value for s in SalesLeadStatus],
            "integrations": {
                "dealer_portal_active_leads": len(portal_leads),
                "marketplace_listings": len(marketplace_listings),
                "ready_for_sale_inventory": len(inventory),
            },
            "capabilities": [
                "lead_qualification",
                "customer_intent_detection",
                "budget_estimation",
                "vehicle_recommendation",
                "offer_generation",
                "follow_up_reminders",
            ],
        }
