# Webhook Engine v1 repositories.

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.webhook_engine import (
    WebhookDelivery,
    WebhookDeliveryStatus,
    WebhookFailure,
    WebhookRetry,
    WebhookRetryStatus,
    WebhookSubscription,
    WebhookSubscriptionStatus,
)


class WebhookSubscriptionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        name: str,
        target_url: str,
        secret: str,
        event_types: list[str] | None = None,
        event_version: str = "v1",
        owner_user_id: int | None = None,
        description: str | None = None,
        metadata: dict | None = None,
        status: str = WebhookSubscriptionStatus.ACTIVE.value,
        **extra: Any,
    ) -> WebhookSubscription:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")
        if status not in {s.value for s in WebhookSubscriptionStatus}:
            raise ValueError(f"Invalid status: {status}")

        subscription = WebhookSubscription(
            name=name,
            target_url=target_url,
            secret=secret,
            event_types=event_types or [],
            event_version=event_version,
            owner_user_id=owner_user_id,
            description=description,
            metadata_=metadata,
            status=status,
        )
        self._session.add(subscription)
        await self._session.flush()
        return subscription

    async def get_by_id(self, subscription_id: uuid.UUID) -> WebhookSubscription | None:
        result = await self._session.execute(
            select(WebhookSubscription).where(WebhookSubscription.id == subscription_id)
        )
        return result.scalar_one_or_none()

    async def list_active(self) -> list[WebhookSubscription]:
        result = await self._session.execute(
            select(WebhookSubscription)
            .where(WebhookSubscription.status == WebhookSubscriptionStatus.ACTIVE.value)
            .order_by(WebhookSubscription.created_at.asc())
        )
        return list(result.scalars().all())

    async def list_for_event_type(self, event_type: str) -> list[WebhookSubscription]:
        active = await self.list_active()
        matched: list[WebhookSubscription] = []
        for subscription in active:
            types = subscription.event_types or []
            if not types or event_type in types:
                matched.append(subscription)
        return matched

    async def update_status(
        self,
        subscription_id: uuid.UUID,
        status: str,
    ) -> WebhookSubscription | None:
        subscription = await self.get_by_id(subscription_id)
        if subscription is None:
            return None
        if status not in {s.value for s in WebhookSubscriptionStatus}:
            raise ValueError(f"Invalid status: {status}")
        subscription.status = status
        await self._session.flush()
        return subscription


class WebhookDeliveryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        subscription_id: uuid.UUID,
        event_type: str,
        payload: dict,
        event_version: str = "v1",
        source_event_id: uuid.UUID | None = None,
        signature: str | None = None,
        status: str = WebhookDeliveryStatus.PENDING.value,
        **extra: Any,
    ) -> WebhookDelivery:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")

        delivery = WebhookDelivery(
            subscription_id=subscription_id,
            source_event_id=source_event_id,
            event_type=event_type,
            event_version=event_version,
            payload=payload,
            signature=signature,
            status=status,
        )
        self._session.add(delivery)
        await self._session.flush()
        return delivery

    async def get_by_id(self, delivery_id: uuid.UUID) -> WebhookDelivery | None:
        result = await self._session.execute(
            select(WebhookDelivery).where(WebhookDelivery.id == delivery_id)
        )
        return result.scalar_one_or_none()

    async def list_by_subscription(
        self,
        subscription_id: uuid.UUID,
        *,
        limit: int = 50,
    ) -> list[WebhookDelivery]:
        result = await self._session.execute(
            select(WebhookDelivery)
            .where(WebhookDelivery.subscription_id == subscription_id)
            .order_by(WebhookDelivery.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def list_dead_letter(
        self,
        *,
        subscription_id: uuid.UUID | None = None,
        limit: int = 50,
    ) -> list[WebhookDelivery]:
        query = select(WebhookDelivery).where(
            WebhookDelivery.status == WebhookDeliveryStatus.DEAD_LETTER.value
        )
        if subscription_id is not None:
            query = query.where(WebhookDelivery.subscription_id == subscription_id)
        result = await self._session.execute(
            query.order_by(WebhookDelivery.updated_at.desc()).limit(limit)
        )
        return list(result.scalars().all())


class WebhookFailureRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        delivery_id: uuid.UUID,
        subscription_id: uuid.UUID,
        attempt_number: int,
        error_message: str,
        http_status: int | None = None,
        is_terminal: bool = False,
        **extra: Any,
    ) -> WebhookFailure:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")

        failure = WebhookFailure(
            delivery_id=delivery_id,
            subscription_id=subscription_id,
            attempt_number=attempt_number,
            error_message=error_message,
            http_status=http_status,
            is_terminal=is_terminal,
        )
        self._session.add(failure)
        await self._session.flush()
        return failure

    async def list_for_delivery(self, delivery_id: uuid.UUID) -> list[WebhookFailure]:
        result = await self._session.execute(
            select(WebhookFailure)
            .where(WebhookFailure.delivery_id == delivery_id)
            .order_by(WebhookFailure.attempt_number.asc())
        )
        return list(result.scalars().all())


class WebhookRetryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        delivery_id: uuid.UUID,
        attempt_number: int,
        scheduled_at: datetime,
        status: str = WebhookRetryStatus.PENDING.value,
        **extra: Any,
    ) -> WebhookRetry:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")

        retry = WebhookRetry(
            delivery_id=delivery_id,
            attempt_number=attempt_number,
            scheduled_at=scheduled_at,
            status=status,
        )
        self._session.add(retry)
        await self._session.flush()
        return retry

    async def get_by_id(self, retry_id: uuid.UUID) -> WebhookRetry | None:
        result = await self._session.execute(
            select(WebhookRetry).where(WebhookRetry.id == retry_id)
        )
        return result.scalar_one_or_none()

    async def claim_due(
        self,
        *,
        now: datetime,
        limit: int = 50,
    ) -> list[WebhookRetry]:
        result = await self._session.execute(
            select(WebhookRetry)
            .where(
                WebhookRetry.status == WebhookRetryStatus.PENDING.value,
                WebhookRetry.scheduled_at <= now,
            )
            .order_by(WebhookRetry.scheduled_at.asc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def mark_completed(
        self,
        retry: WebhookRetry,
        *,
        completed_at: datetime,
    ) -> None:
        retry.status = WebhookRetryStatus.COMPLETED.value
        retry.completed_at = completed_at

    async def mark_dead_letter(
        self,
        retry: WebhookRetry,
        *,
        completed_at: datetime,
        error_message: str | None = None,
    ) -> None:
        retry.status = WebhookRetryStatus.DEAD_LETTER.value
        retry.completed_at = completed_at
        retry.error_message = error_message
