# AI Skills domain models.

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4


class SkillState(str, Enum):
    REGISTERED = "registered"
    LOADED = "loaded"
    DISABLED = "disabled"
    FAILED = "failed"


class SkillCategory(str, Enum):
    SCORING = "scoring"
    EXTRACTION = "extraction"
    SUMMARIZATION = "summarization"
    CLASSIFICATION = "classification"
    ESTIMATION = "estimation"
    OCR = "ocr"
    ANALYSIS = "analysis"
    RECOMMENDATION = "recommendation"
    RISK = "risk"


@dataclass
class SkillMetadata:
    skill_id: str
    name: str
    version: str = "1.0.0"
    description: str = ""
    category: str = SkillCategory.ANALYSIS.value
    tags: list[str] = field(default_factory=list)
    capabilities: list[str] = field(default_factory=list)
    permissions: list[str] = field(default_factory=list)
    cache_ttl: float = 3600.0
    enabled: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "skill_id": self.skill_id,
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "category": self.category,
            "tags": self.tags,
            "capabilities": self.capabilities,
            "permissions": self.permissions,
            "cache_ttl": self.cache_ttl,
            "enabled": self.enabled,
        }


@dataclass
class SkillExecutionResult:
    skill_id: str
    execution_id: str
    success: bool
    output: dict[str, Any] = field(default_factory=dict)
    raw_content: str = ""
    tokens_in: int = 0
    tokens_out: int = 0
    cost_usd: float = 0.0
    latency_ms: float = 0.0
    cached: bool = False
    provider_id: str = ""
    model_id: str = ""
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "skill_id": self.skill_id,
            "execution_id": self.execution_id,
            "success": self.success,
            "output": self.output,
            "raw_content": self.raw_content,
            "tokens_in": self.tokens_in,
            "tokens_out": self.tokens_out,
            "cost_usd": self.cost_usd,
            "latency_ms": self.latency_ms,
            "cached": self.cached,
            "provider_id": self.provider_id,
            "model_id": self.model_id,
            "error": self.error,
        }


@dataclass
class SkillHealthResult:
    skill_id: str
    status: str = "healthy"
    message: str = ""
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {"skill_id": self.skill_id, "status": self.status, "message": self.message, "details": self.details}


@dataclass
class SkillRecord:
    metadata: SkillMetadata
    state: SkillState = SkillState.REGISTERED
    loaded_at: str | None = None
    last_error: str | None = None

    @property
    def skill_id(self) -> str:
        return self.metadata.skill_id

    def to_dict(self) -> dict[str, Any]:
        return {
            **self.metadata.to_dict(),
            "state": self.state.value,
            "loaded_at": self.loaded_at,
            "last_error": self.last_error,
        }


@dataclass
class SkillExecutionRequest:
    skill_id: str
    input: dict[str, Any] = field(default_factory=dict)
    plugin_id: str | None = None
    user_id: str | None = None
    request_id: str | None = None
    use_cache: bool = True
    execution_id: str = field(default_factory=lambda: str(uuid4()))
