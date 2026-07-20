# Decision policies — configurable scoring weights and priority profiles.

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class DecisionPolicy:
    """Configurable decision policy with custom scoring weights."""

    policy_id: str
    name: str
    description: str = ""
    weights: dict[str, float] = field(default_factory=dict)
    business_rules: list[str] = field(default_factory=list)
    min_confidence: float = 30.0

    def get_weight(self, criterion: str) -> float:
        return self.weights.get(criterion, 0.1)


DEFAULT_POLICIES: dict[str, DecisionPolicy] = {
    "balanced": DecisionPolicy(
        policy_id="balanced",
        name="Balanced",
        description="Equal weight across cost, time, risk, and confidence",
        weights={
            "execution_cost": 0.15,
            "estimated_duration_ms": 0.15,
            "risk_level": 0.15,
            "confidence_score": 0.15,
            "tool_availability": 0.10,
            "agent_availability": 0.10,
            "resource_consumption": 0.05,
            "business_priority": 0.10,
            "user_preference": 0.05,
        },
    ),
    "cost_first": DecisionPolicy(
        policy_id="cost_first",
        name="Cost Optimization",
        description="Minimize execution cost",
        weights={
            "execution_cost": 0.40,
            "estimated_duration_ms": 0.10,
            "risk_level": 0.10,
            "confidence_score": 0.10,
            "tool_availability": 0.05,
            "agent_availability": 0.05,
            "resource_consumption": 0.10,
            "business_priority": 0.05,
            "user_preference": 0.05,
        },
    ),
    "speed_first": DecisionPolicy(
        policy_id="speed_first",
        name="Time Optimization",
        description="Minimize execution duration",
        weights={
            "execution_cost": 0.10,
            "estimated_duration_ms": 0.40,
            "risk_level": 0.10,
            "confidence_score": 0.10,
            "tool_availability": 0.05,
            "agent_availability": 0.05,
            "resource_consumption": 0.05,
            "business_priority": 0.10,
            "user_preference": 0.05,
        },
    ),
    "risk_averse": DecisionPolicy(
        policy_id="risk_averse",
        name="Risk Averse",
        description="Minimize risk, maximize confidence",
        weights={
            "execution_cost": 0.05,
            "estimated_duration_ms": 0.10,
            "risk_level": 0.30,
            "confidence_score": 0.25,
            "tool_availability": 0.10,
            "agent_availability": 0.10,
            "resource_consumption": 0.05,
            "business_priority": 0.03,
            "user_preference": 0.02,
        },
    ),
    "business_priority": DecisionPolicy(
        policy_id="business_priority",
        name="Business Priority",
        description="Favor high business priority candidates",
        weights={
            "execution_cost": 0.05,
            "estimated_duration_ms": 0.05,
            "risk_level": 0.10,
            "confidence_score": 0.10,
            "tool_availability": 0.05,
            "agent_availability": 0.05,
            "resource_consumption": 0.05,
            "business_priority": 0.40,
            "user_preference": 0.15,
        },
    ),
}


class PolicyRegistry:
    def __init__(self) -> None:
        self._policies: dict[str, DecisionPolicy] = dict(DEFAULT_POLICIES)

    def reset(self) -> None:
        self._policies = dict(DEFAULT_POLICIES)

    def register(self, policy: DecisionPolicy) -> None:
        self._policies[policy.policy_id] = policy

    def get(self, policy_id: str) -> DecisionPolicy:
        from platform_decision.exceptions import PolicyNotFoundError

        if policy_id not in self._policies:
            raise PolicyNotFoundError(policy_id)
        return self._policies[policy_id]

    def list_policies(self) -> list[DecisionPolicy]:
        return list(self._policies.values())


policy_registry = PolicyRegistry()
