# Built-in connector implementations and dynamic loader.

from __future__ import annotations

import logging
from typing import Any, Type

from platform_integrations.connector_base import ConnectorBase
from platform_integrations.models import ConnectorType, ProviderType

logger = logging.getLogger(__name__)


class TelegramConnector(ConnectorBase):
    provider = ProviderType.TELEGRAM.value
    connector_type = ConnectorType.BIDIRECTIONAL
    version = "1.0.0"

    async def send(self, operation: str, payload: dict[str, Any]) -> dict[str, Any]:
        return {"provider": self.provider, "operation": operation, "sent": True, "payload": payload}


class EmailConnector(ConnectorBase):
    provider = ProviderType.EMAIL.value
    connector_type = ConnectorType.OUTBOUND
    version = "1.0.0"

    async def send(self, operation: str, payload: dict[str, Any]) -> dict[str, Any]:
        return {"provider": self.provider, "operation": operation, "message_id": "email-stub"}


class SmsConnector(ConnectorBase):
    provider = ProviderType.SMS.value
    connector_type = ConnectorType.OUTBOUND
    version = "1.0.0"

    async def send(self, operation: str, payload: dict[str, Any]) -> dict[str, Any]:
        return {"provider": self.provider, "operation": operation, "message_id": "sms-stub"}


class HttpRestConnector(ConnectorBase):
    provider = ProviderType.HTTP_REST.value
    connector_type = ConnectorType.BIDIRECTIONAL
    version = "1.0.0"

    async def send(self, operation: str, payload: dict[str, Any]) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "operation": operation,
            "status": 200,
            "body": payload,
        }


class WebhookConnector(ConnectorBase):
    provider = ProviderType.WEBHOOK.value
    connector_type = ConnectorType.WEBHOOK
    version = "1.0.0"

    async def send(self, operation: str, payload: dict[str, Any]) -> dict[str, Any]:
        return {"provider": self.provider, "operation": operation, "delivered": True}

    async def receive(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"provider": self.provider, "received": True, "payload": payload}


class WebSocketConnector(ConnectorBase):
    provider = ProviderType.WEBSOCKET.value
    connector_type = ConnectorType.STREAMING
    version = "1.0.0"

    async def send(self, operation: str, payload: dict[str, Any]) -> dict[str, Any]:
        return {"provider": self.provider, "operation": operation, "streamed": True}


class FutureProviderConnector(ConnectorBase):
    """Stub for future providers — disabled by default."""

    connector_type = ConnectorType.OUTBOUND
    version = "0.1.0"

    def __init__(self, connector_id: str, *, provider: str, config: dict[str, Any] | None = None) -> None:
        super().__init__(connector_id, config=config)
        self.provider = provider

    async def send(self, operation: str, payload: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError(f"Provider {self.provider} is not yet implemented")


_BUILTIN_CLASSES: dict[str, Type[ConnectorBase]] = {
    ProviderType.TELEGRAM.value: TelegramConnector,
    ProviderType.EMAIL.value: EmailConnector,
    ProviderType.SMS.value: SmsConnector,
    ProviderType.HTTP_REST.value: HttpRestConnector,
    ProviderType.WEBHOOK.value: WebhookConnector,
    ProviderType.WEBSOCKET.value: WebSocketConnector,
}

_FUTURE_PROVIDERS = (
    ProviderType.WHATSAPP.value,
    ProviderType.BITRIX24.value,
    ProviderType.AMOCRM.value,
    ProviderType.GOOGLE.value,
    ProviderType.OPENAI.value,
    ProviderType.STRIPE.value,
)


class ConnectorLoader:
    def __init__(self) -> None:
        self._custom_classes: dict[str, Type[ConnectorBase]] = {}

    def register_class(self, provider: str, connector_class: Type[ConnectorBase]) -> None:
        self._custom_classes[provider] = connector_class
        logger.info("connector_class_registered provider=%s", provider)

    def create(self, provider: str, connector_id: str, *, config: dict[str, Any] | None = None) -> ConnectorBase:
        if provider in self._custom_classes:
            return self._custom_classes[provider](connector_id, config=config)

        cls = _BUILTIN_CLASSES.get(provider)
        if cls is not None:
            return cls(connector_id, config=config)

        if provider in _FUTURE_PROVIDERS:
            return FutureProviderConnector(connector_id, provider=provider, config=config)

        raise KeyError(f"Unknown provider: {provider}")

    def list_providers(self) -> list[str]:
        providers = set(_BUILTIN_CLASSES) | set(_FUTURE_PROVIDERS) | set(self._custom_classes)
        return sorted(providers)

    def reset(self) -> None:
        self._custom_classes.clear()


connector_loader = ConnectorLoader()
