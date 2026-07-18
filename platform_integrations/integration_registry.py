# Integration registry — provider catalog and metadata.

from __future__ import annotations

from platform_integrations.models import ConnectorType, ProviderType

PROVIDER_CATALOG: dict[str, dict] = {
    ProviderType.TELEGRAM.value: {
        "connector_type": ConnectorType.BIDIRECTIONAL.value,
        "version": "1.0.0",
        "implemented": True,
        "description": "Telegram Bot API messaging",
    },
    ProviderType.EMAIL.value: {
        "connector_type": ConnectorType.OUTBOUND.value,
        "version": "1.0.0",
        "implemented": True,
        "description": "SMTP / email delivery",
    },
    ProviderType.SMS.value: {
        "connector_type": ConnectorType.OUTBOUND.value,
        "version": "1.0.0",
        "implemented": True,
        "description": "SMS gateway",
    },
    ProviderType.HTTP_REST.value: {
        "connector_type": ConnectorType.BIDIRECTIONAL.value,
        "version": "1.0.0",
        "implemented": True,
        "description": "Generic HTTP REST client",
    },
    ProviderType.WEBHOOK.value: {
        "connector_type": ConnectorType.WEBHOOK.value,
        "version": "1.0.0",
        "implemented": True,
        "description": "Inbound/outbound webhooks",
    },
    ProviderType.WEBSOCKET.value: {
        "connector_type": ConnectorType.STREAMING.value,
        "version": "1.0.0",
        "implemented": True,
        "description": "WebSocket streaming",
    },
    ProviderType.WHATSAPP.value: {
        "connector_type": ConnectorType.BIDIRECTIONAL.value,
        "version": "0.1.0",
        "implemented": False,
        "description": "WhatsApp Business API (future)",
    },
    ProviderType.BITRIX24.value: {
        "connector_type": ConnectorType.BIDIRECTIONAL.value,
        "version": "0.1.0",
        "implemented": False,
        "description": "Bitrix24 CRM (future)",
    },
    ProviderType.AMOCRM.value: {
        "connector_type": ConnectorType.BIDIRECTIONAL.value,
        "version": "0.1.0",
        "implemented": False,
        "description": "amoCRM (future)",
    },
    ProviderType.GOOGLE.value: {
        "connector_type": ConnectorType.BIDIRECTIONAL.value,
        "version": "0.1.0",
        "implemented": False,
        "description": "Google APIs (future)",
    },
    ProviderType.OPENAI.value: {
        "connector_type": ConnectorType.OUTBOUND.value,
        "version": "0.1.0",
        "implemented": False,
        "description": "OpenAI / LLM providers (future)",
    },
    ProviderType.STRIPE.value: {
        "connector_type": ConnectorType.WEBHOOK.value,
        "version": "0.1.0",
        "implemented": False,
        "description": "Stripe payments (future)",
    },
}


class IntegrationRegistry:
    @staticmethod
    def list_providers() -> dict[str, dict]:
        return dict(PROVIDER_CATALOG)

    @staticmethod
    def get_provider(provider: str) -> dict | None:
        return PROVIDER_CATALOG.get(provider)

    @staticmethod
    def connector_types() -> list[str]:
        return [ct.value for ct in ConnectorType]


integration_registry = IntegrationRegistry()
