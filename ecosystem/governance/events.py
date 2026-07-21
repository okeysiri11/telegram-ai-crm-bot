# Platform governance events — Sprint 7.6.

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from events.base_event import BaseEvent


@dataclass(kw_only=True)
class PolicyCreatedEvent(BaseEvent):
    policy_id: str = ""
    name: str = ""
    domain: str = ""


@dataclass(kw_only=True)
class PolicyUpdatedEvent(BaseEvent):
    policy_id: str = ""
    name: str = ""
    version: str = ""


@dataclass(kw_only=True)
class CompliancePassedEvent(BaseEvent):
    check_id: str = ""
    policy_id: str = ""
    subject_id: str = ""


@dataclass(kw_only=True)
class ComplianceFailedEvent(BaseEvent):
    check_id: str = ""
    policy_id: str = ""
    subject_id: str = ""
    findings: list[str] = field(default_factory=list)


@dataclass(kw_only=True)
class LifecycleChangedEvent(BaseEvent):
    record_id: str = ""
    kind: str = ""
    entity_id: str = ""
    state: str = ""
    version: str = ""


@dataclass(kw_only=True)
class RiskDetectedEvent(BaseEvent):
    risk_id: str = ""
    category: str = ""
    severity: str = ""
    title: str = ""


@dataclass(kw_only=True)
class GovernanceActionExecutedEvent(BaseEvent):
    action_id: str = ""
    action_type: str = ""
    domain: str = ""
    actor: str = ""
