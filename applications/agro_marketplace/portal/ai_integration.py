# Portal AI hooks — Assistant, Workforce, Identity via bridges only.

from __future__ import annotations

from typing import Any

from applications.agro_marketplace.integrations.ecosystem_bridge import EcosystemBridge, ecosystem_bridge
from applications.agro_marketplace.integrations.platform_bridge import PlatformBridge, platform_bridge


class PortalAIIntegration:
    def __init__(
        self,
        platform: PlatformBridge | None = None,
        ecosystem: EcosystemBridge | None = None,
    ) -> None:
        self._platform = platform or platform_bridge
        self._ecosystem = ecosystem or ecosystem_bridge

    async def chat(
        self,
        message: str,
        *,
        role: str = "farmer",
        user_id: str = "",
    ) -> dict[str, Any]:
        context = {"portal_role": role, "surface": "portal"}
        result = await self._ecosystem.ask_assistant(message, user_id=user_id, context=context)
        await self._platform.start_ai_workflow("portal_assistant", {"role": role, "user_id": user_id})
        return result if isinstance(result, dict) else {"reply": str(result), "role": role}

    async def recommendation_widgets(self, role: str, user_id: str = "") -> list[dict[str, Any]]:
        await self._ecosystem.invoke_workforce(
            "portal_recommendations",
            context={"role": role, "user_id": user_id},
        )
        widgets = [
            {"type": "recommendation", "title": f"{role.title()} tips", "items": []},
        ]
        if role == "farmer":
            widgets.append({"type": "crop_advice", "title": "Crop advisor", "items": ["Check moisture"]})
        elif role == "buyer":
            widgets.append({"type": "sourcing", "title": "Sourcing matches", "items": ["Open RFQs"]})
        elif role == "executive":
            widgets.append({"type": "kpi", "title": "Executive highlights", "items": ["Review KPIs"]})
        return widgets

    async def smart_notification(self, recipient_id: str, signal: str) -> dict[str, Any]:
        self._ecosystem.check_governance("smart_notification", {"recipient_id": recipient_id, "signal": signal})
        return {
            "recipient_id": recipient_id,
            "title": "AI Alert",
            "body": f"Smart alert: {signal}",
            "channel": "ai_alert",
        }


portal_ai = PortalAIIntegration()
