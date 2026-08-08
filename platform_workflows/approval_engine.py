"""Epic 45.3 — Approval Engine (Human Mode waits, AI Mode auto)."""
from __future__ import annotations
from typing import Any
from platform_workflows.ua_store import ua_store

class ApprovalEngine:
    def requires_approval(self, owner_id: str) -> bool:
        try:
            from platform_modes.manager import mode_manager
            from platform_modes.mode_state import WorkMode
            mode = mode_manager.get(owner_id).mode
            return mode == WorkMode.HUMAN_MODE
        except Exception:
            return True  # Human First default
    def request(self, run_id: str, *, step: dict[str, Any], preview: str) -> dict[str, Any]:
        run = ua_store.runs.get(run_id)
        if not run:
            return {"error": "run_not_found"}
        run.status = "awaiting_approval"
        run.result["pending_approval"] = {"step": step, "preview": preview}
        ua_store.runs[run_id] = run
        return {"status": "awaiting_approval", "run_id": run_id, "preview": preview}
    def approve(self, run_id: str, owner_id: str) -> dict[str, Any]:
        run = ua_store.runs.get(run_id)
        if not run or run.owner_id != owner_id:
            return {"error": "not_found"}
        run.status = "running"
        run.result.pop("pending_approval", None)
        run.logs.append("Утверждено пользователем")
        ua_store.runs[run_id] = run
        return run.to_dict()
    def reject(self, run_id: str, owner_id: str) -> dict[str, Any]:
        run = ua_store.runs.get(run_id)
        if not run or run.owner_id != owner_id:
            return {"error": "not_found"}
        run.status = "cancelled"
        run.logs.append("Отклонено пользователем")
        ua_store.runs[run_id] = run
        return run.to_dict()

approval_engine = ApprovalEngine()
