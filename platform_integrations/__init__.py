# Platform Integration Hub — single entry point for external systems.

from platform_integrations.integration_router import register_integration_routes
from platform_integrations.integration_service import IntegrationService, integration_service
from platform_integrations.n8n_bridge import N8nBridge, n8n_bridge
from platform_integrations.extended_provider_catalog import (
    EXTENDED_PROVIDER_CATALOG,
    catalog_summary,
    list_providers,
)

__all__ = [
    "IntegrationService",
    "integration_service",
    "register_integration_routes",
    "N8nBridge",
    "n8n_bridge",
    "EXTENDED_PROVIDER_CATALOG",
    "catalog_summary",
    "list_providers",
]
