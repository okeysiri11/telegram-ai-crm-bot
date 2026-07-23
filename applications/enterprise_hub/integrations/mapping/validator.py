"""Schema / mapping validator."""

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


class MappingValidator:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def validate(
        self,
        *,
        data: dict[str, Any],
        required: list[str] | None = None,
    ) -> dict[str, Any]:
        if not isinstance(data, dict):
            raise ValidationError("data must be an object")
        req = required or []
        missing = [k for k in req if k not in data]
        vid = _id("eip_mval")
        return self.store.eip_mapping_validations.save(
            vid,
            {
                "validation_id": vid,
                "valid": not missing,
                "missing": missing,
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"validations": self.store.eip_mapping_validations.count()}
