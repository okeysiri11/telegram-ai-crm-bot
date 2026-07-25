"""Builder Academy 2.0 engine — Sprint 28.6."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.platform_builder.academy_v2.ai_guide import AIGuide
from applications.platform_builder.academy_v2.analysis import analyze_builder, business_impact
from applications.platform_builder.academy_v2.catalogs import (
    EXPERIENCE_LEVELS,
    LEARNING_PATH,
    WIZARD_STEPS,
    contextual_help_for,
    full_catalog,
)
from applications.platform_builder.academy_v2.progress import AcademyProgress
from applications.platform_builder.academy_v2.recommendations import RecommendationEngine
from applications.platform_builder.shared.exceptions import NotFoundError, ValidationError
from applications.platform_builder.shared.store import PlatformBuilderStore, platform_builder_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:10]}"


class AcademyV2:
    """Next-generation Builder Academy with AI Guide and adaptive learning."""

    def __init__(self, store: PlatformBuilderStore | None = None) -> None:
        self.store = store or platform_builder_store
        self.guide = AIGuide(self.store)
        self.recommendations = RecommendationEngine(self.store)
        self.progress = AcademyProgress(self.store)

    def catalog(self) -> dict[str, Any]:
        return {
            "ready": True,
            "version": "2.0.0",
            "sprint": "28.6",
            "operational": True,
            "ai_guide_ready": True,
            "interactive_learning_ready": True,
            "recommendation_engine_ready": True,
            "progress_tracking_ready": True,
            **full_catalog(),
        }

    def adapt_behavior(self, level: str) -> dict[str, Any]:
        match = next((l for l in EXPERIENCE_LEVELS if l["id"] == level), EXPERIENCE_LEVELS[0])
        return {
            "level": match["id"],
            "name": match["name"],
            "description": match["description"],
            "adaptations": dict(match["adaptations"]),
            "builder_behavior": {
                "help_density": "full"
                if match["adaptations"]["show_best_practices"]
                else ("minimal" if match["id"] == "expert" else "balanced"),
                "coach_visible": match["id"] != "expert",
                "auto_recommendations": match["adaptations"]["auto_recommend"],
            },
        }

    def contextual_help(self, field: str, builder_id: str = "generic") -> dict[str, Any]:
        return contextual_help_for(field, builder_id)

    def interactive_learning(self, user_id: str = "owner") -> dict[str, Any]:
        snap = self.progress.snapshot(user_id)
        return {
            "tips": [
                "Use Contextual Help on every field before skipping ahead.",
                "Ask the AI Guide when a step feels unclear.",
                "Apply at least one Smart Recommendation before create.",
            ],
            "walkthroughs": [
                {"id": "first_run", "title": "First Academy Walkthrough", "steps": 5},
                {"id": "ai_coach", "title": "Meet the AI Guide", "steps": 3},
            ],
            "progress": snap,
            "achievements": snap.get("achievement_cards") or [],
            "learning_path": list(LEARNING_PATH),
            "elements": ["Tips", "Walkthroughs", "Progress", "Achievements", "Learning Path"],
        }

    def live_analysis(self, draft: dict[str, Any] | None = None, builder_id: str = "generic") -> dict[str, Any]:
        return analyze_builder(draft, builder_id=builder_id)

    def impact(self, option_id: str, option_name: str | None = None) -> dict[str, Any]:
        return business_impact(option_id, option_name)

    def start_session(self, *, user_id: str = "owner") -> dict[str, Any]:
        sid = _id("acadv2")
        progress = self.progress.get_or_create(user_id)
        record = {
            "session_id": sid,
            "user_id": user_id,
            "status": "in_progress",
            "step": 1,
            "draft": {
                "experience_level": progress.get("experience_level") or "beginner",
                "builder_id": "vertical",
                "field": "modules",
                "industry": "medical",
                "question": "",
                "draft_snapshot": {
                    "name": "Demo Clinic",
                    "modules": ["crm", "knowledge_base"],
                    "ai_mode": "connect_existing",
                    "knowledge_topics": [],
                    "dashboard_widgets": ["kpi_overview"],
                },
                "completed_lessons": list(progress.get("completed_lessons") or []),
                "enable_ai_guide": True,
                "enable_recommendations": True,
            },
            "created_at": _now(),
            "updated_at": _now(),
        }
        self.store.academy_v2_sessions.save(sid, record)
        return record

    def get_session(self, session_id: str) -> dict[str, Any]:
        session = self.store.academy_v2_sessions.get(session_id)
        if not session:
            raise NotFoundError(f"Academy 2.0 session not found: {session_id}")
        return session

    def update_session(self, session_id: str, patch: dict[str, Any]) -> dict[str, Any]:
        session = self.get_session(session_id)
        if "step" in patch:
            step = int(patch["step"])
            if step < 1 or step > 10:
                raise ValidationError("step must be between 1 and 10")
            session["step"] = step
        if "draft" in patch and isinstance(patch["draft"], dict):
            session["draft"] = {**session["draft"], **patch["draft"]}
            if "experience_level" in patch["draft"]:
                self.progress.set_level(session["user_id"], patch["draft"]["experience_level"])
        session["updated_at"] = _now()
        self.store.academy_v2_sessions.save(session_id, session)
        return session

    def summary(self, session_id: str) -> dict[str, Any]:
        session = self.get_session(session_id)
        draft = session["draft"]
        level = draft.get("experience_level") or "beginner"
        snap = self.progress.snapshot(session["user_id"])
        recs = self.recommendations.recommend(
            builder_id=draft.get("builder_id") or "vertical",
            industry=draft.get("industry"),
        )
        analysis = self.live_analysis(draft.get("draft_snapshot") or {}, draft.get("builder_id") or "vertical")
        return {
            "session_id": session_id,
            "title": "Academy 2.0 Summary",
            "configuration": {
                "experience_level": level,
                "adaptations": self.adapt_behavior(level),
                "builder_id": draft.get("builder_id"),
                "ai_guide": draft.get("enable_ai_guide", True),
                "recommendations": draft.get("enable_recommendations", True),
            },
            "recommendations": recs,
            "learning_progress": snap,
            "business_readiness": {
                "score": analysis["readiness_score"],
                "ready": analysis["ready"],
                "missing": analysis["missing_components"],
            },
            "analysis": analysis,
        }

    def create(self, session_id: str) -> dict[str, Any]:
        session = self.get_session(session_id)
        draft = session["draft"]
        user_id = session["user_id"]
        level = draft.get("experience_level") or "beginner"
        self.progress.set_level(user_id, level)

        for lesson in draft.get("completed_lessons") or ["intro", "help", "guide"]:
            self.progress.complete_lesson(user_id, lesson)
        self.progress.complete_builder(user_id, draft.get("builder_id") or "academy_v2")
        self.progress.unlock_achievement(user_id, "guided_learner")
        if draft.get("enable_ai_guide"):
            self.progress.unlock_achievement(user_id, "ai_coach_user")

        analysis = self.live_analysis(draft.get("draft_snapshot") or {}, draft.get("builder_id") or "vertical")
        if analysis["readiness_score"] >= 80:
            self.progress.unlock_achievement(user_id, "business_ready")
        if analysis.get("optimization_ideas"):
            self.progress.unlock_achievement(user_id, "optimizer")

        recs = self.recommendations.recommend(
            builder_id=draft.get("builder_id") or "vertical",
            industry=draft.get("industry"),
        )
        learning_state = self.progress.register_state(
            user_id,
            {
                "experience_level": level,
                "completed_lessons": draft.get("completed_lessons") or [],
                "completed_builders": [draft.get("builder_id") or "academy_v2"],
            },
        )

        session["status"] = "created"
        session["updated_at"] = _now()
        self.store.academy_v2_sessions.save(session_id, session)

        return {
            "ok": True,
            "session_id": session_id,
            "progress": self.progress.snapshot(user_id),
            "recommendations": recs,
            "learning_state": learning_state,
            "analysis": analysis,
            "adaptations": self.adapt_behavior(level),
            "message": "Academy progress, recommendations, and learning state registered.",
        }

    def status(self) -> dict[str, Any]:
        return {
            "ready": True,
            "operational": True,
            "version": "2.0.0",
            "wizard_steps": len(WIZARD_STEPS),
            "experience_levels": [l["id"] for l in EXPERIENCE_LEVELS],
            "ai_guide": self.guide.status(),
            "recommendations": self.recommendations.status(),
            "sessions": len(self.store.academy_v2_sessions.list_all()),
            "progress_records": len(self.store.academy_progress.list_all()),
        }
