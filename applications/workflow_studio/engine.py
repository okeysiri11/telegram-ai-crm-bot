"""Flow Engine — visual/background execution, debugger, retries, rollback (Sprint 12.2)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.workflow_studio.editor import VisualEditor, visual_editor
from applications.workflow_studio.shared.exceptions import NotFoundError, ValidationError
from applications.workflow_studio.shared.store import WorkflowStudioStore, workflow_studio_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class FlowEngine:
    def __init__(self, store: WorkflowStudioStore | None = None, editor: VisualEditor | None = None) -> None:
        self.store = store or workflow_studio_store
        self.editor = editor or visual_editor

    def execute(
        self,
        workflow_id: str,
        *,
        mode: str = "visual",
        input_data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if mode not in {"visual", "background", "step"}:
            raise ValidationError("mode must be visual|background|step")
        wf = self.editor.get_workflow(workflow_id)
        eid = f"exec_{uuid.uuid4().hex[:12]}"
        node_ids = list(wf.get("node_ids") or [])
        timeline: list[dict[str, Any]] = []
        errors: list[dict[str, Any]] = []
        for idx, nid in enumerate(node_ids):
            node = self.store.nodes.get(nid)
            if not node:
                continue
            bp = self.store.breakpoints.get(f"{workflow_id}:{nid}")
            if bp and bp.get("enabled") and mode == "step":
                timeline.append({"step": idx, "node_id": nid, "status": "paused_breakpoint", "at": _now()})
                break
            try:
                result = self._run_node(node, input_data or {})
                timeline.append({"step": idx, "node_id": nid, "node_type": node["node_type"], "status": "ok", "result": result, "at": _now()})
                self._log(eid, f"node {nid} ok")
            except Exception as exc:  # noqa: BLE001 — capture step errors into timeline
                err = {"step": idx, "node_id": nid, "error": str(exc), "at": _now()}
                errors.append(err)
                timeline.append({**err, "status": "error"})
                self._log(eid, f"node {nid} error: {exc}")
                if not (node.get("properties") or {}).get("retry"):
                    break
                # retry once
                try:
                    result = self._run_node(node, input_data or {})
                    timeline.append({"step": idx, "node_id": nid, "status": "retry_ok", "result": result, "at": _now()})
                    errors.pop()
                except Exception as retry_exc:  # noqa: BLE001
                    timeline.append({"step": idx, "node_id": nid, "status": "retry_failed", "error": str(retry_exc), "at": _now()})
                    break

        status = "failed" if errors else "completed"
        if timeline and timeline[-1].get("status") == "paused_breakpoint":
            status = "paused"
        execution = {
            "execution_id": eid,
            "workflow_id": workflow_id,
            "mode": mode,
            "status": status,
            "timeline": timeline,
            "errors": errors,
            "input": dict(input_data or {}),
            "started_at": _now(),
            "finished_at": _now(),
        }
        self.store.executions.save(eid, execution)
        return execution

    def _run_node(self, node: dict[str, Any], data: dict[str, Any]) -> dict[str, Any]:
        ntype = node.get("node_type")
        if ntype == "condition":
            expr = (node.get("properties") or {}).get("expression", True)
            return {"branch": bool(expr)}
        if ntype == "delay":
            return {"delayed_ms": int((node.get("properties") or {}).get("ms", 0))}
        if ntype in {"llm", "ai_agent", "reasoning", "planning", "decision"}:
            return {"assistant": True, "summary": f"{ntype} processed", "echo": data.get("prompt", "")}
        if ntype == "notification":
            return {"notified": True, "channel": (node.get("properties") or {}).get("channel", "email")}
        if (node.get("properties") or {}).get("force_error"):
            raise RuntimeError("forced node error")
        return {"ok": True, "node_type": ntype}

    def set_breakpoint(self, workflow_id: str, *, node_id: str, enabled: bool = True) -> dict[str, Any]:
        self.editor.get_workflow(workflow_id)
        key = f"{workflow_id}:{node_id}"
        bp = {"breakpoint_id": key, "workflow_id": workflow_id, "node_id": node_id, "enabled": enabled, "at": _now()}
        self.store.breakpoints.save(key, bp)
        return bp

    def live_logs(self, execution_id: str) -> list[dict[str, Any]]:
        return [log for log in self.store.logs.list_all() if log.get("execution_id") == execution_id]

    def get_execution(self, execution_id: str) -> dict[str, Any]:
        item = self.store.executions.get(execution_id)
        if item is None:
            raise NotFoundError("execution", execution_id)
        return item

    def retry(self, execution_id: str) -> dict[str, Any]:
        prev = self.get_execution(execution_id)
        return self.execute(prev["workflow_id"], mode=prev.get("mode", "background"), input_data=prev.get("input"))

    def rollback_execution(self, execution_id: str) -> dict[str, Any]:
        prev = self.get_execution(execution_id)
        prev["status"] = "rolled_back"
        prev["rolled_back_at"] = _now()
        self.store.executions.save(execution_id, prev)
        self._log(execution_id, "execution rolled back")
        return prev

    def debugger_state(self, execution_id: str) -> dict[str, Any]:
        exe = self.get_execution(execution_id)
        return {
            "execution_id": execution_id,
            "status": exe["status"],
            "timeline": exe.get("timeline", []),
            "breakpoints": [b for b in self.store.breakpoints.list_all() if b.get("workflow_id") == exe["workflow_id"]],
            "logs": self.live_logs(execution_id),
        }

    def _log(self, execution_id: str, message: str) -> None:
        lid = f"log_{uuid.uuid4().hex[:10]}"
        self.store.logs.save(lid, {"log_id": lid, "execution_id": execution_id, "message": message, "at": _now()})

    def status(self) -> dict[str, Any]:
        return {
            "flow_engine": "1.0",
            "executions": len(self.store.executions.list_all()),
            "ready": True,
        }


flow_engine = FlowEngine()
