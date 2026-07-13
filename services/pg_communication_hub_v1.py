# Communication Hub v1 — product layer.

from __future__ import annotations

import uuid
from typing import Any

from services.pg_communication_hub_engine import CommunicationHubError, CommunicationHubV1

HUB_FEATURES = frozenset({
    "unified_inbox",
    "message_routing",
    "lead_attribution",
    "conversation_history",
    "auto_response",
    "escalation_to_manager",
})


class CommunicationHubProductError(Exception):
    pass


class CommunicationHubV1Product:
    @staticmethod
    async def user_can_access(user_id: int) -> bool:
        return await CommunicationHubV1.user_can_access(user_id)

    @staticmethod
    def list_features() -> list[dict[str, str]]:
        labels = {
            "unified_inbox": "Unified Inbox",
            "message_routing": "Message Routing",
            "lead_attribution": "Lead Attribution",
            "conversation_history": "Conversation History",
            "auto_response": "Auto Response",
            "escalation_to_manager": "Escalation to Manager",
        }
        return [{"code": k, "label": labels[k]} for k in sorted(HUB_FEATURES)]

    @staticmethod
    async def get_hub(actor_id: int, tenant_id: uuid.UUID) -> dict[str, Any]:
        try:
            return {
                **await CommunicationHubV1.get_hub_dashboard(actor_id, tenant_id),
                "features": list(HUB_FEATURES),
            }
        except CommunicationHubError as exc:
            raise CommunicationHubProductError(str(exc)) from exc

    @staticmethod
    async def get_feature(
        actor_id: int,
        tenant_id: uuid.UUID,
        feature: str,
        *,
        conversation_id: str | None = None,
    ) -> dict[str, Any]:
        if feature not in HUB_FEATURES:
            raise CommunicationHubProductError(f"Unknown feature: {feature}")
        try:
            if feature == "unified_inbox":
                return {"feature": feature, **await CommunicationHubV1.get_unified_inbox(actor_id, tenant_id)}
            if feature == "conversation_history":
                if not conversation_id:
                    inbox = await CommunicationHubV1.get_unified_inbox(actor_id, tenant_id, limit=1)
                    if not inbox["messages"]:
                        return {"feature": feature, "messages": [], "count": 0}
                    conversation_id = inbox["messages"][0]["conversation_id"]
                return {
                    "feature": feature,
                    **await CommunicationHubV1.get_conversation_history(
                        actor_id, tenant_id, conversation_id
                    ),
                }
            return {"feature": feature, "status": "available", "description": feature.replace("_", " ")}
        except CommunicationHubError as exc:
            raise CommunicationHubProductError(str(exc)) from exc
