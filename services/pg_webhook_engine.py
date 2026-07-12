# Webhook Engine v1 — subscriptions, signed delivery, retries, dead letter queue.

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import aiohttp

from config import OWNER_ID
from database.models.audit_log import AuditAction
from database.models.webhook_engine import (
    WebhookDeliveryStatus,
    WebhookRetryStatus,
    WebhookSubscriptionStatus,
)
from database.session import get_session
from repositories.audit_repository import AuditRepository
from repositories.user_role_repository import UserRoleRepository
from repositories.webhook_engine_repository import (
    WebhookDeliveryRepository,
    WebhookFailureRepository,
    WebhookRetryRepository,
    WebhookSubscriptionRepository,
)
from services import crm_event_bus as event_bus

logger = logging.getLogger(__name__)

WEBHOOK_ROLES = frozenset({"OWNER", "ADMIN", "MANAGER"})

WEBHOOK_PUBLIC_EVENTS = frozenset({
    "deal.created",
    "deal.updated",
    "vehicle.sold",
    "vehicle.imported",
    "payment.completed",
    "settlement.completed",
})

SOURCE_EVENT_MAP: dict[str, str] = {
    "vehicle.import.completed": "vehicle.imported",
    "payment.received": "payment.completed",
}

SUBSCRIBE_SOURCE_EVENTS = frozenset(WEBHOOK_PUBLIC_EVENTS) | frozenset(SOURCE_EVENT_MAP)

MAX_DELIVERY_ATTEMPTS = 5
RETRY_DELAYS_SECONDS = (60, 300, 900, 3600)
HTTP_TIMEOUT_SECONDS = 15
RESPONSE_BODY_MAX_LEN = 4096

_handlers_registered = False


class WebhookEngineError(Exception):
    pass


class WebhookEngineV1:
    @staticmethod
    async def user_can_access(user_id: int) -> bool:
        if user_id == OWNER_ID:
            return True
        async with get_session() as session:
            roles = await UserRoleRepository(session).get_user_roles(user_id)
            return any(role.code in WEBHOOK_ROLES for role in roles)

    @staticmethod
    def _subscription_snapshot(subscription) -> dict[str, Any]:
        return {
            "id": str(subscription.id),
            "name": subscription.name,
            "target_url": subscription.target_url,
            "event_types": subscription.event_types or [],
            "event_version": subscription.event_version,
            "status": subscription.status,
            "owner_user_id": subscription.owner_user_id,
            "description": subscription.description,
            "created_at": subscription.created_at.isoformat(),
            "updated_at": subscription.updated_at.isoformat(),
        }

    @staticmethod
    def _delivery_snapshot(delivery) -> dict[str, Any]:
        return {
            "id": str(delivery.id),
            "subscription_id": str(delivery.subscription_id),
            "source_event_id": str(delivery.source_event_id)
            if delivery.source_event_id
            else None,
            "event_type": delivery.event_type,
            "event_version": delivery.event_version,
            "status": delivery.status,
            "attempt_count": delivery.attempt_count,
            "http_status": delivery.http_status,
            "delivered_at": delivery.delivered_at.isoformat()
            if delivery.delivered_at
            else None,
            "next_retry_at": delivery.next_retry_at.isoformat()
            if delivery.next_retry_at
            else None,
            "created_at": delivery.created_at.isoformat(),
        }

    @staticmethod
    def _normalize_event_type(source_event_type: str) -> str | None:
        webhook_type = SOURCE_EVENT_MAP.get(source_event_type, source_event_type)
        if webhook_type not in WEBHOOK_PUBLIC_EVENTS:
            return None
        return webhook_type

    @staticmethod
    def _build_envelope(
        *,
        delivery_id: uuid.UUID,
        event_type: str,
        event_version: str,
        aggregate_type: str,
        aggregate_id: uuid.UUID,
        payload: dict[str, Any],
        source_event_id: uuid.UUID | None,
    ) -> dict[str, Any]:
        return {
            "id": str(delivery_id),
            "event_type": event_type,
            "event_version": event_version,
            "aggregate_type": aggregate_type,
            "aggregate_id": str(aggregate_id),
            "source_event_id": str(source_event_id) if source_event_id else None,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "data": payload,
        }

    @staticmethod
    def sign_payload(secret: str, timestamp: str, body: str) -> str:
        message = f"{timestamp}.{body}".encode("utf-8")
        digest = hmac.new(secret.encode("utf-8"), message, hashlib.sha256).hexdigest()
        return f"sha256={digest}"

    @staticmethod
    def verify_signature(
        secret: str,
        timestamp: str,
        body: str,
        signature_header: str,
    ) -> bool:
        expected = WebhookEngineV1.sign_payload(secret, timestamp, body)
        return hmac.compare_digest(expected, signature_header)

    @staticmethod
    async def create_subscription(
        *,
        actor_id: int,
        name: str,
        target_url: str,
        event_types: list[str] | None = None,
        event_version: str = "v1",
        description: str | None = None,
        owner_user_id: int | None = None,
        secret: str | None = None,
    ) -> dict[str, Any]:
        if not await WebhookEngineV1.user_can_access(actor_id):
            raise WebhookEngineError("Access denied")

        normalized_types = event_types or []
        for event_type in normalized_types:
            if event_type not in WEBHOOK_PUBLIC_EVENTS:
                raise WebhookEngineError(f"Unsupported event type: {event_type}")

        generated_secret = secret or secrets.token_hex(32)

        async with get_session() as session:
            repo = WebhookSubscriptionRepository(session)
            subscription = await repo.create(
                name=name,
                target_url=target_url,
                secret=generated_secret,
                event_types=normalized_types,
                event_version=event_version,
                description=description,
                owner_user_id=owner_user_id or actor_id,
            )
            await AuditRepository(session).create_log(
                user_id=actor_id,
                entity_type="webhook_subscription",
                entity_id=str(subscription.id),
                action=AuditAction.CREATE.value,
                new_value={"name": name, "target_url": target_url},
            )
            snapshot = WebhookEngineV1._subscription_snapshot(subscription)
            snapshot["secret"] = generated_secret
            return snapshot

    @staticmethod
    async def list_subscriptions(*, actor_id: int) -> list[dict[str, Any]]:
        if not await WebhookEngineV1.user_can_access(actor_id):
            raise WebhookEngineError("Access denied")

        async with get_session() as session:
            subscriptions = await WebhookSubscriptionRepository(session).list_active()
            return [
                WebhookEngineV1._subscription_snapshot(subscription)
                for subscription in subscriptions
            ]

    @staticmethod
    async def deactivate_subscription(
        *,
        actor_id: int,
        subscription_id: uuid.UUID,
    ) -> dict[str, Any]:
        if not await WebhookEngineV1.user_can_access(actor_id):
            raise WebhookEngineError("Access denied")

        async with get_session() as session:
            repo = WebhookSubscriptionRepository(session)
            subscription = await repo.update_status(
                subscription_id,
                WebhookSubscriptionStatus.REVOKED.value,
            )
            if subscription is None:
                raise WebhookEngineError("Subscription not found")
            await AuditRepository(session).create_log(
                user_id=actor_id,
                entity_type="webhook_subscription",
                entity_id=str(subscription.id),
                action=AuditAction.UPDATE.value,
                new_value={"status": subscription.status},
            )
            return WebhookEngineV1._subscription_snapshot(subscription)

    @staticmethod
    async def list_deliveries(
        *,
        actor_id: int,
        subscription_id: uuid.UUID,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        if not await WebhookEngineV1.user_can_access(actor_id):
            raise WebhookEngineError("Access denied")

        async with get_session() as session:
            deliveries = await WebhookDeliveryRepository(session).list_by_subscription(
                subscription_id,
                limit=limit,
            )
            return [WebhookEngineV1._delivery_snapshot(delivery) for delivery in deliveries]

    @staticmethod
    async def list_dead_letter(
        *,
        actor_id: int,
        subscription_id: uuid.UUID | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        if not await WebhookEngineV1.user_can_access(actor_id):
            raise WebhookEngineError("Access denied")

        async with get_session() as session:
            deliveries = await WebhookDeliveryRepository(session).list_dead_letter(
                subscription_id=subscription_id,
                limit=limit,
            )
            return [WebhookEngineV1._delivery_snapshot(delivery) for delivery in deliveries]

    @staticmethod
    async def dispatch_platform_event(
        *,
        source_event_type: str,
        aggregate_type: str,
        aggregate_id: uuid.UUID,
        payload: dict[str, Any] | None,
        source_event_id: uuid.UUID | None = None,
    ) -> list[uuid.UUID]:
        webhook_event_type = WebhookEngineV1._normalize_event_type(source_event_type)
        if webhook_event_type is None:
            return []

        async with get_session() as session:
            subscriptions = await WebhookSubscriptionRepository(session).list_for_event_type(
                webhook_event_type
            )
            if not subscriptions:
                return []

            delivery_ids: list[uuid.UUID] = []
            delivery_repo = WebhookDeliveryRepository(session)
            for subscription in subscriptions:
                delivery = await delivery_repo.create(
                    subscription_id=subscription.id,
                    source_event_id=source_event_id,
                    event_type=webhook_event_type,
                    event_version=subscription.event_version,
                    payload={},
                )
                envelope = WebhookEngineV1._build_envelope(
                    delivery_id=delivery.id,
                    event_type=webhook_event_type,
                    event_version=subscription.event_version,
                    aggregate_type=aggregate_type,
                    aggregate_id=aggregate_id,
                    payload=payload or {},
                    source_event_id=source_event_id,
                )
                delivery.payload = envelope
                delivery_ids.append(delivery.id)

            await session.commit()

        for delivery_id in delivery_ids:
            await WebhookEngineV1._attempt_delivery(delivery_id)

        return delivery_ids

    @staticmethod
    async def _attempt_delivery(delivery_id: uuid.UUID) -> bool:
        async with get_session() as session:
            delivery_repo = WebhookDeliveryRepository(session)
            failure_repo = WebhookFailureRepository(session)
            retry_repo = WebhookRetryRepository(session)
            subscription_repo = WebhookSubscriptionRepository(session)

            delivery = await delivery_repo.get_by_id(delivery_id)
            if delivery is None:
                return False
            if delivery.status in {
                WebhookDeliveryStatus.DELIVERED.value,
                WebhookDeliveryStatus.DEAD_LETTER.value,
            }:
                return delivery.status == WebhookDeliveryStatus.DELIVERED.value

            subscription = await subscription_repo.get_by_id(delivery.subscription_id)
            if subscription is None:
                return False
            if subscription.status != WebhookSubscriptionStatus.ACTIVE.value:
                return False

            attempt_number = delivery.attempt_count + 1
            body = json.dumps(delivery.payload, separators=(",", ":"), sort_keys=True)
            timestamp = str(int(datetime.now(timezone.utc).timestamp()))
            signature = WebhookEngineV1.sign_payload(subscription.secret, timestamp, body)

            headers = {
                "Content-Type": "application/json",
                "User-Agent": "TelegramBotCourse-Webhook/1.0",
                "X-Webhook-Signature": signature,
                "X-Webhook-Timestamp": timestamp,
                "X-Webhook-Event-Type": delivery.event_type,
                "X-Webhook-Event-Version": delivery.event_version,
                "X-Webhook-Delivery-Id": str(delivery.id),
            }

            http_status: int | None = None
            response_body: str | None = None
            error_message: str | None = None
            success = False

            try:
                timeout = aiohttp.ClientTimeout(total=HTTP_TIMEOUT_SECONDS)
                async with aiohttp.ClientSession(timeout=timeout) as http:
                    async with http.post(
                        subscription.target_url,
                        data=body,
                        headers=headers,
                    ) as response:
                        http_status = response.status
                        raw_body = await response.text()
                        response_body = raw_body[:RESPONSE_BODY_MAX_LEN]
                        success = 200 <= response.status < 300
                        if not success:
                            error_message = f"HTTP {response.status}: {response_body[:200]}"
            except Exception as exc:
                error_message = str(exc)

            now = datetime.now(timezone.utc)
            delivery.attempt_count = attempt_number
            delivery.signature = signature
            delivery.http_status = http_status
            delivery.response_body = response_body

            if success:
                delivery.status = WebhookDeliveryStatus.DELIVERED.value
                delivery.delivered_at = now
                delivery.next_retry_at = None
                await session.commit()
                return True

            await failure_repo.create(
                delivery_id=delivery.id,
                subscription_id=subscription.id,
                attempt_number=attempt_number,
                error_message=error_message or "Delivery failed",
                http_status=http_status,
                is_terminal=attempt_number >= MAX_DELIVERY_ATTEMPTS,
            )

            if attempt_number >= MAX_DELIVERY_ATTEMPTS:
                delivery.status = WebhookDeliveryStatus.DEAD_LETTER.value
                delivery.next_retry_at = None
                await session.commit()
                logger.warning(
                    "webhook_dead_letter",
                    extra={
                        "delivery_id": str(delivery.id),
                        "subscription_id": str(subscription.id),
                        "event_type": delivery.event_type,
                    },
                )
                return False

            delay_index = min(attempt_number - 1, len(RETRY_DELAYS_SECONDS) - 1)
            next_retry_at = now + timedelta(seconds=RETRY_DELAYS_SECONDS[delay_index])
            delivery.status = WebhookDeliveryStatus.FAILED.value
            delivery.next_retry_at = next_retry_at
            await retry_repo.create(
                delivery_id=delivery.id,
                attempt_number=attempt_number + 1,
                scheduled_at=next_retry_at,
            )
            await session.commit()
            return False

    @staticmethod
    async def process_pending_retries(*, limit: int = 50) -> dict[str, int]:
        stats = {"claimed": 0, "delivered": 0, "failed": 0, "dead_letter": 0}
        now = datetime.now(timezone.utc)

        async with get_session() as session:
            retry_repo = WebhookRetryRepository(session)
            due_retries = await retry_repo.claim_due(now=now, limit=limit)
            stats["claimed"] = len(due_retries)
            retry_items = [(retry.id, retry.delivery_id) for retry in due_retries]
            await session.commit()

        for retry_id, delivery_id in retry_items:
            ok = await WebhookEngineV1._attempt_delivery(delivery_id)
            async with get_session() as session:
                retry_repo = WebhookRetryRepository(session)
                delivery_repo = WebhookDeliveryRepository(session)
                delivery = await delivery_repo.get_by_id(delivery_id)
                retry = await retry_repo.get_by_id(retry_id)
                if retry is None:
                    continue

                completed_at = datetime.now(timezone.utc)
                if ok:
                    await retry_repo.mark_completed(retry, completed_at=completed_at)
                    stats["delivered"] += 1
                elif delivery and delivery.status == WebhookDeliveryStatus.DEAD_LETTER.value:
                    await retry_repo.mark_dead_letter(
                        retry,
                        completed_at=completed_at,
                        error_message="Moved to dead letter queue",
                    )
                    stats["dead_letter"] += 1
                else:
                    stats["failed"] += 1
                await session.commit()

        return stats

    @staticmethod
    async def _on_crm_event(event) -> None:
        await WebhookEngineV1.dispatch_platform_event(
            source_event_type=event.event_type,
            aggregate_type=event.aggregate_type,
            aggregate_id=event.aggregate_id,
            payload=event.payload,
            source_event_id=event.id,
        )

    @staticmethod
    def register_event_handlers() -> None:
        global _handlers_registered
        if _handlers_registered:
            return
        for event_type in SUBSCRIBE_SOURCE_EVENTS:
            event_bus.subscribe(
                event_type,
                WebhookEngineV1._on_crm_event,
                handler_id="webhook_engine_v1",
            )
        _handlers_registered = True
        logger.info(
            "webhook_engine_handlers_registered",
            extra={"event_types": sorted(SUBSCRIBE_SOURCE_EVENTS)},
        )
