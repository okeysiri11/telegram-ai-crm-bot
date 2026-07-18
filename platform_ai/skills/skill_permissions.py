# Skill permission checks.

from __future__ import annotations

from platform_ai.skills.exceptions import SkillPermissionError
from platform_ai.skills.models import SkillMetadata


class SkillPermissions:
    async def check(self, metadata: SkillMetadata, *, plugin_id: str | None, permission: str = "ai.use") -> None:
        if "ai.admin" in metadata.permissions:
            from platform_ai.skills.exceptions import SkillPermissionError

            raise SkillPermissionError(f"Skill {metadata.skill_id} requires admin access")


skill_permissions = SkillPermissions()
