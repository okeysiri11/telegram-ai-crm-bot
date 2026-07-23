"""Shared exceptions — Finance Enterprise."""

from __future__ import annotations


class FinanceEnterpriseError(Exception):
    pass


class NotFoundError(FinanceEnterpriseError):
    def __init__(self, entity: str, entity_id: str) -> None:
        super().__init__(f"{entity} not found: {entity_id}")
        self.entity = entity
        self.entity_id = entity_id


class ValidationError(FinanceEnterpriseError):
    pass
