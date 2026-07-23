"""Task management — registry, assignment, workflow, activity log."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.legal_enterprise.config import DEFAULT_CONFIG
from applications.legal_enterprise.shared.exceptions import NotFoundError, ValidationError
from applications.legal_enterprise.shared.store import LegalEnterpriseStore, legal_enterprise_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class TaskManagement:
    def __init__(self, store: LegalEnterpriseStore | None = None) -> None:
        self.store = store or legal_enterprise_store
        self.priorities = list(DEFAULT_CONFIG.cm_priorities)

    def create_task(
        self,
        *,
        case_id: str,
        title: str,
        assignee: str = "",
        priority: str = "medium",
        due_on: str = "",
    ) -> dict[str, Any]:
        if self.store.cm_cases.get(case_id) is None:
            raise NotFoundError("case", case_id)
        if not title:
            raise ValidationError("title required")
        pri = priority.lower().strip()
        if pri not in self.priorities:
            raise ValidationError(f"priority must be one of {self.priorities}")
        tid = _id("cm_task")
        task = self.store.cm_tasks.save(
            tid,
            {
                "task_id": tid,
                "case_id": case_id,
                "title": title,
                "assignee": assignee,
                "priority": pri,
                "due_on": due_on,
                "status": "open",
                "created_at": _now(),
            },
        )
        self.log_activity(case_id=case_id, action="task_created", detail=title)
        return task

    def assign(self, *, task_id: str, assignee: str) -> dict[str, Any]:
        task = self.store.cm_tasks.get(task_id)
        if task is None:
            raise NotFoundError("task", task_id)
        if not assignee:
            raise ValidationError("assignee required")
        task["assignee"] = assignee
        self.store.cm_tasks.save(task_id, task)
        self.log_activity(case_id=task["case_id"], action="task_assigned", detail=assignee)
        return task

    def set_priority(self, *, task_id: str, priority: str) -> dict[str, Any]:
        task = self.store.cm_tasks.get(task_id)
        if task is None:
            raise NotFoundError("task", task_id)
        pri = priority.lower().strip()
        if pri not in self.priorities:
            raise ValidationError(f"priority must be one of {self.priorities}")
        task["priority"] = pri
        self.store.cm_tasks.save(task_id, task)
        return task

    def automate_workflow(
        self, *, case_id: str, workflow: str, steps: list[str] | None = None
    ) -> dict[str, Any]:
        if self.store.cm_cases.get(case_id) is None:
            raise NotFoundError("case", case_id)
        if not workflow:
            raise ValidationError("workflow required")
        wid = _id("cm_wf")
        return self.store.cm_workflows.save(
            wid,
            {
                "workflow_id": wid,
                "case_id": case_id,
                "workflow": workflow,
                "steps": steps or ["intake", "review", "file", "monitor"],
                "status": "active",
                "at": _now(),
            },
        )

    def request_approval(
        self, *, case_id: str, item: str, requester: str, approver: str = ""
    ) -> dict[str, Any]:
        if self.store.cm_cases.get(case_id) is None:
            raise NotFoundError("case", case_id)
        if not item:
            raise ValidationError("item required")
        aid = _id("cm_apr")
        return self.store.cm_approvals.save(
            aid,
            {
                "approval_id": aid,
                "case_id": case_id,
                "item": item,
                "requester": requester or "system",
                "approver": approver,
                "status": "pending",
                "at": _now(),
            },
        )

    def log_activity(self, *, case_id: str, action: str, detail: str = "") -> dict[str, Any]:
        if self.store.cm_cases.get(case_id) is None:
            raise NotFoundError("case", case_id)
        if not action:
            raise ValidationError("action required")
        lid = _id("cm_act")
        return self.store.cm_activity.save(
            lid,
            {
                "activity_id": lid,
                "case_id": case_id,
                "action": action,
                "detail": detail,
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "tasks": self.store.cm_tasks.count(),
            "workflows": self.store.cm_workflows.count(),
            "approvals": self.store.cm_approvals.count(),
            "activity": self.store.cm_activity.count(),
        }
