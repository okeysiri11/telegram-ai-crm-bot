"""AI Execution Policies — Sprint 24.1."""

from __future__ import annotations

from typing import Any

from platform_workflow_intelligence.models import EXECUTION_POLICIES


class AIExecutionPolicies:
    def set_policy(self, workflow: dict[str, Any], *, policy: str) -> dict[str, Any]:
        policy = (policy or "").lower()
        if policy not in EXECUTION_POLICIES:
            raise ValueError(f"unsupported policy: {policy}")
        updated = dict(workflow)
        updated["policy"] = policy
        updated["critical_requires_owner"] = policy in ("requires_owner",) or policy != "automatic"
        return updated

    def list_policies(self) -> list[str]:
        return list(EXECUTION_POLICIES)
