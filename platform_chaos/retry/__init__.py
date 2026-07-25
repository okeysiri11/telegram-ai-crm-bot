"""Retry Engine — Sprint 25.3."""

from __future__ import annotations

from typing import Any

from platform_chaos.models import RETRY_STRATEGIES


class RetryEngine:
    def run(self, *, strategy: str = "exponential_backoff", max_attempts: int = 3) -> dict[str, Any]:
        strategy = (strategy or "").lower()
        if strategy not in RETRY_STRATEGIES:
            raise ValueError(f"unsupported retry strategy: {strategy}")
        max_attempts = max(1, int(max_attempts))
        delays = []
        for i in range(max_attempts):
            if strategy == "fixed_delay":
                delays.append(100)
            elif strategy == "exponential_backoff":
                delays.append(50 * (2 ** i))
            elif strategy == "linear_retry":
                delays.append(50 * (i + 1))
            else:
                delays.append(0)
        return {
            "strategy": strategy,
            "attempts": max_attempts,
            "delays_ms": delays,
            "success": True,
            "avg_recovery_ms": round(sum(delays) / len(delays), 2),
            "strategies": list(RETRY_STRATEGIES),
        }
