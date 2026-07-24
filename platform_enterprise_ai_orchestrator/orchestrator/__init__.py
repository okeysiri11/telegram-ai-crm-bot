"""AI Orchestrator — Sprint 24.0."""

from __future__ import annotations

from typing import Any


class AIOrchestrator:
    def select_agents(self, *, registry_agents: list[dict[str, Any]], required_roles: list[str] | None = None) -> list[dict[str, Any]]:
        active = [a for a in registry_agents if a.get("status") == "active"]
        if required_roles:
            roles = {r.lower() for r in required_roles}
            selected = [a for a in active if a.get("role") in roles]
            if selected:
                return selected
        return active

    def run(
        self,
        *,
        problem: str,
        agents: list[dict[str, Any]],
        council_result: dict[str, Any],
    ) -> dict[str, Any]:
        opinions = list(council_result.get("opinions") or [])
        stances = {o["stance"] for o in opinions}
        contradictions = []
        if len(stances) > 1:
            contradictions.append(
                {
                    "type": "stance_divergence",
                    "stances": sorted(stances),
                    "agents": [{"agent_id": o["agent_id"], "stance": o["stance"]} for o in opinions],
                }
            )
        agreement = [o for o in opinions if o["stance"] == "support"]
        disagreement = [o for o in opinions if o["stance"] != "support"]
        conclusion = {
            "summary": f"Council reviewed: {problem[:120]}",
            "recommended": "proceed_with_controls" if contradictions else "proceed",
            "requires_owner": True,
        }
        return {
            "problem": problem,
            "agents_selected": [a.get("agent_id") for a in agents],
            "discussion": opinions,
            "aggregated": {
                "agreement_count": len(agreement),
                "disagreement_count": len(disagreement),
            },
            "contradictions": contradictions,
            "conclusion": conclusion,
            "ai_may_act": False,
        }
