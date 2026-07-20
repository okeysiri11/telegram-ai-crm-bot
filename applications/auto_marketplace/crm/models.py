# CRM & Sales Pipeline domain models — Sprint 6.3.

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


class LeadSource(str, enum.Enum):
    WEB = "web"
    MOBILE = "mobile"
    PHONE = "phone"
    REFERRAL = "referral"
    DEALER = "dealer"
    ADVERTISEMENT = "advertisement"
    AI_AGENT = "ai_agent"
    OTHER = "other"


class CRMLeadStatus(str, enum.Enum):
    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    UNQUALIFIED = "unqualified"
    CONVERTED = "converted"
    LOST = "lost"


class DealStage(str, enum.Enum):
    PROSPECT = "prospect"
    QUALIFICATION = "qualification"
    PROPOSAL = "proposal"
    NEGOTIATION = "negotiation"
    APPROVAL = "approval"
    CLOSED_WON = "closed_won"
    CLOSED_LOST = "closed_lost"


class CRMRole(str, enum.Enum):
    OWNER = "owner"
    ADMINISTRATOR = "administrator"
    SALES_MANAGER = "sales_manager"
    SALES_AGENT = "sales_agent"
    DEALER = "dealer"
    CUSTOMER = "customer"
    AI_AGENT = "ai_agent"


class TaskStatus(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class InteractionType(str, enum.Enum):
    CALL = "call"
    EMAIL = "email"
    MEETING = "meeting"
    NOTE = "note"
    SMS = "sms"
    CHAT = "chat"


@dataclass
class CustomerProfile:
    customer_id: str = field(default_factory=_id)
    first_name: str = ""
    last_name: str = ""
    email: str = ""
    phone: str = ""
    segment: str = "standard"
    intent_score: float = 0.0
    lifetime_value: float = 0.0
    preferences: dict[str, Any] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)
    owner_agent_id: str = ""
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "customer_id": self.customer_id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "email": self.email,
            "phone": self.phone,
            "segment": self.segment,
            "intent_score": self.intent_score,
            "lifetime_value": self.lifetime_value,
            "preferences": dict(self.preferences),
            "tags": list(self.tags),
            "owner_agent_id": self.owner_agent_id,
            "created_at": self.created_at,
        }


@dataclass
class CRMLead:
    lead_id: str = field(default_factory=_id)
    customer_id: str = ""
    vehicle_id: str = ""
    dealer_id: str = ""
    source: LeadSource = LeadSource.WEB
    status: CRMLeadStatus = CRMLeadStatus.NEW
    score: float = 0.0
    assigned_agent_id: str = ""
    notes: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=_ts)
    qualified_at: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "lead_id": self.lead_id,
            "customer_id": self.customer_id,
            "vehicle_id": self.vehicle_id,
            "dealer_id": self.dealer_id,
            "source": self.source.value,
            "status": self.status.value,
            "score": self.score,
            "assigned_agent_id": self.assigned_agent_id,
            "notes": self.notes,
            "metadata": dict(self.metadata),
            "created_at": self.created_at,
            "qualified_at": self.qualified_at,
        }


@dataclass
class SalesOpportunity:
    opportunity_id: str = field(default_factory=_id)
    lead_id: str = ""
    customer_id: str = ""
    dealer_id: str = ""
    vehicle_id: str = ""
    stage: DealStage = DealStage.PROSPECT
    amount: float = 0.0
    probability: float = 0.1
    expected_close_at: float | None = None
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "opportunity_id": self.opportunity_id,
            "lead_id": self.lead_id,
            "customer_id": self.customer_id,
            "dealer_id": self.dealer_id,
            "vehicle_id": self.vehicle_id,
            "stage": self.stage.value,
            "amount": self.amount,
            "probability": self.probability,
            "expected_close_at": self.expected_close_at,
            "created_at": self.created_at,
        }


@dataclass
class CRMDeal:
    deal_id: str = field(default_factory=_id)
    opportunity_id: str = ""
    customer_id: str = ""
    dealer_id: str = ""
    vehicle_id: str = ""
    stage: DealStage = DealStage.PROSPECT
    amount: float = 0.0
    probability: float = 0.1
    win: bool | None = None
    owner_agent_id: str = ""
    created_at: float = field(default_factory=_ts)
    closed_at: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "deal_id": self.deal_id,
            "opportunity_id": self.opportunity_id,
            "customer_id": self.customer_id,
            "dealer_id": self.dealer_id,
            "vehicle_id": self.vehicle_id,
            "stage": self.stage.value,
            "amount": self.amount,
            "probability": self.probability,
            "win": self.win,
            "owner_agent_id": self.owner_agent_id,
            "created_at": self.created_at,
            "closed_at": self.closed_at,
        }


@dataclass
class Contact:
    contact_id: str = field(default_factory=_id)
    customer_id: str = ""
    name: str = ""
    email: str = ""
    phone: str = ""
    role: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {k: getattr(self, k) for k in self.__dataclass_fields__}


@dataclass
class Interaction:
    interaction_id: str = field(default_factory=_id)
    customer_id: str = ""
    lead_id: str = ""
    deal_id: str = ""
    interaction_type: InteractionType = InteractionType.NOTE
    subject: str = ""
    body: str = ""
    agent_id: str = ""
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "interaction_id": self.interaction_id,
            "customer_id": self.customer_id,
            "lead_id": self.lead_id,
            "deal_id": self.deal_id,
            "interaction_type": self.interaction_type.value,
            "subject": self.subject,
            "body": self.body,
            "agent_id": self.agent_id,
            "created_at": self.created_at,
        }


@dataclass
class PhoneCall:
    call_id: str = field(default_factory=_id)
    customer_id: str = ""
    agent_id: str = ""
    direction: str = "outbound"
    duration_sec: int = 0
    summary: str = ""
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {k: getattr(self, k) for k in self.__dataclass_fields__}


@dataclass
class EmailMessage:
    email_id: str = field(default_factory=_id)
    customer_id: str = ""
    agent_id: str = ""
    subject: str = ""
    body: str = ""
    direction: str = "outbound"
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {k: getattr(self, k) for k in self.__dataclass_fields__}


@dataclass
class Meeting:
    meeting_id: str = field(default_factory=_id)
    customer_id: str = ""
    agent_id: str = ""
    title: str = ""
    scheduled_at: float = field(default_factory=_ts)
    duration_min: int = 30
    location: str = ""
    completed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {k: getattr(self, k) for k in self.__dataclass_fields__}


@dataclass
class CRMTask:
    task_id: str = field(default_factory=_id)
    title: str = ""
    description: str = ""
    customer_id: str = ""
    lead_id: str = ""
    deal_id: str = ""
    assigned_agent_id: str = ""
    status: TaskStatus = TaskStatus.PENDING
    due_at: float | None = None
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "title": self.title,
            "description": self.description,
            "customer_id": self.customer_id,
            "lead_id": self.lead_id,
            "deal_id": self.deal_id,
            "assigned_agent_id": self.assigned_agent_id,
            "status": self.status.value,
            "due_at": self.due_at,
            "created_at": self.created_at,
        }


@dataclass
class Reminder:
    reminder_id: str = field(default_factory=_id)
    task_id: str = ""
    customer_id: str = ""
    message: str = ""
    trigger_at: float = field(default_factory=_ts)
    triggered: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {k: getattr(self, k) for k in self.__dataclass_fields__}


@dataclass
class SalesAgent:
    agent_id: str = field(default_factory=_id)
    name: str = ""
    email: str = ""
    team_id: str = ""
    active: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {k: getattr(self, k) for k in self.__dataclass_fields__}


@dataclass
class SalesTeam:
    team_id: str = field(default_factory=_id)
    name: str = ""
    manager_id: str = ""
    dealer_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {k: getattr(self, k) for k in self.__dataclass_fields__}
