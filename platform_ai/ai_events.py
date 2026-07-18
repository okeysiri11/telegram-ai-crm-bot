# AI Platform events.

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from events.base_event import BaseEvent


@dataclass(kw_only=True)
class AIRequestStartedEvent(BaseEvent):
    request_id: str = ""
    provider_id: str = ""
    model_id: str = ""
    task_type: str = ""
    plugin_id: str | None = None


@dataclass(kw_only=True)
class AIRequestCompletedEvent(BaseEvent):
    request_id: str = ""
    provider_id: str = ""
    model_id: str = ""
    tokens_in: int = 0
    tokens_out: int = 0
    cost_usd: float = 0.0
    cached: bool = False
    latency_ms: float = 0.0


@dataclass(kw_only=True)
class AIProviderFailedEvent(BaseEvent):
    request_id: str = ""
    provider_id: str = ""
    model_id: str = ""
    error: str = ""


@dataclass(kw_only=True)
class AIFallbackUsedEvent(BaseEvent):
    request_id: str = ""
    original_provider: str = ""
    fallback_provider: str = ""
    reason: str = ""


@dataclass(kw_only=True)
class CostThresholdExceededEvent(BaseEvent):
    total_usd: float = 0.0
    threshold_usd: float = 0.0
    details: dict[str, Any] = field(default_factory=dict)


async def publish_ai_event(event: BaseEvent) -> None:
    from events.event_bus import PlatformEventBus

    await PlatformEventBus.publish(event, wait=False)
