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
