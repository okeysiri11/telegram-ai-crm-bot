# Platform Integration Hub — single entry point for external systems.

from platform_integrations.integration_router import register_integration_routes
from platform_integrations.integration_service import IntegrationService, integration_service

__all__ = [
    "IntegrationService",
    "integration_service",
    "register_integration_routes",
]
