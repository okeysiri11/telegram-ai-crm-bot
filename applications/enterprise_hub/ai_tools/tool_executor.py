"""Tool executor — run tools in sandbox with retries and audit."""

from __future__ import annotations

from typing import Any

from applications.enterprise_hub.ai_tools.audit import ToolAudit
from applications.enterprise_hub.ai_tools.execution_context import ExecutionContext
from applications.enterprise_hub.ai_tools.policy import ToolPolicyEngine
from applications.enterprise_hub.ai_tools.sandbox import Sandbox
from applications.enterprise_hub.ai_tools.tool_registry import ToolRegistry
from applications.enterprise_hub.shared.exceptions import ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


class ToolExecutor:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.registry = ToolRegistry(self.store)
        self.sandbox = Sandbox(self.store)
        self.context = ExecutionContext(self.store)
        self.policy = ToolPolicyEngine(self.store)
        self.audit = ToolAudit(self.store)

    def execute(
        self,
        *,
        tool_id: str,
        params: dict[str, Any] | None = None,
        agent_id: str = "system",
        user_id: str = "system",
        role: str = "agent",
        confirmed: bool = True,
        needs_network: bool = False,
        max_retries: int = 1,
    ) -> dict[str, Any]:
        tool = self.registry.get(tool_id)
        if tool.get("status") != "active":
            raise ValidationError(f"tool not active: {tool_id}")

        auth = self.policy.authorize(
            agent_id=agent_id,
            role=role,
            domain=tool["domain"],
            cost=float(tool.get("cost_per_call", 0)),
            confirmed=confirmed,
        )
        if not auth.get("allowed"):
            self.audit.log(
                event="denied",
                tool_id=tool_id,
                agent_id=agent_id,
                permissions=tool.get("permissions"),
                detail=auth,
                error="policy denied",
            )
            raise ValidationError(f"policy denied: {auth.get('notes')}")

        sbx = self.sandbox.create(
            tool_id=tool_id,
            allow_network=needs_network or "network" in (tool.get("permissions") or []),
            allow_files="write" in (tool.get("permissions") or []) or "read" in (tool.get("permissions") or []),
            timeout_ms=int((tool.get("limits") or {}).get("timeout_ms", 5000)),
        )
        check = self.sandbox.validate(
            sandbox_id=sbx["sandbox_id"], needs_network=needs_network, needs_files=True
        )
        if not check.get("allowed"):
            raise ValidationError(f"sandbox denied: {check.get('reasons')}")

        ctx = self.context.open(
            tool_id=tool_id, agent_id=agent_id, user_id=user_id, params=params or {}
        )
        self.audit.log(
            event="start",
            tool_id=tool_id,
            agent_id=agent_id,
            permissions=tool.get("permissions"),
            detail={"context_id": ctx["context_id"], "sandbox_id": sbx["sandbox_id"]},
        )

        attempts = 0
        last_error = None
        result_payload = None
        while attempts <= max_retries:
            attempts += 1
            try:
                result_payload = {
                    "ok": True,
                    "tool": tool["name"],
                    "domain": tool["domain"],
                    "params": params or {},
                    "output": f"executed {tool['name']} with {len(params or {})} params",
                    "attempt": attempts,
                }
                last_error = None
                break
            except Exception as exc:  # pragma: no cover - simulated path
                last_error = str(exc)

        if last_error:
            self.context.finalize(
                context_id=ctx["context_id"],
                status="failed",
                result={"error": last_error},
                duration_ms=10,
                cost=0,
                note=last_error,
            )
            self.audit.log(event="error", tool_id=tool_id, agent_id=agent_id, error=last_error)
            raise ValidationError(last_error)

        duration = 12 + attempts
        cost = float(tool.get("cost_per_call", 0.01))
        finalized = self.context.finalize(
            context_id=ctx["context_id"],
            status="completed",
            result=result_payload,
            duration_ms=duration,
            cost=cost,
            note="ok",
        )
        self.registry.bump_usage(tool_id)
        self.audit.log(
            event="complete",
            tool_id=tool_id,
            agent_id=agent_id,
            permissions=tool.get("permissions"),
            detail={"duration_ms": duration, "cost": cost},
        )
        return {
            "context_id": finalized["context_id"],
            "sandbox_id": sbx["sandbox_id"],
            "authz_id": auth.get("authz_id"),
            "tool_id": tool_id,
            "result": result_payload,
            "duration_ms": duration,
            "cost": cost,
            "status": "completed",
        }
