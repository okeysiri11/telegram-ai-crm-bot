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

from applications.enterprise_hub.api_standardization.models import AUTH_MECHANISMS


class SecurityGovernance:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def check(self, *, public_unauthenticated: list[str] | None = None) -> dict[str, Any]:
        unauth = list(public_unauthenticated or [])
        # health endpoints may be unauthenticated; others flagged
        flagged = [p for p in unauth if not p.endswith("/health")]
        cid = _id("eas_sec")
        record = {
            "check_id": cid,
            "required_mechanisms": list(AUTH_MECHANISMS),
            "unauthenticated_paths": unauth,
            "flagged": flagged,
            "passed": len(flagged) == 0,
            "checked_at": _now(),
        }
        self.store.eas_governance.save(cid, record)
        return record
