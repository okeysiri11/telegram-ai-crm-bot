# Sprint 9.6 — Digital Twin, AI ops, simulation, alerts models.

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


class AlertSeverity(str, enum.Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertType(str, enum.Enum):
    CRITICAL_CONGESTION = "critical_congestion"
    ETA_VIOLATION = "eta_violation"
    EQUIPMENT_FAILURE = "equipment_failure"
    CONTAINER_DELAY = "container_delay"
    CUSTOMS_DELAY = "customs_delay"
    WEATHER_WARNING = "weather_warning"
    SAFETY_EVENT = "safety_event"
    CAPACITY_THRESHOLD = "capacity_threshold"


class SimulationScenario(str, enum.Enum):
    STORM_DELAYS = "storm_delays"
    EQUIPMENT_FAILURES = "equipment_failures"
    TRAFFIC_OVERLOAD = "traffic_overload"
    TERMINAL_SHUTDOWN = "terminal_shutdown"
    BERTH_UNAVAILABLE = "berth_unavailable"
    CONTAINER_OVERFLOW = "container_overflow"
    PEAK_SEASON = "peak_season"
    EMERGENCY_RESPONSE = "emergency_response"


class WeatherCondition(str, enum.Enum):
    CLEAR = "clear"
    CLOUDY = "cloudy"
    RAIN = "rain"
    STORM = "storm"
    FOG = "fog"


@dataclass
class WeatherState:
    condition: WeatherCondition = WeatherCondition.CLEAR
    wind_knots: float = 0.0
    visibility_km: float = 10.0
    temperature_c: float = 25.0
    updated_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "condition": self.condition.value,
            "wind_knots": self.wind_knots,
            "visibility_km": self.visibility_km,
            "temperature_c": self.temperature_c,
            "updated_at": self.updated_at,
        }


@dataclass
class TwinSnapshot:
    snapshot_id: str = field(default_factory=_id)
    port_id: str = ""
    ships: int = 0
    berths: int = 0
    berths_occupied: int = 0
    warehouses: int = 0
    yards_slots: int = 0
    yards_occupied: int = 0
    equipment: int = 0
    containers: int = 0
    vehicles: int = 0
    rail_assets: int = 0
    road_assets: int = 0
    weather: WeatherState = field(default_factory=WeatherState)
    utilization: float = 0.0
    created_at: float = field(default_factory=_ts)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "port_id": self.port_id,
            "ships": self.ships,
            "berths": self.berths,
            "berths_occupied": self.berths_occupied,
            "warehouses": self.warehouses,
            "yards_slots": self.yards_slots,
            "yards_occupied": self.yards_occupied,
            "equipment": self.equipment,
            "containers": self.containers,
            "vehicles": self.vehicles,
            "rail_assets": self.rail_assets,
            "road_assets": self.road_assets,
            "weather": self.weather.to_dict(),
            "utilization": self.utilization,
            "created_at": self.created_at,
            "metadata": dict(self.metadata),
        }


@dataclass
class PortAlert:
    alert_id: str = field(default_factory=_id)
    alert_type: AlertType = AlertType.CAPACITY_THRESHOLD
    severity: AlertSeverity = AlertSeverity.WARNING
    title: str = ""
    message: str = ""
    related_id: str = ""
    acknowledged: bool = False
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "alert_id": self.alert_id,
            "alert_type": self.alert_type.value,
            "severity": self.severity.value,
            "title": self.title,
            "message": self.message,
            "related_id": self.related_id,
            "acknowledged": self.acknowledged,
            "created_at": self.created_at,
        }


@dataclass
class SimulationRun:
    run_id: str = field(default_factory=_id)
    scenario: SimulationScenario = SimulationScenario.PEAK_SEASON
    name: str = ""
    parameters: dict[str, Any] = field(default_factory=dict)
    impact: dict[str, Any] = field(default_factory=dict)
    recommendations: list[str] = field(default_factory=list)
    status: str = "completed"
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "scenario": self.scenario.value,
            "name": self.name,
            "parameters": dict(self.parameters),
            "impact": dict(self.impact),
            "recommendations": list(self.recommendations),
            "status": self.status,
            "created_at": self.created_at,
        }


@dataclass
class OptimizationPlan:
    plan_id: str = field(default_factory=_id)
    plan_type: str = "berth_allocation"
    title: str = ""
    actions: list[dict[str, Any]] = field(default_factory=list)
    score: float = 0.0
    status: str = "proposed"
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "plan_type": self.plan_type,
            "title": self.title,
            "actions": list(self.actions),
            "score": self.score,
            "status": self.status,
            "created_at": self.created_at,
        }


@dataclass
class PredictionResult:
    prediction_id: str = field(default_factory=_id)
    prediction_type: str = "queue"
    subject: str = ""
    value: float = 0.0
    unit: str = ""
    confidence: float = 0.0
    horizon_hours: float = 24.0
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "prediction_id": self.prediction_id,
            "prediction_type": self.prediction_type,
            "subject": self.subject,
            "value": self.value,
            "unit": self.unit,
            "confidence": self.confidence,
            "horizon_hours": self.horizon_hours,
            "metadata": dict(self.metadata),
            "created_at": self.created_at,
        }


@dataclass
class ExecutiveKPI:
    name: str = ""
    value: float = 0.0
    unit: str = ""
    status: str = "ok"
    trend: str = "stable"

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "value": self.value,
            "unit": self.unit,
            "status": self.status,
            "trend": self.trend,
        }


@dataclass
class DecisionRecommendation:
    recommendation_id: str = field(default_factory=_id)
    title: str = ""
    rationale: str = ""
    priority: str = "medium"
    actions: list[str] = field(default_factory=list)
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "recommendation_id": self.recommendation_id,
            "title": self.title,
            "rationale": self.rationale,
            "priority": self.priority,
            "actions": list(self.actions),
            "created_at": self.created_at,
        }
