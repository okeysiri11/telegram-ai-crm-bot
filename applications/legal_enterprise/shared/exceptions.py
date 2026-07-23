"""Shared exceptions — Legal Enterprise."""

from __future__ import annotations


class LegalEnterpriseError(Exception):
    pass


class NotFoundError(LegalEnterpriseError):
    def __init__(self, entity: str, entity_id: str) -> None:
        super().__init__(f"{entity} not found: {entity_id}")
        self.entity = entity
        self.entity_id = entity_id


class ValidationError(LegalEnterpriseError):
    pass
