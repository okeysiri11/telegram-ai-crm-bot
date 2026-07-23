"""Custom skill template."""

from __future__ import annotations

from typing import Any

from applications.enterprise_hub.ai_tools.skill_registry import SkillRegistry
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


class CustomSkill:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.skills = SkillRegistry(store or enterprise_hub_store)

    def register(self, *, name: str, steps: list[dict[str, Any]], description: str = "") -> dict[str, Any]:
        return self.skills.register(name=name, description=description, steps=steps, category="custom")
