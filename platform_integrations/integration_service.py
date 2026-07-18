# Integration service — single entry point for all external communication.

from __future__ import annotations

import logging
import time
from typing import Any

from platform_integrations.connector_registry import connector_registry
from platform_integrations.exceptions import ConnectorDisabledError, ConnectorNotFoundError
from platform_integrations.health_monitor import health_monitor
from platform_integrations.integration_events import ConnectorFailedEvent
from platform_integrations.integration_registry import integration_registry
from platform_integrations.models import IntegrationStatistics
from platform_integrations.payload_mapper import payload_mapper
from platform_integrations.provider_manager import provider_manager
from platform_integrations.queue_manager import queue_manager
from platform_integrations.rate_limiter import rate_limiter
from platform_integrations.retry_manager import retry_manager
from platform_integrations.webhook_manager import webhook_manager

logger = logging.getLogger(__name__)


class IntegrationService:
    """All platform modules must invoke external systems through this service."""

    def __init__(self) -> None:
        self.stats = IntegrationStatistics()

    def bootstrap(self) -> None:
        provider_manager.bootstrap_defaults()

    def reset(self) -> None:
        import platform_integrations.provider_manager as pm

        connector_registry.reset()
        webhook_manager.reset()
        retry_manager.reset()
        queue_manager.reset()
        rate_limiter.reset()
        health_monitor.reset()
        self.stats = IntegrationStatistics()
        pm._BOOTSTRAPPED = False

    async def invoke(
        self,
        connector_id: str,
        operation: str,
        payload: dict[str, Any],
        *,
        api_key: str | None = None,
        endpoint: str = "default",
        retry_on_failure: bool = True,
    ) -> dict[str, Any]:
        """Outbound invocation — rate-limited, mapped, retried on failure."""
        meta = connector_registry.get_metadata(connector_id)
        if not meta.enabled:
            raise ConnectorDisabledError(f"Connector {connector_id} is disabled")

        rate_limiter.check(provider=meta.provider, endpoint=endpoint, api_key=api_key)
        external_payload = payload_mapper.to_external(meta.provider, payload)
        self.stats.total_invocations += 1

        connector = connector_registry.get(connector_id)
        try:
            result = await connector.invoke(operation, external_payload)
            self.stats.successful_invocations += 1
            return payload_mapper.to_internal(meta.provider, result)
        except Exception as exc:
            self.stats.failed_invocations += 1
            from events.event_bus import publish

            await publish(
                ConnectorFailedEvent(
                    connector_id=connector_id,
                    provider=meta.provider,
                    error=str(exc),
                    operation=operation,
                )
            )
            if retry_on_failure:
                record = retry_manager.schedule(
                    connector_id=connector_id,
                    operation=operation,
                    payload=payload,
                    error=str(exc),
                )
                self.stats.retries_scheduled += 1
                await retry_manager.publish_scheduled(record)
            raise

    async def invoke_by_provider(
        self,
        provider: str,
        operation: str,
        payload: dict[str, Any],
        **kwargs: Any,
    ) -> dict[str, Any]:
        connector_id = f"{provider}-default"
        if connector_id not in {m.connector_id for m in connector_registry.list_metadata()}:
            connector_registry.register(provider, connector_id=connector_id)
        return await self.invoke(connector_id, operation, payload, **kwargs)

    async def enqueue(self, connector_id: str, operation: str, payload: dict[str, Any]):
        return await queue_manager.enqueue(connector_id, operation, payload)

    async def process_webhook(
        self,
        webhook_id: str,
        *,
        body: bytes,
        signature: str | None,
        nonce: str | None,
        timestamp: str | None,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        started = time.perf_counter()
        registration = webhook_manager.get(webhook_id)
        if not registration.enabled:
            raise ConnectorDisabledError(f"Webhook {webhook_id} is disabled")

        webhook_manager.validate_signature(registration, body=body, signature=signature)
        webhook_manager.check_replay(nonce=nonce, timestamp=timestamp)
        self.stats.webhooks_received += 1

        await webhook_manager.audit_webhook(
            event_type="INTEGRATION_WEBHOOK_RECEIVED",
            webhook_id=webhook_id,
            provider=registration.provider,
            payload={"size": len(body)},
        )
        await webhook_manager.publish_received(registration, len(body))

        connector_id = registration.connector_id or f"{registration.provider}-default"
        try:
            result = await self.invoke(
                connector_id,
                "receive",
                payload,
                retry_on_failure=False,
            )
            success = True
        except Exception as exc:
            result = {"error": str(exc)}
            success = False

        duration_ms = round((time.perf_counter() - started) * 1000, 2)
        self.stats.webhooks_processed += 1
        await webhook_manager.publish_processed(
            registration,
            success=success,
            duration_ms=duration_ms,
        )
        await webhook_manager.audit_webhook(
            event_type="INTEGRATION_WEBHOOK_PROCESSED",
            webhook_id=webhook_id,
            provider=registration.provider,
            payload={"success": success, "duration_ms": duration_ms},
        )
        return result

    def register_webhook(self, **kwargs):
        return webhook_manager.register(**kwargs)

    async def health(self) -> dict[str, Any]:
        checks = await health_monitor.check_all()
        return {
            "overall_status": await health_monitor.overall_status(),
            "connectors": [h.to_dict() for h in checks],
        }

    def status(self) -> dict[str, Any]:
        return {
            "providers": integration_registry.list_providers(),
            "connectors": [m.to_dict() for m in connector_registry.list_metadata()],
            "webhooks": [w.to_dict() for w in webhook_manager.list_webhooks()],
            "health": [h.to_dict() for h in health_monitor.cached()],
            "statistics": self.stats.to_dict(),
            "retry_history": [r.to_dict() for r in retry_manager.history(limit=20)],
            "dead_letter_queue": retry_manager.dead_letter_queue(),
            "queue": [],
            "rate_limits": rate_limiter.stats(),
        }


integration_service = IntegrationService()
