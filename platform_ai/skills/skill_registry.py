# Skill registry — dynamic registration with versioning, categories, tags.

from __future__ import annotations

import logging
from typing import Type

from platform_ai.skills.exceptions import SkillNotFoundError
from platform_ai.skills.models import SkillRecord, SkillState
from platform_ai.skills.skill_base import AISkill

logger = logging.getLogger(__name__)


class SkillRegistry:
    def __init__(self) -> None:
        self._skills: dict[str, Type[AISkill]] = {}
        self._records: dict[str, SkillRecord] = {}
        self._versions: dict[str, list[str]] = {}

    def reset(self) -> None:
        self._skills.clear()
        self._records.clear()
        self._versions.clear()

    def register(self, skill_cls: Type[AISkill]) -> SkillRecord:
        meta = skill_cls.metadata()
        skill_id = meta.skill_id
        if not skill_id:
            raise ValueError(f"Skill class {skill_cls.__name__} missing skill_id")

        self._skills[skill_id] = skill_cls
        record = SkillRecord(metadata=meta, state=SkillState.REGISTERED)
        self._records[skill_id] = record

        versions = self._versions.setdefault(skill_id, [])
        if meta.version not in versions:
            versions.append(meta.version)

        logger.info("skill_registered id=%s version=%s", skill_id, meta.version)
        return record

    def get_class(self, skill_id: str) -> Type[AISkill]:
        if skill_id not in self._skills:
            raise SkillNotFoundError(skill_id)
        return self._skills[skill_id]

    def get_record(self, skill_id: str) -> SkillRecord:
        if skill_id not in self._records:
            raise SkillNotFoundError(skill_id)
        return self._records[skill_id]

    def list_records(self) -> list[SkillRecord]:
        return list(self._records.values())

    def list_by_category(self, category: str) -> list[SkillRecord]:
        return [r for r in self._records.values() if r.metadata.category == category]

    def list_by_tag(self, tag: str) -> list[SkillRecord]:
        return [r for r in self._records.values() if tag in r.metadata.tags]

    def set_state(self, skill_id: str, state: SkillState, *, error: str | None = None) -> None:
        record = self.get_record(skill_id)
        record.state = state
        record.last_error = error

    def unregister(self, skill_id: str) -> None:
        self._skills.pop(skill_id, None)
        self._records.pop(skill_id, None)

    def versions(self, skill_id: str) -> list[str]:
        return list(self._versions.get(skill_id, []))

    def summary(self) -> dict:
        by_category: dict[str, int] = {}
        for r in self._records.values():
            by_category[r.metadata.category] = by_category.get(r.metadata.category, 0) + 1
        return {
            "total": len(self._records),
            "by_category": by_category,
            "skills": [r.to_dict() for r in self._records.values()],
        }


skill_registry = SkillRegistry()
