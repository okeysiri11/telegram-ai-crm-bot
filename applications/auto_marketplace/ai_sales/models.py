# AI Sales Agents domain models — Sprint 6.4.

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


class AgentType(str, enum.Enum):
    SALES = "sales_agent"
    CUSTOMER_ASSISTANT = "customer_assistant"
    DEALER_ASSISTANT = "dealer_assistant"
    RECOMMENDATION = "recommendation_agent"
    LEAD_QUALIFICATION = "lead_qualification_agent"
    NEGOTIATION = "negotiation_assistant"
    FOLLOW_UP = "follow_up_agent"
    DELIVERY = "delivery_assistant"


class LeadTemperature(str, enum.Enum):
    HOT = "hot"
    WARM = "warm"
    COLD = "cold"


class ConversationChannel(str, enum.Enum):
    WEB = "web"
    MOBILE = "mobile"
    PHONE = "phone"
    EMAIL = "email"
    SMS = "sms"
    CHAT = "chat"


class Sentiment(str, enum.Enum):
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"


@dataclass
class ConversationTurn:
    role: str = "user"
    content: str = ""
    channel: ConversationChannel = ConversationChannel.CHAT
    timestamp: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "role": self.role,
            "content": self.content,
            "channel": self.channel.value,
            "timestamp": self.timestamp,
        }


@dataclass
class ConversationSession:
    session_id: str = field(default_factory=_id)
    customer_id: str = ""
    agent_type: AgentType = AgentType.CUSTOMER_ASSISTANT
    channel: ConversationChannel = ConversationChannel.CHAT
    turns: list[ConversationTurn] = field(default_factory=list)
    summary: str = ""
    sentiment: Sentiment = Sentiment.NEUTRAL
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=_ts)
    updated_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "customer_id": self.customer_id,
            "agent_type": self.agent_type.value,
            "channel": self.channel.value,
            "turns": [t.to_dict() for t in self.turns],
            "summary": self.summary,
            "sentiment": self.sentiment.value,
            "metadata": dict(self.metadata),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class CustomerIntelligenceProfile:
    profile_id: str = field(default_factory=_id)
    customer_id: str = ""
    purchase_intent: float = 0.0
    budget_min: float = 0.0
    budget_max: float = 0.0
    preferred_makes: list[str] = field(default_factory=list)
    preferred_body_types: list[str] = field(default_factory=list)
    behavior_score: float = 0.0
    communication_channels: list[str] = field(default_factory=list)
    vehicle_preferences: dict[str, Any] = field(default_factory=dict)
    last_analyzed_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "profile_id": self.profile_id,
            "customer_id": self.customer_id,
            "purchase_intent": self.purchase_intent,
            "budget_min": self.budget_min,
            "budget_max": self.budget_max,
            "preferred_makes": list(self.preferred_makes),
            "preferred_body_types": list(self.preferred_body_types),
            "behavior_score": self.behavior_score,
            "communication_channels": list(self.communication_channels),
            "vehicle_preferences": dict(self.vehicle_preferences),
            "last_analyzed_at": self.last_analyzed_at,
        }


@dataclass
class LeadIntelligenceReport:
    lead_id: str = ""
    score: float = 0.0
    temperature: LeadTemperature = LeadTemperature.COLD
    priority: int = 3
    purchase_probability: float = 0.0
    expected_deal_value: float = 0.0
    qualified: bool = False
    reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "lead_id": self.lead_id,
            "score": self.score,
            "temperature": self.temperature.value,
            "priority": self.priority,
            "purchase_probability": self.purchase_probability,
            "expected_deal_value": self.expected_deal_value,
            "qualified": self.qualified,
            "reasons": list(self.reasons),
        }


@dataclass
class VehicleRecommendation:
    vehicle_id: str = ""
    recommendation_type: str = "personalized"
    score: float = 0.0
    reason: str = ""
    vehicle: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "vehicle_id": self.vehicle_id,
            "recommendation_type": self.recommendation_type,
            "score": self.score,
            "reason": self.reason,
            "vehicle": dict(self.vehicle),
        }


@dataclass
class SalesOffer:
    offer_id: str = field(default_factory=_id)
    customer_id: str = ""
    vehicle_id: str = ""
    dealer_id: str = ""
    amount: float = 0.0
    trade_in_value: float = 0.0
    accessories: list[str] = field(default_factory=list)
    valid_until: float = field(default_factory=lambda: _ts() + 86400 * 7)
    status: str = "draft"
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "offer_id": self.offer_id,
            "customer_id": self.customer_id,
            "vehicle_id": self.vehicle_id,
            "dealer_id": self.dealer_id,
            "amount": self.amount,
            "trade_in_value": self.trade_in_value,
            "accessories": list(self.accessories),
            "valid_until": self.valid_until,
            "status": self.status,
            "created_at": self.created_at,
        }


@dataclass
class KnowledgeArticle:
    article_id: str = field(default_factory=_id)
    title: str = ""
    category: str = "general"
    content: str = ""
    tags: list[str] = field(default_factory=list)
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "article_id": self.article_id,
            "title": self.title,
            "category": self.category,
            "content": self.content,
            "tags": list(self.tags),
            "created_at": self.created_at,
        }
