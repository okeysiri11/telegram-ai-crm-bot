"""Extension Lifecycle — Sprint 25.0."""

from __future__ import annotations

from typing import Any

from platform_enterprise_extension_sdk.models import LIFECYCLE_STATUSES

TRANSITIONS = {
    "draft": ("testing", "archived"),
    "testing": ("verified", "draft", "archived"),
    "verified": ("published", "testing", "deprecated"),
    "published": ("installed", "deprecated", "archived"),
    "installed": ("updated", "deprecated", "archived"),
    "updated": ("installed", "deprecated"),
    "deprecated": ("archived",),
    "archived": (),
}


class ExtensionLifecycle:
    def transition(self, *, extension: dict[str, Any], to_status: str) -> dict[str, Any]:
        to_status = (to_status or "").lower()
        if to_status not in LIFECYCLE_STATUSES:
            raise ValueError(f"unsupported status: {to_status}")
        current = (extension.get("status") or "draft").lower()
        allowed = TRANSITIONS.get(current, ())
        if to_status not in allowed:
            raise ValueError(f"illegal transition {current} → {to_status}")
        updated = dict(extension)
        updated["status"] = to_status
        hist = list(updated.get("lifecycle_history") or [])
        hist.append({"from": current, "to": to_status})
        updated["lifecycle_history"] = hist[-50:]
        return updated

    def path(self) -> list[str]:
        return list(LIFECYCLE_STATUSES)
