"""Pilot Control Center — Sprint 23.0."""

from __future__ import annotations

from typing import Any


class PilotControlCenter:
    def profile(self, *, company_id: str, readiness_pct: float = 0.0, staff_trained: bool = False, daily_users: int = 0, feedback: list[str] | None = None, issues: list[str] | None = None, improvements: list[str] | None = None, rollout_status: str = "pilot") -> dict[str, Any]:
        if not company_id:
            raise ValueError("company_id is required")
        readiness = max(0.0, min(100.0, float(readiness_pct)))
        return {
            "company_id": company_id,
            "rollout_status": rollout_status,
            "readiness_pct": readiness,
            "staff_trained": bool(staff_trained),
            "daily_users": int(daily_users),
            "latest_feedback": list(feedback or []),
            "issues": list(issues or []),
            "improvements_done": list(improvements or []),
            "pilot": True,
        }
