# Business Intelligence domain models — Sprint 6.6.

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


class DashboardRole(str, enum.Enum):
    OWNER = "owner"
    ADMINISTRATOR = "administrator"
    SALES_MANAGER = "sales_manager"
    DEALER = "dealer"
    FINANCE_MANAGER = "finance_manager"
    OPERATIONS = "operations"
    AI_AGENT = "ai_agent"


class ReportPeriod(str, enum.Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUAL = "annual"
    CUSTOM = "custom"


class InsightType(str, enum.Enum):
    ANOMALY = "anomaly"
    TREND = "trend"
    OPPORTUNITY = "opportunity"
    RISK = "risk"
    RECOMMENDATION = "recommendation"
    ALERT = "alert"


class ExportFormat(str, enum.Enum):
    PDF = "pdf"
    EXCEL = "excel"
    CSV = "csv"


@dataclass
class KPIValue:
    name: str = ""
    value: float = 0.0
    unit: str = ""
    change_pct: float = 0.0
    target: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "value": self.value,
            "unit": self.unit,
            "change_pct": self.change_pct,
            "target": self.target,
        }


@dataclass
class DashboardSnapshot:
    snapshot_id: str = field(default_factory=_id)
    role: DashboardRole = DashboardRole.OWNER
    title: str = ""
    widgets: list[dict[str, Any]] = field(default_factory=list)
    kpis: list[KPIValue] = field(default_factory=list)
    updated_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "role": self.role.value,
            "title": self.title,
            "widgets": list(self.widgets),
            "kpis": [k.to_dict() for k in self.kpis],
            "updated_at": self.updated_at,
        }


@dataclass
class ForecastResult:
    forecast_id: str = field(default_factory=_id)
    forecast_type: str = "sales"
    period_days: int = 30
    predictions: list[dict[str, Any]] = field(default_factory=list)
    confidence: float = 0.0
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "forecast_id": self.forecast_id,
            "forecast_type": self.forecast_type,
            "period_days": self.period_days,
            "predictions": list(self.predictions),
            "confidence": self.confidence,
            "created_at": self.created_at,
        }


@dataclass
class BusinessInsight:
    insight_id: str = field(default_factory=_id)
    insight_type: InsightType = InsightType.TREND
    title: str = ""
    description: str = ""
    severity: str = "info"
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "insight_id": self.insight_id,
            "insight_type": self.insight_type.value,
            "title": self.title,
            "description": self.description,
            "severity": self.severity,
            "metadata": dict(self.metadata),
            "created_at": self.created_at,
        }


@dataclass
class BIReport:
    report_id: str = field(default_factory=_id)
    title: str = ""
    period: ReportPeriod = ReportPeriod.DAILY
    sections: dict[str, Any] = field(default_factory=dict)
    export_urls: dict[str, str] = field(default_factory=dict)
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "report_id": self.report_id,
            "title": self.title,
            "period": self.period.value,
            "sections": dict(self.sections),
            "export_urls": dict(self.export_urls),
            "created_at": self.created_at,
        }


@dataclass
class ChartData:
    chart_id: str = field(default_factory=_id)
    chart_type: str = "line"
    title: str = ""
    labels: list[str] = field(default_factory=list)
    datasets: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "chart_id": self.chart_id,
            "chart_type": self.chart_type,
            "title": self.title,
            "labels": list(self.labels),
            "datasets": list(self.datasets),
        }
