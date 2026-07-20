# CRM lifecycle events.

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from events.base_event import BaseEvent


@dataclass(kw_only=True)
class LeadCreatedEvent(BaseEvent):
    lead_id: str = ""
    customer_id: str = ""
    source: str = ""


@dataclass(kw_only=True)
class LeadQualifiedEvent(BaseEvent):
    lead_id: str = ""
    score: float = 0.0
    agent_id: str = ""


@dataclass(kw_only=True)
class DealOpenedEvent(BaseEvent):
    deal_id: str = ""
    customer_id: str = ""
    amount: float = 0.0


@dataclass(kw_only=True)
class DealUpdatedEvent(BaseEvent):
    deal_id: str = ""
    stage: str = ""
    probability: float = 0.0


@dataclass(kw_only=True)
class DealWonEvent(BaseEvent):
    deal_id: str = ""
    amount: float = 0.0
    customer_id: str = ""


@dataclass(kw_only=True)
class DealLostEvent(BaseEvent):
    deal_id: str = ""
    reason: str = ""


@dataclass(kw_only=True)
class CustomerCreatedEvent(BaseEvent):
    customer_id: str = ""
    email: str = ""


@dataclass(kw_only=True)
class TaskCreatedEvent(BaseEvent):
    task_id: str = ""
    assigned_agent_id: str = ""
    customer_id: str = ""


@dataclass(kw_only=True)
class ReminderTriggeredEvent(BaseEvent):
    reminder_id: str = ""
    task_id: str = ""
    customer_id: str = ""
