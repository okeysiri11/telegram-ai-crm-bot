"""Permission Engine — Sprint 25.0."""

from __future__ import annotations

from typing import Any

from platform_enterprise_extension_sdk.models import PERMISSION_SCOPES


class PermissionEngine:
    def request(self, *, extension_id: str, scopes: list[str]) -> dict[str, Any]:
        if not extension_id:
            raise ValueError("extension_id is required")
        scopes = [s.lower() for s in (scopes or [])]
        invalid = [s for s in scopes if s not in PERMISSION_SCOPES]
        if invalid:
            raise ValueError(f"unsupported scopes: {invalid}")
        if not scopes:
            raise ValueError("extensions must explicitly request permissions")
        return {
            "extension_id": extension_id,
            "requested": scopes,
            "granted": [],
            "status": "awaiting_owner_or_admin",
            "requires_approval": True,
            "auto_granted": False,
        }

    def decide(self, *, extension_id: str, actor: str, action: str, scopes: list[str]) -> dict[str, Any]:
        action = (action or "").lower()
        if actor not in ("platform_owner", "admin"):
            raise ValueError("only platform_owner or admin may grant permissions")
        if action not in ("approve", "reject"):
            raise ValueError("action must be approve or reject")
        scopes = [s.lower() for s in (scopes or [])]
        return {
            "extension_id": extension_id,
            "actor": actor,
            "action": action,
            "scopes": scopes,
            "granted": scopes if action == "approve" else [],
            "status": "approved" if action == "approve" else "rejected",
        }
