"""AI Guide for Builder Academy 2.0 — Sprint 28.6."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.platform_builder.academy_v2.catalogs import AI_GUIDE_FUNCTIONS
from applications.platform_builder.shared.store import PlatformBuilderStore, platform_builder_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:10]}"


class AIGuide:
    """Builder AI Guide — explain, recommend, answer, improve, warn."""

    def __init__(self, store: PlatformBuilderStore | None = None) -> None:
        self.store = store or platform_builder_store

    def explain_step(self, *, builder_id: str, step: str, level: str = "beginner") -> dict[str, Any]:
        detail = {
            "beginner": f"Let’s walk through «{step}» together. This step shapes how {builder_id} will work.",
            "intermediate": f"«{step}» configures a key part of {builder_id}. Keep defaults unless you have a clear need.",
            "advanced": f"Tune «{step}» for {builder_id}; skip fluff and focus on required fields.",
            "expert": f"{step}: configure required fields, then continue.",
        }
        return {
            "function": "Explain current step",
            "builder_id": builder_id,
            "step": step,
            "level": level,
            "message": detail.get(level, detail["beginner"]),
            "at": _now(),
        }

    def recommend_configuration(self, *, builder_id: str, draft: dict[str, Any] | None = None) -> dict[str, Any]:
        draft = draft or {}
        suggestions = []
        if not draft.get("modules"):
            suggestions.append("Add CRM and Knowledge Base modules for a strong first vertical.")
        if not draft.get("ai_team") and builder_id in ("vertical", "ai", "concierge"):
            suggestions.append("Connect at least one AI Specialist for day-one assistance.")
        if not draft.get("name"):
            suggestions.append("Set a clear builder name before create.")
        if not suggestions:
            suggestions.append("Configuration looks solid — run Live Analysis before create.")
        return {
            "function": "Recommend configuration",
            "builder_id": builder_id,
            "suggestions": suggestions,
            "at": _now(),
        }

    def answer(self, *, question: str, builder_id: str = "generic", step: str = "") -> dict[str, Any]:
        q = (question or "").strip().lower()
        if "module" in q:
            answer = "Modules are capability packs (CRM, ERP, Knowledge…). Pick what the business needs first."
        elif "concierge" in q:
            answer = "AI Concierge is the organization’s central intelligence — not an AI Agent. One per organization."
        elif "mistake" in q or "wrong" in q:
            answer = "Common mistake: creating without Knowledge or AI Team. Academy flags this in Live Analysis."
        elif "best" in q:
            answer = "Best practice: finish Contextual Help, accept recommendations, then create."
        else:
            answer = (
                f"For {builder_id}"
                + (f" · step «{step}»" if step else "")
                + ": use Contextual Help for Purpose / Example / Best Practice, then ask for recommendations."
            )
        record = {
            "answer_id": _id("guide_ans"),
            "question": question,
            "answer": answer,
            "builder_id": builder_id,
            "step": step,
            "at": _now(),
        }
        self.store.ai_guide_messages.save(record["answer_id"], record)
        return record

    def suggest_improvements(self, *, draft: dict[str, Any] | None = None) -> dict[str, Any]:
        draft = draft or {}
        ideas = []
        if len(draft.get("modules") or []) < 3:
            ideas.append("Add Analytics for visibility after go-live.")
        if not draft.get("dashboard_widgets"):
            ideas.append("Include KPI Overview and AI Team Status widgets.")
        if not draft.get("knowledge_topics"):
            ideas.append("Attach SOPs as Knowledge Sources.")
        if not ideas:
            ideas.append("Enable Daily Digest proactive assistance via Concierge.")
        return {"function": "Suggest improvements", "improvements": ideas, "at": _now()}

    def warn_missing(self, *, draft: dict[str, Any] | None = None) -> dict[str, Any]:
        draft = draft or {}
        missing = []
        for key, label in (
            ("name", "Name"),
            ("modules", "Modules"),
            ("ai_team", "AI Team"),
            ("knowledge_topics", "Knowledge Sources"),
        ):
            value = draft.get(key)
            if value is None or value == "" or value == []:
                missing.append(label)
        return {
            "function": "Warn about missing components",
            "missing": missing,
            "has_warnings": bool(missing),
            "message": (
                f"Missing: {', '.join(missing)}" if missing else "No critical components missing."
            ),
            "at": _now(),
        }

    def coach(
        self,
        *,
        builder_id: str,
        step: str,
        question: str | None = None,
        draft: dict[str, Any] | None = None,
        level: str = "beginner",
    ) -> dict[str, Any]:
        payload = {
            "guide_id": _id("aiguide"),
            "builder_id": builder_id,
            "step": step,
            "level": level,
            "functions": list(AI_GUIDE_FUNCTIONS),
            "explain": self.explain_step(builder_id=builder_id, step=step, level=level),
            "recommend": self.recommend_configuration(builder_id=builder_id, draft=draft),
            "improvements": self.suggest_improvements(draft=draft),
            "warnings": self.warn_missing(draft=draft),
            "ready": True,
            "at": _now(),
        }
        if question:
            payload["answer"] = self.answer(question=question, builder_id=builder_id, step=step)
        self.store.ai_guide_sessions.save(payload["guide_id"], payload)
        return payload

    def status(self) -> dict[str, Any]:
        return {
            "ready": True,
            "operational": True,
            "functions": list(AI_GUIDE_FUNCTIONS),
            "sessions": len(self.store.ai_guide_sessions.list_all()),
            "messages": len(self.store.ai_guide_messages.list_all()),
        }
