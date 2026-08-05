# Skill permission checks.

from __future__ import annotations

from platform_ai.skills.exceptions import SkillPermissionError
from platform_ai.skills.models import SkillMetadata


class SkillPermissions:
    async def check(self, metadata: SkillMetadata, *, plugin_id: str | None, permission: str = "ai.use") -> None:
        """Enforce skill permission metadata.

        Skills declaring elevated scopes (`ai.admin`, `*`) require a caller
        plugin identity. Previously any `ai.admin` skill was unconditionally
        denied (inverted check) — Sprint 37.2.
        """
        required = list(metadata.permissions or []) or [permission]
        elevated = any(p in {"ai.admin", "*", "management.admin"} for p in required)
        if elevated and not plugin_id:
            raise SkillPermissionError(
                f"Skill {metadata.skill_id} requires authenticated admin/plugin access"
            )


skill_permissions = SkillPermissions()
