"""Enterprise Operations Dashboard — Sprint 23.0."""

from __future__ import annotations

from typing import Any


class OperationsDashboard:
    def render(self, *, companies: list[dict[str, Any]] | None = None, services: dict[str, str] | None = None, releases: list[dict[str, Any]] | None = None, users: int = 0, ai_agents: int = 0) -> dict[str, Any]:
        companies = list(companies or [])
        services = dict(services or {})
        releases = list(releases or [])
        by_stage = {"onboarding": 0, "pilot": 0, "production": 0, "active": 0, "new_registrations": 0}
        for c in companies:
            stage = (c.get("stage") or "onboarding").lower()
            if stage in by_stage:
                by_stage[stage] += 1
            if c.get("status") == "Active" or stage in ("pilot", "production"):
                by_stage["active"] += 1
            if c.get("new_registration"):
                by_stage["new_registrations"] += 1
        return {
            "companies_total": len(companies),
            "active_companies": by_stage["active"],
            "new_registrations": by_stage["new_registrations"],
            "onboarding": by_stage["onboarding"],
            "pilot": by_stage["pilot"],
            "production": by_stage["production"],
            "users": int(users),
            "active_ai_agents": int(ai_agents),
            "service_status": services or {"hub": "ok", "api": "ok", "ai": "ok"},
            "latest_releases": releases[-5:],
            "stage": "pilot_release",
        }
