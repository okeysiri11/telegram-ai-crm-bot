# Sprint 8.4 — Agricultural AI domain models.

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


class AgroAgentType(str, enum.Enum):
    FARMER_ASSISTANT = "farmer_assistant"
    BUYER_ASSISTANT = "buyer_assistant"
    SUPPLIER_ASSISTANT = "supplier_assistant"
    EXPORTER_ASSISTANT = "exporter_assistant"
    MARKETPLACE_MODERATOR = "marketplace_moderator"
    PRICING_ADVISOR = "pricing_advisor"
    CROP_ADVISOR = "crop_advisor"
    WAREHOUSE_ADVISOR = "warehouse_advisor"
    LOGISTICS_ADVISOR = "logistics_advisor"
    EXECUTIVE_AGRO_AI = "executive_agro_ai"


class ForecastKind(str, enum.Enum):
    PRICE = "price"
    DEMAND = "demand"
    SUPPLY = "supply"
    HARVEST = "harvest"
    RISK = "risk"
    SEASON = "season"
    STORAGE = "storage"
    EXPORT = "export"
    REVENUE = "revenue"
    MARKET_TREND = "market_trend"


class KnowledgeKind(str, enum.Enum):
    CROP_TAXONOMY = "crop_taxonomy"
    SEASONALITY = "seasonality"
    REGIONAL = "regional"
    MARKET_TREND = "market_trend"
    QUALITY_STANDARD = "quality_standard"
    EXPORT_REGULATION = "export_regulation"
    GENERAL = "general"


@dataclass
class AgroAgent:
    agent_id: str = field(default_factory=_id)
    agent_type: AgroAgentType = AgroAgentType.FARMER_ASSISTANT
    name: str = ""
    description: str = ""
    skills: list[str] = field(default_factory=list)
    is_active: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type.value,
            "name": self.name,
            "description": self.description,
            "skills": list(self.skills),
            "is_active": self.is_active,
            "created_at": self.created_at,
        }


@dataclass
class AgentInvocation:
    invocation_id: str = field(default_factory=_id)
    agent_type: AgroAgentType = AgroAgentType.FARMER_ASSISTANT
    user_id: str = ""
    message: str = ""
    context: dict[str, Any] = field(default_factory=dict)
    reply: str = ""
    actions: list[dict[str, Any]] = field(default_factory=list)
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "invocation_id": self.invocation_id,
            "agent_type": self.agent_type.value,
            "user_id": self.user_id,
            "message": self.message,
            "reply": self.reply,
            "actions": list(self.actions),
            "created_at": self.created_at,
        }


@dataclass
class Recommendation:
    recommendation_id: str = field(default_factory=_id)
    kind: str = "product"
    subject_id: str = ""
    items: list[dict[str, Any]] = field(default_factory=list)
    score: float = 0.0
    rationale: str = ""
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "recommendation_id": self.recommendation_id,
            "kind": self.kind,
            "subject_id": self.subject_id,
            "items": list(self.items),
            "score": self.score,
            "rationale": self.rationale,
            "created_at": self.created_at,
        }


@dataclass
class ForecastResult:
    forecast_id: str = field(default_factory=_id)
    kind: ForecastKind = ForecastKind.PRICE
    subject: str = ""
    region: str = ""
    horizon_days: int = 30
    values: list[dict[str, Any]] = field(default_factory=list)
    confidence: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "forecast_id": self.forecast_id,
            "kind": self.kind.value,
            "subject": self.subject,
            "region": self.region,
            "horizon_days": self.horizon_days,
            "values": list(self.values),
            "confidence": self.confidence,
            "metadata": dict(self.metadata),
            "created_at": self.created_at,
        }


@dataclass
class KnowledgeArticle:
    article_id: str = field(default_factory=_id)
    kind: KnowledgeKind = KnowledgeKind.GENERAL
    title: str = ""
    body: str = ""
    tags: list[str] = field(default_factory=list)
    region: str = ""
    crop: str = ""
    source: str = "agro_knowledge"
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "article_id": self.article_id,
            "kind": self.kind.value,
            "title": self.title,
            "body": self.body,
            "tags": list(self.tags),
            "region": self.region,
            "crop": self.crop,
            "source": self.source,
            "created_at": self.created_at,
        }


@dataclass
class ExecutiveReport:
    report_id: str = field(default_factory=_id)
    title: str = ""
    summary: str = ""
    sections: list[dict[str, Any]] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)
    recommendations: list[str] = field(default_factory=list)
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "report_id": self.report_id,
            "title": self.title,
            "summary": self.summary,
            "sections": list(self.sections),
            "metrics": dict(self.metrics),
            "recommendations": list(self.recommendations),
            "created_at": self.created_at,
        }


@dataclass
class AIWorkflowTask:
    task_id: str = field(default_factory=_id)
    title: str = ""
    task_type: str = ""
    related_id: str = ""
    assignee_agent: str = ""
    status: str = "open"
    payload: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "title": self.title,
            "task_type": self.task_type,
            "related_id": self.related_id,
            "assignee_agent": self.assignee_agent,
            "status": self.status,
            "payload": dict(self.payload),
            "created_at": self.created_at,
        }
