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



from applications.enterprise_hub.digital_twin.models import RELATION_KINDS


class RelationshipManager:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def link(
        self,
        *,
        source_id: str,
        target_id: str,
        kind: str = "depends_on",
        label: str = "",
    ) -> dict[str, Any]:
        if kind not in RELATION_KINDS:
            raise ValidationError(f"invalid relation kind: {kind}")
        if not self.store.edt_twins.get(source_id) or not self.store.edt_twins.get(target_id):
            raise NotFoundError("source or target twin not found")
        rid = _id("edt_rel")
        record = {
            "relationship_id": rid,
            "source_id": source_id,
            "target_id": target_id,
            "kind": kind,
            "label": label or kind,
            "created_at": _now(),
        }
        self.store.edt_relationships.save(rid, record)
        src = self.store.edt_twins.get(source_id)
        src.setdefault("relationships", []).append(rid)
        self.store.edt_twins.save(source_id, src)
        return record

    def graph(self, *, root_id: str | None = None) -> dict[str, Any]:
        rels = self.store.edt_relationships.list_all()
        twins = {t["twin_id"]: t for t in self.store.edt_twins.list_all()}
        nodes = [{"id": tid, "name": t.get("name"), "type": t.get("twin_type")} for tid, t in twins.items()]
        edges = [{"id": r["relationship_id"], "source": r["source_id"], "target": r["target_id"], "kind": r["kind"]} for r in rels]
        if root_id:
            connected = {root_id}
            changed = True
            while changed:
                changed = False
                for e in edges:
                    if e["source"] in connected and e["target"] not in connected:
                        connected.add(e["target"])
                        changed = True
                    if e["target"] in connected and e["source"] not in connected:
                        connected.add(e["source"])
                        changed = True
            nodes = [n for n in nodes if n["id"] in connected]
            edges = [e for e in edges if e["source"] in connected and e["target"] in connected]
        return {"nodes": nodes, "edges": edges, "node_count": len(nodes), "edge_count": len(edges)}

    def status(self) -> dict[str, Any]:
        return {"relationships": len(self.store.edt_relationships.list_all())}
