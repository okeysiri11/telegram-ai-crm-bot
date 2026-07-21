# Workforce events — Sprint 7.4.

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from events.base_event import BaseEvent


@dataclass(kw_only=True)
class ExecutiveDecisionMadeEvent(BaseEvent):
    decision_id: str = ""
    executive_role: str = ""
    title: str = ""
    approved: bool = True
    task_id: str = ""


@dataclass(kw_only=True)
class DepartmentTaskAssignedEvent(BaseEvent):
    task_id: str = ""
    department_type: str = ""
    specialist_id: str = ""
    priority: str = ""


@dataclass(kw_only=True)
class WorkCompletedEvent(BaseEvent):
    task_id: str = ""
    department_type: str = ""
    specialist_id: str = ""
    result: dict[str, Any] = field(default_factory=dict)


@dataclass(kw_only=True)
class EscalationTriggeredEvent(BaseEvent):
    escalation_id: str = ""
    task_id: str = ""
    to_role: str = ""
    reason: str = ""


@dataclass(kw_only=True)
class ObjectiveCompletedEvent(BaseEvent):
    objective_id: str = ""
    title: str = ""
    horizon: str = ""


@dataclass(kw_only=True)
class PlanningUpdatedEvent(BaseEvent):
    plan_id: str = ""
    horizon: str = ""
    title: str = ""
