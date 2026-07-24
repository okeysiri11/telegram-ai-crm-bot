"""Publishing engine — Sprint 21.6."""

from __future__ import annotations

from typing import Any
import uuid

from platform_documentation.models import PUBLISH_FORMATS


class PublishingEngine:
    def publish(self, *, docs: list[dict[str, Any]], formats: list[str] | None = None) -> dict[str, Any]:
        selected = list(formats or PUBLISH_FORMATS)
        unknown = [f for f in selected if f not in PUBLISH_FORMATS]
        if unknown:
            raise ValueError(f"unsupported formats: {', '.join(unknown)}")
        artifacts = []
        for fmt in selected:
            artifacts.append(
                {
                    "artifact_id": f"pub_{uuid.uuid4().hex[:10]}",
                    "format": fmt,
                    "pages": len(docs),
                    "url": f"/docs/published/{fmt}/index",
                }
            )
        return {
            "publish_id": f"pubrun_{uuid.uuid4().hex[:10]}",
            "formats": selected,
            "artifacts": artifacts,
            "portals": {
                "developer": True,
                "administrator": True,
                "internal": True,
            },
        }
