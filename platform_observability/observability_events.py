# Observability events — published to Platform EventBus.

from __future__ import annotations

from dataclasses import dataclass

from events.base_event import BaseEvent


@dataclass(kw_only=True)
class AlertRaisedEvent(BaseEvent):
    alert_id: str
    name: str
    severity: str
    source: str
    message: str


@dataclass(kw_only=True)
class AlertResolvedEvent(BaseEvent):
    alert_id: str
    name: str
    source: str


@dataclass(kw_only=True)
class HealthChangedEvent(BaseEvent):
    component: str
    previous_status: str
    current_status: str


@dataclass(kw_only=True)
class MetricThresholdExceededEvent(BaseEvent):
    metric_name: str
    value: float
    threshold: float
    severity: str = "warning"
