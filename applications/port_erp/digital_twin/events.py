# Sprint 9.6 — AI operations events.

from __future__ import annotations

from dataclasses import dataclass

from events.base_event import BaseEvent


@dataclass(kw_only=True)
class TwinSnapshotTakenEvent(BaseEvent):
    snapshot_id: str = ""
    utilization: float = 0.0


@dataclass(kw_only=True)
class AlertRaisedEvent(BaseEvent):
    alert_id: str = ""
    alert_type: str = ""
    severity: str = ""


@dataclass(kw_only=True)
class SimulationCompletedEvent(BaseEvent):
    run_id: str = ""
    scenario: str = ""


@dataclass(kw_only=True)
class OptimizationProposedEvent(BaseEvent):
    plan_id: str = ""
    plan_type: str = ""
    score: float = 0.0


@dataclass(kw_only=True)
class ExecutiveBriefingReadyEvent(BaseEvent):
    briefing_id: str = ""
    kpi_count: int = 0
