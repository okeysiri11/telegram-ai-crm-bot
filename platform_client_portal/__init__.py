"""Client Portal & Mobile Experience — Sprint 22.8 / v6.9.0.

Design target: src/modules/client-portal (import path platform_client_portal).
Self-service client cabinet over Beauty/Commerce/Booking. AI recommends only.
"""

from platform_client_portal.facade import ClientPortalLibrary, client_portal_library

__all__ = ["ClientPortalLibrary", "client_portal_library"]
