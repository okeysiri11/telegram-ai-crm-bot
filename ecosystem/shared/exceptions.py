# Ecosystem — shared exceptions.

from __future__ import annotations


class EcosystemError(Exception):
    """Base ecosystem error."""


class NotFoundError(EcosystemError):
    def __init__(self, resource: str, entity_id: str) -> None:
        super().__init__(f"{resource} not found: {entity_id}")
        self.resource = resource
        self.entity_id = entity_id


class ValidationError(EcosystemError):
    def __init__(self, message: str) -> None:
        super().__init__(message)


class AuthorizationError(EcosystemError):
    def __init__(self, message: str = "Unauthorized") -> None:
        super().__init__(message)
