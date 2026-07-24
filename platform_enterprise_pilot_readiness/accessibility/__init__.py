"""Accessibility checks — Sprint 23.1."""

from __future__ import annotations

from typing import Any


class AccessibilityAudit:
    def check(self, *, devices: list[str] | None = None, scale: float = 1.0, readability: float = 0.9) -> dict[str, Any]:
        devices = list(devices or ["mobile", "tablet", "desktop"])
        required = {"mobile", "tablet", "desktop"}
        covered = required.issubset(set(devices))
        scale = float(scale)
        readability = float(readability)
        return {
            "devices": devices,
            "mobile_ok": "mobile" in devices,
            "tablet_ok": "tablet" in devices,
            "desktop_ok": "desktop" in devices or "large_monitor" in devices,
            "scale_support": scale >= 1.0,
            "readability": readability,
            "accessible": covered and scale >= 1.0 and readability >= 0.8,
        }
