# Agro Marketplace — shared exceptions.

from __future__ import annotations


class AgroMarketplaceError(Exception):
    """Base application error."""


class NotFoundError(AgroMarketplaceError):
    def __init__(self, resource: str, entity_id: str) -> None:
        super().__init__(f"{resource} not found: {entity_id}")
        self.resource = resource
        self.entity_id = entity_id


class ValidationError(AgroMarketplaceError):
    def __init__(self, message: str) -> None:
        super().__init__(message)


class AuthorizationError(AgroMarketplaceError):
    def __init__(self, message: str = "Unauthorized") -> None:
        super().__init__(message)
