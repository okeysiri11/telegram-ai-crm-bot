"""Data transformer — format conversion, filter, merge, normalize."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.shared.exceptions import ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class DataTransformer:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def transform(
        self,
        *,
        data: Any,
        operation: str = "normalize",
        options: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        op = operation.lower().strip()
        opts = options or {}
        if op == "filter" and isinstance(data, dict):
            keys = opts.get("keys") or list(data.keys())
            out: Any = {k: data[k] for k in keys if k in data}
        elif op == "merge" and isinstance(data, list):
            merged: dict[str, Any] = {}
            for item in data:
                if isinstance(item, dict):
                    merged.update(item)
            out = merged
        elif op == "format":
            out = {"format": opts.get("format", "json"), "data": data}
        else:
            # normalize
            if isinstance(data, dict):
                out = {str(k).lower(): v for k, v in data.items()}
            else:
                out = data
        tid = _id("eip_xf")
        return self.store.eip_transforms.save(
            tid,
            {
                "transform_id": tid,
                "operation": op,
                "result": out,
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"transforms": self.store.eip_transforms.count()}
