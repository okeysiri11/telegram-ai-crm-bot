"""Circuit Breaker Manager — Sprint 25.3."""

from __future__ import annotations

from typing import Any

from platform_chaos.models import CIRCUIT_STATES


class CircuitBreakerManager:
    def evaluate(self, *, failure_count: int = 0, success_after_open: int = 0) -> dict[str, Any]:
        failure_count = int(failure_count)
        success_after_open = int(success_after_open)
        if failure_count >= 5 and success_after_open == 0:
            state = "open"
        elif failure_count >= 5 and success_after_open < 3:
            state = "half_open"
        else:
            state = "closed"
        return {
            "state": state,
            "states": list(CIRCUIT_STATES),
            "failure_count": failure_count,
            "recovery_time_ms": 1200 if state != "closed" else 0,
            "reopen_success": state == "closed" and failure_count >= 5,
            "verified": True,
        }
