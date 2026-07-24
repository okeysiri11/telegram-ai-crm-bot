"""Public API contract for extensions — Sprint 25.0."""

from __future__ import annotations

from typing import Any


class PublicExtensionAPI:
    ALLOWED = (
        "extensions.register",
        "extensions.permissions.request",
        "extensions.marketplace.list",
        "extensions.invoke_skill",
        "ai.provider_hub.invoke",
        "workflow.trigger",
        "knowledge_graph.query",
        "notifications.send",
    )

    FORBIDDEN = (
        "core.internal",
        "core.store.direct",
        "core.config.mutate",
        "platform_core.modify",
    )

    def call(self, *, method: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        method = (method or "").strip()
        if method in self.FORBIDDEN or method.startswith("core."):
            raise ValueError("direct access to Enterprise Core internals is forbidden")
        if method not in self.ALLOWED:
            raise ValueError(f"method not in public API: {method}")
        return {
            "method": method,
            "payload": dict(payload or {}),
            "via_public_api": True,
            "direct_core_access": False,
            "ok": True,
        }
