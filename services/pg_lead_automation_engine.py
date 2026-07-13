# Lead Automation Engine v1 — intake, scoring, duplicate detection, manager assignment.

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Any

from config import MANAGER_ID, MANAGERS, OWNER_ID
from database.models.audit_log import AuditAction
from database.models.lead_automation_engine import (
    AutomationLeadSource,
    AutomationLeadStatus,
)
from database.session import get_session
from repositories.audit_repository import AuditRepository
from repositories.car_repository import CarRepository
from repositories.lead_automation_repository import LeadAutomationRepository
from repositories.user_role_repository import UserRoleRepository

LEAD_AUTOMATION_ROLES = frozenset({"OWNER", "ADMIN", "MANAGER"})

SOURCE_BASE_SCORES: dict[str, int] = {
    AutomationLeadSource.TELEGRAM.value: 20,
    AutomationLeadSource.INSTAGRAM.value: 15,
    AutomationLeadSource.FACEBOOK.value: 15,
    AutomationLeadSource.TIKTOK.value: 10,
    AutomationLeadSource.WEBSITE.value: 25,
    AutomationLeadSource.MANUAL.value: 5,
}


class LeadAutomationEngineError(Exception):
    pass


class LeadAutomationEngineV1:
    @staticmethod
    async def user_can_access(user_id: int) -> bool:
        if user_id == OWNER_ID:
            return True
        async with get_session() as session:
            roles = await UserRoleRepository(session).get_user_roles(user_id)
            return any(role.code in LEAD_AUTOMATION_ROLES for role in roles)

    @staticmethod
    def _lead_snapshot(lead) -> dict[str, Any]:
        return LeadAutomationRepository.snapshot(lead)

    @staticmethod
    def calculate_score(
        *,
        source: str,
        phone: str | None = None,
        email: str | None = None,
        car_id: uuid.UUID | None = None,
        budget: Decimal | float | int | None = None,
        customer_name: str | None = None,
        source_metadata: dict | None = None,
    ) -> tuple[int, dict[str, int]]:
        factors: dict[str, int] = {}
        factors["source_base"] = SOURCE_BASE_SCORES.get(source, 0)

        if phone and phone.strip():
            factors["has_phone"] = 15
        if email and email.strip():
            factors["has_email"] = 10
        if car_id is not None:
            factors["car_interest"] = 20
        if budget is not None and Decimal(str(budget)) > 0:
            factors["has_budget"] = 15
        if customer_name and len(customer_name.strip()) > 2:
            factors["valid_name"] = 5

        metadata = source_metadata or {}
        if metadata.get("utm_campaign") or metadata.get("campaign_id"):
            factors["campaign_attribution"] = 5
        if metadata.get("message_count", 0) > 1:
            factors["engagement"] = 5

        total = min(100, sum(factors.values()))
        return total, factors

    @staticmethod
    async def _manager_pool(session) -> list[int]:
        pool = set(MANAGERS.keys()) | {MANAGER_ID, OWNER_ID}
        return sorted(pool)

    @staticmethod
    async def assign_manager(session) -> int:
        repo = LeadAutomationRepository(session)
        pool = await LeadAutomationEngineV1._manager_pool(session)
        if not pool:
            return OWNER_ID

        loads = {manager_id: await repo.count_open_leads(manager_id) for manager_id in pool}
        return min(pool, key=lambda mid: loads[mid])

    @staticmethod
    async def ingest_lead(
        *,
        source: str,
        customer_name: str,
        phone: str | None = None,
        email: str | None = None,
        telegram_user_id: int | None = None,
        car_id: uuid.UUID | None = None,
        budget: Decimal | float | int | None = None,
        external_reference: str | None = None,
        source_metadata: dict | None = None,
        notes: str | None = None,
        actor_id: int | None = None,
    ) -> dict[str, Any]:
        """Automatic lead creation with duplicate detection, scoring, and assignment."""
        if source not in SOURCE_BASE_SCORES:
            raise LeadAutomationEngineError(f"Invalid lead source: {source}")

        async with get_session() as session:
            repo = LeadAutomationRepository(session)

            if car_id is not None:
                car = await CarRepository(session).get_car(car_id)
                if car is None:
                    raise LeadAutomationEngineError(f"Car not found: {car_id}")

            duplicate = await repo.find_duplicate(
                phone=phone,
                email=email,
                telegram_user_id=telegram_user_id,
                external_reference=external_reference,
                source=source,
            )

            if duplicate is not None:
                await repo.create_source_event(
                    lead_id=duplicate.id,
                    source=source,
                    event_type="duplicate_detected",
                    payload={
                        "matched_by": LeadAutomationEngineV1._duplicate_match_reason(
                            duplicate,
                            phone=phone,
                            email=email,
                            telegram_user_id=telegram_user_id,
                            external_reference=external_reference,
                            source=source,
                        ),
                        "incoming": {
                            "customer_name": customer_name,
                            "phone": phone,
                            "email": email,
                            "telegram_user_id": telegram_user_id,
                            "external_reference": external_reference,
                        },
                    },
                )
                return {
                    **LeadAutomationEngineV1._lead_snapshot(duplicate),
                    "created": False,
                    "duplicate_detected": True,
                }

            score, factors = LeadAutomationEngineV1.calculate_score(
                source=source,
                phone=phone,
                email=email,
                car_id=car_id,
                budget=budget,
                customer_name=customer_name,
                source_metadata=source_metadata,
            )
            manager_id = await LeadAutomationEngineV1.assign_manager(session)

            lead = await repo.create_lead(
                customer_name=customer_name,
                source=source,
                phone=phone,
                email=email,
                telegram_user_id=telegram_user_id,
                car_id=car_id,
                assigned_manager_id=manager_id,
                score=score,
                status=AutomationLeadStatus.ASSIGNED.value,
                external_reference=external_reference,
                budget=budget,
                source_metadata=source_metadata,
                scoring_factors=factors,
                notes=notes,
            )

            await repo.create_source_event(
                lead_id=lead.id,
                source=source,
                event_type="created",
                payload={
                    "score": score,
                    "assigned_manager_id": manager_id,
                    "scoring_factors": factors,
                },
            )
            await repo.create_source_event(
                lead_id=lead.id,
                source=source,
                event_type="manager_assigned",
                payload={"assigned_manager_id": manager_id},
            )

            if actor_id is not None:
                await AuditRepository(session).create_log(
                    user_id=actor_id,
                    entity_type="automation_lead",
                    entity_id=str(lead.id),
                    action=AuditAction.CREATE.value,
                    new_value={"source": source, "score": score, "manager_id": manager_id},
                )

            return {
                **LeadAutomationEngineV1._lead_snapshot(lead),
                "created": True,
                "duplicate_detected": False,
            }

    @staticmethod
    def _duplicate_match_reason(
        existing,
        *,
        phone: str | None,
        email: str | None,
        telegram_user_id: int | None,
        external_reference: str | None,
        source: str,
    ) -> str:
        from repositories.lead_automation_repository import normalize_email, normalize_phone

        if telegram_user_id is not None and existing.telegram_user_id == telegram_user_id:
            return "telegram_user_id"
        phone_norm = normalize_phone(phone)
        if phone_norm and existing.phone_normalized == phone_norm:
            return "phone"
        email_norm = normalize_email(email)
        if email_norm and existing.email_normalized == email_norm:
            return "email"
        if external_reference and existing.external_reference == external_reference:
            return "external_reference"
        return "unknown"

    @staticmethod
    async def ingest_from_telegram(
        *,
        user_id: int,
        username: str | None,
        first_name: str | None,
        last_name: str | None,
        car_id: uuid.UUID | None = None,
        metadata: dict | None = None,
    ) -> dict[str, Any]:
        name_parts = [part for part in (first_name, last_name) if part]
        customer_name = " ".join(name_parts) if name_parts else (username or f"User {user_id}")
        payload = dict(metadata or {})
        payload.update({
            "telegram_username": username,
            "first_name": first_name,
            "last_name": last_name,
        })

        return await LeadAutomationEngineV1.ingest_lead(
            source=AutomationLeadSource.TELEGRAM.value,
            customer_name=customer_name,
            telegram_user_id=user_id,
            car_id=car_id,
            source_metadata=payload,
            notes=f"Auto-created from Telegram (@{username})" if username else "Auto-created from Telegram",
        )

    @staticmethod
    async def ingest_manual(
        actor_id: int,
        *,
        customer_name: str,
        phone: str | None = None,
        email: str | None = None,
        car_id: uuid.UUID | None = None,
        budget: Decimal | float | int | None = None,
        notes: str | None = None,
    ) -> dict[str, Any]:
        if not await LeadAutomationEngineV1.user_can_access(actor_id):
            raise LeadAutomationEngineError("Access denied")

        return await LeadAutomationEngineV1.ingest_lead(
            source=AutomationLeadSource.MANUAL.value,
            customer_name=customer_name,
            phone=phone,
            email=email,
            car_id=car_id,
            budget=budget,
            notes=notes,
            actor_id=actor_id,
            source_metadata={"created_by": actor_id},
        )

    @staticmethod
    async def ingest_from_channel(
        source: str,
        *,
        customer_name: str,
        external_reference: str,
        phone: str | None = None,
        email: str | None = None,
        car_id: uuid.UUID | None = None,
        metadata: dict | None = None,
    ) -> dict[str, Any]:
        allowed = {
            AutomationLeadSource.INSTAGRAM.value,
            AutomationLeadSource.FACEBOOK.value,
            AutomationLeadSource.TIKTOK.value,
            AutomationLeadSource.WEBSITE.value,
        }
        if source not in allowed:
            raise LeadAutomationEngineError(f"Unsupported channel source: {source}")

        return await LeadAutomationEngineV1.ingest_lead(
            source=source,
            customer_name=customer_name,
            phone=phone,
            email=email,
            car_id=car_id,
            external_reference=external_reference,
            source_metadata=metadata,
        )

    @staticmethod
    async def get_lead(actor_id: int, lead_id: uuid.UUID) -> dict[str, Any]:
        if not await LeadAutomationEngineV1.user_can_access(actor_id):
            raise LeadAutomationEngineError("Access denied")

        async with get_session() as session:
            lead = await LeadAutomationRepository(session).get_by_id(lead_id)
            if lead is None:
                raise LeadAutomationEngineError(f"Lead not found: {lead_id}")
            return LeadAutomationEngineV1._lead_snapshot(lead)

    @staticmethod
    async def list_leads(
        actor_id: int,
        *,
        source: str | None = None,
        status: str | None = None,
        assigned_manager_id: int | None = None,
        min_score: int | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        if not await LeadAutomationEngineV1.user_can_access(actor_id):
            raise LeadAutomationEngineError("Access denied")

        async with get_session() as session:
            leads = await LeadAutomationRepository(session).list_leads(
                source=source,
                status=status,
                assigned_manager_id=assigned_manager_id,
                min_score=min_score,
                limit=limit,
            )
            return [LeadAutomationEngineV1._lead_snapshot(lead) for lead in leads]

    @staticmethod
    async def get_lead_source_history(
        actor_id: int,
        lead_id: uuid.UUID,
    ) -> list[dict[str, Any]]:
        if not await LeadAutomationEngineV1.user_can_access(actor_id):
            raise LeadAutomationEngineError("Access denied")

        async with get_session() as session:
            lead = await LeadAutomationRepository(session).get_by_id(lead_id)
            if lead is None:
                raise LeadAutomationEngineError(f"Lead not found: {lead_id}")
            events = await LeadAutomationRepository(session).list_source_events(lead_id)
            return [LeadAutomationRepository.event_snapshot(event) for event in events]

    @staticmethod
    async def get_source_stats(actor_id: int) -> dict[str, int]:
        if not await LeadAutomationEngineV1.user_can_access(actor_id):
            raise LeadAutomationEngineError("Access denied")

        async with get_session() as session:
            return await LeadAutomationRepository(session).source_stats()
