"""CRM DTOs — Sprint 21.3."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from platform_contracts.dto.base.base_dto import BaseDTO

@dataclass
class ContactDTO(BaseDTO):
    entity_type: str = "contact"
    domain: str = "crm"
    name: str = ""
    status: str = "active"
    attributes: dict[str, Any] = field(default_factory=dict)

@dataclass
class DealDTO(BaseDTO):
    entity_type: str = "deal"
    domain: str = "crm"
    name: str = ""
    status: str = "active"
    attributes: dict[str, Any] = field(default_factory=dict)

@dataclass
class AccountDTO(BaseDTO):
    entity_type: str = "account"
    domain: str = "crm"
    name: str = ""
    status: str = "active"
    attributes: dict[str, Any] = field(default_factory=dict)

__all__ = ['ContactDTO', 'DealDTO', 'AccountDTO']
