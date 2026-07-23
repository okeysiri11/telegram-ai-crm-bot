"""Objective manager — break goals into measurable objectives."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.ai_os.goal_manager import GoalManager
from applications.enterprise_hub.shared.exceptions import ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class ObjectiveManager:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.goals = GoalManager(self.store)

    def create(
        self,
        *,
        goal_id: str,
        title: str,
        success_metric: str = "completed",
        assignee: str = "system",
    ) -> dict[str, Any]:
        self.goals.get(goal_id)
        if not title:
            raise ValidationError("title is required")
        oid = _id("aios_obj")
        return self.store.aios_objectives.save(
            oid,
            {
                "objective_id": oid,
                "goal_id": goal_id,
                "title": title.strip(),
                "success_metric": success_metric,
                "assignee": assignee,
                "status": "open",
                "created_at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"objectives": self.store.aios_objectives.count()}
