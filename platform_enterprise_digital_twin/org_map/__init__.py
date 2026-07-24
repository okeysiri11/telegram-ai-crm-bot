"""Organization Map — Sprint 24.5."""

from __future__ import annotations

from typing import Any


class OrganizationMap:
    def render(self, *, twin: dict[str, Any]) -> dict[str, Any]:
        branches = list(twin.get("branches") or [])
        employees = list(twin.get("employees") or [])
        nodes = [{"id": twin.get("company_id"), "type": "company"}]
        links = []
        for b in branches:
            bid = b.get("branch_id") or b.get("name")
            nodes.append({"id": bid, "type": "branch", **b})
            links.append({"from": twin.get("company_id"), "to": bid, "relation": "has_branch"})
        teams: dict[str, list] = {}
        for e in employees:
            team = e.get("team") or e.get("department") or "general"
            teams.setdefault(team, []).append(e.get("employee_id") or e.get("name"))
            nodes.append({"id": e.get("employee_id") or e.get("name"), "type": "employee", "team": team})
            links.append({"from": e.get("branch_id") or twin.get("company_id"), "to": e.get("employee_id") or e.get("name"), "relation": "employs"})
        return {
            "company_id": twin.get("company_id"),
            "nodes": nodes,
            "links": links,
            "departments": list(teams.keys()),
            "teams": teams,
            "visual": True,
        }
