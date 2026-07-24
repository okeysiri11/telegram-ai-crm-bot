"""WAREHOUSE DTOs — Sprint 21.3."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from platform_contracts.dto.base.base_dto import BaseDTO

@dataclass
class StockItemDTO(BaseDTO):
    entity_type: str = "stock_item"
    domain: str = "warehouse"
    name: str = ""
    status: str = "active"
    attributes: dict[str, Any] = field(default_factory=dict)

@dataclass
class BinDTO(BaseDTO):
    entity_type: str = "bin"
    domain: str = "warehouse"
    name: str = ""
    status: str = "active"
    attributes: dict[str, Any] = field(default_factory=dict)

__all__ = ['StockItemDTO', 'BinDTO']
