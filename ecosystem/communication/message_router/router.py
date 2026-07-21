# Message router — routing, priority queues, DLQ, retries, delivery confirmation.

from __future__ import annotations

import time
from typing import Any

from events.publisher import publish

from ecosystem.communication.events import MessageDeliveredEvent
from ecosystem.communication.models import (
    DeliveryConfirmation,
    DeliveryStatus,
    Envelope,
    MessagePriority,
    MessageType,
)
from ecosystem.config import DEFAULT_CONFIG
from ecosystem.shared.exceptions import NotFoundError, ValidationError
from ecosystem.shared.store import EcosystemStore, ecosystem_store


PRIORITY_ORDER = {
    MessagePriority.CRITICAL: 0,
    MessagePriority.HIGH: 1,
    MessagePriority.NORMAL: 2,
    MessagePriority.LOW: 3,
}


class MessageRouter:
    """Routes messages between applications with retry and dead-letter support."""

    def __init__(self, store: EcosystemStore | None = None) -> None:
        self._store = store or ecosystem_store
        self._pending: list[str] = []

    async def send(
        self,
        *,
        message_type: MessageType,
        source_application: str,
        target_application: str = "",
        payload: dict[str, Any],
        topic: str = "",
        priority: MessagePriority = MessagePriority.NORMAL,
        correlation_id: str = "",
        reply_to: str = "",
        headers: dict[str, str] | None = None,
    ) -> Envelope:
        if not source_application:
            raise ValidationError("source_application is required")
        envelope = Envelope(
            message_type=message_type,
            source_application=source_application,
            target_application=target_application,
            topic=topic,
            payload=payload,
            priority=priority,
            correlation_id=correlation_id,
            reply_to=reply_to,
            headers=headers or {},
            max_retries=DEFAULT_CONFIG.default_max_retries,
        )
        self._store.envelopes.save(envelope.message_id, envelope)
        self._pending.append(envelope.message_id)
        return await self.route(envelope.message_id)

    async def request(
        self,
        source_application: str,
        target_application: str,
        payload: dict[str, Any],
        *,
        topic: str = "request",
    ) -> Envelope:
        return await self.send(
            message_type=MessageType.REQUEST,
            source_application=source_application,
            target_application=target_application,
            payload=payload,
            topic=topic,
            priority=MessagePriority.HIGH,
        )

    async def respond(self, request_id: str, payload: dict[str, Any], *, source_application: str = "") -> Envelope:
        request = self.get_message(request_id)
        return await self.send(
            message_type=MessageType.RESPONSE,
            source_application=source_application or request.target_application,
            target_application=request.source_application,
            payload=payload,
            topic="response",
            correlation_id=request.message_id,
            reply_to=request.message_id,
        )

    async def publish_subscribe(
        self,
        source_application: str,
        topic: str,
        payload: dict[str, Any],
        *,
        priority: MessagePriority = MessagePriority.NORMAL,
    ) -> Envelope:
        return await self.send(
            message_type=MessageType.EVENT,
            source_application=source_application,
            payload=payload,
            topic=topic,
            priority=priority,
        )

    async def broadcast(
        self,
        source_application: str,
        payload: dict[str, Any],
        *,
        topic: str = "broadcast",
    ) -> Envelope:
        return await self.send(
            message_type=MessageType.BROADCAST,
            source_application=source_application,
            payload=payload,
            topic=topic,
            priority=MessagePriority.HIGH,
        )

    async def direct(
        self,
        source_application: str,
        target_application: str,
        payload: dict[str, Any],
    ) -> Envelope:
        return await self.send(
            message_type=MessageType.DIRECT,
            source_application=source_application,
            target_application=target_application,
            payload=payload,
            topic="direct",
            priority=MessagePriority.NORMAL,
        )

    async def command(
        self,
        source_application: str,
        target_application: str,
        command_name: str,
        payload: dict[str, Any],
    ) -> Envelope:
        return await self.send(
            message_type=MessageType.COMMAND,
            source_application=source_application,
            target_application=target_application,
            payload={"command": command_name, **payload},
            topic=f"command.{command_name}",
            priority=MessagePriority.HIGH,
        )

    async def query(
        self,
        source_application: str,
        target_application: str,
        query_name: str,
        payload: dict[str, Any],
    ) -> Envelope:
        return await self.send(
            message_type=MessageType.QUERY,
            source_application=source_application,
            target_application=target_application,
            payload={"query": query_name, **payload},
            topic=f"query.{query_name}",
            priority=MessagePriority.NORMAL,
        )

    async def route(self, message_id: str) -> Envelope:
        envelope = self.get_message(message_id)
        targets = self._resolve_targets(envelope)
        if not targets and envelope.message_type not in (MessageType.BROADCAST, MessageType.EVENT):
            return await self._fail_or_retry(envelope, "No route target")

        envelope.status = DeliveryStatus.ROUTED
        self._store.envelopes.save(envelope.message_id, envelope)

        for target in targets:
            confirmation = DeliveryConfirmation(
                message_id=envelope.message_id,
                application_id=target,
                status=DeliveryStatus.DELIVERED,
            )
            self._store.delivery_confirmations.save(confirmation.confirmation_id, confirmation)
            await publish(
                MessageDeliveredEvent(
                    message_id=envelope.message_id,
                    target_application=target,
                    message_type=envelope.message_type.value,
                )
            )

        envelope.status = DeliveryStatus.DELIVERED
        envelope.delivered_at = time.time()
        if envelope.message_id in self._pending:
            self._pending.remove(envelope.message_id)
        self._store.envelopes.save(envelope.message_id, envelope)
        return envelope

    def acknowledge(self, message_id: str, application_id: str) -> DeliveryConfirmation:
        envelope = self.get_message(message_id)
        confirmation = DeliveryConfirmation(
            message_id=message_id,
            application_id=application_id,
            status=DeliveryStatus.ACKNOWLEDGED,
        )
        self._store.delivery_confirmations.save(confirmation.confirmation_id, confirmation)
        envelope.status = DeliveryStatus.ACKNOWLEDGED
        self._store.envelopes.save(message_id, envelope)
        return confirmation

    def pending_queue(self) -> list[Envelope]:
        messages = [self.get_message(mid) for mid in list(self._pending) if self._store.envelopes.get(mid)]
        return sorted(messages, key=lambda m: PRIORITY_ORDER.get(m.priority, 99))

    def dead_letters(self) -> list[Envelope]:
        return self._store.dead_letters.list_all()

    def confirmations(self, message_id: str) -> list[DeliveryConfirmation]:
        return [c for c in self._store.delivery_confirmations.list_all() if c.message_id == message_id]

    def get_message(self, message_id: str) -> Envelope:
        envelope = self._store.envelopes.get(message_id)
        if envelope is None:
            raise NotFoundError("Message", message_id)
        return envelope

    def discover_route(self, capability: str) -> list[str]:
        apps = []
        for reg in self._store.registrations.list_all():
            if capability in reg.capabilities and reg.is_connected:
                apps.append(reg.application_id)
        return apps

    def _resolve_targets(self, envelope: Envelope) -> list[str]:
        if envelope.target_application:
            return [envelope.target_application]
        if envelope.message_type == MessageType.BROADCAST:
            return [
                r.application_id
                for r in self._store.registrations.list_all()
                if r.is_connected and r.application_id != envelope.source_application
            ]
        if envelope.topic:
            return [
                s.application_id
                for s in self._store.subscriptions.list_all()
                if s.is_active and s.topic in (envelope.topic, "*") and s.application_id != envelope.source_application
            ]
        return []

    async def _fail_or_retry(self, envelope: Envelope, reason: str) -> Envelope:
        envelope.retry_count += 1
        envelope.headers["last_error"] = reason
        if envelope.retry_count > envelope.max_retries:
            envelope.status = DeliveryStatus.DEAD_LETTER
            self._store.dead_letters.save(envelope.message_id, envelope)
            if envelope.message_id in self._pending:
                self._pending.remove(envelope.message_id)
        else:
            envelope.status = DeliveryStatus.FAILED
        self._store.envelopes.save(envelope.message_id, envelope)
        return envelope


message_router = MessageRouter()
