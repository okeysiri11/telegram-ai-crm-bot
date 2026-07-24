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

class NamingGovernance:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def check(self, paths: list[str]) -> dict[str, Any]:
        issues = []
        for path in paths:
            if not path.startswith("/"):
                issues.append({"path": path, "issue": "must_start_with_slash"})
            if path.endswith("/") and path != "/":
                issues.append({"path": path, "issue": "trailing_slash"})
            if any(ch.isupper() for ch in path):
                issues.append({"path": path, "issue": "must_be_lowercase"})
        cid = _id("eas_name")
        record = {
            "check_id": cid,
            "checked": len(paths),
            "issues": issues,
            "passed": len(issues) == 0,
            "checked_at": _now(),
        }
        self.store.eas_governance.save(cid, record)
        return record
