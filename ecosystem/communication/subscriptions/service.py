# Subscription management for pub/sub topics.

from __future__ import annotations

from ecosystem.communication.models import Subscription
from ecosystem.shared.exceptions import NotFoundError, ValidationError
from ecosystem.shared.store import EcosystemStore, ecosystem_store


class SubscriptionService:
    def __init__(self, store: EcosystemStore | None = None) -> None:
        self._store = store or ecosystem_store

    def subscribe(
        self,
        application_id: str,
        topic: str,
        *,
        event_filter: str = "",
    ) -> Subscription:
        if not application_id or not topic:
            raise ValidationError("application_id and topic are required")
        existing = next(
            (
                s
                for s in self._store.subscriptions.list_all()
                if s.application_id == application_id and s.topic == topic and s.is_active
            ),
            None,
        )
        if existing:
            return existing
        subscription = Subscription(
            application_id=application_id,
            topic=topic,
            event_filter=event_filter,
        )
        self._store.subscriptions.save(subscription.subscription_id, subscription)
        return subscription

    def unsubscribe(self, subscription_id: str) -> Subscription:
        subscription = self.get(subscription_id)
        subscription.is_active = False
        self._store.subscriptions.save(subscription_id, subscription)
        return subscription

    def get(self, subscription_id: str) -> Subscription:
        subscription = self._store.subscriptions.get(subscription_id)
        if subscription is None:
            raise NotFoundError("Subscription", subscription_id)
        return subscription

    def list_for_application(self, application_id: str) -> list[Subscription]:
        return [s for s in self._store.subscriptions.list_all() if s.application_id == application_id and s.is_active]

    def list_for_topic(self, topic: str) -> list[Subscription]:
        return [s for s in self._store.subscriptions.list_all() if s.topic == topic and s.is_active]

    def list_all(self) -> list[Subscription]:
        return [s for s in self._store.subscriptions.list_all() if s.is_active]


subscription_service = SubscriptionService()
