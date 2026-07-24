"""LOGISTICS DTOs — Sprint 21.3."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from platform_contracts.dto.base.base_dto import BaseDTO

@dataclass
class ShipmentDTO(BaseDTO):
    entity_type: str = "shipment"
    domain: str = "logistics"
    name: str = ""
    status: str = "active"
    attributes: dict[str, Any] = field(default_factory=dict)

@dataclass
class RouteDTO(BaseDTO):
    entity_type: str = "route"
    domain: str = "logistics"
    name: str = ""
    status: str = "active"
    attributes: dict[str, Any] = field(default_factory=dict)

__all__ = ['ShipmentDTO', 'RouteDTO']
