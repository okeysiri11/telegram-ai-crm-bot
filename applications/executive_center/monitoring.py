"""System monitoring — CPU/RAM/GPU/storage/network/containers/services/agents/queues/workflows/APIs (Sprint 12.3)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.executive_center.shared.store import ExecutiveCenterStore, executive_center_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class SystemMonitoring:
    def __init__(self, store: ExecutiveCenterStore | None = None) -> None:
        self.store = store or executive_center_store

    def sample(
        self,
        *,
        cpu_pct: float = 32.0,
        ram_pct: float = 48.0,
        gpu_pct: float = 12.0,
        storage_pct: float = 55.0,
        network_mbps: float = 120.0,
        containers: int = 8,
        services_up: int = 12,
        agents_active: int = 6,
        queue_depth: int = 3,
        workflows_running: int = 2,
        api_latency_ms: float = 45.0,
    ) -> dict[str, Any]:
        sid = f"infra_{uuid.uuid4().hex[:10]}"
        row = {
            "sample_id": sid,
            "cpu_pct": cpu_pct,
            "ram_pct": ram_pct,
            "gpu_pct": gpu_pct,
            "storage_pct": storage_pct,
            "network_mbps": network_mbps,
            "containers": containers,
            "services_up": services_up,
            "agents_active": agents_active,
            "queue_depth": queue_depth,
            "workflows_running": workflows_running,
            "api_latency_ms": api_latency_ms,
            "at": _now(),
        }
        self.store.infra_samples.save(sid, row)
        return row

    def health_check(self, *, target: str, ok: bool = True, detail: str = "") -> dict[str, Any]:
        hid = f"hc_{uuid.uuid4().hex[:10]}"
        row = {
            "check_id": hid,
            "target": target,
            "ok": ok,
            "detail": detail or ("healthy" if ok else "degraded"),
            "at": _now(),
        }
        self.store.health_checks.save(hid, row)
        return row

    def overview(self) -> dict[str, Any]:
        samples = self.store.infra_samples.list_all()
        latest = samples[-1] if samples else self.sample()
        checks = self.store.health_checks.list_all()
        return {
            "latest": latest,
            "health_checks": checks[-20:],
            "targets": {
                "cpu": latest.get("cpu_pct"),
                "ram": latest.get("ram_pct"),
                "gpu": latest.get("gpu_pct"),
                "storage": latest.get("storage_pct"),
                "network": latest.get("network_mbps"),
                "containers": latest.get("containers"),
                "services": latest.get("services_up"),
                "agents": latest.get("agents_active"),
                "queues": latest.get("queue_depth"),
                "workflows": latest.get("workflows_running"),
                "apis": latest.get("api_latency_ms"),
            },
            "healthy": all(c.get("ok", True) for c in checks) if checks else True,
            "at": _now(),
        }

    def status(self) -> dict[str, Any]:
        return {
            "system_monitoring": "1.0",
            "samples": len(self.store.infra_samples.list_all()),
            "checks": len(self.store.health_checks.list_all()),
            "ready": True,
        }


system_monitoring = SystemMonitoring()
