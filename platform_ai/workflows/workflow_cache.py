# Workflow result cache with TTL and invalidation.

from __future__ import annotations

import hashlib
import json
import time
from typing import Any

from platform_ai.workflows.models import WorkflowExecutionResult


class WorkflowCache:
    def __init__(self) -> None:
        self._store: dict[str, tuple[float, WorkflowExecutionResult]] = {}
        self._default_ttl = 3600.0

    def reset(self) -> None:
        self._store.clear()

    def _key(self, workflow_id: str, input_data: dict[str, Any]) -> str:
        payload = json.dumps({"workflow_id": workflow_id, "input": input_data}, sort_keys=True, default=str)
        return hashlib.sha256(payload.encode()).hexdigest()

    def get(self, workflow_id: str, input_data: dict[str, Any], ttl: float | None = None) -> WorkflowExecutionResult | None:
        key = self._key(workflow_id, input_data)
        entry = self._store.get(key)
        if not entry:
            return None
        expires_at, result = entry
        if time.time() > expires_at:
            del self._store[key]
            return None
        cached = WorkflowExecutionResult(
            execution_id=result.execution_id,
            workflow_id=result.workflow_id,
            status=result.status,
            output=dict(result.output),
            step_results=list(result.step_results),
            memory=dict(result.memory),
            latency_ms=result.latency_ms,
            cost_usd=result.cost_usd,
            cached=True,
        )
        return cached

    def set(self, workflow_id: str, input_data: dict[str, Any], result: WorkflowExecutionResult, ttl: float | None = None) -> None:
        key = self._key(workflow_id, input_data)
        self._store[key] = (time.time() + (ttl or self._default_ttl), result)

    def invalidate(self, workflow_id: str | None = None) -> int:
        if workflow_id is None:
            count = len(self._store)
            self._store.clear()
            return count
        keys = [k for k, (_, r) in self._store.items() if r.workflow_id == workflow_id]
        for k in keys:
            del self._store[k]
        return len(keys)

    def stats(self) -> dict[str, Any]:
        return {"entries": len(self._store)}


workflow_cache = WorkflowCache()
