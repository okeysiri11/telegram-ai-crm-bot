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

class CompatibilityGovernance:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def check(self, *, breaking_changes: list[str] | None = None) -> dict[str, Any]:
        breaking = list(breaking_changes or [])
        cid = _id("eas_compat")
        record = {
            "check_id": cid,
            "breaking_changes": breaking,
            "backward_compatible": len(breaking) == 0,
            "checked_at": _now(),
        }
        self.store.eas_governance.save(cid, record)
        return record
