"""Goal manager — strategic goals, priorities, deadlines, dependencies."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.ai_os.models import GOAL_KINDS, PRIORITIES
from applications.enterprise_hub.shared.exceptions import NotFoundError, ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class GoalManager:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def create(
        self,
        *,
        title: str,
        kind: str = "operational",
        priority: str = "normal",
        deadline: str | None = None,
        depends_on: list[str] | None = None,
    ) -> dict[str, Any]:
        if not title or not str(title).strip():
            raise ValidationError("title is required")
        k = kind.lower().strip()
        if k not in GOAL_KINDS:
            raise ValidationError(f"kind must be one of {list(GOAL_KINDS)}")
        pr = priority.lower().strip()
        if pr not in PRIORITIES:
            raise ValidationError(f"priority must be one of {list(PRIORITIES)}")
        gid = _id("aios_goal")
        return self.store.aios_goals.save(
            gid,
            {
                "goal_id": gid,
                "title": title.strip(),
                "kind": k,
                "priority": pr,
                "deadline": deadline,
                "depends_on": depends_on or [],
                "status": "active",
                "created_at": _now(),
            },
        )

    def get(self, goal_id: str) -> dict[str, Any]:
        item = self.store.aios_goals.get(goal_id)
        if not item:
            raise NotFoundError(f"goal not found: {goal_id}")
        return item

    def status(self) -> dict[str, Any]:
        return {"goals": self.store.aios_goals.count(), "kinds": list(GOAL_KINDS)}
