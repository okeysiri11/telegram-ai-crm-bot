# Automotive AI Copilot v1 — pricing, inventory, margin, supplier intelligence.

from __future__ import annotations

import statistics
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from config import OWNER_ID
from database.models.automotive_ai_copilot import (
    DecisionStatus,
    FeedbackRating,
    PredictionType,
    RecommendationType,
)
from database.models.automotive_inventory import VehicleStatus
from database.session import get_session
from repositories.automotive_ai_copilot_repository import (
    AiDecisionRepository,
    AiFeedbackRepository,
    AiPredictionRepository,
    AiRecommendationRepository,
)
from repositories.automotive_cost_repository import (
    VehicleCostItemRepository,
    VehicleCostRepository,
)
from repositories.automotive_inventory_repository import VehicleRepository
from repositories.user_role_repository import UserRoleRepository

COPILOT_ROLES = frozenset({"OWNER", "ADMIN", "MANAGER"})
MODEL_VERSION = "automotive-copilot-v1.0.0"
MONEY = Decimal("0.01")
CONF = Decimal("0.0001")
SLOW_MOVING_DAYS = 90


class AutomotiveAiCopilotEngineError(Exception):
    pass


class AutomotiveAiCopilotEngineV1:
    @staticmethod
    async def user_can_access(user_id: int) -> bool:
        if user_id == OWNER_ID:
            return True
        async with get_session() as session:
            roles = await UserRoleRepository(session).get_user_roles(user_id)
            return any(role.code in COPILOT_ROLES for role in roles)

    @staticmethod
    def _quantize(amount: Decimal) -> Decimal:
        return amount.quantize(MONEY, rounding=ROUND_HALF_UP)

    @staticmethod
    def _confidence(score: float) -> Decimal:
        return Decimal(str(max(0.0, min(1.0, score)))).quantize(CONF)

    @staticmethod
    def _recommendation_snapshot(rec) -> dict[str, Any]:
        return {
            "id": str(rec.id),
            "recommendation_type": rec.recommendation_type,
            "vehicle_id": str(rec.vehicle_id) if rec.vehicle_id else None,
            "entity_type": rec.entity_type,
            "entity_id": rec.entity_id,
            "title": rec.title,
            "summary": rec.summary,
            "recommended_value": (
                str(rec.recommended_value) if rec.recommended_value is not None else None
            ),
            "currency": rec.currency,
            "confidence_score": str(rec.confidence_score),
            "model_version": rec.model_version,
            "input_context": rec.input_context,
            "created_at": rec.created_at.isoformat(),
        }

    @staticmethod
    def _prediction_snapshot(pred) -> dict[str, Any]:
        return {
            "id": str(pred.id),
            "prediction_type": pred.prediction_type,
            "vehicle_id": str(pred.vehicle_id) if pred.vehicle_id else None,
            "predicted_value": str(pred.predicted_value),
            "unit": pred.unit,
            "confidence_score": str(pred.confidence_score),
            "model_version": pred.model_version,
            "valid_until": pred.valid_until.isoformat() if pred.valid_until else None,
            "metadata": pred.metadata_,
            "created_at": pred.created_at.isoformat(),
        }

    @staticmethod
    def _decision_snapshot(decision) -> dict[str, Any]:
        return {
            "id": str(decision.id),
            "decision_type": decision.decision_type,
            "status": decision.status,
            "recommendation_id": (
                str(decision.recommendation_id) if decision.recommendation_id else None
            ),
            "prediction_id": (
                str(decision.prediction_id) if decision.prediction_id else None
            ),
            "vehicle_id": str(decision.vehicle_id) if decision.vehicle_id else None,
            "applied_value": (
                str(decision.applied_value) if decision.applied_value is not None else None
            ),
            "model_version": decision.model_version,
            "decided_at": (
                decision.decided_at.isoformat() if decision.decided_at else None
            ),
        }

    @staticmethod
    def _feedback_snapshot(feedback) -> dict[str, Any]:
        return {
            "id": str(feedback.id),
            "rating": feedback.rating,
            "comment": feedback.comment,
            "model_version": feedback.model_version,
            "recommendation_id": (
                str(feedback.recommendation_id) if feedback.recommendation_id else None
            ),
            "decision_id": (
                str(feedback.decision_id) if feedback.decision_id else None
            ),
            "created_at": feedback.created_at.isoformat(),
        }

    @staticmethod
    async def _get_vehicle(actor_id: int, vehicle_id: uuid.UUID):
        from services.pg_automotive_inventory_engine import AutomotiveInventoryEngineV1

        detail = await AutomotiveInventoryEngineV1.get_vehicle(actor_id, vehicle_id)
        return detail["vehicle"]

    @staticmethod
    async def _days_in_inventory(vehicle_id: uuid.UUID) -> int:
        async with get_session() as session:
            vehicle = await VehicleRepository(session).get_by_id(vehicle_id)
            if vehicle is None:
                return 0
            return max(0, (datetime.now(timezone.utc) - vehicle.created_at).days)

    @staticmethod
    async def _similar_vehicle_prices(
        session,
        make: str,
        model: str,
    ) -> tuple[Decimal | None, Decimal | None]:
        vehicles = await VehicleRepository(session).list_all(limit=500)
        purchases: list[float] = []
        sales: list[float] = []
        for v in vehicles:
            if v.make.lower() != make.lower() or v.model.lower() != model.lower():
                continue
            if v.purchase_price:
                purchases.append(float(v.purchase_price))
            if v.sale_price:
                sales.append(float(v.sale_price))
        avg_purchase = Decimal(str(statistics.mean(purchases))) if purchases else None
        avg_sale = Decimal(str(statistics.mean(sales))) if sales else None
        return avg_purchase, avg_sale

    @staticmethod
    async def recommend_purchase_price(
        actor_id: int,
        vehicle_id: uuid.UUID,
    ) -> dict[str, Any]:
        if not await AutomotiveAiCopilotEngineV1.user_can_access(actor_id):
            raise AutomotiveAiCopilotEngineError("Access denied")

        async with get_session() as session:
            vehicle = await VehicleRepository(session).get_by_id(vehicle_id)
            if vehicle is None:
                raise AutomotiveAiCopilotEngineError(f"Vehicle not found: {vehicle_id}")

            avg_purchase, _ = await AutomotiveAiCopilotEngineV1._similar_vehicle_prices(
                session, vehicle.make, vehicle.model
            )
            base = avg_purchase or vehicle.purchase_price or vehicle.target_price
            if base is None:
                raise AutomotiveAiCopilotEngineError("Insufficient pricing data")

            recommended = AutomotiveAiCopilotEngineV1._quantize(base * Decimal("0.97"))
            confidence = AutomotiveAiCopilotEngineV1._confidence(
                0.85 if avg_purchase else 0.65
            )

            rec = await AiRecommendationRepository(session).create(
                recommendation_type=RecommendationType.PURCHASE_PRICE.value,
                vehicle_id=vehicle_id,
                title=f"Purchase price for {vehicle.make} {vehicle.model}",
                summary=(
                    f"Recommended max purchase price based on "
                    f"{vehicle.make} {vehicle.model} market data."
                ),
                recommended_value=recommended,
                currency=vehicle.currency,
                confidence_score=confidence,
                model_version=MODEL_VERSION,
                input_context={
                    "make": vehicle.make,
                    "model": vehicle.model,
                    "year": vehicle.year,
                    "avg_market_purchase": str(avg_purchase) if avg_purchase else None,
                },
                created_by=actor_id,
            )
            return AutomotiveAiCopilotEngineV1._recommendation_snapshot(rec)

    @staticmethod
    async def recommend_sale_price(
        actor_id: int,
        vehicle_id: uuid.UUID,
    ) -> dict[str, Any]:
        if not await AutomotiveAiCopilotEngineV1.user_can_access(actor_id):
            raise AutomotiveAiCopilotEngineError("Access denied")

        async with get_session() as session:
            vehicle = await VehicleRepository(session).get_by_id(vehicle_id)
            if vehicle is None:
                raise AutomotiveAiCopilotEngineError(f"Vehicle not found: {vehicle_id}")

            cost = await VehicleCostRepository(session).get_by_vehicle(vehicle_id)
            _, avg_sale = await AutomotiveAiCopilotEngineV1._similar_vehicle_prices(
                session, vehicle.make, vehicle.model
            )

            if cost and cost.target_price:
                recommended = AutomotiveAiCopilotEngineV1._quantize(cost.target_price)
                confidence = 0.9
            elif vehicle.target_price:
                recommended = AutomotiveAiCopilotEngineV1._quantize(vehicle.target_price)
                confidence = 0.75
            elif avg_sale:
                recommended = AutomotiveAiCopilotEngineV1._quantize(
                    avg_sale * Decimal("1.03")
                )
                confidence = 0.7
            else:
                raise AutomotiveAiCopilotEngineError("Insufficient pricing data")

            rec = await AiRecommendationRepository(session).create(
                recommendation_type=RecommendationType.SALE_PRICE.value,
                vehicle_id=vehicle_id,
                title=f"Sale price for {vehicle.stock_number}",
                summary="Recommended list price based on cost sheet and market comps.",
                recommended_value=recommended,
                currency=vehicle.currency,
                confidence_score=AutomotiveAiCopilotEngineV1._confidence(confidence),
                model_version=MODEL_VERSION,
                input_context={
                    "target_price": str(vehicle.target_price) if vehicle.target_price else None,
                    "cost_target": str(cost.target_price) if cost else None,
                    "avg_market_sale": str(avg_sale) if avg_sale else None,
                },
                created_by=actor_id,
            )
            return AutomotiveAiCopilotEngineV1._recommendation_snapshot(rec)

    @staticmethod
    async def identify_slow_moving_inventory(
        actor_id: int,
    ) -> list[dict[str, Any]]:
        if not await AutomotiveAiCopilotEngineV1.user_can_access(actor_id):
            raise AutomotiveAiCopilotEngineError("Access denied")

        now = datetime.now(timezone.utc)
        results: list[dict[str, Any]] = []

        async with get_session() as session:
            vehicles = await VehicleRepository(session).list_by_status(
                VehicleStatus.IN_STOCK.value,
                limit=500,
            )
            for vehicle in vehicles:
                days = max(0, (now - vehicle.created_at).days)
                if days < SLOW_MOVING_DAYS:
                    continue
                rec = await AiRecommendationRepository(session).create(
                    recommendation_type=RecommendationType.SLOW_MOVING_INVENTORY.value,
                    vehicle_id=vehicle.id,
                    title=f"Slow moving: {vehicle.stock_number}",
                    summary=(
                        f"Vehicle in stock {days} days — consider price adjustment "
                        f"or liquidation."
                    ),
                    recommended_value=Decimal(str(days)),
                    currency=None,
                    confidence_score=AutomotiveAiCopilotEngineV1._confidence(
                        min(0.95, 0.6 + days / 300)
                    ),
                    model_version=MODEL_VERSION,
                    input_context={"days_in_inventory": days, "status": vehicle.status},
                    created_by=actor_id,
                )
                results.append(
                    AutomotiveAiCopilotEngineV1._recommendation_snapshot(rec)
                )
        return results

    @staticmethod
    async def recommend_liquidation_discount(
        actor_id: int,
        vehicle_id: uuid.UUID,
    ) -> dict[str, Any]:
        if not await AutomotiveAiCopilotEngineV1.user_can_access(actor_id):
            raise AutomotiveAiCopilotEngineError("Access denied")

        days = await AutomotiveAiCopilotEngineV1._days_in_inventory(vehicle_id)
        if days <= 60:
            discount = Decimal("0.05")
            confidence = 0.6
        elif days <= 90:
            discount = Decimal("0.10")
            confidence = 0.75
        elif days <= 120:
            discount = Decimal("0.15")
            confidence = 0.85
        else:
            discount = Decimal("0.20")
            confidence = 0.92

        async with get_session() as session:
            vehicle = await VehicleRepository(session).get_by_id(vehicle_id)
            if vehicle is None:
                raise AutomotiveAiCopilotEngineError(f"Vehicle not found: {vehicle_id}")

            rec = await AiRecommendationRepository(session).create(
                recommendation_type=RecommendationType.LIQUIDATION_DISCOUNT.value,
                vehicle_id=vehicle_id,
                title=f"Liquidation discount for {vehicle.stock_number}",
                summary=f"Recommend {discount * 100}% discount after {days} days in inventory.",
                recommended_value=discount,
                currency=None,
                confidence_score=AutomotiveAiCopilotEngineV1._confidence(confidence),
                model_version=MODEL_VERSION,
                input_context={"days_in_inventory": days},
                created_by=actor_id,
            )
            return AutomotiveAiCopilotEngineV1._recommendation_snapshot(rec)

    @staticmethod
    async def predict_sale_probability(
        actor_id: int,
        vehicle_id: uuid.UUID,
    ) -> dict[str, Any]:
        if not await AutomotiveAiCopilotEngineV1.user_can_access(actor_id):
            raise AutomotiveAiCopilotEngineError("Access denied")

        days = await AutomotiveAiCopilotEngineV1._days_in_inventory(vehicle_id)
        async with get_session() as session:
            vehicle = await VehicleRepository(session).get_by_id(vehicle_id)
            if vehicle is None:
                raise AutomotiveAiCopilotEngineError(f"Vehicle not found: {vehicle_id}")

            base_prob = max(0.1, 1.0 - days / 180.0)
            if vehicle.status == VehicleStatus.RESERVED.value:
                base_prob = min(0.95, base_prob + 0.3)
            elif vehicle.status == VehicleStatus.IN_STOCK.value:
                base_prob = max(0.15, base_prob)

            pred = await AiPredictionRepository(session).create(
                prediction_type=PredictionType.SALE_PROBABILITY.value,
                vehicle_id=vehicle_id,
                predicted_value=AutomotiveAiCopilotEngineV1._quantize(
                    Decimal(str(round(base_prob, 4)))
                ),
                unit="probability",
                confidence_score=AutomotiveAiCopilotEngineV1._confidence(0.7),
                model_version=MODEL_VERSION,
                valid_until=datetime.now(timezone.utc) + timedelta(days=30),
                metadata={"days_in_inventory": days, "status": vehicle.status},
                created_by=actor_id,
            )
            return AutomotiveAiCopilotEngineV1._prediction_snapshot(pred)

    @staticmethod
    async def predict_holding_period(
        actor_id: int,
        vehicle_id: uuid.UUID,
    ) -> dict[str, Any]:
        if not await AutomotiveAiCopilotEngineV1.user_can_access(actor_id):
            raise AutomotiveAiCopilotEngineError("Access denied")

        async with get_session() as session:
            vehicle = await VehicleRepository(session).get_by_id(vehicle_id)
            if vehicle is None:
                raise AutomotiveAiCopilotEngineError(f"Vehicle not found: {vehicle_id}")

            sold = await VehicleRepository(session).list_by_status(
                VehicleStatus.SOLD.value,
                limit=200,
            )
            periods: list[int] = []
            for v in sold:
                if v.make.lower() == vehicle.make.lower():
                    periods.append(max(1, (v.updated_at - v.created_at).days))

            predicted_days = int(statistics.mean(periods)) if periods else 45
            confidence = 0.8 if len(periods) >= 5 else 0.55

            pred = await AiPredictionRepository(session).create(
                prediction_type=PredictionType.HOLDING_PERIOD.value,
                vehicle_id=vehicle_id,
                predicted_value=Decimal(str(predicted_days)),
                unit="days",
                confidence_score=AutomotiveAiCopilotEngineV1._confidence(confidence),
                model_version=MODEL_VERSION,
                valid_until=datetime.now(timezone.utc) + timedelta(days=60),
                metadata={"sample_size": len(periods)},
                created_by=actor_id,
            )
            return AutomotiveAiCopilotEngineV1._prediction_snapshot(pred)

    @staticmethod
    async def estimate_expected_margin(
        actor_id: int,
        vehicle_id: uuid.UUID,
    ) -> dict[str, Any]:
        if not await AutomotiveAiCopilotEngineV1.user_can_access(actor_id):
            raise AutomotiveAiCopilotEngineError("Access denied")

        async with get_session() as session:
            cost = await VehicleCostRepository(session).get_by_vehicle(vehicle_id)
            if cost is None:
                vehicle = await VehicleRepository(session).get_by_id(vehicle_id)
                if vehicle is None:
                    raise AutomotiveAiCopilotEngineError(f"Vehicle not found: {vehicle_id}")
                purchase = vehicle.purchase_price or Decimal("0")
                if purchase <= 0:
                    raise AutomotiveAiCopilotEngineError("No cost data for vehicle")

                from services.pg_automotive_cost_engine import AutomotiveCostEngineV1

                await AutomotiveCostEngineV1.build_default_cost_sheet(
                    actor_id,
                    vehicle_id,
                    purchase_amount=purchase,
                    currency=vehicle.currency,
                )
                cost = await VehicleCostRepository(session).get_by_vehicle(vehicle_id)

            if cost is None or cost.total_cost <= 0:
                raise AutomotiveAiCopilotEngineError("No cost data for vehicle")

            margin_pct = (
                (cost.margin_amount / cost.total_cost) * Decimal("100")
            ).quantize(Decimal("0.01"))

            pred = await AiPredictionRepository(session).create(
                prediction_type=PredictionType.EXPECTED_MARGIN.value,
                vehicle_id=vehicle_id,
                predicted_value=margin_pct,
                unit="percent",
                confidence_score=AutomotiveAiCopilotEngineV1._confidence(0.82),
                model_version=MODEL_VERSION,
                valid_until=datetime.now(timezone.utc) + timedelta(days=30),
                metadata={
                    "total_cost": str(cost.total_cost),
                    "margin_amount": str(cost.margin_amount),
                    "target_price": str(cost.target_price),
                },
                created_by=actor_id,
            )
            return AutomotiveAiCopilotEngineV1._prediction_snapshot(pred)

    @staticmethod
    async def detect_abnormal_costs(
        actor_id: int,
        vehicle_id: uuid.UUID,
    ) -> list[dict[str, Any]]:
        if not await AutomotiveAiCopilotEngineV1.user_can_access(actor_id):
            raise AutomotiveAiCopilotEngineError("Access denied")

        results: list[dict[str, Any]] = []
        async with get_session() as session:
            items = await VehicleCostItemRepository(session).list_by_vehicle(vehicle_id)
            if len(items) < 2:
                return results

            amounts = [float(item.amount) for item in items]
            mean = statistics.mean(amounts)
            stdev = statistics.stdev(amounts) if len(amounts) > 1 else 0
            threshold = mean + 2 * stdev

            for item in items:
                if float(item.amount) <= threshold:
                    continue
                rec = await AiRecommendationRepository(session).create(
                    recommendation_type=RecommendationType.ABNORMAL_COST.value,
                    vehicle_id=vehicle_id,
                    entity_type="cost_item",
                    entity_id=str(item.id),
                    title=f"Abnormal cost: {item.cost_type}",
                    summary=(
                        f"Cost item {item.cost_type} (${item.amount}) exceeds "
                        f"expected range (threshold ${threshold:.2f})."
                    ),
                    recommended_value=item.amount,
                    currency=item.currency,
                    confidence_score=AutomotiveAiCopilotEngineV1._confidence(0.78),
                    model_version=MODEL_VERSION,
                    input_context={
                        "cost_type": item.cost_type,
                        "mean": mean,
                        "threshold": threshold,
                    },
                    created_by=actor_id,
                )
                results.append(
                    AutomotiveAiCopilotEngineV1._recommendation_snapshot(rec)
                )
        return results

    @staticmethod
    async def identify_risky_suppliers(
        actor_id: int,
    ) -> list[dict[str, Any]]:
        if not await AutomotiveAiCopilotEngineV1.user_can_access(actor_id):
            raise AutomotiveAiCopilotEngineError("Access denied")

        from services.pg_automotive_analytics_engine import AutomotiveAnalyticsEngineV1

        analytics = await AutomotiveAnalyticsEngineV1.get_supplier_analytics(actor_id)
        results: list[dict[str, Any]] = []

        async with get_session() as session:
            for row in analytics.get("suppliers", []):
                low_stock = row.get("low_stock_count", 0)
                parts_count = row.get("parts_count", 0)
                risk_score = low_stock / max(parts_count, 1)
                if risk_score < 0.3 and low_stock < 3:
                    continue

                rec = await AiRecommendationRepository(session).create(
                    recommendation_type=RecommendationType.RISKY_SUPPLIER.value,
                    entity_type="supplier",
                    entity_id=row["supplier_id"],
                    title=f"Risky supplier: {row['name']}",
                    summary=(
                        f"Supplier has {low_stock} low-stock parts out of "
                        f"{parts_count} tracked parts."
                    ),
                    recommended_value=Decimal(str(round(risk_score, 4))),
                    confidence_score=AutomotiveAiCopilotEngineV1._confidence(
                        min(0.9, 0.5 + risk_score)
                    ),
                    model_version=MODEL_VERSION,
                    input_context=row,
                    created_by=actor_id,
                )
                results.append(
                    AutomotiveAiCopilotEngineV1._recommendation_snapshot(rec)
                )
        return results

    @staticmethod
    async def identify_profitable_regions(
        actor_id: int,
    ) -> list[dict[str, Any]]:
        if not await AutomotiveAiCopilotEngineV1.user_can_access(actor_id):
            raise AutomotiveAiCopilotEngineError("Access denied")

        region_stats: dict[str, dict[str, Any]] = {}
        async with get_session() as session:
            vehicles = await VehicleRepository(session).list_all(limit=1000)
            for vehicle in vehicles:
                region = "UNKNOWN"
                if vehicle.notes and "region:" in vehicle.notes.lower():
                    region = vehicle.notes.split("region:")[-1].strip().split()[0]
                entry = region_stats.setdefault(
                    region,
                    {"count": 0, "revenue": Decimal("0"), "margin": Decimal("0")},
                )
                entry["count"] += 1
                if vehicle.sale_price:
                    entry["revenue"] += vehicle.sale_price
                if vehicle.sale_price and vehicle.purchase_price:
                    entry["margin"] += vehicle.sale_price - vehicle.purchase_price

            results: list[dict[str, Any]] = []
            for region, stats in sorted(
                region_stats.items(),
                key=lambda x: float(x[1]["margin"]),
                reverse=True,
            ):
                if stats["count"] == 0:
                    continue
                avg_margin = stats["margin"] / stats["count"]
                rec = await AiRecommendationRepository(session).create(
                    recommendation_type=RecommendationType.PROFITABLE_REGION.value,
                    entity_type="region",
                    entity_id=region,
                    title=f"Region performance: {region}",
                    summary=(
                        f"{stats['count']} vehicles, avg margin "
                        f"${AutomotiveAiCopilotEngineV1._quantize(avg_margin)}."
                    ),
                    recommended_value=AutomotiveAiCopilotEngineV1._quantize(avg_margin),
                    currency="USD",
                    confidence_score=AutomotiveAiCopilotEngineV1._confidence(
                        min(0.9, 0.5 + stats["count"] / 20)
                    ),
                    model_version=MODEL_VERSION,
                    input_context={
                        "region": region,
                        "vehicle_count": stats["count"],
                        "total_revenue": str(stats["revenue"]),
                        "total_margin": str(stats["margin"]),
                    },
                    created_by=actor_id,
                )
                results.append(
                    AutomotiveAiCopilotEngineV1._recommendation_snapshot(rec)
                )
        return results

    @staticmethod
    async def record_decision(
        actor_id: int,
        *,
        decision_type: str,
        recommendation_id: uuid.UUID | None = None,
        prediction_id: uuid.UUID | None = None,
        vehicle_id: uuid.UUID | None = None,
        status: str = DecisionStatus.ACCEPTED.value,
        applied_value: Decimal | None = None,
        notes: str | None = None,
    ) -> dict[str, Any]:
        if not await AutomotiveAiCopilotEngineV1.user_can_access(actor_id):
            raise AutomotiveAiCopilotEngineError("Access denied")

        async with get_session() as session:
            decision = await AiDecisionRepository(session).create(
                decision_type=decision_type,
                model_version=MODEL_VERSION,
                recommendation_id=recommendation_id,
                prediction_id=prediction_id,
                vehicle_id=vehicle_id,
                status=status,
            )
            decision = await AiDecisionRepository(session).update_status(
                decision.id,
                status,
                decided_by=actor_id,
                applied_value=applied_value,
                notes=notes,
            )
            return AutomotiveAiCopilotEngineV1._decision_snapshot(decision)

    @staticmethod
    async def submit_feedback(
        actor_id: int,
        *,
        rating: str,
        recommendation_id: uuid.UUID | None = None,
        decision_id: uuid.UUID | None = None,
        comment: str | None = None,
        model_version: str = MODEL_VERSION,
    ) -> dict[str, Any]:
        if not await AutomotiveAiCopilotEngineV1.user_can_access(actor_id):
            raise AutomotiveAiCopilotEngineError("Access denied")
        if rating not in {r.value for r in FeedbackRating}:
            raise AutomotiveAiCopilotEngineError(f"Invalid rating: {rating}")

        async with get_session() as session:
            feedback = await AiFeedbackRepository(session).create(
                rating=rating,
                model_version=model_version,
                recommendation_id=recommendation_id,
                decision_id=decision_id,
                comment=comment,
                submitted_by=actor_id,
            )
            return AutomotiveAiCopilotEngineV1._feedback_snapshot(feedback)

    @staticmethod
    async def get_recommendation_history(
        actor_id: int,
        *,
        model_version: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        if not await AutomotiveAiCopilotEngineV1.user_can_access(actor_id):
            raise AutomotiveAiCopilotEngineError("Access denied")

        async with get_session() as session:
            recs = await AiRecommendationRepository(session).list_history(
                model_version=model_version or MODEL_VERSION,
                limit=limit,
            )
            return [
                AutomotiveAiCopilotEngineV1._recommendation_snapshot(r) for r in recs
            ]

    @staticmethod
    async def analyze_vehicle(
        actor_id: int,
        vehicle_id: uuid.UUID,
    ) -> dict[str, Any]:
        if not await AutomotiveAiCopilotEngineV1.user_can_access(actor_id):
            raise AutomotiveAiCopilotEngineError("Access denied")

        purchase = await AutomotiveAiCopilotEngineV1.recommend_purchase_price(
            actor_id, vehicle_id
        )
        sale = await AutomotiveAiCopilotEngineV1.recommend_sale_price(actor_id, vehicle_id)
        liquidation = await AutomotiveAiCopilotEngineV1.recommend_liquidation_discount(
            actor_id, vehicle_id
        )
        sale_prob = await AutomotiveAiCopilotEngineV1.predict_sale_probability(
            actor_id, vehicle_id
        )
        holding = await AutomotiveAiCopilotEngineV1.predict_holding_period(
            actor_id, vehicle_id
        )
        margin = await AutomotiveAiCopilotEngineV1.estimate_expected_margin(
            actor_id, vehicle_id
        )
        abnormal = await AutomotiveAiCopilotEngineV1.detect_abnormal_costs(
            actor_id, vehicle_id
        )

        return {
            "vehicle_id": str(vehicle_id),
            "model_version": MODEL_VERSION,
            "recommendations": {
                "purchase_price": purchase,
                "sale_price": sale,
                "liquidation_discount": liquidation,
                "abnormal_costs": abnormal,
            },
            "predictions": {
                "sale_probability": sale_prob,
                "holding_period": holding,
                "expected_margin": margin,
            },
        }
