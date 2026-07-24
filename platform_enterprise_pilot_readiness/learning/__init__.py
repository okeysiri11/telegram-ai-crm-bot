"""AI Learning Assistant — Sprint 23.1."""

from __future__ import annotations

from typing import Any


class AILearningAssistant:
    def observe(self, *, user_id: str, action: str, repeat_count: int = 1) -> dict[str, Any]:
        if not user_id or not action:
            raise ValueError("user_id and action are required")
        repeat_count = int(repeat_count)
        offer_training = repeat_count >= 3
        tip = None
        if offer_training:
            tip = f"You already searched for {action} {repeat_count} times. Want a faster way?"
        return {
            "user_id": user_id,
            "action": action,
            "repeat_count": repeat_count,
            "difficulty_detected": offer_training,
            "training_offer": tip,
            "ai_may_act": False,
            "proposes_only": True,
        }
