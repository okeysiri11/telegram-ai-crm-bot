"""Versioned documentation — Sprint 21.6."""

from __future__ import annotations

from typing import Any

from platform_documentation.models import DOC_CHANNELS


class DocumentationVersioning:
    def matrix(self, *, version: str) -> dict[str, Any]:
        return {
            "version": version,
            "channels": list(DOC_CHANNELS),
            "default_channel": "release_candidate" if "rc" in version else "release",
            "sets": [
                {"channel": ch, "bundle": f"{version}/{ch}"} for ch in DOC_CHANNELS
            ],
        }
