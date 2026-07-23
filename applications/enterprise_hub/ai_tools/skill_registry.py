"""Skill registry — composite tool chains."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.ai_tools.models import SKILL_STATUSES
from applications.enterprise_hub.shared.exceptions import NotFoundError, ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class SkillRegistry:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def register(
        self,
        *,
        name: str,
        description: str = "",
        steps: list[dict[str, Any]] | None = None,
        category: str = "general",
    ) -> dict[str, Any]:
        if not name or not str(name).strip():
            raise ValidationError("name is required")
        if not steps:
            raise ValidationError("steps are required")
        sid = _id("ats_skl")
        return self.store.ats_skills.save(
            sid,
            {
                "skill_id": sid,
                "name": name.strip(),
                "description": description,
                "category": category,
                "steps": steps,
                "status": "active",
                "rating": 5.0,
                "usage_count": 0,
                "registered_at": _now(),
            },
        )

    def get(self, skill_id: str) -> dict[str, Any]:
        item = self.store.ats_skills.get(skill_id)
        if not item:
            raise NotFoundError(f"skill not found: {skill_id}")
        return item

    def set_status(self, *, skill_id: str, status: str) -> dict[str, Any]:
        skill = self.get(skill_id)
        st = status.lower().strip()
        if st not in SKILL_STATUSES:
            raise ValidationError(f"status must be one of {list(SKILL_STATUSES)}")
        skill["status"] = st
        return self.store.ats_skills.save(skill_id, skill)

    def status(self) -> dict[str, Any]:
        return {"skills": self.store.ats_skills.count()}
