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

from applications.enterprise_hub.api_standardization.docs_gen.openapi import OpenApiBuilder


class ReDoc:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.openapi = OpenApiBuilder(self.store)

    def render(self, openapi_id: str | None = None) -> dict[str, Any]:
        if openapi_id:
            spec_rec = self.store.eas_openapi.get(openapi_id)
            if not spec_rec:
                raise NotFoundError(f"openapi not found: {openapi_id}")
        else:
            spec_rec = self.openapi.build()
        rid = _id("eas_redoc")
        record = {
            "redoc_id": rid,
            "openapi_id": spec_rec["openapi_id"],
            "ui": {"type": "redoc", "url": f"/docs/redoc/{rid}"},
            "rendered_at": _now(),
        }
        self.store.eas_redoc.save(rid, record)
        return record
