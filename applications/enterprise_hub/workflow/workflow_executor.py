"""Workflow executor — run blocks, conditions, actions, approvals."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.shared.exceptions import NotFoundError, ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store
from applications.enterprise_hub.workflow.actions import ActionRegistry
from applications.enterprise_hub.workflow.conditions import ConditionEngine


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class WorkflowExecutor:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.actions = ActionRegistry(self.store)
        self.conditions = ConditionEngine(self.store)

    def execute(
        self,
        *,
        workflow_id: str,
        executor: str = "system",
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        wf = self.store.wf_definitions.get(workflow_id)
        if wf is None:
            raise NotFoundError(f"workflow not found: {workflow_id}")
        if wf.get("status") not in ("published", "draft"):
            raise ValidationError("workflow not executable")
        ctx = context or {}
        logs: list[str] = []
        errors: list[str] = []
        action_ids: list[str] = []
        current_step = "start"
        started = _now()

        for block in wf.get("blocks") or []:
            btype = str(block.get("type", "")).lower()
            current_step = btype
            config = block.get("config") or {}
            logs.append(f"enter:{btype}")
            if btype == "decision":
                cond = self.conditions.check(
                    condition_type=config.get("condition_type", "status"),
                    expected=config.get("expected", ctx.get("status", "open")),
                    actual=ctx.get("status", config.get("expected", "open")),
                    context=ctx,
                )
                logs.append(f"decision:{cond['passed']}")
                if not cond["passed"]:
                    logs.append("branch:skip")
                    continue
            elif btype == "approval":
                mode = config.get("mode", "auto")
                appr = self._approval(workflow_id=workflow_id, mode=mode, approvers=config.get("approvers"))
                logs.append(f"approval:{appr['outcome']}")
                if appr["outcome"] != "approved":
                    errors.append("approval_rejected")
                    break
            elif btype == "ai_decision":
                cond = self.conditions.check(
                    condition_type="ai_decision",
                    expected="approve",
                    actual=ctx.get("ai_decision", "approve"),
                    context=ctx,
                )
                logs.append(f"ai_decision:{cond['passed']}")
            elif btype == "notification":
                act = self.actions.execute(
                    action_type=config.get("channel", "email"),
                    target=config.get("target", ctx.get("recipient", "")),
                    payload=config,
                )
                action_ids.append(act["action_id"])
            elif btype == "api_call":
                act = self.actions.execute(
                    action_type="api",
                    target=config.get("url", ""),
                    payload=config,
                )
                action_ids.append(act["action_id"])
            elif btype == "database_update":
                act = self.actions.execute(
                    action_type="sql",
                    target=config.get("table", ""),
                    payload=config,
                )
                action_ids.append(act["action_id"])
            elif btype == "delay":
                logs.append(f"delay:{config.get('seconds', 0)}")
            elif btype in ("start", "finish"):
                pass
            else:
                act = self.actions.execute(
                    action_type=config.get("action_type", "custom"),
                    target=config.get("target", ""),
                    payload=config,
                )
                action_ids.append(act["action_id"])

        result = "failed" if errors else "completed"
        eid = _id("wf_run")
        return self.store.wf_executions.save(
            eid,
            {
                "execution_id": eid,
                "workflow_id": workflow_id,
                "version": wf.get("version", 1),
                "trigger": wf.get("trigger", ""),
                "executor": executor,
                "current_step": current_step,
                "result": result,
                "duration_ms": 10.0,
                "logs": logs,
                "errors": errors,
                "action_ids": action_ids,
                "started_at": started,
                "at": _now(),
            },
        )

    def _approval(
        self, *, workflow_id: str, mode: str = "auto", approvers: list[str] | None = None
    ) -> dict[str, Any]:
        from applications.enterprise_hub.workflow.models import APPROVAL_MODES

        m = mode.lower().strip()
        if m not in APPROVAL_MODES:
            m = "auto"
        outcome = "approved"
        if m == "auto" or m == "ai":
            outcome = "approved"
        elif approvers:
            outcome = "approved"
        aid = _id("wf_appr")
        return self.store.wf_approvals.save(
            aid,
            {
                "approval_id": aid,
                "workflow_id": workflow_id,
                "mode": m,
                "approvers": approvers or [],
                "outcome": outcome,
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "executions": self.store.wf_executions.count(),
            "approvals": self.store.wf_approvals.count(),
            "actions": self.actions.status(),
            "conditions": self.conditions.status(),
        }
