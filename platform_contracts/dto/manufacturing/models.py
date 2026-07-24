"""MANUFACTURING DTOs — Sprint 21.3."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from platform_contracts.dto.base.base_dto import BaseDTO

@dataclass
class WorkOrderDTO(BaseDTO):
    entity_type: str = "work_order"
    domain: str = "manufacturing"
    name: str = ""
    status: str = "active"
    attributes: dict[str, Any] = field(default_factory=dict)

@dataclass
class BomDTO(BaseDTO):
    entity_type: str = "bom"
    domain: str = "manufacturing"
    name: str = ""
    status: str = "active"
    attributes: dict[str, Any] = field(default_factory=dict)

__all__ = ['WorkOrderDTO', 'BomDTO']
