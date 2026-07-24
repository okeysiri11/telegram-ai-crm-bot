"""AI Safety guards — Sprint 24.8."""

from __future__ import annotations

from typing import Any

from platform_enterprise_learning_engine.models import AI_SAFETY


class AISafety:
    def enforce(self, *, intent: str) -> dict[str, Any]:
        intent = (intent or "").lower()
        blocked = {
            "modify_algorithms": "no_self_modify_algorithms",
            "delete_knowledge": "no_delete_knowledge",
            "spread_unconfirmed": "no_spread_unconfirmed",
            "learn_unconfirmed_errors": "no_learn_from_unconfirmed_errors",
        }
        if intent in blocked:
            return {
                "allowed": False,
                "intent": intent,
                "rule": blocked[intent],
                "rules": list(AI_SAFETY),
            }
        return {"allowed": True, "intent": intent, "rules": list(AI_SAFETY)}
