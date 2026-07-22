# Sprint 10.3 — AI vehicle intelligence models.

from __future__ import annotations

import enum
import time
import uuid
from dataclasses import dataclass, field
from typing import Any


def _id() -> str:
    return str(uuid.uuid4())


def _ts() -> float:
    return time.time()


class RecommendationKind(str, enum.Enum):
    PERSONAL = "personal"
    SIMILAR = "similar"
    ALTERNATIVE = "alternative"
    BUDGET = "budget_optimization"
    OWNERSHIP_COST = "ownership_cost"
    FAMILY = "family"
    COMMERCIAL = "commercial"
    FLEET = "fleet"


@dataclass
class SmartRecommendation:
    recommendation_id: str = field(default_factory=_id)
    kind: RecommendationKind = RecommendationKind.PERSONAL
    buyer_id: str = ""
    vehicle_id: str = ""
    score: float = 0.0
    reason: str = ""
    payload: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "recommendation_id": self.recommendation_id,
            "kind": self.kind.value,
            "buyer_id": self.buyer_id,
            "vehicle_id": self.vehicle_id,
            "score": self.score,
            "reason": self.reason,
            "payload": dict(self.payload),
            "created_at": self.created_at,
        }


@dataclass
class AIPriceInsight:
    insight_id: str = field(default_factory=_id)
    vehicle_id: str = ""
    vin: str = ""
    market_value: float = 0.0
    fair_price: float = 0.0
    dealer_price: float = 0.0
    wholesale_price: float = 0.0
    retail_price: float = 0.0
    predicted_price: float = 0.0
    trend: str = "stable"
    depreciation_12m: float = 0.0
    residual_value_36m: float = 0.0
    currency: str = "USD"
    confidence: float = 0.7
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "insight_id": self.insight_id,
            "vehicle_id": self.vehicle_id,
            "vin": self.vin,
            "market_value": self.market_value,
            "fair_price": self.fair_price,
            "dealer_price": self.dealer_price,
            "wholesale_price": self.wholesale_price,
            "retail_price": self.retail_price,
            "predicted_price": self.predicted_price,
            "trend": self.trend,
            "depreciation_12m": self.depreciation_12m,
            "residual_value_36m": self.residual_value_36m,
            "currency": self.currency,
            "confidence": self.confidence,
            "created_at": self.created_at,
        }


@dataclass
class AIInspectionResult:
    analysis_id: str = field(default_factory=_id)
    vehicle_id: str = ""
    photo_urls: list[str] = field(default_factory=list)
    damage_detected: list[dict[str, Any]] = field(default_factory=list)
    paint_score: float = 0.0
    body_alignment_score: float = 0.0
    wheel_score: float = 0.0
    interior_score: float = 0.0
    engine_bay_score: float = 0.0
    risk_score: float = 0.0
    repair_estimate: float = 0.0
    overall_score: float = 0.0
    findings: list[str] = field(default_factory=list)
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "analysis_id": self.analysis_id,
            "vehicle_id": self.vehicle_id,
            "photo_urls": list(self.photo_urls),
            "damage_detected": list(self.damage_detected),
            "paint_score": self.paint_score,
            "body_alignment_score": self.body_alignment_score,
            "wheel_score": self.wheel_score,
            "interior_score": self.interior_score,
            "engine_bay_score": self.engine_bay_score,
            "risk_score": self.risk_score,
            "repair_estimate": self.repair_estimate,
            "overall_score": self.overall_score,
            "findings": list(self.findings),
            "created_at": self.created_at,
        }


@dataclass
class VehicleForecast:
    forecast_id: str = field(default_factory=_id)
    vehicle_id: str = ""
    vin: str = ""
    future_value: float = 0.0
    maintenance_cost_12m: float = 0.0
    repair_probability: float = 0.0
    insurance_risk: float = 0.0
    ownership_cost_12m: float = 0.0
    market_demand: str = "medium"
    currency: str = "USD"
    horizon_months: int = 12
    confidence: float = 0.7
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "forecast_id": self.forecast_id,
            "vehicle_id": self.vehicle_id,
            "vin": self.vin,
            "future_value": self.future_value,
            "maintenance_cost_12m": self.maintenance_cost_12m,
            "repair_probability": self.repair_probability,
            "insurance_risk": self.insurance_risk,
            "ownership_cost_12m": self.ownership_cost_12m,
            "market_demand": self.market_demand,
            "currency": self.currency,
            "horizon_months": self.horizon_months,
            "confidence": self.confidence,
            "created_at": self.created_at,
        }


@dataclass
class AssistantReply:
    reply_id: str = field(default_factory=_id)
    session_id: str = ""
    query: str = ""
    intent: str = ""
    answer: str = ""
    suggestions: list[str] = field(default_factory=list)
    vehicles: list[dict[str, Any]] = field(default_factory=list)
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "reply_id": self.reply_id,
            "session_id": self.session_id,
            "query": self.query,
            "intent": self.intent,
            "answer": self.answer,
            "suggestions": list(self.suggestions),
            "vehicles": list(self.vehicles),
            "created_at": self.created_at,
        }


@dataclass
class VehicleKnowledgeCard:
    card_id: str = field(default_factory=_id)
    make: str = ""
    model: str = ""
    year: int = 0
    specifications: dict[str, Any] = field(default_factory=dict)
    common_problems: list[str] = field(default_factory=list)
    recalls: list[str] = field(default_factory=list)
    maintenance_schedule: list[dict[str, Any]] = field(default_factory=list)
    reliability_rating: float = 0.0
    fuel_consumption_l_100km: float = 0.0
    service_intervals_km: int = 10000
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "card_id": self.card_id,
            "make": self.make,
            "model": self.model,
            "year": self.year,
            "specifications": dict(self.specifications),
            "common_problems": list(self.common_problems),
            "recalls": list(self.recalls),
            "maintenance_schedule": list(self.maintenance_schedule),
            "reliability_rating": self.reliability_rating,
            "fuel_consumption_l_100km": self.fuel_consumption_l_100km,
            "service_intervals_km": self.service_intervals_km,
            "created_at": self.created_at,
        }
