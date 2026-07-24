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




class ConsistencyChecker:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def check(self) -> dict[str, Any]:
        twins = self.store.edt_twins.list_all()
        rels = self.store.edt_relationships.list_all()
        twin_ids = {t["twin_id"] for t in twins}
        broken = [r for r in rels if r.get("source_id") not in twin_ids or r.get("target_id") not in twin_ids]
        inactive_links = []
        for r in rels:
            src = self.store.edt_twins.get(r.get("source_id"))
            tgt = self.store.edt_twins.get(r.get("target_id"))
            if src and tgt and (src.get("status") == "deleted" or tgt.get("status") == "deleted"):
                inactive_links.append(r["relationship_id"])
        cid = _id("edt_cons")
        return self.store.edt_consistency.save(
            cid,
            {
                "check_id": cid,
                "twins": len(twins),
                "relationships": len(rels),
                "broken_links": len(broken),
                "inactive_links": inactive_links,
                "consistent": len(broken) == 0,
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        items = self.store.edt_consistency.list_all()
        return {"checks": len(items), "last_consistent": items[-1]["consistent"] if items else True}
