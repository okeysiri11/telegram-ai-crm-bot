"""Extension Registry — Sprint 25.0."""

from __future__ import annotations

from typing import Any

from platform_enterprise_extension_sdk.models import EXTENSION_TYPES, LIFECYCLE_STATUSES


class ExtensionRegistry:
    def register(
        self,
        *,
        extension_id: str,
        name: str,
        version: str = "1.0.0",
        author: str = "",
        publisher: str = "",
        industry: str = "general",
        extension_type: str = "industry_module",
        dependencies: list[str] | None = None,
        required_permissions: list[str] | None = None,
        compatibility: dict[str, Any] | None = None,
        signature: str | None = None,
        status: str = "draft",
    ) -> dict[str, Any]:
        if not extension_id or not name:
            raise ValueError("extension_id and name are required")
        extension_type = (extension_type or "industry_module").lower()
        if extension_type not in EXTENSION_TYPES:
            raise ValueError(f"unsupported extension_type: {extension_type}")
        status = (status or "draft").lower()
        if status not in LIFECYCLE_STATUSES:
            raise ValueError(f"unsupported status: {status}")
        return {
            "extension_id": extension_id,
            "name": name.strip(),
            "version": version,
            "author": author or "unknown",
            "publisher": publisher or author or "unknown",
            "industry": industry,
            "extension_type": extension_type,
            "dependencies": list(dependencies or []),
            "required_permissions": list(required_permissions or []),
            "compatibility": dict(compatibility or {"platform_min": "8.0.0"}),
            "signature": signature,
            "status": status,
            "signed": bool(signature),
        }

    def set_status(self, extension: dict[str, Any], *, status: str) -> dict[str, Any]:
        status = (status or "").lower()
        if status not in LIFECYCLE_STATUSES:
            raise ValueError(f"unsupported status: {status}")
        updated = dict(extension)
        updated["status"] = status
        return updated
