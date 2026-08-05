"""Authentication package — AuthenticationProvider (layer) + IdentitySecurity (hardening)."""

from __future__ import annotations

from platform_security.authentication.identity import IdentitySecurity
from platform_security.authentication.provider import (
    AuthenticationProvider,
    OAuthProvider,
    authentication_provider,
)

__all__ = [
    "AuthenticationProvider",
    "OAuthProvider",
    "authentication_provider",
    "IdentitySecurity",
]
