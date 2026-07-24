"""HR DTOs — Sprint 21.3."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from platform_contracts.dto.base.base_dto import BaseDTO

@dataclass
class EmployeeDTO(BaseDTO):
    entity_type: str = "employee"
    domain: str = "hr"
    name: str = ""
    status: str = "active"
    attributes: dict[str, Any] = field(default_factory=dict)

@dataclass
class LeaveDTO(BaseDTO):
    entity_type: str = "leave"
    domain: str = "hr"
    name: str = ""
    status: str = "active"
    attributes: dict[str, Any] = field(default_factory=dict)

__all__ = ['EmployeeDTO', 'LeaveDTO']
