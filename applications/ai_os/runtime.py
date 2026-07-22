"""AI Runtime — execution, sandbox, security, context, state, checkpoint, recovery (Sprint 12.4)."""

from __future__ import annotations

import copy
import uuid
from datetime import datetime, timezone
from typing import Any

from applications.ai_os.shared.exceptions import NotFoundError, ValidationError
from applications.ai_os.shared.store import AIOSStore, ai_os_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class AIRuntime:
    def __init__(self, store: AIOSStore | None = None) -> None:
        self.store = store or ai_os_store

    def create_context(self, *, name: str = "default", data: dict[str, Any] | None = None) -> dict[str, Any]:
        cid = f"ctx_{uuid.uuid4().hex[:12]}"
        ctx = {"context_id": cid, "name": name, "data": dict(data or {}), "at": _now()}
        self.store.contexts.save(cid, ctx)
        return ctx

    def execute(
        self,
        *,
        name: str,
        payload: dict[str, Any] | None = None,
        context_id: str = "",
        sandboxed: bool = True,
    ) -> dict[str, Any]:
        if sandboxed and isinstance(payload, dict) and payload.get("unsafe"):
            raise ValidationError("security layer blocked unsafe payload in sandbox")
        jid = f"rt_{uuid.uuid4().hex[:12]}"
        job = {
            "runtime_id": jid,
            "name": name,
            "payload": dict(payload or {}),
            "context_id": context_id,
            "sandboxed": sandboxed,
            "security": "allowed",
            "state": {"step": 0, "status": "running"},
            "status": "running",
            "started_at": _now(),
        }
        # simple execution
        job["state"] = {"step": 1, "status": "completed", "result": {"echo": payload, "ok": True}}
        job["status"] = "completed"
        job["finished_at"] = _now()
        self.store.runtime_jobs.save(jid, job)
        self.checkpoint(jid)
        return job

    def get(self, runtime_id: str) -> dict[str, Any]:
        item = self.store.runtime_jobs.get(runtime_id)
        if item is None:
            raise NotFoundError("runtime_job", runtime_id)
        return item

    def checkpoint(self, runtime_id: str) -> dict[str, Any]:
        job = self.get(runtime_id)
        cid = f"chk_{uuid.uuid4().hex[:10]}"
        snap = {
            "checkpoint_id": cid,
            "runtime_id": runtime_id,
            "state": copy.deepcopy(job.get("state") or {}),
            "status": job.get("status"),
            "at": _now(),
        }
        self.store.checkpoints.save(cid, snap)
        return snap

    def recover(self, runtime_id: str, *, checkpoint_id: str | None = None) -> dict[str, Any]:
        job = self.get(runtime_id)
        snaps = [c for c in self.store.checkpoints.list_all() if c.get("runtime_id") == runtime_id]
        if checkpoint_id:
            snap = self.store.checkpoints.get(checkpoint_id)
            if snap is None or snap.get("runtime_id") != runtime_id:
                raise NotFoundError("checkpoint", checkpoint_id or "")
        else:
            if not snaps:
                raise ValidationError("no checkpoint available")
            snap = snaps[-1]
        job["state"] = copy.deepcopy(snap.get("state") or {})
        job["status"] = "recovered"
        job["recovered_from"] = snap.get("checkpoint_id")
        job["updated_at"] = _now()
        self.store.runtime_jobs.save(runtime_id, job)
        return job

    def state(self, runtime_id: str) -> dict[str, Any]:
        job = self.get(runtime_id)
        return {"runtime_id": runtime_id, "state": job.get("state"), "status": job.get("status")}

    def status(self) -> dict[str, Any]:
        return {
            "ai_runtime": "1.0",
            "jobs": len(self.store.runtime_jobs.list_all()),
            "checkpoints": len(self.store.checkpoints.list_all()),
            "ready": True,
        }


ai_runtime = AIRuntime()
