"""FINANCE DTOs — Sprint 21.3."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from platform_contracts.dto.base.base_dto import BaseDTO

@dataclass
class PaymentDTO(BaseDTO):
    entity_type: str = "payment"
    domain: str = "finance"
    name: str = ""
    status: str = "active"
    attributes: dict[str, Any] = field(default_factory=dict)

@dataclass
class LedgerEntryDTO(BaseDTO):
    entity_type: str = "ledger_entry"
    domain: str = "finance"
    name: str = ""
    status: str = "active"
    attributes: dict[str, Any] = field(default_factory=dict)

__all__ = ['PaymentDTO', 'LedgerEntryDTO']
