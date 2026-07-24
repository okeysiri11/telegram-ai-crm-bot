
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

from applications.enterprise_hub.business_capabilities.capability_registry import CapabilityRegistry


class DependencyEngine:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.registry = CapabilityRegistry(self.store)

    def link(self, source_key: str, target_key: str, kind: str = "depends_on") -> dict[str, Any]:
        if source_key == target_key:
            raise ValidationError("cannot depend on self")
        self.registry.require_key(source_key)
        self.registry.require_key(target_key)
        did = _id("ebc_dep")
        return self.store.ebc_dependencies.save(
            did,
            {
                "dependency_id": did,
                "source_key": source_key,
                "target_key": target_key,
                "kind": kind,
                "linked_at": _now(),
            },
        )

    def link_many(self, pairs: list[tuple[str, str]]) -> list[dict[str, Any]]:
        return [self.link(s, t) for s, t in pairs]

    def graph(self) -> dict[str, Any]:
        deps = self.store.ebc_dependencies.list_all()
        nodes = sorted({d["source_key"] for d in deps} | {d["target_key"] for d in deps})
        edges = [{"from": d["source_key"], "to": d["target_key"], "kind": d.get("kind")} for d in deps]
        gid = _id("ebc_dgraph")
        record = {"graph_id": gid, "nodes": nodes, "edges": edges, "edge_count": len(edges), "built_at": _now()}
        self.store.ebc_dependency_graphs.save(gid, record)
        return record

    def downstream(self, key: str) -> list[str]:
        seen: set[str] = set()
        frontier = [key]
        while frontier:
            cur = frontier.pop()
            for d in self.store.ebc_dependencies.list_all():
                if d["source_key"] == cur and d["target_key"] not in seen:
                    seen.add(d["target_key"])
                    frontier.append(d["target_key"])
        return sorted(seen)

    def status(self) -> dict[str, Any]:
        return {
            "dependencies": len(self.store.ebc_dependencies.list_all()),
            "graphs": len(self.store.ebc_dependency_graphs.list_all()),
        }
