"""Test Environment Manager — Sprint 25.1."""

from __future__ import annotations

from typing import Any

from platform_testing.models import ENVIRONMENTS


class TestEnvironmentManager:
    def provision(self, *, environment: str, run_id: str) -> dict[str, Any]:
        environment = (environment or "local").lower()
        if environment not in ENVIRONMENTS:
            raise ValueError(f"unsupported environment: {environment}")
        return {
            "environment": environment,
            "run_id": run_id,
            "isolated": True,
            "supported": list(ENVIRONMENTS),
            "ready": True,
        }
