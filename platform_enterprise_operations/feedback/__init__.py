"""Feedback Intelligence — Sprint 23.0."""

from __future__ import annotations

from typing import Any

from platform_enterprise_operations.models import FEEDBACK_ROLES


class FeedbackIntelligence:
    def collect(self, *, role: str, message: str, company_id: str = "", kind: str = "feedback") -> dict[str, Any]:
        role = (role or "").lower()
        if role not in FEEDBACK_ROLES:
            raise ValueError(f"unsupported role: {role}")
        if not message or not str(message).strip():
            raise ValueError("message is required")
        kind = (kind or "feedback").lower()
        if kind not in ("feedback", "suggestion", "error", "review"):
            kind = "feedback"
        return {
            "role": role,
            "company_id": company_id or None,
            "kind": kind,
            "message": str(message).strip(),
            "routed_to": "product_intelligence",
            "auto_forward": True,
        }
