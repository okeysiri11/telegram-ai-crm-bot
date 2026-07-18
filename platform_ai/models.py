# AI Platform domain models.

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4


class ProviderStatus(str, Enum):
    AVAILABLE = "available"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"


class TaskType(str, Enum):
    CHAT = "chat"
    COMPLETION = "completion"
    SUMMARIZATION = "summarization"
    CLASSIFICATION = "classification"
    EXTRACTION = "extraction"
    CODE = "code"
    EMBEDDING = "embedding"


@dataclass
class ModelCapabilities:
    chat: bool = True
    vision: bool = False
    function_calling: bool = False
    streaming: bool = False
    embedding: bool = False


@dataclass
class ModelPricing:
    input_per_1k: float = 0.0
    output_per_1k: float = 0.0
    currency: str = "USD"


@dataclass
class AIModelRecord:
    provider_id: str
    model_id: str
    display_name: str
    context_window: int = 8192
    pricing: ModelPricing = field(default_factory=ModelPricing)
    capabilities: ModelCapabilities = field(default_factory=ModelCapabilities)
    status: ProviderStatus = ProviderStatus.AVAILABLE
    task_types: list[str] = field(default_factory=lambda: [TaskType.CHAT.value])

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider_id": self.provider_id,
            "model_id": self.model_id,
            "display_name": self.display_name,
            "context_window": self.context_window,
            "pricing": {
                "input_per_1k": self.pricing.input_per_1k,
                "output_per_1k": self.pricing.output_per_1k,
                "currency": self.pricing.currency,
            },
            "capabilities": {
                "chat": self.capabilities.chat,
                "vision": self.capabilities.vision,
                "function_calling": self.capabilities.function_calling,
                "streaming": self.capabilities.streaming,
                "embedding": self.capabilities.embedding,
            },
            "status": self.status.value,
            "task_types": self.task_types,
        }


@dataclass
class AIProviderRecord:
    provider_id: str
    name: str
    enabled: bool = True
    status: ProviderStatus = ProviderStatus.AVAILABLE
    latency_ms: float = 0.0
    models: list[str] = field(default_factory=list)
    config: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider_id": self.provider_id,
            "name": self.name,
            "enabled": self.enabled,
            "status": self.status.value,
            "latency_ms": self.latency_ms,
            "models": self.models,
            "config": {k: v for k, v in self.config.items() if not k.endswith("_key")},
        }


@dataclass
class AIMessage:
    role: str
    content: str


@dataclass
class AIRequest:
    prompt: str = ""
    messages: list[AIMessage] = field(default_factory=list)
    task_type: TaskType = TaskType.CHAT
    model: str | None = None
    provider: str | None = None
    plugin_id: str | None = None
    template_id: str | None = None
    template_vars: dict[str, Any] = field(default_factory=dict)
    context: dict[str, Any] = field(default_factory=dict)
    max_tokens: int = 1024
    temperature: float = 0.7
    use_cache: bool = True
    request_id: str = field(default_factory=lambda: str(uuid4()))


@dataclass
class AIResponse:
    request_id: str
    provider_id: str
    model_id: str
    content: str
    tokens_in: int = 0
    tokens_out: int = 0
    cost_usd: float = 0.0
    latency_ms: float = 0.0
    cached: bool = False
    fallback_used: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "provider_id": self.provider_id,
            "model_id": self.model_id,
            "content": self.content,
            "tokens_in": self.tokens_in,
            "tokens_out": self.tokens_out,
            "cost_usd": self.cost_usd,
            "latency_ms": self.latency_ms,
            "cached": self.cached,
            "fallback_used": self.fallback_used,
            "metadata": self.metadata,
        }


@dataclass
class PromptTemplate:
    template_id: str
    name: str
    body: str
    version: int = 1
    parent_id: str | None = None
    variables: list[str] = field(default_factory=list)
    description: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "template_id": self.template_id,
            "name": self.name,
            "body": self.body,
            "version": self.version,
            "parent_id": self.parent_id,
            "variables": self.variables,
            "description": self.description,
            "created_at": self.created_at,
        }


@dataclass
class CostRecord:
    request_id: str
    provider_id: str
    model_id: str
    plugin_id: str | None
    tokens_in: int
    tokens_out: int
    cost_usd: float
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
