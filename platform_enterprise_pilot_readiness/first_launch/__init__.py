"""First Launch Experience — Sprint 23.1."""

from __future__ import annotations

from typing import Any


class FirstLaunchExperience:
    def tour(self, *, user_id: str, role: str = "admin") -> dict[str, Any]:
        if not user_id:
            raise ValueError("user_id is required")
        return {
            "user_id": user_id,
            "role": role,
            "interactive_tour": True,
            "hints": ["book_client", "open_pos", "check_dashboard"],
            "feature_explanations": {
                "booking": "Schedule visits in under a minute",
                "commerce": "Sell services and products at the desk",
                "ai_advisor": "AI recommends — you decide",
            },
            "ai_recommendations": ["complete_profile", "invite_staff", "import_clients"],
            "ai_may_act": False,
        }
