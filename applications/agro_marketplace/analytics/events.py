# Sprint 8.6 — Analytics / BI events.

from __future__ import annotations

from dataclasses import dataclass, field

from events.base_event import BaseEvent


@dataclass(kw_only=True)
class DashboardUpdatedEvent(BaseEvent):
    dashboard_kind: str = ""
    snapshot_id: str = ""


@dataclass(kw_only=True)
class ForecastGeneratedEvent(BaseEvent):
    forecast_id: str = ""
    kind: str = ""
    subject: str = ""
    confidence: float = 0.0


@dataclass(kw_only=True)
class InsightGeneratedEvent(BaseEvent):
    insight_id: str = ""
    kind: str = ""
    title: str = ""
    score: float = 0.0


@dataclass(kw_only=True)
class AnomalyDetectedEvent(BaseEvent):
    anomaly_id: str = ""
    metric: str = ""
    severity: str = ""
    observed: float = 0.0


@dataclass(kw_only=True)
class ExecutiveReportCreatedEvent(BaseEvent):
    report_id: str = ""
    title: str = ""


@dataclass(kw_only=True)
class KPICalculatedEvent(BaseEvent):
    snapshot_id: str = ""
    name: str = ""
    value: float = 0.0


@dataclass(kw_only=True)
class SimulationCompletedEvent(BaseEvent):
    scenario_id: str = ""
    name: str = ""
    status: str = ""
