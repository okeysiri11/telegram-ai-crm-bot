"""Authorization package — AuthorizationManager (layer) + AccessControl (hardening)."""

from __future__ import annotations

from platform_security.authorization.access import AccessControl
from platform_security.authorization.manager import AuthorizationManager, authorization_manager

__all__ = [
    "AuthorizationManager",
    "authorization_manager",
    "AccessControl",
]
