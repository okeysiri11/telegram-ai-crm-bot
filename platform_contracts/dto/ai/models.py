"""AI DTOs — Sprint 21.3."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from platform_contracts.dto.base.base_dto import BaseDTO

@dataclass
class AgentDTO(BaseDTO):
    entity_type: str = "agent"
    domain: str = "ai"
    name: str = ""
    status: str = "active"
    attributes: dict[str, Any] = field(default_factory=dict)

@dataclass
class PromptDTO(BaseDTO):
    entity_type: str = "prompt"
    domain: str = "ai"
    name: str = ""
    status: str = "active"
    attributes: dict[str, Any] = field(default_factory=dict)

@dataclass
class InferenceDTO(BaseDTO):
    entity_type: str = "inference"
    domain: str = "ai"
    name: str = ""
    status: str = "active"
    attributes: dict[str, Any] = field(default_factory=dict)

__all__ = ['AgentDTO', 'PromptDTO', 'InferenceDTO']
