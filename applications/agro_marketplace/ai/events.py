# Sprint 8.4 — Agricultural AI events.

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from events.base_event import BaseEvent


@dataclass(kw_only=True)
class RecommendationGeneratedEvent(BaseEvent):
    recommendation_id: str = ""
    kind: str = ""
    subject_id: str = ""
    count: int = 0


@dataclass(kw_only=True)
class ForecastCompletedEvent(BaseEvent):
    forecast_id: str = ""
    kind: str = ""
    subject: str = ""
    confidence: float = 0.0


@dataclass(kw_only=True)
class LeadQualifiedAIEvent(BaseEvent):
    lead_id: str = ""
    score: float = 0.0
    qualified: bool = False


@dataclass(kw_only=True)
class PriceEstimatedEvent(BaseEvent):
    product_id: str = ""
    estimated_price: float = 0.0
    currency: str = "USD"


@dataclass(kw_only=True)
class DemandPredictedEvent(BaseEvent):
    subject: str = ""
    region: str = ""
    predicted_demand: float = 0.0


@dataclass(kw_only=True)
class TradeOpportunityDetectedEvent(BaseEvent):
    opportunity_count: int = 0
    top_score: float = 0.0
    opportunities: list[dict[str, Any]] = field(default_factory=list)


@dataclass(kw_only=True)
class ExecutiveReportGeneratedEvent(BaseEvent):
    report_id: str = ""
    title: str = ""
