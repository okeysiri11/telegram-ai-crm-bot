"""HEALTHCARE DTOs — Sprint 21.3."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from platform_contracts.dto.base.base_dto import BaseDTO

@dataclass
class PatientDTO(BaseDTO):
    entity_type: str = "patient"
    domain: str = "healthcare"
    name: str = ""
    status: str = "active"
    attributes: dict[str, Any] = field(default_factory=dict)

@dataclass
class EncounterDTO(BaseDTO):
    entity_type: str = "encounter"
    domain: str = "healthcare"
    name: str = ""
    status: str = "active"
    attributes: dict[str, Any] = field(default_factory=dict)

__all__ = ['PatientDTO', 'EncounterDTO']
