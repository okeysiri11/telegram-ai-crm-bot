"""Consistency checks across related records."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class ConsistencyChecker:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def check(self) -> dict[str, Any]:
        issues: list[str] = []
        for rel in self.store.edp_relationships.list_all():
            if not isinstance(rel, dict):
                continue
            if self.store.edp_entities.get(rel.get("from_entity_id", "")) is None:
                issues.append(f"missing_from:{rel.get('relationship_id')}")
            if self.store.edp_entities.get(rel.get("to_entity_id", "")) is None:
                issues.append(f"missing_to:{rel.get('relationship_id')}")
        for ent in self.store.edp_entities.list_all():
            if isinstance(ent, dict) and not ent.get("name"):
                issues.append(f"empty_name:{ent.get('entity_id')}")
        cid = _id("edp_cons")
        return self.store.edp_consistency.save(
            cid,
            {
                "check_id": cid,
                "issues": issues,
                "ok": not issues,
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"checks": self.store.edp_consistency.count()}
