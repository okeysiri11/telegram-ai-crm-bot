# Business Intelligence events — Sprint 6.6.

from __future__ import annotations

from dataclasses import dataclass

from events.base_event import BaseEvent


@dataclass(kw_only=True)
class DashboardUpdatedEvent(BaseEvent):
    snapshot_id: str = ""
    role: str = ""


@dataclass(kw_only=True)
class BIReportGeneratedEvent(BaseEvent):
    report_id: str = ""
    period: str = ""
    title: str = ""


@dataclass(kw_only=True)
class ForecastCompletedEvent(BaseEvent):
    forecast_id: str = ""
    forecast_type: str = ""
    confidence: float = 0.0


@dataclass(kw_only=True)
class InsightGeneratedEvent(BaseEvent):
    insight_id: str = ""
    insight_type: str = ""
    title: str = ""


@dataclass(kw_only=True)
class RiskDetectedEvent(BaseEvent):
    insight_id: str = ""
    title: str = ""
    severity: str = ""


@dataclass(kw_only=True)
class OpportunityDetectedEvent(BaseEvent):
    insight_id: str = ""
    title: str = ""
    metadata: dict | None = None
