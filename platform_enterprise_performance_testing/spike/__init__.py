"""Spike Test Engine — Sprint 25.2."""

from __future__ import annotations

from typing import Any


class SpikeTestEngine:
    def run(self, *, pattern: list[int] | None = None) -> dict[str, Any]:
        pattern = list(pattern or [100, 1000, 5000, 100])
        steps = []
        for i, users in enumerate(pattern):
            latency = round(40 + users * 0.05, 2)
            steps.append({"step": i + 1, "users": int(users), "latency_ms": latency, "ok": users <= 5000})
        # recovery = time from peak back to baseline
        peak = max(pattern) if pattern else 0
        baseline = pattern[-1] if pattern else 0
        recovery_ms = round(abs(peak - baseline) * 0.2, 2)
        return {
            "engine": "spike",
            "pattern": pattern,
            "steps": steps,
            "recovery_ms": recovery_ms,
            "recovered": baseline <= pattern[0] if pattern else True,
        }
