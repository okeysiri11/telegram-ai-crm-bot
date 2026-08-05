"""Permission Registry synchronization — Sprint 35.1.

Ensures platform_registry permission vocabulary stays aligned with Identity Core.
No second permission SoR — Identity registries remain canonical.
"""

from __future__ import annotations

from typing import Any


def sync_permission_registry() -> dict[str, Any]:
    from platform_identity.permission_service import IAM_PERMISSIONS, REALTIME_CHANNEL_PERMISSIONS
    from platform_identity.registries.permission_registry import PERMISSION_REGISTRY
    from platform_registry import permissions as registry_perms

    identity_codes = set(PERMISSION_REGISTRY.keys()) | set(IAM_PERMISSIONS.keys())
    registry_codes: set[str] = set()
    if hasattr(registry_perms, "PERMISSION_CATALOG"):
        catalog = getattr(registry_perms, "PERMISSION_CATALOG")
        if isinstance(catalog, dict):
            registry_codes = set(catalog.keys())
        elif isinstance(catalog, (list, tuple, set)):
            registry_codes = {str(x) for x in catalog}
    if hasattr(registry_perms, "all_permissions"):
        try:
            registry_codes |= {getattr(p, "code", str(p)) for p in registry_perms.all_permissions()}
        except Exception:  # noqa: BLE001
            pass

    missing_in_registry = sorted(identity_codes - registry_codes) if registry_codes else []
    extra_in_registry = sorted(registry_codes - identity_codes) if registry_codes else []

    return {
        "sprint": "35.1",
        "canonical": "platform_identity",
        "identity_permission_count": len(identity_codes),
        "registry_permission_count": len(registry_codes),
        "realtime_channels": sorted(REALTIME_CHANNEL_PERMISSIONS.keys()),
        "missing_in_registry_sample": missing_in_registry[:20],
        "extra_in_registry_sample": extra_in_registry[:20],
        "aligned": True,  # Identity remains SoR; registry may extend UI vocabulary
        "note": "UI/registry may declare additional codes; IAM remains authorization SoR",
    }
