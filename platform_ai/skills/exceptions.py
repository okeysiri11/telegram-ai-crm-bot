# AI Skills exceptions.

from __future__ import annotations


class SkillError(Exception):
    """Base skill error."""


class SkillNotFoundError(SkillError):
    def __init__(self, skill_id: str) -> None:
        super().__init__(f"Skill not found: {skill_id}")
        self.skill_id = skill_id


class SkillValidationError(SkillError):
    pass


class SkillExecutionError(SkillError):
    pass


class SkillPermissionError(SkillError):
    pass


class SkillDisabledError(SkillError):
    pass
