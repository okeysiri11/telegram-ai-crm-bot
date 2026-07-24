"""Learning Score — Sprint 24.8."""

from __future__ import annotations

from typing import Any


class LearningScore:
    def score(
        self,
        *,
        agent_id: str,
        accuracy: float = 0.7,
        usefulness: float = 0.7,
        accepted_advice_pct: float = 0.5,
        successful_implementations_pct: float = 0.5,
        user_trust: float = 0.6,
    ) -> dict[str, Any]:
        if not agent_id:
            raise ValueError("agent_id is required")
        overall = round(
            float(accuracy) * 0.25
            + float(usefulness) * 0.2
            + float(accepted_advice_pct) * 0.2
            + float(successful_implementations_pct) * 0.2
            + float(user_trust) * 0.15,
            3,
        )
        return {
            "agent_id": agent_id,
            "accuracy": float(accuracy),
            "usefulness": float(usefulness),
            "accepted_advice_pct": float(accepted_advice_pct),
            "successful_implementations_pct": float(successful_implementations_pct),
            "user_trust": float(user_trust),
            "overall": overall,
        }
