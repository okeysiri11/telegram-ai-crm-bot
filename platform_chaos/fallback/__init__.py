"""Fallback Engine — Sprint 25.3."""

from __future__ import annotations

from typing import Any

from platform_chaos.models import FALLBACK_TARGETS


class FallbackEngine:
    def activate(self, *, preferred: str | None = None) -> dict[str, Any]:
        preferred = (preferred or "degraded_mode").lower()
        if preferred not in FALLBACK_TARGETS:
            raise ValueError(f"unsupported fallback: {preferred}")
        return {
            "activated": True,
            "fallback": preferred,
            "targets": list(FALLBACK_TARGETS),
            "service_continued": True,
            "degraded": preferred == "degraded_mode",
        }
