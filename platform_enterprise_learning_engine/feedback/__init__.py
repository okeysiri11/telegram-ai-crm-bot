"""Feedback Intelligence — Sprint 24.8."""

from __future__ import annotations

from typing import Any

from platform_enterprise_learning_engine.models import FEEDBACK_CLASSES


class FeedbackIntelligence:
    KEYWORDS = {
        "suggestion": ("suggest", "propose", "idea"),
        "error": ("error", "bug", "fail"),
        "ux_issue": ("ux", "confusing", "hard to use"),
        "wish": ("wish", "want", "hope"),
        "new_feature": ("feature", "add", "new"),
        "complaint": ("complaint", "angry", "bad"),
        "success_case": ("success", "worked", "great"),
        "refusal_reason": ("refuse", "cancel", "decline"),
    }

    def classify(self, *, text: str) -> dict[str, Any]:
        lower = (text or "").lower()
        matched = "suggestion"
        for cls, keys in self.KEYWORDS.items():
            if any(k in lower for k in keys):
                matched = cls
                break
        return {
            "text": text,
            "class": matched,
            "classes": list(FEEDBACK_CLASSES),
            "auto_classified": True,
        }
