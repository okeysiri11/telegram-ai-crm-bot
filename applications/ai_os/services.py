"""AI Communication + Enterprise HA + Observability (Sprint 12.4)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.ai_os.shared.exceptions import NotFoundError, ValidationError
from applications.ai_os.shared.store import AIOSStore, ai_os_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


CHANNELS = (
    "agent_to_agent",
    "application_to_application",
    "human_to_ai",
    "ai_to_human",
    "cross_platform",
)


class AICommunication:
    def __init__(self, store: AIOSStore | None = None) -> None:
        self.store = store or ai_os_store

    def send(
        self,
        *,
        channel: str,
        sender: str,
        recipient: str,
        body: str,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if channel not in CHANNELS:
            raise ValidationError(f"channel must be one of {CHANNELS}")
        mid = f"msg_{uuid.uuid4().hex[:12]}"
        row = {
            "message_id": mid,
            "channel": channel,
            "sender": sender,
            "recipient": recipient,
            "body": body,
            "metadata": dict(metadata or {}),
            "at": _now(),
        }
        self.store.messages.save(mid, row)
        return row

    def inbox(self, recipient: str) -> list[dict[str, Any]]:
        return [m for m in self.store.messages.list_all() if m.get("recipient") == recipient]

    def status(self) -> dict[str, Any]:
        return {"ai_communication": "1.0", "channels": list(CHANNELS), "messages": len(self.store.messages.list_all()), "ready": True}


class EnterpriseAIOS:
    def __init__(self, store: AIOSStore | None = None) -> None:
        self.store = store or ai_os_store

    def create_cluster(self, *, name: str, region: str = "global", nodes: int = 3) -> dict[str, Any]:
        cid = f"cl_{uuid.uuid4().hex[:10]}"
        cluster = {
            "cluster_id": cid,
            "name": name,
            "region": region,
            "ha": True,
            "horizontal_scaling": True,
            "distributed_ai": True,
            "load_balancer": "round_robin",
            "status": "online",
            "created_at": _now(),
        }
        self.store.clusters.save(cid, cluster)
        for i in range(max(1, nodes)):
            nid = f"node_{cid}_{i}"
            self.store.nodes.save(
                nid,
                {"node_id": nid, "cluster_id": cid, "index": i, "status": "ready", "load": 0.1 * i, "at": _now()},
            )
        return cluster

    def get_cluster(self, cluster_id: str) -> dict[str, Any]:
        item = self.store.clusters.get(cluster_id)
        if item is None:
            raise NotFoundError("cluster", cluster_id)
        return item

    def scale(self, cluster_id: str, *, nodes: int) -> dict[str, Any]:
        cluster = self.get_cluster(cluster_id)
        existing = [n for n in self.store.nodes.list_all() if n.get("cluster_id") == cluster_id]
        while len(existing) < nodes:
            i = len(existing)
            nid = f"node_{cluster_id}_{i}"
            node = {"node_id": nid, "cluster_id": cluster_id, "index": i, "status": "ready", "load": 0.0, "at": _now()}
            self.store.nodes.save(nid, node)
            existing.append(node)
        cluster["scaled_to"] = nodes
        cluster["updated_at"] = _now()
        self.store.clusters.save(cluster_id, cluster)
        return {"cluster": cluster, "nodes": existing[:nodes]}

    def failover(self, cluster_id: str, *, from_node: str, to_node: str = "") -> dict[str, Any]:
        self.get_cluster(cluster_id)
        nodes = [n for n in self.store.nodes.list_all() if n.get("cluster_id") == cluster_id]
        src = self.store.nodes.get(from_node)
        if src is None:
            raise NotFoundError("node", from_node)
        src["status"] = "failed"
        self.store.nodes.save(from_node, src)
        target = self.store.nodes.get(to_node) if to_node else next((n for n in nodes if n.get("node_id") != from_node and n.get("status") == "ready"), None)
        if target is None:
            raise ValidationError("no healthy failover target")
        target["status"] = "primary"
        target["load"] = float(target.get("load", 0)) + float(src.get("load", 0))
        self.store.nodes.save(target["node_id"], target)
        return {"failed": from_node, "primary": target["node_id"], "at": _now()}

    def disaster_recovery(self, cluster_id: str) -> dict[str, Any]:
        cluster = self.get_cluster(cluster_id)
        for node in [n for n in self.store.nodes.list_all() if n.get("cluster_id") == cluster_id]:
            node["status"] = "ready"
            node["load"] = 0.1
            self.store.nodes.save(node["node_id"], node)
        cluster["status"] = "recovered"
        cluster["updated_at"] = _now()
        self.store.clusters.save(cluster_id, cluster)
        return {"cluster_id": cluster_id, "status": "recovered", "at": _now()}

    def load_balance(self, cluster_id: str) -> dict[str, Any]:
        nodes = [n for n in self.store.nodes.list_all() if n.get("cluster_id") == cluster_id and n.get("status") in {"ready", "primary"}]
        if not nodes:
            raise ValidationError("no nodes available")
        chosen = min(nodes, key=lambda n: float(n.get("load", 0)))
        chosen["load"] = float(chosen.get("load", 0)) + 0.05
        self.store.nodes.save(chosen["node_id"], chosen)
        return {"selected": chosen["node_id"], "strategy": "least_load"}

    def status(self) -> dict[str, Any]:
        return {
            "enterprise": "1.0",
            "clusters": len(self.store.clusters.list_all()),
            "nodes": len(self.store.nodes.list_all()),
            "ready": True,
        }


class Observability:
    def __init__(self, store: AIOSStore | None = None) -> None:
        self.store = store or ai_os_store

    def log(self, *, level: str, message: str, source: str = "ai_os") -> dict[str, Any]:
        lid = f"log_{uuid.uuid4().hex[:10]}"
        row = {"log_id": lid, "level": level, "message": message, "source": source, "at": _now()}
        self.store.logs.save(lid, row)
        return row

    def metric(self, *, name: str, value: float, tags: dict[str, Any] | None = None) -> dict[str, Any]:
        mid = f"met_{uuid.uuid4().hex[:10]}"
        row = {"metric_id": mid, "name": name, "value": value, "tags": dict(tags or {}), "at": _now()}
        self.store.metrics.save(mid, row)
        return row

    def trace(self, *, name: str, spans: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        tid = f"tr_{uuid.uuid4().hex[:10]}"
        row = {"trace_id": tid, "name": name, "spans": list(spans or []), "at": _now()}
        self.store.traces.save(tid, row)
        return row

    def alert(self, *, severity: str, message: str, source: str = "ai_os") -> dict[str, Any]:
        aid = f"al_{uuid.uuid4().hex[:10]}"
        row = {"alert_id": aid, "severity": severity, "message": message, "source": source, "status": "open", "at": _now()}
        self.store.alerts.save(aid, row)
        return row

    def health_dashboard(self) -> dict[str, Any]:
        return {
            "type": "health_dashboard",
            "logs": len(self.store.logs.list_all()),
            "alerts_open": len([a for a in self.store.alerts.list_all() if a.get("status") == "open"]),
            "at": _now(),
        }

    def performance_dashboard(self) -> dict[str, Any]:
        metrics = self.store.metrics.list_all()
        return {
            "type": "performance_dashboard",
            "metrics": metrics[-20:],
            "traces": len(self.store.traces.list_all()),
            "at": _now(),
        }

    def status(self) -> dict[str, Any]:
        return {
            "observability": "1.0",
            "logs": len(self.store.logs.list_all()),
            "metrics": len(self.store.metrics.list_all()),
            "traces": len(self.store.traces.list_all()),
            "alerts": len(self.store.alerts.list_all()),
            "ready": True,
        }


ai_communication = AICommunication()
enterprise_ai_os = EnterpriseAIOS()
observability = Observability()
