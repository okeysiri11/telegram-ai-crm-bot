"""CONSTRUCTION DTOs — Sprint 21.3."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from platform_contracts.dto.base.base_dto import BaseDTO

@dataclass
class SiteDTO(BaseDTO):
    entity_type: str = "site"
    domain: str = "construction"
    name: str = ""
    status: str = "active"
    attributes: dict[str, Any] = field(default_factory=dict)

@dataclass
class WorkPackageDTO(BaseDTO):
    entity_type: str = "work_package"
    domain: str = "construction"
    name: str = ""
    status: str = "active"
    attributes: dict[str, Any] = field(default_factory=dict)

__all__ = ['SiteDTO', 'WorkPackageDTO']
