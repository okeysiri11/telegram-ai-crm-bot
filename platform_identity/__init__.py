# Platform Identity & Access Management — single authorization source.

from platform_identity.authentication import authentication_service
from platform_identity.authorization import authorization_service
from platform_identity.identity_service import IdentityService, identity_service
from platform_identity.identity_router import register_identity_routes

__all__ = [
    "IdentityService",
    "authentication_service",
    "authorization_service",
    "identity_service",
    "register_identity_routes",
]
