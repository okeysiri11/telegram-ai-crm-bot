# Auto Marketplace — shared exceptions.

from __future__ import annotations


class AutoMarketplaceError(Exception):
    """Base application error."""


class NotFoundError(AutoMarketplaceError):
    def __init__(self, resource: str, entity_id: str) -> None:
        super().__init__(f"{resource} not found: {entity_id}")
        self.resource = resource
        self.entity_id = entity_id


class ValidationError(AutoMarketplaceError):
    def __init__(self, message: str) -> None:
        super().__init__(message)


class AuthorizationError(AutoMarketplaceError):
    def __init__(self, message: str = "Unauthorized") -> None:
        super().__init__(message)
