"""Orchestrator monitoring — timeline, status, performance, failures, history."""

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


class OrchestratorMonitoring:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def track(
        self,
        *,
        execution_id: str,
        task: str,
        status: str = "running",
        duration_ms: float = 0.0,
    ) -> dict[str, Any]:
        if not execution_id or not task:
            raise ValidationError("execution_id and task required")
        tid = _id("orch_mon")
        return self.store.orch_monitors.save(
            tid,
            {
                "monitor_id": tid,
                "execution_id": execution_id,
                "task": task,
                "status": status,
                "duration_ms": float(duration_ms),
                "at": _now(),
            },
        )

    def failure(
        self, *, execution_id: str, reason: str, analysis: str = ""
    ) -> dict[str, Any]:
        if not execution_id or not reason:
            raise ValidationError("execution_id and reason required")
        fid = _id("orch_fail")
        return self.store.orch_failures.save(
            fid,
            {
                "failure_id": fid,
                "execution_id": execution_id,
                "reason": reason,
                "analysis": analysis or reason,
                "at": _now(),
            },
        )

    def history(self, *, execution_id: str, summary: str = "") -> dict[str, Any]:
        if not execution_id:
            raise ValidationError("execution_id required")
        hid = _id("orch_hist")
        return self.store.orch_history.save(
            hid,
            {
                "history_id": hid,
                "execution_id": execution_id,
                "summary": summary or f"history for {execution_id}",
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "monitors": self.store.orch_monitors.count(),
            "failures": self.store.orch_failures.count(),
            "history": self.store.orch_history.count(),
        }
