# AI Sales events — Sprint 6.4.

from __future__ import annotations

from dataclasses import dataclass

from events.base_event import BaseEvent


@dataclass(kw_only=True)
class RecommendationGeneratedEvent(BaseEvent):
    customer_id: str = ""
    recommendation_type: str = ""
    vehicle_ids: list[str] | None = None


@dataclass(kw_only=True)
class AISalesLeadQualifiedEvent(BaseEvent):
    lead_id: str = ""
    score: float = 0.0
    temperature: str = ""


@dataclass(kw_only=True)
class ConversationSummarizedEvent(BaseEvent):
    session_id: str = ""
    customer_id: str = ""
    summary: str = ""


@dataclass(kw_only=True)
class CustomerIntentDetectedEvent(BaseEvent):
    customer_id: str = ""
    intent_score: float = 0.0
    intent_label: str = ""


@dataclass(kw_only=True)
class OfferGeneratedEvent(BaseEvent):
    offer_id: str = ""
    customer_id: str = ""
    vehicle_id: str = ""
    amount: float = 0.0


@dataclass(kw_only=True)
class FollowUpScheduledEvent(BaseEvent):
    lead_id: str = ""
    customer_id: str = ""
    scheduled_at: float = 0.0
    channel: str = ""
