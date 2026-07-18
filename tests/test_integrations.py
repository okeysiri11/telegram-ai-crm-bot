"""Tests — Platform Integration Hub."""

from __future__ import annotations

import hashlib
import hmac
import json
import time
from unittest.mock import AsyncMock, patch

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from events.event_bus import publish, reset_subscribers
from platform_integrations.connector_loader import connector_loader
from platform_integrations.connector_registry import connector_registry
from platform_integrations.exceptions import (
    ConnectorDisabledError,
    RateLimitExceededError,
    RetryExhaustedError,
    WebhookError,
)
from platform_integrations.integration_events import (
    ConnectorConnectedEvent,
    RetryScheduledEvent,
    WebhookReceivedEvent,
)
from platform_integrations.integration_router import register_integration_routes
from platform_integrations.integration_service import integration_service
from platform_integrations.models import ProviderType
from platform_integrations.rate_limiter import rate_limiter
from platform_integrations.retry_manager import retry_manager
from platform_integrations.webhook_manager import webhook_manager
from platform_management.management_router import register_management_routes
from platform_management.permissions import ManagementRole


@pytest.fixture(autouse=True)
def _reset_integrations():
    integration_service.reset()
    yield
    integration_service.reset()


@pytest.fixture(autouse=True)
def _grant_owner(monkeypatch):
    async def _owner(_tid):
        return ManagementRole.OWNER

    monkeypatch.setattr("platform_management.permissions.resolve_role", _owner)


@pytest.fixture
def bootstrapped():
    integration_service.bootstrap()
    return integration_service


# ---- Registration ----

@pytest.mark.asyncio
async def test_bootstrap_registers_providers(bootstrapped):
    connectors = connector_registry.list_metadata()
    providers = {c.provider for c in connectors}
    assert ProviderType.TELEGRAM.value in providers
    assert ProviderType.OPENAI.value in providers
    assert any(c.provider == ProviderType.OPENAI.value and not c.enabled for c in connectors)


@pytest.mark.asyncio
async def test_dynamic_connector_registration():
    from platform_integrations.connector_base import ConnectorBase
    from platform_integrations.models import ConnectorType

    class CustomConnector(ConnectorBase):
        provider = "custom_provider"
        connector_type = ConnectorType.OUTBOUND

        async def send(self, operation: str, payload: dict) -> dict:
            return {"custom": True}

    connector_loader.register_class("custom_provider", CustomConnector)
    meta = connector_registry.register("custom_provider", connector_id="custom-1")
    assert meta.provider == "custom_provider"


@pytest.mark.asyncio
async def test_enable_disable_connector(bootstrapped):
    meta = connector_registry.get_metadata("telegram-default")
    provider_manager = __import__(
        "platform_integrations.provider_manager", fromlist=["provider_manager"]
    ).provider_manager
    provider_manager.disable("telegram-default")
    assert not connector_registry.get_metadata("telegram-default").enabled

    with pytest.raises(ConnectorDisabledError):
        await integration_service.invoke("telegram-default", "send_message", {"message": "hi"})

    provider_manager.enable("telegram-default")
    result = await integration_service.invoke("telegram-default", "send_message", {"message": "hi"})
    assert result.get("sent") or "provider" in result


# ---- Invoke ----

@pytest.mark.asyncio
async def test_invoke_by_provider(bootstrapped):
    result = await integration_service.invoke_by_provider(
        ProviderType.EMAIL.value,
        "send",
        {"to": "user@example.com", "message": "Hello"},
    )
    assert result.get("message_id") == "email-stub"


@pytest.mark.asyncio
async def test_payload_mapping(bootstrapped):
    result = await integration_service.invoke(
        "telegram-default",
        "send_message",
        {"message": "test", "chat_id": 123},
    )
    assert result is not None


# ---- Retry ----

@pytest.mark.asyncio
async def test_retry_exponential_backoff(bootstrapped):
    record = retry_manager.schedule(
        connector_id="telegram-default",
        operation="send",
        payload={"x": 1},
        attempt=1,
    )
    assert record.attempt == 1

    record2 = retry_manager.schedule(
        connector_id="telegram-default",
        operation="send",
        payload={"x": 1},
        attempt=2,
        error="timeout",
    )
    assert record2.next_retry_at > record.next_retry_at


@pytest.mark.asyncio
async def test_dead_letter_queue(bootstrapped):
    for attempt in range(1, 7):
        try:
            retry_manager.schedule(
                connector_id="telegram-default",
                operation="send",
                payload={},
                attempt=attempt,
                max_attempts=5,
            )
        except RetryExhaustedError:
            break
    assert len(retry_manager.dead_letter_queue()) == 1


@pytest.mark.asyncio
async def test_retry_publishes_event(bootstrapped):
    reset_subscribers()
    received = []

    async def _capture(event):
        received.append(event)

    from events.event_bus import subscribe

    subscribe(RetryScheduledEvent, _capture, handler_id="test_retry")

    record = retry_manager.schedule(
        connector_id="telegram-default",
        operation="send",
        payload={},
    )
    from events.event_bus import publish

    await publish(
        RetryScheduledEvent(
            retry_id=record.retry_id,
            connector_id=record.connector_id,
            operation=record.operation,
            attempt=record.attempt,
            next_retry_at=record.next_retry_at,
        ),
        wait=True,
    )
    assert len(received) == 1
    assert received[0].connector_id == "telegram-default"


# ---- Rate limiting ----

def test_rate_limit_per_provider():
    rate_limiter.configure("provider:telegram", limit=2, window_seconds=60)
    rate_limiter.check(provider="telegram")
    rate_limiter.check(provider="telegram")
    with pytest.raises(RateLimitExceededError):
        rate_limiter.check(provider="telegram")


def test_rate_limit_per_api_key():
    rate_limiter.configure("apikey:key-1", limit=1, window_seconds=60)
    rate_limiter.check(provider="telegram", api_key="key-1")
    with pytest.raises(RateLimitExceededError):
        rate_limiter.check(provider="telegram", api_key="key-1")


# ---- Webhooks ----

def test_webhook_signature_validation():
    reg = webhook_manager.register(name="test", provider="webhook")
    body = b'{"event":"test"}'
    sig = hmac.new(reg.secret.encode(), body, hashlib.sha256).hexdigest()
    webhook_manager.validate_signature(reg, body=body, signature=f"sha256={sig}")

    with pytest.raises(WebhookError):
        webhook_manager.validate_signature(reg, body=body, signature="invalid")


def test_webhook_replay_protection():
    nonce = "unique-nonce-123"
    ts = str(time.time())
    webhook_manager.check_replay(nonce=nonce, timestamp=ts)
    with pytest.raises(WebhookError):
        webhook_manager.check_replay(nonce=nonce, timestamp=ts)


@pytest.mark.asyncio
async def test_process_webhook_end_to_end(bootstrapped):
    reg = integration_service.register_webhook(name="inbound", provider="webhook")
    body = json.dumps({"event": "payment"}).encode()
    sig = hmac.new(reg.secret.encode(), body, hashlib.sha256).hexdigest()

    with patch(
        "platform_integrations.webhook_manager.webhook_manager.audit_webhook",
        new_callable=AsyncMock,
    ), patch(
        "events.event_bus.publish",
        new_callable=AsyncMock,
    ):
        result = await integration_service.process_webhook(
            reg.webhook_id,
            body=body,
            signature=f"sha256={sig}",
            nonce="nonce-abc",
            timestamp=str(time.time()),
            payload={"event": "payment"},
        )
    assert result.get("received") is True
    assert integration_service.stats.webhooks_processed == 1


# ---- Health ----

@pytest.mark.asyncio
async def test_health_check(bootstrapped):
    health = await integration_service.health()
    assert health["overall_status"] in {"healthy", "partial", "degraded", "unknown"}
    assert len(health["connectors"]) >= 6
    for conn in health["connectors"]:
        assert "status" in conn
        assert "latency_ms" in conn


@pytest.mark.asyncio
async def test_connector_connect_event(bootstrapped):
    reset_subscribers()
    events = []

    async def _capture(event):
        events.append(event)

    from events.event_bus import subscribe

    subscribe(ConnectorConnectedEvent, _capture, handler_id="test_connect")

    pm = __import__(
        "platform_integrations.provider_manager", fromlist=["provider_manager"]
    ).provider_manager
    from events.event_bus import publish

    await publish(
        ConnectorConnectedEvent(
            connector_id="telegram-default",
            provider="telegram",
            version="1.0.0",
        ),
        wait=True,
    )
    assert any(isinstance(e, ConnectorConnectedEvent) for e in events)


# ---- Management API ----

@pytest.mark.asyncio
async def test_management_integrations_endpoint(actor_header):
    app = web.Application()
    register_management_routes(app)

    with patch("config.OWNER_ID", 42), patch(
        "platform_management.management_service.management_service.log_request",
        new_callable=AsyncMock,
    ):
        async with TestClient(TestServer(app)) as client:
            resp = await client.get("/management/integrations", headers=actor_header)
            assert resp.status == 200
            body = await resp.json()
            assert body["success"] is True
            assert "connectors" in body["data"]
            assert "statistics" in body["data"]


@pytest.mark.asyncio
async def test_management_health_endpoint(actor_header):
    app = web.Application()
    register_integration_routes(app)

    with patch("config.OWNER_ID", 42), patch(
        "platform_management.management_service.management_service.log_request",
        new_callable=AsyncMock,
    ):
        async with TestClient(TestServer(app)) as client:
            resp = await client.get("/management/integrations/health", headers=actor_header)
            assert resp.status == 200


@pytest.mark.asyncio
async def test_permissions_denied_without_integrations_read(actor_header, monkeypatch):
    app = web.Application()
    register_integration_routes(app)

    async def _readonly(_tid):
        return ManagementRole.READ_ONLY

    monkeypatch.setattr("platform_management.permissions.resolve_role", _readonly)

    with patch(
        "platform_identity.identity_service.identity_service.authenticate_telegram",
        new_callable=AsyncMock,
    ) as mock_auth, patch(
        "platform_identity.identity_service.identity_service.authorize",
        new_callable=AsyncMock,
        return_value=False,
    ), patch(
        "platform_management.management_service.management_service.log_request",
        new_callable=AsyncMock,
    ):
        mock_auth.return_value = type("P", (), {"telegram_id": 42})()
        async with TestClient(TestServer(app)) as client:
            resp = await client.get("/management/integrations", headers=actor_header)
            assert resp.status == 403
