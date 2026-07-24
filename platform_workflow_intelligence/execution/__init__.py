"""Execution Engine — Sprint 24.1."""

from __future__ import annotations

from typing import Any

from platform_workflow_intelligence.models import EXECUTION_POLICIES


class ExecutionEngine:
    def run(
        self,
        *,
        workflow: dict[str, Any],
        mode: str = "async",
        policy: str | None = None,
        owner_approved: bool = False,
        manager_approved: bool = False,
        simulate: bool = False,
    ) -> dict[str, Any]:
        policy = (policy or workflow.get("policy") or "requires_owner").lower()
        if policy not in EXECUTION_POLICIES:
            raise ValueError(f"unsupported policy: {policy}")
        mode = (mode or "async").lower()
        if mode not in ("sync", "async"):
            mode = "async"

        if policy == "simulation_only" or simulate:
            return {
                "status": "simulated",
                "mode": mode,
                "policy": policy,
                "executed": False,
                "queue": False,
                "retries": 0,
                "rollback": False,
                "compensation": False,
                "ai_started": False,
            }
        if policy == "ai_recommendation_only":
            return {
                "status": "recommendation_only",
                "mode": mode,
                "policy": policy,
                "executed": False,
                "ai_started": False,
                "recommendation": "await_human_policy",
            }
        if policy == "requires_owner" and not owner_approved:
            return {
                "status": "blocked_awaiting_owner",
                "mode": mode,
                "policy": policy,
                "executed": False,
                "ai_started": False,
                "owner_decision_center": True,
            }
        if policy == "requires_manager" and not manager_approved:
            return {
                "status": "blocked_awaiting_manager",
                "mode": mode,
                "policy": policy,
                "executed": False,
                "ai_started": False,
            }
        # automatic or approved
        return {
            "status": "completed",
            "mode": mode,
            "policy": policy,
            "executed": True,
            "queue": mode == "async",
            "retries": 0,
            "rollback_supported": True,
            "compensation_supported": True,
            "ai_started": False,
            "success": True,
        }
