# Port ERP shared exceptions.

from __future__ import annotations


class PortERPError(Exception):
    """Base Port ERP error."""


class NotFoundError(PortERPError):
    def __init__(self, entity: str, entity_id: str) -> None:
        super().__init__(f"{entity} not found: {entity_id}")
        self.entity = entity
        self.entity_id = entity_id


class ValidationError(PortERPError):
    pass


class AuthorizationError(PortERPError):
    pass
