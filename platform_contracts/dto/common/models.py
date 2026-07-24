"""COMMON DTOs — Sprint 21.3."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from platform_contracts.dto.base.base_dto import BaseDTO

@dataclass
class MoneyDTO(BaseDTO):
    entity_type: str = "money"
    domain: str = "common"
    name: str = ""
    status: str = "active"
    attributes: dict[str, Any] = field(default_factory=dict)

@dataclass
class AddressDTO(BaseDTO):
    entity_type: str = "address"
    domain: str = "common"
    name: str = ""
    status: str = "active"
    attributes: dict[str, Any] = field(default_factory=dict)

@dataclass
class PeriodDTO(BaseDTO):
    entity_type: str = "period"
    domain: str = "common"
    name: str = ""
    status: str = "active"
    attributes: dict[str, Any] = field(default_factory=dict)

__all__ = ['MoneyDTO', 'AddressDTO', 'PeriodDTO']
