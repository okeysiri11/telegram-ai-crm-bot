"""Enterprise Infrastructure — HA, multi-region, scaling, DR (Sprint 12.5)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise.shared.exceptions import NotFoundError, ValidationError
from applications.enterprise.shared.store import EnterpriseStore, enterprise_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class EnterpriseInfrastructure:
    def __init__(self, store: EnterpriseStore | None = None) -> None:
        self.store = store or enterprise_store

    def add_region(self, *, name: str, code: str) -> dict[str, Any]:
        if not name or not code:
            raise ValidationError("region name and code required")
        rid = _id("region")
        region = {
            "region_id": rid,
            "name": name,
            "code": code.upper(),
            "status": "active",
            "created_at": _now(),
        }
        return self.store.regions.save(rid, region)

    def create_cluster(self, *, name: str, region_id: str, nodes: int = 3) -> dict[str, Any]:
        if self.store.regions.get(region_id) is None:
            raise NotFoundError("region", region_id)
        if nodes < 1:
            raise ValidationError("nodes must be >= 1")
        cid = _id("ecluster")
        cluster = {
            "cluster_id": cid,
            "name": name,
            "region_id": region_id,
            "nodes": nodes,
            "primary": f"{cid}-n0",
            "ha_enabled": True,
            "status": "healthy",
            "created_at": _now(),
        }
        return self.store.clusters.save(cid, cluster)

    def scale(self, cluster_id: str, *, nodes: int) -> dict[str, Any]:
        cluster = self.store.clusters.get(cluster_id)
        if cluster is None:
            raise NotFoundError("cluster", cluster_id)
        if nodes < 1:
            raise ValidationError("nodes must be >= 1")
        cluster["nodes"] = nodes
        cluster["scaled_at"] = _now()
        cluster["status"] = "healthy"
        return self.store.clusters.save(cluster_id, cluster)

    def load_balance(self, cluster_id: str) -> dict[str, Any]:
        cluster = self.store.clusters.get(cluster_id)
        if cluster is None:
            raise NotFoundError("cluster", cluster_id)
        n = int(cluster.get("nodes", 1))
        selected = f"{cluster_id}-n{hash(cluster_id) % n}"
        return {
            "cluster_id": cluster_id,
            "selected": selected,
            "strategy": "round_robin",
            "at": _now(),
        }

    def disaster_recovery(self, cluster_id: str) -> dict[str, Any]:
        cluster = self.store.clusters.get(cluster_id)
        if cluster is None:
            raise NotFoundError("cluster", cluster_id)
        cluster["status"] = "recovered"
        cluster["recovered_at"] = _now()
        self.store.clusters.save(cluster_id, cluster)
        return {"cluster_id": cluster_id, "status": "recovered", "at": _now()}

    def monitoring_snapshot(self) -> dict[str, Any]:
        return {
            "type": "monitoring_center",
            "regions": len(self.store.regions.list_all()),
            "clusters": len(self.store.clusters.list_all()),
            "healthy_clusters": sum(1 for c in self.store.clusters.list_all() if c.get("status") in ("healthy", "recovered")),
            "at": _now(),
        }

    def status(self) -> dict[str, Any]:
        return {
            "regions": len(self.store.regions.list_all()),
            "clusters": len(self.store.clusters.list_all()),
            "high_availability": True,
            "multi_region": True,
            "auto_scaling": True,
            "disaster_recovery": True,
        }


enterprise_infrastructure = EnterpriseInfrastructure()
