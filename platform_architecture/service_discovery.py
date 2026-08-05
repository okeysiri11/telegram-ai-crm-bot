"""Platform Service Discovery — Sprint 35.1.

Read-only discovery over the Canonical Service Registry.
Does not introduce a second registry or discovery bus.
"""

from __future__ import annotations

from typing import Any

from platform_architecture.canonical_services import (
    CANONICAL_SERVICES,
    canonical_for,
    canonical_summary,
    list_canonical_services,
)


class PlatformServiceDiscovery:
    """Finalize discovery as a query API over CANONICAL_SERVICES."""

    def list_services(self) -> list[dict[str, Any]]:
        return list_canonical_services()

    def get(self, service: str) -> dict[str, Any] | None:
        return canonical_for(service)

    def summary(self) -> dict[str, Any]:
        data = canonical_summary()
        data["sprint"] = "35.1"
        data["foundation_locked"] = True
        data["single_registry"] = True
        return data

    def require_canonical(self, capability: str) -> dict[str, Any]:
        meta = canonical_for(capability)
        if meta is None:
            raise KeyError(f"unknown canonical capability: {capability}")
        return meta

    def identity_registration(self) -> dict[str, Any]:
        return {
            "canonical": "platform_identity",
            "adapters": CANONICAL_SERVICES.get("identity_core", {}).get("legacy_adapters", []),
            "isam": "applications/enterprise_hub/security (adapter)",
        }

    def permission_registration(self) -> dict[str, Any]:
        from platform_identity.permission_service import IAM_PERMISSIONS, REALTIME_CHANNEL_PERMISSIONS
        from platform_identity.registries.permission_registry import PERMISSION_REGISTRY

        return {
            "iam_permissions": len(IAM_PERMISSIONS),
            "registry_permissions": len(PERMISSION_REGISTRY),
            "realtime_channels": sorted(REALTIME_CHANNEL_PERMISSIONS.keys()),
            "sor": "platform_identity.registries.permission_registry + IAM_PERMISSIONS",
        }

    def navigation_registration(self) -> dict[str, Any]:
        from platform_registry.menus import MENU_CATALOG

        return {
            "sor": "platform_registry.menus.MENU_CATALOG",
            "menu_count": len(MENU_CATALOG),
            "projections": [
                "src/web/src/platform-registry/menuCatalog.ts (fallback)",
                "src/web/src/shell/enterprise/shellModuleRegistry.ts",
                "src/web/src/modules/moduleCatalog.ts",
            ],
        }


platform_service_discovery = PlatformServiceDiscovery()
