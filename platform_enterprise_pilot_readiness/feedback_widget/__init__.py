"""Pilot Feedback Widget — Sprint 23.1."""

from __future__ import annotations

from typing import Any

from platform_enterprise_pilot_readiness.models import FEEDBACK_KINDS


class PilotFeedbackWidget:
    def submit(
        self,
        *,
        kind: str,
        message: str,
        rating: float | None = None,
        screenshot: str | None = None,
        feature: str = "",
        user_id: str = "",
    ) -> dict[str, Any]:
        kind = (kind or "").lower()
        if kind not in FEEDBACK_KINDS:
            raise ValueError(f"unsupported kind: {kind}")
        if not message or not str(message).strip():
            raise ValueError("message is required")
        return {
            "kind": kind,
            "message": str(message).strip(),
            "rating": float(rating) if rating is not None else None,
            "screenshot": screenshot,
            "feature": feature or None,
            "user_id": user_id or None,
            "cta": "Предложить улучшение",
            "routed_to": "product_intelligence",
            "auto_forward": True,
        }
