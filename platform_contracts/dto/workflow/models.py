"""WORKFLOW DTOs — Sprint 21.3."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from platform_contracts.dto.base.base_dto import BaseDTO

@dataclass
class WorkflowDTO(BaseDTO):
    entity_type: str = "workflow"
    domain: str = "workflow"
    name: str = ""
    status: str = "active"
    attributes: dict[str, Any] = field(default_factory=dict)

@dataclass
class TaskDTO(BaseDTO):
    entity_type: str = "task"
    domain: str = "workflow"
    name: str = ""
    status: str = "active"
    attributes: dict[str, Any] = field(default_factory=dict)

@dataclass
class ApprovalDTO(BaseDTO):
    entity_type: str = "approval"
    domain: str = "workflow"
    name: str = ""
    status: str = "active"
    attributes: dict[str, Any] = field(default_factory=dict)

__all__ = ['WorkflowDTO', 'TaskDTO', 'ApprovalDTO']
