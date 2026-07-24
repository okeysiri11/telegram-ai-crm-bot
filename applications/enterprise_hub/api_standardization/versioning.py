from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.shared.exceptions import NotFoundError, ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"

from applications.enterprise_hub.api_standardization.models import API_VERSIONS


class ApiVersioning:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def matrix(self) -> dict[str, Any]:
        vid = _id("eas_ver")
        record = {
            "versioning_id": vid,
            "supported": list(API_VERSIONS),
            "default": "v1",
            "compatibility": {
                "v1": "stable",
                "v2": "stable",
                "experimental": "opt_in",
                "deprecated": "read_only_sunset",
            },
            "backward_compatible": True,
            "built_at": _now(),
        }
        self.store.eas_versioning.save(vid, record)
        return record

    def resolve(self, version: str | None) -> dict[str, Any]:
        v = (version or "v1").lower()
        if v not in API_VERSIONS:
            raise ValidationError(f"unsupported API version: {version}")
        return {
            "version": v,
            "status": "deprecated" if v == "deprecated" else "active",
            "compatible_with": ["v1"] if v in ("v1", "v2", "deprecated") else ["experimental"],
        }
