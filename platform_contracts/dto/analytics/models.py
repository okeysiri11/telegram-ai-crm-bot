"""ANALYTICS DTOs — Sprint 21.3."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from platform_contracts.dto.base.base_dto import BaseDTO

@dataclass
class MetricDTO(BaseDTO):
    entity_type: str = "metric"
    domain: str = "analytics"
    name: str = ""
    status: str = "active"
    attributes: dict[str, Any] = field(default_factory=dict)

@dataclass
class ReportDTO(BaseDTO):
    entity_type: str = "report"
    domain: str = "analytics"
    name: str = ""
    status: str = "active"
    attributes: dict[str, Any] = field(default_factory=dict)

__all__ = ['MetricDTO', 'ReportDTO']
