# Outbound webhook subscriptions and delivery (partner integrations).

from __future__ import annotations

from events.publisher import publish

from applications.agro_marketplace.portal.events import WebhookTriggeredEvent
from applications.agro_marketplace.portal.models import WebhookSubscription
from applications.agro_marketplace.shared.exceptions import NotFoundError, ValidationError
from applications.agro_marketplace.shared.store import AgroStore, agro_store


class WebhooksService:
    def __init__(self, store: AgroStore | None = None) -> None:
        self._store = store or agro_store

    def subscribe(self, subscription: WebhookSubscription) -> WebhookSubscription:
        if not subscription.target_url:
            raise ValidationError("target_url is required")
        if not subscription.event_types:
            raise ValidationError("event_types required")
        return self._store.webhook_subscriptions.save(subscription.subscription_id, subscription)

    def list_subscriptions(self, *, partner_id: str | None = None) -> list[WebhookSubscription]:
        items = self._store.webhook_subscriptions.list_all()
        if partner_id:
            items = [s for s in items if s.partner_id == partner_id]
        return items

    def get(self, subscription_id: str) -> WebhookSubscription:
        sub = self._store.webhook_subscriptions.get(subscription_id)
        if sub is None:
            raise NotFoundError("WebhookSubscription", subscription_id)
        return sub

    async def trigger(self, event_type: str, payload: dict) -> list[dict]:
        deliveries = []
        for sub in self.list_subscriptions():
            if not sub.is_active:
                continue
            if event_type not in sub.event_types and "*" not in sub.event_types:
                continue
            delivery = {
                "subscription_id": sub.subscription_id,
                "target_url": sub.target_url,
                "event_type": event_type,
                "payload": payload,
                "status": "delivered",
            }
            self._store.webhook_deliveries.save(
                f"{sub.subscription_id}:{event_type}:{len(deliveries)}",
                delivery,
            )
            await publish(
                WebhookTriggeredEvent(
                    subscription_id=sub.subscription_id,
                    event_type=event_type,
                    target_url=sub.target_url,
                )
            )
            deliveries.append(delivery)
        return deliveries


webhooks_service = WebhooksService()
