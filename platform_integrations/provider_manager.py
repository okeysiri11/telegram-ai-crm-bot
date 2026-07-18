# Provider manager — enable/disable and lifecycle orchestration.

from __future__ import annotations

import logging

from platform_integrations.connector_registry import connector_registry
from platform_integrations.integration_events import ConnectorConnectedEvent, ConnectorFailedEvent
from platform_integrations.integration_registry import integration_registry
from platform_integrations.models import ProviderType

logger = logging.getLogger(__name__)

_BOOTSTRAPPED = False


class ProviderManager:
    @staticmethod
    def bootstrap_defaults() -> list[str]:
        global _BOOTSTRAPPED
        if _BOOTSTRAPPED:
            return [m.connector_id for m in connector_registry.list_metadata()]

        registered: list[str] = []
        for provider in (
            ProviderType.TELEGRAM.value,
            ProviderType.EMAIL.value,
            ProviderType.SMS.value,
            ProviderType.HTTP_REST.value,
            ProviderType.WEBHOOK.value,
            ProviderType.WEBSOCKET.value,
        ):
            meta = connector_registry.register(provider, enabled=True)
            registered.append(meta.connector_id)

        for provider in (
            ProviderType.WHATSAPP.value,
            ProviderType.BITRIX24.value,
            ProviderType.AMOCRM.value,
            ProviderType.GOOGLE.value,
            ProviderType.OPENAI.value,
            ProviderType.STRIPE.value,
        ):
            meta = connector_registry.register(provider, enabled=False, description="Future provider")
            registered.append(meta.connector_id)

        _BOOTSTRAPPED = True
        logger.info("integration_providers_bootstrapped count=%s", len(registered))
        return registered

    @staticmethod
    async def connect(connector_id: str) -> None:
        meta = connector_registry.get_metadata(connector_id)
        if not meta.enabled:
            return
        connector = connector_registry.get(connector_id)
        try:
            await connector.connect()
            from events.event_bus import publish

            await publish(
                ConnectorConnectedEvent(
                    connector_id=connector_id,
                    provider=meta.provider,
                    version=meta.version,
                )
            )
        except Exception as exc:
            from events.event_bus import publish

            await publish(
                ConnectorFailedEvent(
                    connector_id=connector_id,
                    provider=meta.provider,
                    error=str(exc),
                    operation="connect",
                )
            )
            raise

    @staticmethod
    async def connect_all_enabled() -> None:
        for meta in connector_registry.list_metadata():
            if meta.enabled:
                try:
                    await ProviderManager.connect(meta.connector_id)
                except Exception:
                    logger.warning("connector_connect_failed id=%s", meta.connector_id, exc_info=True)

    @staticmethod
    def enable(connector_id: str):
        return connector_registry.enable(connector_id)

    @staticmethod
    def disable(connector_id: str):
        return connector_registry.disable(connector_id)

    @staticmethod
    def catalog():
        return integration_registry.list_providers()


provider_manager = ProviderManager()
