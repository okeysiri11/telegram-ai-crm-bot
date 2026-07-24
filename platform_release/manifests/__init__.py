"""Production manifests — Sprint 21.8."""

from __future__ import annotations

from typing import Any

from platform_release.models import LTS_LABEL, LTS_VERSION, PRODUCTION_STATUSES


class ProductionManifest:
    def publish(self, *, approval: dict[str, Any]) -> dict[str, Any]:
        return {
            "manifest_version": LTS_VERSION,
            "label": LTS_LABEL,
            "statuses": list(PRODUCTION_STATUSES),
            "approved": approval.get("approved", False),
            "published": approval.get("approved", False),
            "channel": "stable-lts",
        }
