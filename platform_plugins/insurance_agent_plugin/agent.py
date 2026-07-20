from __future__ import annotations

from typing import Any

from platform_agents.base_agent import BaseAgent
from platform_agents.models import AgentExecutionResult


class InsuranceAgent(BaseAgent):
    agent_id = "insurance_agent"
    name = "Insurance Agent Plugin"
    description = "Insurance vertical — policies, claims, underwriting"
    author = "Plugin Author"
    version = "1.0.0"
    capabilities = ["policy_quote", "claim_status", "underwriting_review"]
    priority = 70

    async def execute(self, capability: str, payload: dict[str, Any] | None = None) -> AgentExecutionResult:
        self.validate_capability(capability)
        return AgentExecutionResult(
            agent_id=self.agent_id,
            capability=capability,
            success=True,
            output={"plugin": True, "capability": capability},
        )
