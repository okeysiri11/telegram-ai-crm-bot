"""MARITIME DTOs — Sprint 21.3."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from platform_contracts.dto.base.base_dto import BaseDTO

@dataclass
class VesselDTO(BaseDTO):
    entity_type: str = "vessel"
    domain: str = "maritime"
    name: str = ""
    status: str = "active"
    attributes: dict[str, Any] = field(default_factory=dict)

@dataclass
class BerthCallDTO(BaseDTO):
    entity_type: str = "berth_call"
    domain: str = "maritime"
    name: str = ""
    status: str = "active"
    attributes: dict[str, Any] = field(default_factory=dict)

__all__ = ['VesselDTO', 'BerthCallDTO']
