"""Chief Drone AI — multi-agent ecosystem orchestration (Sprint 11.10)."""

from __future__ import annotations

from typing import Any

from applications.drone_platform.ai.safety_ai import SafetyAIAssistant


CHIEF_AI_CAPABILITIES = (
    "chief_drone_ai",
    "engineering_ai",
    "firmware_ai",
    "mission_ai_agent",
    "manufacturing_ai",
    "maintenance_ai",
    "fleet_ai",
    "cloud_ai_agent",
    "documentation_ai",
    "knowledge_ai",
    "multi_agent_collaborate",
)

AGENT_ROSTER = (
    "chief",
    "engineering",
    "firmware",
    "mission",
    "manufacturing",
    "maintenance",
    "fleet",
    "cloud",
    "documentation",
    "knowledge",
)


class ChiefDroneAIAssistant(SafetyAIAssistant):
    """All domain AIs collaborate through a multi-agent engine facade."""

    def capabilities(self) -> list[str]:
        return list(dict.fromkeys([*super().capabilities(), *CHIEF_AI_CAPABILITIES]))

    def roster(self) -> dict[str, Any]:
        return {"agents": list(AGENT_ROSTER), "engine": "platform_multi_agent", "policy": "engineering_assistance_only"}

    def chief_drone_ai(self, *, query: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        ctx = dict(context or {})
        response = {
            "role": "chief",
            "query": query,
            "plan": ["Assess domain", "Delegate to specialists", "Synthesize recommendations"],
            "delegates": ["engineering", "mission", "fleet", "cloud"],
            "context": ctx,
        }
        return self._session(agent="chief_drone_ai", query=query, context=ctx, response=response)

    def engineering_ai(self, *, query: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        response = {"role": "engineering", "advice": "Validate design margins and BOM availability", "query": query, "context": dict(context or {})}
        return self._session(agent="engineering_ai", query=query, context=dict(context or {}), response=response)

    def firmware_ai(self, *, query: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        response = {"role": "firmware", "advice": "Stage firmware on ground; verify parameter diffs", "query": query, "context": dict(context or {})}
        return self._session(agent="firmware_ai", query=query, context=dict(context or {}), response=response)

    def mission_ai_agent(self, *, query: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        response = {"role": "mission", "advice": "Validate geofence, battery reserve, and operator readiness", "query": query, "context": dict(context or {})}
        return self._session(agent="mission_ai_agent", query=query, context=dict(context or {}), response=response)

    def manufacturing_ai(self, *, query: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        response = {"role": "manufacturing", "advice": "Check production order readiness and QA gates", "query": query, "context": dict(context or {})}
        return self._session(agent="manufacturing_ai", query=query, context=dict(context or {}), response=response)

    def maintenance_ai(self, *, query: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        response = {"role": "maintenance", "advice": "Schedule predictive maintenance from health signals", "query": query, "context": dict(context or {})}
        return self._session(agent="maintenance_ai", query=query, context=dict(context or {}), response=response)

    def fleet_ai(self, *, query: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        response = {"role": "fleet", "advice": "Optimize assignment toward available high-readiness aircraft", "query": query, "context": dict(context or {})}
        return self._session(agent="fleet_ai", query=query, context=dict(context or {}), response=response)

    def cloud_ai_agent(self, *, query: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        response = {"role": "cloud", "advice": "Sync twins and audit remote operations channels", "query": query, "context": dict(context or {})}
        return self._session(agent="cloud_ai_agent", query=query, context=dict(context or {}), response=response)

    def documentation_ai(self, *, query: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        response = {"role": "documentation", "advice": "Update enterprise docs and certification evidence", "query": query, "context": dict(context or {})}
        return self._session(agent="documentation_ai", query=query, context=dict(context or {}), response=response)

    def knowledge_ai(self, *, query: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        response = {"role": "knowledge", "advice": "Refresh knowledge graph links and registries", "query": query, "context": dict(context or {})}
        return self._session(agent="knowledge_ai", query=query, context=dict(context or {}), response=response)

    def multi_agent_collaborate(self, *, query: str, agents: list[str] | None = None, context: dict[str, Any] | None = None) -> dict[str, Any]:
        selected = list(agents or ["engineering", "mission", "fleet", "cloud"])
        contributions = []
        dispatch = {
            "engineering": self.engineering_ai,
            "firmware": self.firmware_ai,
            "mission": self.mission_ai_agent,
            "manufacturing": self.manufacturing_ai,
            "maintenance": self.maintenance_ai,
            "fleet": self.fleet_ai,
            "cloud": self.cloud_ai_agent,
            "documentation": self.documentation_ai,
            "knowledge": self.knowledge_ai,
            "chief": self.chief_drone_ai,
        }
        for name in selected:
            fn = dispatch.get(name)
            if fn:
                contributions.append(fn(query=query, context=context))
        response = {
            "engine": "platform_multi_agent",
            "query": query,
            "agents": selected,
            "contributions": [{"agent": c.get("agent"), "advice": (c.get("response") or {}).get("advice") or (c.get("response") or {}).get("plan")} for c in contributions],
            "synthesis": "Combine specialist advice; prioritize safety and certification compliance.",
            "policy": "engineering_assistance_only",
        }
        return self._session(agent="multi_agent_collaborate", query=query, context={"agents": selected}, response=response)

    def assist(self, *, agent: str, query: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        ctx = dict(context or {})
        key = agent.lower().replace("-", "_")
        dispatch = {
            "chief_drone_ai": lambda: self.chief_drone_ai(query=query, context=ctx),
            "chief": lambda: self.chief_drone_ai(query=query, context=ctx),
            "engineering_ai": lambda: self.engineering_ai(query=query, context=ctx),
            "firmware_ai": lambda: self.firmware_ai(query=query, context=ctx),
            "mission_ai_agent": lambda: self.mission_ai_agent(query=query, context=ctx),
            "manufacturing_ai": lambda: self.manufacturing_ai(query=query, context=ctx),
            "maintenance_ai": lambda: self.maintenance_ai(query=query, context=ctx),
            "fleet_ai": lambda: self.fleet_ai(query=query, context=ctx),
            "cloud_ai_agent": lambda: self.cloud_ai_agent(query=query, context=ctx),
            "documentation_ai": lambda: self.documentation_ai(query=query, context=ctx),
            "knowledge_ai": lambda: self.knowledge_ai(query=query, context=ctx),
            "multi_agent_collaborate": lambda: self.multi_agent_collaborate(query=query, agents=ctx.get("agents"), context=ctx),
        }
        if key in dispatch:
            return dispatch[key]()
        return super().assist(agent=agent, query=query, context=context)


from applications.drone_platform.shared.store import drone_store

chief_drone_ai = ChiefDroneAIAssistant(store=drone_store)
