"""LEGAL DTOs — Sprint 21.3."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from platform_contracts.dto.base.base_dto import BaseDTO

@dataclass
class ContractDTO(BaseDTO):
    entity_type: str = "contract"
    domain: str = "legal"
    name: str = ""
    status: str = "active"
    attributes: dict[str, Any] = field(default_factory=dict)

@dataclass
class CaseDTO(BaseDTO):
    entity_type: str = "case"
    domain: str = "legal"
    name: str = ""
    status: str = "active"
    attributes: dict[str, Any] = field(default_factory=dict)

__all__ = ['ContractDTO', 'CaseDTO']
