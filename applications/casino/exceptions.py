"""Casino shared exceptions."""

from __future__ import annotations


class CasinoError(Exception):
    pass


class AuthenticationError(CasinoError):
    pass


class AuthorizationError(CasinoError):
    pass


class ValidationError(CasinoError):
    pass


class NotFoundError(CasinoError):
    pass


class InsufficientChipsError(CasinoError):
    pass


class DuplicateSettlementError(CasinoError):
    pass


class RateLimitError(CasinoError):
    def __init__(self, message: str, *, retry_after: int = 0) -> None:
        super().__init__(message)
        self.retry_after = int(retry_after)
