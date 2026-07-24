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

from applications.enterprise_hub.api_standardization.models import HTTP_METHODS, STANDARD_REST_RESOURCES


class RestStandard:
    """Canonical REST resource map under /api/{version}/."""

    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def catalog(self, version: str = "v1") -> dict[str, Any]:
        resources = []
        for name in STANDARD_REST_RESOURCES:
            resources.append(
                {
                    "path": f"/api/{version}/{name}",
                    "methods": list(HTTP_METHODS),
                    "resource": name,
                }
            )
        rid = _id("eas_rest")
        record = {
            "standard_id": rid,
            "version": version,
            "base_path": f"/api/{version}/",
            "resources": resources,
            "methods": list(HTTP_METHODS),
            "built_at": _now(),
        }
        self.store.eas_rest_standards.save(rid, record)
        return record
