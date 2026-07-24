"""INTEGRATION DTOs — Sprint 21.3."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from platform_contracts.dto.base.base_dto import BaseDTO

@dataclass
class ConnectorDTO(BaseDTO):
    entity_type: str = "connector"
    domain: str = "integration"
    name: str = ""
    status: str = "active"
    attributes: dict[str, Any] = field(default_factory=dict)

@dataclass
class SyncJobDTO(BaseDTO):
    entity_type: str = "sync_job"
    domain: str = "integration"
    name: str = ""
    status: str = "active"
    attributes: dict[str, Any] = field(default_factory=dict)

__all__ = ['ConnectorDTO', 'SyncJobDTO']
