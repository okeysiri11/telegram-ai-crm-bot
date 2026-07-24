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

from applications.enterprise_hub.api_standardization.models import API_CATEGORIES, HTTP_METHODS


class EndpointRegistry:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def register(
        self,
        *,
        path: str,
        method: str = "GET",
        category: str = "public",
        service: str = "custom",
        version: str = "v1",
        deprecated: bool = False,
    ) -> dict[str, Any]:
        if not path:
            raise ValidationError("path is required")
        method = method.upper()
        if method not in HTTP_METHODS:
            raise ValidationError(f"invalid method: {method}")
        if category not in API_CATEGORIES:
            raise ValidationError(f"invalid category: {category}")
        rid = _id("eas_reg")
        return self.store.eas_registry.save(
            rid,
            {
                "registry_id": rid,
                "path": path,
                "method": method,
                "category": category,
                "service": service,
                "version": version,
                "deprecated": deprecated,
                "registered_at": _now(),
            },
        )

    def list_all(self) -> list[dict[str, Any]]:
        return self.store.eas_registry.list_all()

    def status(self) -> dict[str, Any]:
        items = self.list_all()
        return {
            "registered": len(items),
            "deprecated": sum(1 for i in items if i.get("deprecated")),
        }
