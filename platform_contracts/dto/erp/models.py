"""ERP DTOs — Sprint 21.3."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from platform_contracts.dto.base.base_dto import BaseDTO

@dataclass
class OrderDTO(BaseDTO):
    entity_type: str = "order"
    domain: str = "erp"
    name: str = ""
    status: str = "active"
    attributes: dict[str, Any] = field(default_factory=dict)

@dataclass
class InvoiceDTO(BaseDTO):
    entity_type: str = "invoice"
    domain: str = "erp"
    name: str = ""
    status: str = "active"
    attributes: dict[str, Any] = field(default_factory=dict)

@dataclass
class ProductDTO(BaseDTO):
    entity_type: str = "product"
    domain: str = "erp"
    name: str = ""
    status: str = "active"
    attributes: dict[str, Any] = field(default_factory=dict)

__all__ = ['OrderDTO', 'InvoiceDTO', 'ProductDTO']
