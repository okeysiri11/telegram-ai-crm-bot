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
    ProviderType.N8N.value: {
        "connector_type": ConnectorType.WEBHOOK.value,
        "version": "1.0.0",
        "implemented": True,
        "description": "n8n external workflow orchestration (no business logic)",
    },
    ProviderType.ANTHROPIC.value: {
        "connector_type": ConnectorType.OUTBOUND.value,
        "version": "1.0.0",
        "implemented": True,
        "description": "Anthropic via AI Provider Hub",
    },
    ProviderType.OPENROUTER.value: {
        "connector_type": ConnectorType.OUTBOUND.value,
        "version": "1.0.0",
        "implemented": True,
        "description": "OpenRouter via AI Provider Hub",
    },
    ProviderType.LITELLM.value: {
        "connector_type": ConnectorType.OUTBOUND.value,
        "version": "1.0.0",
        "implemented": True,
        "description": "LiteLLM gateway via AI Provider Hub",
    },
    ProviderType.SLACK.value: {
        "connector_type": ConnectorType.BIDIRECTIONAL.value,
        "version": "0.1.0",
        "implemented": False,
        "description": "Slack workspace messaging",
    },
    ProviderType.DISCORD.value: {
        "connector_type": ConnectorType.BIDIRECTIONAL.value,
        "version": "0.1.0",
        "implemented": False,
        "description": "Discord bots / webhooks",
    },
    ProviderType.HUBSPOT.value: {
        "connector_type": ConnectorType.BIDIRECTIONAL.value,
        "version": "0.1.0",
        "implemented": False,
        "description": "HubSpot CRM",
    },
    ProviderType.SALESFORCE.value: {
        "connector_type": ConnectorType.BIDIRECTIONAL.value,
        "version": "0.1.0",
        "implemented": False,
        "description": "Salesforce CRM",
    },
    ProviderType.S3.value: {
        "connector_type": ConnectorType.OUTBOUND.value,
        "version": "0.1.0",
        "implemented": False,
        "description": "Amazon S3 object storage",
    },
    ProviderType.MINIO.value: {
        "connector_type": ConnectorType.OUTBOUND.value,
        "version": "0.1.0",
        "implemented": False,
        "description": "MinIO S3-compatible storage",
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
