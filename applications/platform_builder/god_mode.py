"""God Mode — Platform Owner only management surface."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.platform_builder.config import DEFAULT_CONFIG
from applications.platform_builder.shared.exceptions import ForbiddenError, ValidationError
from applications.platform_builder.shared.store import PlatformBuilderStore, platform_builder_store

PLATFORM_OWNER_ROLE = "platform_owner"

GOD_CAPABILITIES = (
    "edit_any_object",
    "edit_any_vertical",
    "edit_any_application",
    "edit_any_ai",
    "edit_any_organization",
    "edit_any_workflow",
    "edit_any_knowledge_base",
    "edit_any_dashboard",
    "edit_any_automation",
    "edit_any_api",
    "edit_any_template",
    "edit_any_builder",
    "system_diagnostics",
    "architecture_management",
    "developer_console",
    "version_history",
    "rollback_manager",
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:10]}"


def is_platform_owner(role: str | None) -> bool:
    return (role or "").strip().lower() in {
        PLATFORM_OWNER_ROLE,
        "owner",
        "platform-owner",
    }


class GodMode:
    def __init__(self, store: PlatformBuilderStore | None = None) -> None:
        self.store = store or platform_builder_store
        self._history: list[dict[str, Any]] = [
            {
                "version_id": "v_seed",
                "label": "Platform Builder Core seed",
                "created_at": _now(),
            }
        ]

    def require_owner(self, role: str | None) -> None:
        if not is_platform_owner(role):
            raise ForbiddenError("God Mode is available only to Platform Owner")

    def status(self, role: str | None) -> dict[str, Any]:
        self.require_owner(role)
        return {
            "ready": True,
            "isolated": True,
            "visible_to": PLATFORM_OWNER_ROLE,
            "version": "2.0.0",
            "sprint": DEFAULT_CONFIG.sprint,
            "expansion_ready": True,
            "platform_control_center_ready": True,
            "capabilities": list(GOD_CAPABILITIES),
            "diagnostics": {
                "builders_online": True,
                "academy_online": True,
                "framework_online": True,
                "api_online": True,
                "control_center_online": True,
            },
            "architecture": {
                "application": "platform_builder",
                "api_prefix": "/api/platform-builder/v1",
                "web_module": "src/web/platform-builder",
                "control_center": "applications/platform_builder/control_center",
            },
            "developer_console": {"prompt": "platform-builder>", "ready": True},
            "version_history": list(self._history),
            "rollback_manager": {"ready": True, "checkpoints": len(self._history)},
        }

    def action(self, role: str | None, action: str, target: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        self.require_owner(role)
        if action not in GOD_CAPABILITIES and action not in ("inspect", "rollback"):
            raise ValidationError(f"Unsupported God Mode action: {action}")
        rid = _id("god")
        record = {
            "action_id": rid,
            "action": action,
            "target": target,
            "payload": payload or {},
            "status": "recorded",
            "created_at": _now(),
        }
        if action == "rollback":
            record["status"] = "rollback_prepared"
            record["checkpoint"] = self._history[-1] if self._history else None
        if action == "version_history":
            record["history"] = list(self._history)
        self.store.god_actions.save(rid, record)
        self._history.append(
            {
                "version_id": _id("ver"),
                "label": f"{action}:{target}",
                "created_at": _now(),
            }
        )
        self.store.versions.save(self._history[-1]["version_id"], self._history[-1])
        return {"ok": True, **record}
