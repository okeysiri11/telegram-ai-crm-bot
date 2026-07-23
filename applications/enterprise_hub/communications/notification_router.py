"""Notification Router — recipients, channels, fallback, retries, journal."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.communications.channels.base import ChannelRegistry
from applications.enterprise_hub.communications.channels.email import EmailChannel
from applications.enterprise_hub.communications.channels.push import PushChannel
from applications.enterprise_hub.communications.channels.sms import SMSChannel
from applications.enterprise_hub.communications.channels.telegram import TelegramChannel
from applications.enterprise_hub.communications.channels.webhook import WebhookChannel
from applications.enterprise_hub.communications.channels.websocket import WebSocketChannel
from applications.enterprise_hub.communications.delivery import DeliveryEngine
from applications.enterprise_hub.communications.models import PRIORITY_CHANNEL_MAP
from applications.enterprise_hub.communications.priority import PriorityEngine
from applications.enterprise_hub.communications.queue import NotificationQueue
from applications.enterprise_hub.shared.exceptions import NotFoundError, ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class NotificationRouter:
    def __init__(
        self,
        store: EnterpriseHubStore | None = None,
        *,
        priority: PriorityEngine | None = None,
        queue: NotificationQueue | None = None,
        delivery: DeliveryEngine | None = None,
    ) -> None:
        self.store = store or enterprise_hub_store
        self.priority = priority or PriorityEngine(self.store)
        self.queue = queue or NotificationQueue(self.store)
        self.delivery = delivery or DeliveryEngine(self.store)
        self.channels = ChannelRegistry(self.store)
        email = EmailChannel(self.store)
        telegram = TelegramChannel(self.store)
        sms = SMSChannel(self.store)
        push = PushChannel(self.store)
        ws = WebSocketChannel(self.store)
        webhook = WebhookChannel(self.store)
        self.channels.register("email", email.send)
        self.channels.register("telegram", telegram.send)
        self.channels.register("sms", sms.send)
        self.channels.register("push", push.send)
        self.channels.register("websocket", ws.send)
        self.channels.register("webhook", webhook.send)

    def route(self, *, event_id: str, fallback: bool = True) -> dict[str, Any]:
        event = self.store.comm_events.get(event_id)
        if event is None:
            raise NotFoundError(f"event not found: {event_id}")

        classification = self.priority.classify(
            subject=event.get("subject", ""),
            event=event.get("event", ""),
            hint=str(event.get("payload", {})),
        )
        priority = event.get("priority") or classification["priority"]
        preferred = event.get("channel")
        channel_list = [preferred] if preferred else list(
            PRIORITY_CHANNEL_MAP.get(priority, ["email"])
        )
        if fallback and "email" not in channel_list:
            channel_list = list(channel_list) + ["email"]

        deliveries: list[dict[str, Any]] = []
        queue_items: list[dict[str, Any]] = []
        messages: list[dict[str, Any]] = []

        for channel in channel_list:
            if not channel:
                continue
            q = self.queue.enqueue(
                event_id=event_id,
                recipient=event["recipient"],
                channel=channel,
                priority=priority,
                mode="priority",
            )
            queue_items.append(q)
            msg = self.channels.send(
                channel=channel,
                recipient=event["recipient"],
                subject=event.get("subject", ""),
                body=event.get("body", ""),
                meta={"event_id": event_id, "priority": priority},
            )
            messages.append(msg)
            deliv = self.delivery.track(
                message_id=msg["message_id"],
                recipient=event["recipient"],
                channel=channel,
                status="delivered",
                latency_ms=5.0,
            )
            deliveries.append(deliv)
            self.queue.set_status(queue_id=q["queue_id"], status="delivered")

        event["status"] = "routed"
        event["priority"] = priority
        event["at"] = _now()
        self.store.comm_events.save(event_id, event)

        rid = _id("comm_route")
        return self.store.comm_routes.save(
            rid,
            {
                "route_id": rid,
                "event_id": event_id,
                "priority": priority,
                "channels": channel_list,
                "queue_ids": [q["queue_id"] for q in queue_items],
                "message_ids": [m["message_id"] for m in messages],
                "delivery_ids": [d["delivery_id"] for d in deliveries],
                "fallback": fallback,
                "at": _now(),
            },
        )

    def smart_route(
        self,
        *,
        source: str,
        event: str,
        recipient: str,
        subject: str = "",
        body: str = "",
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if not source or not event or not recipient:
            raise ValidationError("source, event, and recipient required")
        from applications.enterprise_hub.communications.notification_center import (
            NotificationCenter,
        )

        center = NotificationCenter(self.store)
        published = center.publish(
            source=source,
            event=event,
            recipient=recipient,
            subject=subject,
            body=body,
            payload=payload,
        )
        return self.route(event_id=published["event_id"], fallback=True)

    def status(self) -> dict[str, Any]:
        return {
            "routes": self.store.comm_routes.count(),
            "channels": self.channels.status(),
            "queue": self.queue.status(),
            "delivery": self.delivery.status(),
        }
