"""Academy progress & learning state — Sprint 28.6."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.platform_builder.academy_v2.catalogs import ACHIEVEMENTS, LEARNING_PATH
from applications.platform_builder.shared.store import PlatformBuilderStore, platform_builder_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:10]}"


LEVEL_ORDER = ("beginner", "intermediate", "advanced", "expert")


class AcademyProgress:
    def __init__(self, store: PlatformBuilderStore | None = None) -> None:
        self.store = store or platform_builder_store

    def get_or_create(self, user_id: str = "owner") -> dict[str, Any]:
        existing = self.store.academy_progress.get(user_id)
        if existing:
            return existing
        record = {
            "user_id": user_id,
            "experience_level": "beginner",
            "completed_builders": [],
            "completed_lessons": [],
            "unlocked_features": ["contextual_help", "ai_guide"],
            "achievements": [],
            "xp": 0,
            "learning_path": list(LEARNING_PATH),
            "updated_at": _now(),
            "sprint": "28.6",
        }
        self.store.academy_progress.save(user_id, record)
        return record

    def set_level(self, user_id: str, level: str) -> dict[str, Any]:
        record = self.get_or_create(user_id)
        if level not in LEVEL_ORDER:
            level = "beginner"
        record["experience_level"] = level
        record["updated_at"] = _now()
        if level in ("advanced", "expert") and "compact_ui" not in record["unlocked_features"]:
            record["unlocked_features"].append("compact_ui")
        self.store.academy_progress.save(user_id, record)
        return record

    def complete_lesson(self, user_id: str, lesson_id: str) -> dict[str, Any]:
        record = self.get_or_create(user_id)
        if lesson_id not in record["completed_lessons"]:
            record["completed_lessons"].append(lesson_id)
            record["xp"] += 10
        if "guided_learner" not in record["achievements"] and len(record["completed_lessons"]) >= 3:
            record["achievements"].append("guided_learner")
        record["updated_at"] = _now()
        self.store.academy_progress.save(user_id, record)
        return record

    def complete_builder(self, user_id: str, builder_id: str) -> dict[str, Any]:
        record = self.get_or_create(user_id)
        if builder_id not in record["completed_builders"]:
            record["completed_builders"].append(builder_id)
            record["xp"] += 25
        if "first_builder" not in record["achievements"]:
            record["achievements"].append("first_builder")
        if record["xp"] >= 50 and "live_analysis" not in record["unlocked_features"]:
            record["unlocked_features"].append("live_analysis")
        # auto level-up
        if record["xp"] >= 100:
            record["experience_level"] = "advanced"
        elif record["xp"] >= 40:
            record["experience_level"] = "intermediate"
        record["updated_at"] = _now()
        self.store.academy_progress.save(user_id, record)
        return record

    def unlock_achievement(self, user_id: str, achievement_id: str) -> dict[str, Any]:
        record = self.get_or_create(user_id)
        if achievement_id not in record["achievements"]:
            record["achievements"].append(achievement_id)
            record["xp"] += 15
        record["updated_at"] = _now()
        self.store.academy_progress.save(user_id, record)
        return record

    def snapshot(self, user_id: str = "owner") -> dict[str, Any]:
        record = self.get_or_create(user_id)
        unlocked_achievements = [
            a for a in ACHIEVEMENTS if a["id"] in record.get("achievements", [])
        ]
        return {
            **record,
            "achievement_cards": unlocked_achievements,
            "available_achievements": list(ACHIEVEMENTS),
            "progress_pct": min(100, int(record.get("xp", 0))),
        }

    def register_state(self, user_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        record = self.get_or_create(user_id)
        if payload.get("experience_level"):
            record = self.set_level(user_id, payload["experience_level"])
        for lesson in payload.get("completed_lessons") or []:
            record = self.complete_lesson(user_id, lesson)
        for builder in payload.get("completed_builders") or []:
            record = self.complete_builder(user_id, builder)
        for ach in payload.get("achievements") or []:
            record = self.unlock_achievement(user_id, ach)
        rid = _id("alearn")
        state = {
            "learning_state_id": rid,
            "user_id": user_id,
            "progress": self.snapshot(user_id),
            "registered_at": _now(),
            "source": "academy_v2",
        }
        self.store.academy_learning_states.save(rid, state)
        return state
