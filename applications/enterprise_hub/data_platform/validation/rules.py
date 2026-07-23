"""Business rule validation engine."""

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


class RuleEngine:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def evaluate(
        self,
        *,
        rule: str,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if not rule:
            raise ValidationError("rule required")
        data = payload or {}
        passed = True
        detail = ""
        if rule == "name_required":
            passed = bool(data.get("name"))
            detail = "name present" if passed else "name missing"
        elif rule == "status_active":
            passed = data.get("status", "active") == "active"
            detail = "active" if passed else "inactive"
        else:
            passed = True
            detail = f"custom:{rule}"
        rid = _id("edp_rule")
        return self.store.edp_rules.save(
            rid,
            {
                "rule_id": rid,
                "rule": rule,
                "passed": passed,
                "detail": detail,
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"evaluations": self.store.edp_rules.count()}
