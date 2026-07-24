"""Multi-Agent Council — Sprint 24.0."""

from __future__ import annotations

from typing import Any


class MultiAgentCouncil:
    def deliberate(
        self,
        *,
        problem: str,
        agents: list[dict[str, Any]],
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if not problem or not str(problem).strip():
            raise ValueError("problem is required")
        if not agents:
            raise ValueError("at least one agent required")
        context = context or {}
        opinions = []
        for a in agents:
            role = a.get("role", "expert")
            stance = "support"
            # simple divergence for demo: security/legal more cautious on high risk
            if role in ("security", "legal") and context.get("risk_level") == "high":
                stance = "caution"
            elif role in ("marketing", "commerce") and context.get("growth_bias"):
                stance = "accelerate"
            opinions.append(
                {
                    "agent_id": a.get("agent_id"),
                    "role": role,
                    "stance": stance,
                    "summary": f"{role} view on: {problem[:80]}",
                    "confidence": 0.8 if stance == "support" else 0.7,
                }
            )
        return {
            "problem": problem.strip(),
            "participants": [a.get("agent_id") for a in agents],
            "opinions": opinions,
            "extensible": True,
        }
