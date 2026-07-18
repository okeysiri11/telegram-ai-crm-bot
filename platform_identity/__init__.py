# Platform Identity & Access Management — single authorization source.

from platform_identity.authentication import authentication_service
from platform_identity.authorization import authorization_service
from platform_identity.identity_service import IdentityService, identity_service


def register_identity_routes(app) -> None:
    from platform_identity.identity_router import register_identity_routes as _register

    _register(app)


__all__ = [
    "IdentityService",
    "authentication_service",
    "authorization_service",
    "identity_service",
    "register_identity_routes",
]
