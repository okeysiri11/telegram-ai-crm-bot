# Sprint 8.6 — Analytics, BI, KPI and dashboard models.

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


class DashboardKind(str, enum.Enum):
    EXECUTIVE = "executive"
    FARMER = "farmer"
    BUYER = "buyer"
    SUPPLIER = "supplier"
    EXPORTER = "exporter"
    WAREHOUSE = "warehouse"
    LOGISTICS = "logistics"
    MARKETPLACE = "marketplace"


class KPIName(str, enum.Enum):
    REVENUE = "revenue"
    GROSS_MARGIN = "gross_margin"
    ORDER_VOLUME = "order_volume"
    MARKETPLACE_GROWTH = "marketplace_growth"
    EXPORT_VOLUME = "export_volume"
    INVENTORY_TURNOVER = "inventory_turnover"
    WAREHOUSE_UTILIZATION = "warehouse_utilization"
    FARMER_ACTIVITY = "farmer_activity"
    BUYER_CONVERSION = "buyer_conversion"
    AI_PERFORMANCE = "ai_performance"


class InsightKind(str, enum.Enum):
    OPPORTUNITY = "opportunity"
    RISK = "risk"
    ANOMALY = "anomaly"
    OPTIMIZATION = "optimization"
    TREND = "trend"


class AnalyticsDomain(str, enum.Enum):
    SALES = "sales"
    INVENTORY = "inventory"
    HARVEST = "harvest"
    CROP = "crop"
    DEMAND = "demand"
    SUPPLY = "supply"
    PRICING = "pricing"
    EXPORT = "export"
    CUSTOMER = "customer"
    REGIONAL = "regional"


@dataclass
class KPISnapshot:
    snapshot_id: str = field(default_factory=_id)
    name: KPIName = KPIName.REVENUE
    value: float = 0.0
    unit: str = ""
    target: float = 0.0
    trend: float = 0.0
    period: str = "current"
    metadata: dict[str, Any] = field(default_factory=dict)
    calculated_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "name": self.name.value,
            "value": self.value,
            "unit": self.unit,
            "target": self.target,
            "trend": self.trend,
            "period": self.period,
            "metadata": dict(self.metadata),
            "calculated_at": self.calculated_at,
        }


@dataclass
class Insight:
    insight_id: str = field(default_factory=_id)
    kind: InsightKind = InsightKind.TREND
    title: str = ""
    summary: str = ""
    score: float = 0.0
    domain: str = ""
    actions: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "insight_id": self.insight_id,
            "kind": self.kind.value,
            "title": self.title,
            "summary": self.summary,
            "score": self.score,
            "domain": self.domain,
            "actions": list(self.actions),
            "metadata": dict(self.metadata),
            "created_at": self.created_at,
        }


@dataclass
class Anomaly:
    anomaly_id: str = field(default_factory=_id)
    metric: str = ""
    observed: float = 0.0
    expected: float = 0.0
    severity: str = "medium"
    domain: str = ""
    notes: str = ""
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "anomaly_id": self.anomaly_id,
            "metric": self.metric,
            "observed": self.observed,
            "expected": self.expected,
            "severity": self.severity,
            "domain": self.domain,
            "notes": self.notes,
            "created_at": self.created_at,
        }


@dataclass
class DashboardSnapshot:
    snapshot_id: str = field(default_factory=_id)
    kind: DashboardKind = DashboardKind.EXECUTIVE
    title: str = ""
    widgets: list[dict[str, Any]] = field(default_factory=list)
    kpis: list[dict[str, Any]] = field(default_factory=list)
    insights: list[dict[str, Any]] = field(default_factory=list)
    subject_id: str = ""
    updated_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "kind": self.kind.value,
            "title": self.title,
            "widgets": list(self.widgets),
            "kpis": list(self.kpis),
            "insights": list(self.insights),
            "subject_id": self.subject_id,
            "updated_at": self.updated_at,
        }


@dataclass
class BIReport:
    report_id: str = field(default_factory=_id)
    title: str = ""
    report_type: str = "executive"
    summary: str = ""
    sections: list[dict[str, Any]] = field(default_factory=list)
    kpis: list[dict[str, Any]] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "report_id": self.report_id,
            "title": self.title,
            "report_type": self.report_type,
            "summary": self.summary,
            "sections": list(self.sections),
            "kpis": list(self.kpis),
            "recommendations": list(self.recommendations),
            "created_at": self.created_at,
        }


@dataclass
class SimulationScenario:
    scenario_id: str = field(default_factory=_id)
    name: str = ""
    description: str = ""
    inputs: dict[str, Any] = field(default_factory=dict)
    results: dict[str, Any] = field(default_factory=dict)
    status: str = "draft"
    created_at: float = field(default_factory=_ts)
    completed_at: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "scenario_id": self.scenario_id,
            "name": self.name,
            "description": self.description,
            "inputs": dict(self.inputs),
            "results": dict(self.results),
            "status": self.status,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
        }


@dataclass
class MetricPoint:
    metric_id: str = field(default_factory=_id)
    name: str = ""
    value: float = 0.0
    unit: str = ""
    domain: str = ""
    dimensions: dict[str, str] = field(default_factory=dict)
    recorded_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "metric_id": self.metric_id,
            "name": self.name,
            "value": self.value,
            "unit": self.unit,
            "domain": self.domain,
            "dimensions": dict(self.dimensions),
            "recorded_at": self.recorded_at,
        }
