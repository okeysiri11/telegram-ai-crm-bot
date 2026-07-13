# Recommendation Engine v1 — vehicle, similarity, upsell, cross-sell, financing recommendations.

from __future__ import annotations

import uuid
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from config import OWNER_ID
from database.models.audit_log import AuditAction
from database.models.car import CarStatus
from database.models.recommendation_engine import RecommendationType
from database.session import get_session
from repositories.ai_sales_agent_repository import SalesAgentCustomerPreferenceRepository
from repositories.audit_repository import AuditRepository
from repositories.recommendation_engine_repository import (
    RecommendationFeedbackRepository,
    RecommendationHistoryRepository,
    RecommendationProfileRepository,
)
from repositories.user_role_repository import UserRoleRepository
from services.pg_ai_sales_assistant_engine import AiSalesAssistantEngineV1
from services.pg_car_engine import CarEngineV1
from services.pg_partner_tenant_engine import PartnerTenantEngineV1

RECOMMENDATION_ENGINE_ROLES = frozenset({"OWNER", "ADMIN", "MANAGER"})
MODEL_VERSION = "recommendation-engine-v1.0.0"
MONEY = Decimal("0.01")
CONF = Decimal("0.0001")

VEHICLE_TYPE_KEYWORDS: dict[str, tuple[str, ...]] = {
    "SUV": ("suv", "crossover", "rav4", "cr-v", "explorer", "tahoe", "highlander", "pilot"),
    "SEDAN": ("sedan", "camry", "accord", "civic", "corolla", "altima", "malibu"),
    "TRUCK": ("truck", "pickup", "f-150", "f150", "silverado", "ram", "tundra"),
    "COUPE": ("coupe", "mustang", "camaro", "challenger"),
    "VAN": ("van", "minivan", "odyssey", "sienna", "pacifica"),
}

CROSS_SELL_CATALOG: tuple[dict[str, Any], ...] = (
    {"code": "EXTENDED_WARRANTY", "label": "Extended Warranty", "price_pct": Decimal("0.05")},
    {"code": "SERVICE_PACKAGE", "label": "Prepaid Service Package", "price_pct": Decimal("0.03")},
    {"code": "GAP_INSURANCE", "label": "GAP Insurance", "price_pct": Decimal("0.015")},
    {"code": "TIRE_PROTECTION", "label": "Tire & Wheel Protection", "price_pct": Decimal("0.01")},
)


class RecommendationEngineError(Exception):
    pass


class RecommendationEngineV1:
    @staticmethod
    async def user_can_access(user_id: int) -> bool:
        if user_id == OWNER_ID:
            return True
        async with get_session() as session:
            roles = await UserRoleRepository(session).get_user_roles(user_id)
            return any(role.code in RECOMMENDATION_ENGINE_ROLES for role in roles)

    @staticmethod
    async def _require_access(actor_id: int, tenant_id: uuid.UUID):
        if not await RecommendationEngineV1.user_can_access(actor_id):
            raise RecommendationEngineError("Recommendation engine access denied")
        return await PartnerTenantEngineV1.resolve_context(actor_id, tenant_id)

    @staticmethod
    def _quantize(amount: Decimal) -> Decimal:
        return amount.quantize(MONEY, rounding=ROUND_HALF_UP)

    @staticmethod
    def _confidence(score: float) -> Decimal:
        return Decimal(str(max(0.0, min(1.0, score)))).quantize(CONF)

    @staticmethod
    def _profile_snapshot(row) -> dict[str, Any]:
        return {
            "id": str(row.id),
            "tenant_id": str(row.tenant_id),
            "company_id": str(row.company_id),
            "sales_lead_id": str(row.sales_lead_id) if row.sales_lead_id else None,
            "user_id": row.user_id,
            "label": row.label,
            "budget_min": str(row.budget_min) if row.budget_min is not None else None,
            "budget_max": str(row.budget_max) if row.budget_max is not None else None,
            "vehicle_type": row.vehicle_type,
            "fuel_type": row.fuel_type,
            "transmission": row.transmission,
            "location": row.location,
            "previous_interactions": row.previous_interactions or [],
            "preferences": row.preferences or {},
            "currency": row.currency,
            "is_active": row.is_active,
            "created_by": row.created_by,
            "metadata": row.metadata_ or {},
            "created_at": row.created_at.isoformat(),
        }

    @staticmethod
    def _history_snapshot(row) -> dict[str, Any]:
        return {
            "id": str(row.id),
            "profile_id": str(row.profile_id),
            "recommendation_type": row.recommendation_type,
            "input_context": row.input_context,
            "result": row.result,
            "confidence_score": str(row.confidence_score),
            "model_version": row.model_version,
            "entity_type": row.entity_type,
            "entity_id": str(row.entity_id) if row.entity_id else None,
            "summary": row.summary,
            "created_by": row.created_by,
            "created_at": row.created_at.isoformat(),
        }

    @staticmethod
    def _feedback_snapshot(row) -> dict[str, Any]:
        return {
            "id": str(row.id),
            "history_id": str(row.history_id),
            "profile_id": str(row.profile_id),
            "feedback_type": row.feedback_type,
            "rating": row.rating,
            "comment": row.comment,
            "created_by": row.created_by,
            "created_at": row.created_at.isoformat(),
        }

    @staticmethod
    async def _get_profile_or_raise(session, profile_id: uuid.UUID, tenant_id: uuid.UUID):
        row = await RecommendationProfileRepository(session).get_by_id(profile_id)
        if row is None or row.tenant_id != tenant_id:
            raise RecommendationEngineError(f"Profile not found: {profile_id}")
        return row

    @staticmethod
    async def _log_history(
        session,
        *,
        profile,
        recommendation_type: str,
        input_context: dict,
        result: dict,
        confidence: float,
        summary: str,
        actor_id: int,
        entity_type: str | None = None,
        entity_id: uuid.UUID | None = None,
    ) -> dict[str, Any]:
        row = await RecommendationHistoryRepository(session).create(
            profile_id=profile.id,
            tenant_id=profile.tenant_id,
            company_id=profile.company_id,
            recommendation_type=recommendation_type,
            input_context=input_context,
            result=result,
            confidence_score=RecommendationEngineV1._confidence(confidence),
            model_version=MODEL_VERSION,
            entity_type=entity_type,
            entity_id=entity_id,
            summary=summary,
            created_by=actor_id,
        )
        await session.refresh(row)
        return RecommendationEngineV1._history_snapshot(row)

    @staticmethod
    def _vehicle_type_match(car: dict[str, Any], vehicle_type: str | None) -> int:
        if not vehicle_type:
            return 0
        haystack = f"{car.get('make', '')} {car.get('model', '')}".lower()
        keywords = VEHICLE_TYPE_KEYWORDS.get(vehicle_type.upper(), (vehicle_type.lower(),))
        return 15 if any(kw in haystack for kw in keywords) else 0

    @staticmethod
    def _profile_similarity(a, b) -> float:
        score = 0.0
        if a.vehicle_type and b.vehicle_type and a.vehicle_type == b.vehicle_type:
            score += 0.25
        if a.fuel_type and b.fuel_type and a.fuel_type.lower() == b.fuel_type.lower():
            score += 0.15
        if a.transmission and b.transmission and a.transmission.lower() == b.transmission.lower():
            score += 0.10
        if a.location and b.location and a.location.lower() == b.location.lower():
            score += 0.15

        a_min = a.budget_min or Decimal("0")
        a_max = a.budget_max or Decimal("999999")
        b_min = b.budget_min or Decimal("0")
        b_max = b.budget_max or Decimal("999999")
        overlap_min = max(a_min, b_min)
        overlap_max = min(a_max, b_max)
        if overlap_max >= overlap_min and a_max > 0 and b_max > 0:
            overlap = float(overlap_max - overlap_min)
            span = float(max(a_max, b_max) - min(a_min, b_min)) or 1.0
            score += min(0.25, overlap / span * 0.25)

        a_intents = {
            item.get("intent") for item in (a.previous_interactions or []) if isinstance(item, dict)
        }
        b_intents = {
            item.get("intent") for item in (b.previous_interactions or []) if isinstance(item, dict)
        }
        a_intents.discard(None)
        b_intents.discard(None)
        if a_intents and b_intents:
            union = a_intents | b_intents
            score += len(a_intents & b_intents) / len(union) * 0.10

        return min(1.0, score)

    @staticmethod
    async def create_profile(
        actor_id: int,
        tenant_id: uuid.UUID,
        *,
        budget_min: Decimal | float | int | None = None,
        budget_max: Decimal | float | int | None = None,
        vehicle_type: str | None = None,
        fuel_type: str | None = None,
        transmission: str | None = None,
        location: str | None = None,
        previous_interactions: list | None = None,
        preferences: dict | None = None,
        sales_lead_id: uuid.UUID | None = None,
        user_id: int | None = None,
        label: str | None = None,
    ) -> dict[str, Any]:
        ctx = await RecommendationEngineV1._require_access(actor_id, tenant_id)

        if sales_lead_id and not any([budget_min, budget_max, vehicle_type]):
            async with get_session() as session:
                prefs = await SalesAgentCustomerPreferenceRepository(session).get_by_lead(
                    sales_lead_id
                )
                if prefs:
                    budget_min = budget_min or prefs.budget_min
                    budget_max = budget_max or prefs.budget_max
                    fuel_type = fuel_type or prefs.fuel_type
                    transmission = transmission or prefs.transmission
                    if prefs.body_types and not vehicle_type:
                        vehicle_type = prefs.body_types[0] if prefs.body_types else None
                    preferences = preferences or {}
                    preferences.setdefault("preferred_makes", prefs.preferred_makes or [])
                    preferences.setdefault("preferred_models", prefs.preferred_models or [])

        async with get_session() as session:
            row = await RecommendationProfileRepository(session).create(
                tenant_id=tenant_id,
                company_id=ctx.company_id,
                budget_min=Decimal(str(budget_min)) if budget_min is not None else None,
                budget_max=Decimal(str(budget_max)) if budget_max is not None else None,
                vehicle_type=vehicle_type,
                fuel_type=fuel_type,
                transmission=transmission,
                location=location,
                previous_interactions=previous_interactions or [],
                preferences=preferences or {},
                sales_lead_id=sales_lead_id,
                user_id=user_id,
                label=label,
                created_by=actor_id,
            )
            await AuditRepository(session).create_log(
                user_id=actor_id,
                company_id=ctx.company_id,
                tenant_id=tenant_id,
                entity_type="recommendation_profile",
                entity_id=str(row.id),
                action=AuditAction.CREATE.value,
                new_value={"vehicle_type": vehicle_type, "location": location},
            )
            await session.refresh(row)
            return RecommendationEngineV1._profile_snapshot(row)

    @staticmethod
    async def recommend_vehicles(
        actor_id: int,
        tenant_id: uuid.UUID,
        profile_id: uuid.UUID,
        *,
        limit: int = 5,
    ) -> dict[str, Any]:
        ctx = await RecommendationEngineV1._require_access(actor_id, tenant_id)
        async with get_session() as session:
            profile = await RecommendationEngineV1._get_profile_or_raise(
                session, profile_id, tenant_id
            )

        cars = await CarEngineV1.list_cars(
            actor_id,
            status=CarStatus.READY_FOR_SALE.value,
            limit=100,
        )
        budget_min = profile.budget_min
        budget_max = profile.budget_max
        preferred_makes = set(
            m.lower() for m in (profile.preferences or {}).get("preferred_makes", [])
        )
        preferred_models = set(
            m.lower() for m in (profile.preferences or {}).get("preferred_models", [])
        )

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
                score += 20
            if preferred_models and any(pm in model for pm in preferred_models):
                score += 15
            score += RecommendationEngineV1._vehicle_type_match(car, profile.vehicle_type)
            if budget_min and budget_max:
                mid = (budget_min + budget_max) / 2
                if mid > 0:
                    delta = abs(price - mid) / mid
                    score += max(0, 15 - int(delta * 20))

            interaction_boost = 0
            for item in profile.previous_interactions or []:
                if not isinstance(item, dict):
                    continue
                text = (item.get("text") or item.get("message") or "").lower()
                if make and make in text:
                    interaction_boost += 5
                if model and model in text:
                    interaction_boost += 5
            score += min(15, interaction_boost)

            scored.append((score, car))

        scored.sort(key=lambda item: item[0], reverse=True)
        recommendations = [{"match_score": s, **c} for s, c in scored[:limit]]
        result = {
            "recommendations": recommendations,
            "count": len(recommendations),
            "inputs": {
                "budget_min": str(budget_min) if budget_min else None,
                "budget_max": str(budget_max) if budget_max else None,
                "vehicle_type": profile.vehicle_type,
                "fuel_type": profile.fuel_type,
                "transmission": profile.transmission,
                "location": profile.location,
            },
        }

        async with get_session() as session:
            profile = await RecommendationEngineV1._get_profile_or_raise(
                session, profile_id, tenant_id
            )
            history = await RecommendationEngineV1._log_history(
                session,
                profile=profile,
                recommendation_type=RecommendationType.VEHICLE.value,
                input_context=result["inputs"],
                result=result,
                confidence=0.75 if recommendations else 0.35,
                summary=f"Recommended {len(recommendations)} vehicles",
                actor_id=actor_id,
                entity_type="car",
                entity_id=uuid.UUID(recommendations[0]["id"]) if recommendations else None,
            )

        return {"history": history, **result, "integration": "car_engine"}

    @staticmethod
    async def match_similar_customers(
        actor_id: int,
        tenant_id: uuid.UUID,
        profile_id: uuid.UUID,
        *,
        limit: int = 5,
    ) -> dict[str, Any]:
        await RecommendationEngineV1._require_access(actor_id, tenant_id)
        async with get_session() as session:
            profile = await RecommendationEngineV1._get_profile_or_raise(
                session, profile_id, tenant_id
            )
            candidates = await RecommendationProfileRepository(session).list_by_tenant(
                tenant_id, limit=200
            )

            matches: list[dict[str, Any]] = []
            for candidate in candidates:
                if candidate.id == profile.id:
                    continue
                similarity = RecommendationEngineV1._profile_similarity(profile, candidate)
                if similarity < 0.2:
                    continue
                matches.append({
                    "profile_id": str(candidate.id),
                    "similarity_score": round(similarity, 4),
                    "label": candidate.label,
                    "vehicle_type": candidate.vehicle_type,
                    "budget_min": str(candidate.budget_min) if candidate.budget_min else None,
                    "budget_max": str(candidate.budget_max) if candidate.budget_max else None,
                    "location": candidate.location,
                })

            matches.sort(key=lambda item: item["similarity_score"], reverse=True)
            matches = matches[:limit]
            result = {"matches": matches, "count": len(matches)}

            history = await RecommendationEngineV1._log_history(
                session,
                profile=profile,
                recommendation_type=RecommendationType.CUSTOMER_SIMILARITY.value,
                input_context={"profile_id": str(profile_id)},
                result=result,
                confidence=0.8 if matches else 0.3,
                summary=f"Found {len(matches)} similar customer profiles",
                actor_id=actor_id,
            )

        return {"history": history, **result}

    @staticmethod
    async def find_upsell_opportunities(
        actor_id: int,
        tenant_id: uuid.UUID,
        profile_id: uuid.UUID,
        *,
        car_id: uuid.UUID | None = None,
        limit: int = 3,
    ) -> dict[str, Any]:
        await RecommendationEngineV1._require_access(actor_id, tenant_id)
        async with get_session() as session:
            profile = await RecommendationEngineV1._get_profile_or_raise(
                session, profile_id, tenant_id
            )

        base_price = profile.budget_max or profile.budget_min or Decimal("25000")
        if car_id:
            car = await CarEngineV1.get_car(actor_id, car_id)
            base_price = Decimal(str(car.get("sale_price") or car.get("total_cost") or base_price))

        cars = await CarEngineV1.list_cars(
            actor_id, status=CarStatus.READY_FOR_SALE.value, limit=100
        )
        opportunities: list[dict[str, Any]] = []
        for car in cars:
            price = Decimal(str(car.get("sale_price") or car.get("total_cost") or "0"))
            if price <= base_price:
                continue
            premium_pct = float((price - base_price) / base_price * 100) if base_price > 0 else 0
            if premium_pct < 5 or premium_pct > 35:
                continue
            opportunities.append({
                "car_id": car["id"],
                "year": car.get("year"),
                "make": car.get("make"),
                "model": car.get("model"),
                "price": str(price),
                "premium_over_budget_pct": round(premium_pct, 2),
                "upsell_reason": "Premium trim with higher value features",
            })

        opportunities.sort(key=lambda item: item["premium_over_budget_pct"])
        opportunities = opportunities[:limit]
        result = {"opportunities": opportunities, "count": len(opportunities), "base_price": str(base_price)}

        async with get_session() as session:
            profile = await RecommendationEngineV1._get_profile_or_raise(
                session, profile_id, tenant_id
            )
            history = await RecommendationEngineV1._log_history(
                session,
                profile=profile,
                recommendation_type=RecommendationType.UPSELL.value,
                input_context={"profile_id": str(profile_id), "car_id": str(car_id) if car_id else None},
                result=result,
                confidence=0.7 if opportunities else 0.35,
                summary=f"Found {len(opportunities)} upsell opportunities",
                actor_id=actor_id,
            )

        return {"history": history, **result}

    @staticmethod
    async def find_cross_sell_opportunities(
        actor_id: int,
        tenant_id: uuid.UUID,
        profile_id: uuid.UUID,
        *,
        vehicle_price: Decimal | float | int | None = None,
    ) -> dict[str, Any]:
        await RecommendationEngineV1._require_access(actor_id, tenant_id)
        async with get_session() as session:
            profile = await RecommendationEngineV1._get_profile_or_raise(
                session, profile_id, tenant_id
            )

        price = Decimal(str(
            vehicle_price or profile.budget_max or profile.budget_min or "25000"
        ))
        opportunities: list[dict[str, Any]] = []
        for item in CROSS_SELL_CATALOG:
            addon_price = RecommendationEngineV1._quantize(price * item["price_pct"])
            opportunities.append({
                "code": item["code"],
                "label": item["label"],
                "estimated_price": str(addon_price),
                "currency": profile.currency,
                "reason": f"Complements {profile.vehicle_type or 'vehicle'} purchase",
            })

        if profile.previous_interactions:
            intents = {
                i.get("intent") for i in profile.previous_interactions if isinstance(i, dict)
            }
            if "FINANCING" in intents or "financing" in str(intents).lower():
                opportunities.append({
                    "code": "CREDIT_INSURANCE",
                    "label": "Credit Life Insurance",
                    "estimated_price": str(RecommendationEngineV1._quantize(price * Decimal("0.008"))),
                    "currency": profile.currency,
                    "reason": "Customer showed financing interest",
                })

        result = {"opportunities": opportunities, "count": len(opportunities), "vehicle_price": str(price)}

        history = await RecommendationEngineV1._log_history(
            session,
            profile=profile,
            recommendation_type=RecommendationType.CROSS_SELL.value,
            input_context={"profile_id": str(profile_id), "vehicle_price": str(price)},
            result=result,
            confidence=0.72,
            summary=f"Suggested {len(opportunities)} cross-sell items",
            actor_id=actor_id,
        )

        return {"history": history, **result}

    @staticmethod
    async def recommend_financing(
        actor_id: int,
        tenant_id: uuid.UUID,
        profile_id: uuid.UUID,
        *,
        car_id: uuid.UUID | None = None,
        vehicle_price: Decimal | float | int | None = None,
        down_payment: Decimal | float | int = 0,
        term_months: int = 60,
        annual_rate_percent: Decimal | float | int = 12,
    ) -> dict[str, Any]:
        await RecommendationEngineV1._require_access(actor_id, tenant_id)
        async with get_session() as session:
            profile = await RecommendationEngineV1._get_profile_or_raise(
                session, profile_id, tenant_id
            )

        price = vehicle_price
        if car_id:
            car = await CarEngineV1.get_car(actor_id, car_id)
            price = car.get("sale_price") or car.get("total_cost")
        if price is None:
            price = profile.budget_max or profile.budget_min or Decimal("25000")

        if profile.budget_max:
            suggested_down = RecommendationEngineV1._quantize(
                Decimal(str(price)) * Decimal("0.15")
            )
            if down_payment == 0:
                down_payment = suggested_down

        financing = AiSalesAssistantEngineV1.calculate_financing(
            vehicle_price=price,
            down_payment=down_payment,
            annual_rate_percent=annual_rate_percent,
            term_months=term_months,
        )

        budget_max = profile.budget_max
        affordable = True
        monthly = Decimal(financing["monthly_payment"])
        if budget_max:
            affordable = monthly <= budget_max / Decimal("48")

        result = {
            "financing": financing,
            "affordable": affordable,
            "recommendation": (
                "Within estimated budget" if affordable else "Consider higher down payment or longer term"
            ),
            "inputs": {
                "vehicle_price": str(price),
                "down_payment": str(down_payment),
                "term_months": term_months,
                "annual_rate_percent": str(annual_rate_percent),
            },
        }

        history = await RecommendationEngineV1._log_history(
            session,
            profile=profile,
            recommendation_type=RecommendationType.FINANCING.value,
            input_context=result["inputs"],
            result=result,
            confidence=0.85 if affordable else 0.55,
            summary=f"Monthly payment {financing['monthly_payment']}",
            actor_id=actor_id,
            entity_type="car" if car_id else None,
            entity_id=car_id,
        )

        return {"history": history, **result, "integration": "sales_assistant_financing"}

    @staticmethod
    async def record_feedback(
        actor_id: int,
        tenant_id: uuid.UUID,
        history_id: uuid.UUID,
        *,
        feedback_type: str,
        rating: int | None = None,
        comment: str | None = None,
    ) -> dict[str, Any]:
        ctx = await RecommendationEngineV1._require_access(actor_id, tenant_id)
        async with get_session() as session:
            history = await RecommendationHistoryRepository(session).get_by_id(history_id)
            if history is None or history.tenant_id != tenant_id:
                raise RecommendationEngineError(f"History not found: {history_id}")

            row = await RecommendationFeedbackRepository(session).create(
                history_id=history_id,
                profile_id=history.profile_id,
                tenant_id=tenant_id,
                feedback_type=feedback_type,
                rating=rating,
                comment=comment,
                created_by=actor_id,
            )
            await AuditRepository(session).create_log(
                user_id=actor_id,
                company_id=ctx.company_id,
                tenant_id=tenant_id,
                entity_type="recommendation_feedback",
                entity_id=str(row.id),
                action=AuditAction.CREATE.value,
                new_value={"feedback_type": feedback_type, "rating": rating},
            )
            await session.refresh(row)
            return RecommendationEngineV1._feedback_snapshot(row)

    @staticmethod
    async def get_profile(
        actor_id: int,
        tenant_id: uuid.UUID,
        profile_id: uuid.UUID,
    ) -> dict[str, Any]:
        await RecommendationEngineV1._require_access(actor_id, tenant_id)
        async with get_session() as session:
            profile = await RecommendationEngineV1._get_profile_or_raise(
                session, profile_id, tenant_id
            )
            history = await RecommendationHistoryRepository(session).list_by_profile(profile_id)
            feedback = await RecommendationFeedbackRepository(session).list_by_profile(profile_id)
            return {
                "profile": RecommendationEngineV1._profile_snapshot(profile),
                "history": [RecommendationEngineV1._history_snapshot(h) for h in history],
                "feedback": [RecommendationEngineV1._feedback_snapshot(f) for f in feedback],
            }

    @staticmethod
    async def list_profiles(
        actor_id: int,
        tenant_id: uuid.UUID,
        *,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        await RecommendationEngineV1._require_access(actor_id, tenant_id)
        async with get_session() as session:
            rows = await RecommendationProfileRepository(session).list_by_tenant(
                tenant_id, limit=limit
            )
            return [RecommendationEngineV1._profile_snapshot(r) for r in rows]

    @staticmethod
    async def get_engine_dashboard(
        actor_id: int,
        tenant_id: uuid.UUID,
    ) -> dict[str, Any]:
        profiles = await RecommendationEngineV1.list_profiles(actor_id, tenant_id, limit=200)
        inventory = await CarEngineV1.list_cars(
            actor_id, status=CarStatus.READY_FOR_SALE.value, limit=50
        )
        return {
            "tenant_id": str(tenant_id),
            "profile_count": len(profiles),
            "inventory_available": len(inventory),
            "recommendation_types": [t.value for t in RecommendationType],
            "inputs": [
                "budget",
                "vehicle_type",
                "fuel_type",
                "transmission",
                "location",
                "previous_interactions",
            ],
            "capabilities": [
                "vehicle_recommendation",
                "customer_similarity_matching",
                "upsell_opportunities",
                "cross_sell_opportunities",
                "financing_recommendation",
            ],
        }
