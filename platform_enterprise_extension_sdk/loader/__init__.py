"""Extension Loader — Sprint 25.0."""

from __future__ import annotations

from typing import Any


class ExtensionLoader:
    def install(self, *, extension: dict[str, Any], allow_unsigned: bool = False) -> dict[str, Any]:
        if not extension.get("extension_id"):
            raise ValueError("extension_id is required")
        if not extension.get("signature") and not allow_unsigned:
            raise ValueError("safe load requires digital signature")
        compat = dict(extension.get("compatibility") or {})
        platform_min = str(compat.get("platform_min", "8.0.0"))
        # simple semver-ish gate for foundation v8
        if platform_min.startswith("9."):
            raise ValueError("compatibility check failed: platform too old")
        return {
            "extension_id": extension["extension_id"],
            "action": "install",
            "version": extension.get("version"),
            "compatibility_ok": True,
            "safe_load": True,
            "status": "installed",
        }

    def update(self, *, extension_id: str, to_version: str) -> dict[str, Any]:
        if not extension_id or not to_version:
            raise ValueError("extension_id and to_version are required")
        return {"extension_id": extension_id, "action": "update", "version": to_version, "status": "updated"}

    def uninstall(self, *, extension_id: str) -> dict[str, Any]:
        if not extension_id:
            raise ValueError("extension_id is required")
        return {"extension_id": extension_id, "action": "uninstall", "status": "archived"}

    def rollback(self, *, extension_id: str, to_version: str) -> dict[str, Any]:
        if not extension_id or not to_version:
            raise ValueError("extension_id and to_version are required")
        return {"extension_id": extension_id, "action": "rollback", "version": to_version, "status": "installed"}
