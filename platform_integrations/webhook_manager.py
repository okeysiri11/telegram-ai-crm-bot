# Webhook manager — register, validate, replay protection, audit.

from __future__ import annotations

import hashlib
import hmac
import logging
import secrets
import time
import uuid
from typing import Any

from platform_integrations.exceptions import WebhookError
from platform_integrations.integration_events import WebhookProcessedEvent, WebhookReceivedEvent
from platform_integrations.models import WebhookRegistration

logger = logging.getLogger(__name__)

REPLAY_WINDOW_SECONDS = 300


class WebhookManager:
    def __init__(self) -> None:
        self._webhooks: dict[str, WebhookRegistration] = {}
        self._seen_nonces: dict[str, float] = {}

    def reset(self) -> None:
        self._webhooks.clear()
        self._seen_nonces.clear()

    def register(
        self,
        *,
        name: str,
        provider: str,
        path: str | None = None,
        secret: str | None = None,
        connector_id: str | None = None,
    ) -> WebhookRegistration:
        webhook_id = str(uuid.uuid4())
        registration = WebhookRegistration(
            webhook_id=webhook_id,
            name=name,
            provider=provider,
            path=path or f"/integrations/inbound/{webhook_id}",
            secret=secret or secrets.token_hex(32),
            connector_id=connector_id,
        )
        self._webhooks[webhook_id] = registration
        logger.info("webhook_registered id=%s provider=%s", webhook_id, provider)
        return registration

    def get(self, webhook_id: str) -> WebhookRegistration:
        reg = self._webhooks.get(webhook_id)
        if reg is None:
            raise WebhookError(f"Webhook {webhook_id} not found")
        return reg

    def list_webhooks(self) -> list[WebhookRegistration]:
        return list(self._webhooks.values())

    def validate_signature(
        self,
        registration: WebhookRegistration,
        *,
        body: bytes,
        signature: str | None,
    ) -> None:
        if not signature:
            raise WebhookError("Missing webhook signature")
        expected = hmac.new(
            registration.secret.encode(),
            body,
            hashlib.sha256,
        ).hexdigest()
        provided = signature.removeprefix("sha256=").strip()
        if not hmac.compare_digest(expected, provided):
            raise WebhookError("Invalid webhook signature")

    def check_replay(self, *, nonce: str | None, timestamp: str | None) -> None:
        if not nonce or not timestamp:
            raise WebhookError("Missing replay protection headers (X-Webhook-Nonce, X-Webhook-Timestamp)")

        try:
            ts = float(timestamp)
        except ValueError as exc:
            raise WebhookError("Invalid timestamp") from exc

        if abs(time.time() - ts) > REPLAY_WINDOW_SECONDS:
            raise WebhookError("Webhook timestamp outside replay window")

        if nonce in self._seen_nonces:
            raise WebhookError("Duplicate webhook nonce — replay detected")

        self._seen_nonces[nonce] = time.monotonic()
        self._purge_old_nonces()

    def _purge_old_nonces(self) -> None:
        cutoff = time.monotonic() - REPLAY_WINDOW_SECONDS * 2
        self._seen_nonces = {k: v for k, v in self._seen_nonces.items() if v > cutoff}

    async def audit_webhook(
        self,
        *,
        event_type: str,
        webhook_id: str,
        provider: str,
        payload: dict[str, Any] | None = None,
    ) -> None:
        try:
            from services.pg_platform_audit_engine import PlatformAuditEngineV1

            await PlatformAuditEngineV1.log(
                event_type=event_type,
                entity_type="webhook",
                entity_id=webhook_id,
                payload={"provider": provider, **(payload or {})},
            )
        except Exception:
            logger.warning("webhook_audit_failed id=%s", webhook_id, exc_info=True)

    async def publish_received(self, registration: WebhookRegistration, payload_size: int) -> None:
        from events.event_bus import publish

        await publish(
            WebhookReceivedEvent(
                webhook_id=registration.webhook_id,
                provider=registration.provider,
                path=registration.path,
                payload_size=payload_size,
            )
        )

    async def publish_processed(
        self,
        registration: WebhookRegistration,
        *,
        success: bool,
        duration_ms: float,
    ) -> None:
        from events.event_bus import publish

        await publish(
            WebhookProcessedEvent(
                webhook_id=registration.webhook_id,
                provider=registration.provider,
                success=success,
                duration_ms=duration_ms,
            )
        )


webhook_manager = WebhookManager()
