# Unified Agro Assistant — routes to specialized agents.

from __future__ import annotations

from typing import Any

from applications.agro_marketplace.agents.service import AgroAgentService, agent_service
from applications.agro_marketplace.ai.models import AgroAgentType
from applications.agro_marketplace.integrations.ecosystem_bridge import EcosystemBridge, ecosystem_bridge


_ROLE_MAP = {
    "farmer": AgroAgentType.FARMER_ASSISTANT,
    "buyer": AgroAgentType.BUYER_ASSISTANT,
    "supplier": AgroAgentType.SUPPLIER_ASSISTANT,
    "exporter": AgroAgentType.EXPORTER_ASSISTANT,
    "moderator": AgroAgentType.MARKETPLACE_MODERATOR,
    "pricing": AgroAgentType.PRICING_ADVISOR,
    "crop": AgroAgentType.CROP_ADVISOR,
    "warehouse": AgroAgentType.WAREHOUSE_ADVISOR,
    "logistics": AgroAgentType.LOGISTICS_ADVISOR,
    "executive": AgroAgentType.EXECUTIVE_AGRO_AI,
}


class AgroAssistantService:
    def __init__(
        self,
        agents: AgroAgentService | None = None,
        ecosystem: EcosystemBridge | None = None,
    ) -> None:
        self._agents = agents or agent_service
        self._ecosystem = ecosystem or ecosystem_bridge

    def _resolve_agent(self, role: str = "", message: str = "") -> AgroAgentType:
        if role and role.lower() in _ROLE_MAP:
            return _ROLE_MAP[role.lower()]
        text = message.lower()
        if any(w in text for w in ("price", "pricing", "quote")):
            return AgroAgentType.PRICING_ADVISOR
        if any(w in text for w in ("crop", "plant", "harvest", "season")):
            return AgroAgentType.CROP_ADVISOR
        if any(w in text for w in ("warehouse", "storage", "inventory")):
            return AgroAgentType.WAREHOUSE_ADVISOR
        if any(w in text for w in ("ship", "delivery", "logistics", "transport")):
            return AgroAgentType.LOGISTICS_ADVISOR
        if any(w in text for w in ("export", "customs", "phytosanitary")):
            return AgroAgentType.EXPORTER_ASSISTANT
        if any(w in text for w in ("report", "executive", "kpi")):
            return AgroAgentType.EXECUTIVE_AGRO_AI
        if any(w in text for w in ("buy", "purchase", "rfq")):
            return AgroAgentType.BUYER_ASSISTANT
        if any(w in text for w in ("supply", "supplier")):
            return AgroAgentType.SUPPLIER_ASSISTANT
        return AgroAgentType.FARMER_ASSISTANT

    async def ask(
        self,
        message: str,
        *,
        user_id: str = "",
        role: str = "",
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        agent_type = self._resolve_agent(role, message)
        invocation = await self._agents.invoke(
            agent_type,
            message,
            user_id=user_id,
            context=context,
        )
        return {
            "agent_type": agent_type.value,
            "invocation": invocation.to_dict(),
            "reply": invocation.reply,
        }


agro_assistant = AgroAssistantService()
