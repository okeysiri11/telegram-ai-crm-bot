# Plugin integrations facade.

from __future__ import annotations

from typing import Any

from platform_plugin_sdk.plugin_api import IntegrationsApi


class PluginIntegrations:
    """Integration Hub wrapper scoped to plugin identity."""

    def __init__(self, plugin_id: str, integrations: IntegrationsApi) -> None:
        self.plugin_id = plugin_id
        self._integrations = integrations

    async def invoke(self, provider: str, action: str, payload: dict[str, Any]) -> dict[str, Any]:
        enriched = {"plugin_id": self.plugin_id, **payload}
        return await self._integrations.invoke(provider, action, enriched)

    async def send_telegram(self, chat_id: int, text: str) -> dict[str, Any]:
        return await self.invoke("telegram", "send_message", {"chat_id": chat_id, "text": text})

    async def send_email(self, to: str, subject: str, body: str) -> dict[str, Any]:
        return await self.invoke("email", "send", {"to": to, "subject": subject, "body": body})
