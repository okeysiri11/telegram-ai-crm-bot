"""Unified Communication Center — Sprint 22.6."""

from __future__ import annotations

from typing import Any

from platform_communications_hub.models import CHANNELS, CONNECTOR_CHANNELS, FUTURE_CHANNELS


class UnifiedCommunicationCenter:
    def send(
        self,
        *,
        channel: str,
        recipient: str,
        body: str,
        template_id: str = "",
        industry: str = "beauty",
        approved: bool = False,
        automation_id: str = "",
    ) -> dict[str, Any]:
        if channel not in CHANNELS:
            raise ValueError(f"unsupported channel: {channel}")
        if not recipient or not body:
            raise ValueError("recipient and body are required")
        if not approved and not automation_id:
            raise ValueError("send requires owner approval or approved automation")
        status = "queued"
        if channel in FUTURE_CHANNELS:
            status = "deferred_future_module"
        elif channel in CONNECTOR_CHANNELS:
            status = "queued_via_connector"
        return {
            "channel": channel,
            "recipient": recipient,
            "body": body,
            "template_id": template_id or None,
            "industry": industry,
            "status": status,
            "approved": bool(approved or automation_id),
            "automation_id": automation_id or None,
            "gateway": "enterprise_communications_hub",
            "delegates_to": "enterprise_comms",
            "ai_sent": False,
        }

    def channels(self) -> dict[str, Any]:
        return {
            "channels": list(CHANNELS),
            "connectors": list(CONNECTOR_CHANNELS),
            "future": list(FUTURE_CHANNELS),
        }
