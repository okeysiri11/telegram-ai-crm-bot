"""Extension SDK surface — Sprint 25.0."""

from __future__ import annotations

from typing import Any

from platform_enterprise_extension_sdk.models import EXTENSION_TYPES


class ExtensionSDK:
    """Official SDK capabilities for building extensions without touching Core."""

    def capabilities(self) -> dict[str, Any]:
        return {
            "sdk_version": "1.0",
            "build_targets": list(EXTENSION_TYPES),
            "public_api_only": True,
            "direct_core_access": False,
            "core_modification_required": False,
        }

    def scaffold(self, *, extension_type: str, name: str) -> dict[str, Any]:
        extension_type = (extension_type or "").lower()
        if extension_type not in EXTENSION_TYPES:
            raise ValueError(f"unsupported extension_type: {extension_type}")
        if not name:
            raise ValueError("name is required")
        return {
            "name": name.strip(),
            "extension_type": extension_type,
            "scaffold": {
                "manifest": f"{name.strip().lower().replace(' ', '_')}.ext.json",
                "entry": "main.py",
                "permissions": [],
                "tests": ["test_smoke.py"],
            },
            "via_sdk": True,
            "modifies_core": False,
        }
