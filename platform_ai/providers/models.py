"""Sprint 43.2 — Provider Manager domain models."""

from __future__ import annotations

import enum
import time
from dataclasses import asdict, dataclass, field
from typing import Any


class ProviderType(str, enum.Enum):
    IMAGE = "image"
    VIDEO = "video"
    VOICE = "voice"
    TEXT = "text"
    MUSIC = "music"
    MULTIMODAL = "multimodal"


class ProviderStatus(str, enum.Enum):
    ACTIVE = "active"
    DEGRADED = "degraded"
    ERROR = "error"
    LIMIT = "limit"
    DISABLED = "disabled"
    UNKNOWN = "unknown"


@dataclass
class ProviderDef:
    id: str
    name: str
    type: str
    api: str
    cost_unit: float
    limits: dict[str, Any] = field(default_factory=dict)
    status: str = ProviderStatus.UNKNOWN.value
    key_ref: str | None = None
    fallback: list[str] = field(default_factory=list)
    timeout_sec: float = 30.0
    retry: int = 2
    health: dict[str, Any] = field(default_factory=dict)
    meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["has_key"] = bool(self.key_ref)
        return d


@dataclass
class ProviderHealth:
    provider_id: str
    ok: bool
    status: str
    latency_ms: float = 0.0
    message: str = ""
    balance: str | None = None
    limit_remaining: int | None = None
    checked_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class GenerationCost:
    model_cost: float = 0.0
    image_cost: float = 0.0
    video_cost: float = 0.0
    voice_cost: float = 0.0
    music_cost: float = 0.0
    tokens_in: int = 0
    tokens_out: int = 0
    total: float = 0.0
    currency: str = "USD"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ProviderResult:
    provider_id: str
    modality: str
    content: str
    media_url: str | None = None
    mode: str = "sandbox"
    cost: GenerationCost = field(default_factory=GenerationCost)
    latency_ms: float = 0.0
    failover_used: bool = False
    tried: list[str] = field(default_factory=list)
    raw: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider_id": self.provider_id,
            "modality": self.modality,
            "content": self.content,
            "media_url": self.media_url,
            "mode": self.mode,
            "cost": self.cost.to_dict(),
            "latency_ms": self.latency_ms,
            "failover_used": self.failover_used,
            "tried": list(self.tried),
            "via": "provider_manager",
            **self.raw,
        }
