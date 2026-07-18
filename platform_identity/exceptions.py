# IAM exceptions.

from __future__ import annotations


class IdentityError(Exception):
    """Base IAM error."""


class AuthenticationError(IdentityError):
    """Identity could not be verified."""


class AuthorizationError(IdentityError):
    """Principal lacks required permission."""


class SessionError(IdentityError):
    """Invalid or expired session."""


class TokenError(IdentityError):
    """JWT validation or rotation failure."""


class ApiKeyError(IdentityError):
    """API key invalid, expired, or disabled."""


class PolicyError(IdentityError):
    """Policy evaluation failure."""
