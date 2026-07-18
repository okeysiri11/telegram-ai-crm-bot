# Integration Hub exceptions.

from __future__ import annotations


class IntegrationError(Exception):
    """Base integration error."""


class ConnectorNotFoundError(IntegrationError):
    """Unknown connector or provider."""


class ConnectorDisabledError(IntegrationError):
    """Connector is disabled."""


class WebhookError(IntegrationError):
    """Webhook validation or processing failure."""


class RateLimitExceededError(IntegrationError):
    """Rate limit exceeded for provider/endpoint/key."""


class RetryExhaustedError(IntegrationError):
    """All retry attempts exhausted — message in DLQ."""


class PayloadMappingError(IntegrationError):
    """Payload transformation failure."""
