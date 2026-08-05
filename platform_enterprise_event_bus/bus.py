"""Enterprise Event Bus engine — Sprint 36.1.

Wraps canonical PlatformEventBus (SoR). Does not replace it.
"""

from __future__ import annotations

import asyncio
import inspect
import logging
import time
import uuid
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any

from events.base_event import BaseEvent
from events.event_bus import PlatformEventBus

from platform_enterprise_event_bus.components import (
    DeadLetterQueue,
    EventAuditLogger,
    EventMetrics,
    EventStore,
    RetryManager,
    TopicManager,
)
from platform_enterprise_event_bus.filters import EventDeserializer, EventFilter, EventSerializer, EventValidator
from platform_enterprise_event_bus.models import (
    DeliveryMode,
    EnterpriseEvent,
    EventPriority,
    Subscription,
)

logger = logging.getLogger(__name__)

Handler = Callable[[EnterpriseEvent], Awaitable[None] | None]


@dataclass
class EnterpriseBusEvent(BaseEvent):
    """Bridge envelope published onto PlatformEventBus SoR."""

    envelope: dict[str, Any] = field(default_factory=dict)

    @property
    def event_type(self) -> str:  # type: ignore[override]
        return "EnterpriseBusEvent"


class EventPublisher:
    def __init__(self, bus: EnterpriseEventBus) -> None:
        self._bus = bus

    async def publish(self, event: EnterpriseEvent | dict[str, Any], **kwargs: Any) -> dict[str, Any]:
        return await self._bus.publish(event, **kwargs)


class EventSubscriber:
    def __init__(self, bus: EnterpriseEventBus) -> None:
        self._bus = bus

    def subscribe(self, **kwargs: Any) -> Subscription:
        return self._bus.subscribe(**kwargs)

    def unsubscribe(self, subscription_id: str) -> bool:
        return self._bus.unsubscribe(subscription_id)


class EventDispatcher:
    def __init__(self, bus: EnterpriseEventBus) -> None:
        self._bus = bus

    async def dispatch(self, event: EnterpriseEvent) -> dict[str, Any]:
        return await self._bus._dispatch(event)


class EventRouter:
    """Routes events to matching subscriptions (topic / type / filters)."""

    def __init__(self, bus: EnterpriseEventBus) -> None:
        self._bus = bus
        self._filter = EventFilter()

    def route(self, event: EnterpriseEvent) -> list[Subscription]:
        return [
            sub
            for sub in self._bus.subscriptions.values()
            if self._filter.matches(event, sub)
        ]


class EventBroker:
    def __init__(self, bus: EnterpriseEventBus) -> None:
        self._bus = bus

    async def broadcast(self, event: EnterpriseEvent) -> dict[str, Any]:
        event.delivery_mode = DeliveryMode.BROADCAST
        return await self._bus.publish(event)

    async def multicast(self, event: EnterpriseEvent, *, targets: list[str]) -> dict[str, Any]:
        event.delivery_mode = DeliveryMode.MULTICAST
        event.metadata["multicast_targets"] = list(targets)
        return await self._bus.publish(event)


class EventReplayEngine:
    def __init__(self, bus: EnterpriseEventBus) -> None:
        self._bus = bus

    async def replay(
        self,
        *,
        event_id: str | None = None,
        event_ids: list[str] | None = None,
        topic: str | None = None,
        since: float | None = None,
        until: float | None = None,
        event_type: str | None = None,
        limit: int = 100,
        actor: str = "system",
    ) -> dict[str, Any]:
        events: list[EnterpriseEvent] = []
        if event_id:
            events = [self._bus.store.get(event_id)]
        elif event_ids:
            events = [self._bus.store.get(eid) for eid in event_ids]
        else:
            events = self._bus.store.list_events(
                topic=topic,
                event_type=event_type,
                since=since,
                until=until,
                limit=limit,
            )
        results = []
        for original in events:
            clone = EnterpriseEvent.from_dict(original.to_dict())
            clone.event_id = f"evt_{uuid.uuid4().hex}"
            clone.causation_id = original.event_id
            clone.metadata = {**clone.metadata, "replayed": True, "replay_of": original.event_id}
            result = await self._bus.publish(clone, actor=actor, bridge=True)
            results.append({"original": original.event_id, "replayed": clone.event_id, "result": result})
        self._bus.audit.log(
            operation="replay",
            actor=actor,
            count=len(results),
            topic=topic,
            result="ok",
        )
        return {"replayed": len(results), "items": results}


class EnterpriseEventBus:
    """
    Enterprise control-plane Event Bus.

    Transport SoR: events.event_bus.PlatformEventBus
    This class adds topics, filters, DLQ, retry, replay, metrics, signing.
    """

    def __init__(self) -> None:
        self.topics = TopicManager()
        self.store = EventStore()
        self.dlq = DeadLetterQueue()
        self.retry = RetryManager()
        self.audit = EventAuditLogger()
        self.metrics = EventMetrics()
        self.serializer = EventSerializer()
        self.deserializer = EventDeserializer()
        self.validator = EventValidator()
        self.filter = EventFilter()
        self.subscriptions: dict[str, Subscription] = {}
        self._handlers: dict[str, list[tuple[str, Handler]]] = {}
        self._live_listeners: list[Callable[[EnterpriseEvent], Awaitable[None] | None]] = []
        self._scheduled: list[EnterpriseEvent] = []
        self._response_waiters: dict[str, asyncio.Future] = {}
        self.publisher = EventPublisher(self)
        self.subscriber = EventSubscriber(self)
        self.dispatcher = EventDispatcher(self)
        self.router = EventRouter(self)
        self.broker = EventBroker(self)
        self.replay_engine = EventReplayEngine(self)
        self._bridge_handler_id: str | None = None

    def reset(self) -> None:
        self.topics.reset()
        self.store.reset()
        self.dlq.reset()
        self.retry.reset()
        self.audit.reset()
        self.metrics.reset()
        self.subscriptions.clear()
        self._handlers.clear()
        self._live_listeners.clear()
        self._scheduled.clear()
        for fut in self._response_waiters.values():
            if not fut.done():
                fut.cancel()
        self._response_waiters.clear()

    def add_live_listener(self, listener: Callable[[EnterpriseEvent], Awaitable[None] | None]) -> None:
        self._live_listeners.append(listener)

    def subscribe(
        self,
        *,
        subscriber_id: str,
        topic: str | None = None,
        event_type: str | None = None,
        event_filter: str | None = None,
        priority_min: str | EventPriority | None = None,
        tenant_id: str | None = None,
        user_id: str | None = None,
        regex: str | None = None,
        wildcard: str | None = None,
        handler: Handler | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Subscription:
        sub = Subscription(
            subscription_id=f"sub_{uuid.uuid4().hex[:12]}",
            subscriber_id=subscriber_id,
            topic=topic,
            event_type=event_type,
            event_filter=event_filter,
            priority_min=priority_min,
            tenant_id=tenant_id,
            user_id=user_id,
            regex=regex,
            wildcard=wildcard,
            metadata=metadata or {},
        )
        self.subscriptions[sub.subscription_id] = sub
        if handler is not None:
            self._handlers.setdefault(sub.subscription_id, []).append((subscriber_id, handler))
        if topic:
            self.topics.ensure(topic)
            count = sum(1 for s in self.subscriptions.values() if s.topic == topic and s.active)
            self.topics.set_subscriber_count(topic, count)
        self.audit.log(
            operation="subscribe",
            publisher=None,
            subscriber=subscriber_id,
            subscription_id=sub.subscription_id,
            topic=topic,
            result="ok",
        )
        return sub

    def unsubscribe(self, subscription_id: str) -> bool:
        sub = self.subscriptions.pop(subscription_id, None)
        self._handlers.pop(subscription_id, None)
        if sub and sub.topic:
            count = sum(1 for s in self.subscriptions.values() if s.topic == sub.topic and s.active)
            self.topics.set_subscriber_count(sub.topic, count)
        self.audit.log(operation="unsubscribe", subscription_id=subscription_id, result="ok" if sub else "missing")
        return sub is not None

    async def publish(
        self,
        event: EnterpriseEvent | dict[str, Any],
        *,
        wait: bool = False,
        actor: str = "system",
        bridge: bool = True,
        sign: bool = True,
    ) -> dict[str, Any]:
        if isinstance(event, dict):
            event = EnterpriseEvent.from_dict(event)
        self.validator.require_valid(event)
        if sign:
            self.validator.sign(event)

        # delayed / scheduled
        now = time.time()
        if event.deliver_at and event.deliver_at > now:
            event.delivery_mode = event.delivery_mode or DeliveryMode.DELAYED
            self._scheduled.append(event)
            self.metrics.set_queued(len(self._scheduled))
            self.audit.log(
                operation="schedule",
                publisher=actor,
                event_id=event.event_id,
                deliver_at=event.deliver_at,
                result="queued",
            )
            return {"event_id": event.event_id, "status": "scheduled", "deliver_at": event.deliver_at}

        self.topics.ensure(event.topic)
        self.topics.bump_event(event.topic)
        self.store.append(event)
        self.metrics.on_publish()

        # Bridge to canonical PlatformEventBus SoR
        if bridge:
            envelope = EnterpriseBusEvent(envelope=event.to_dict())
            await PlatformEventBus.publish(envelope, wait=False)

        result = await self._dispatch(event, wait=wait)

        self.audit.log(
            operation="publish",
            publisher=actor or event.source_service,
            subscriber=None,
            event_id=event.event_id,
            event_type=event.event_type,
            topic=event.topic,
            payload_hash=event.payload_hash(),
            delivery_result=result.get("status"),
            processing_duration=result.get("duration_ms"),
            result="ok" if not result.get("errors") else "partial",
        )

        # request-response wake
        if event.reply_to and event.reply_to in self._response_waiters:
            fut = self._response_waiters[event.reply_to]
            if not fut.done():
                fut.set_result(event)

        await self._emit_live(event)
        return result

    async def request(
        self,
        event: EnterpriseEvent | dict[str, Any],
        *,
        timeout: float = 5.0,
        actor: str = "system",
    ) -> EnterpriseEvent | None:
        if isinstance(event, dict):
            event = EnterpriseEvent.from_dict(event)
        event.delivery_mode = DeliveryMode.REQUEST_RESPONSE
        loop = asyncio.get_running_loop()
        fut: asyncio.Future = loop.create_future()
        self._response_waiters[event.event_id] = fut
        try:
            await self.publish(event, actor=actor, wait=True)
            return await asyncio.wait_for(fut, timeout=timeout)
        except asyncio.TimeoutError:
            return None
        finally:
            self._response_waiters.pop(event.event_id, None)

    async def process_scheduled(self, *, now: float | None = None) -> int:
        now = now if now is not None else time.time()
        due = [e for e in self._scheduled if (e.deliver_at or 0) <= now]
        self._scheduled = [e for e in self._scheduled if (e.deliver_at or 0) > now]
        self.metrics.set_queued(len(self._scheduled))
        for event in due:
            event.deliver_at = None
            await self.publish(event, bridge=True, sign=False)
        return len(due)

    async def _dispatch(self, event: EnterpriseEvent, *, wait: bool = False) -> dict[str, Any]:
        started = time.time()
        matched = self.router.route(event)
        # also invoke handlers registered without subscription filters via topic handlers
        errors: list[str] = []
        delivered = 0

        async def _deliver(sub: Subscription) -> None:
            nonlocal delivered
            handlers = list(self._handlers.get(sub.subscription_id, []))
            delivery = self.retry.begin(event.event_id, sub.subscriber_id)
            t0 = time.time()
            try:
                if not handlers:
                    # passive subscription — counted as delivered for monitoring
                    self.retry.succeed(delivery, duration_ms=(time.time() - t0) * 1000)
                    delivered += 1
                    self.metrics.on_delivered((time.time() - t0) * 1000)
                    return
                for handler_id, handler in handlers:
                    while True:
                        try:
                            result = handler(event)
                            if inspect.isawaitable(result):
                                await result
                            break
                        except Exception as exc:
                            self.retry.fail(delivery, error=str(exc))
                            if self.retry.should_retry(delivery):
                                await asyncio.sleep(self.retry.delay_for(delivery))
                                continue
                            self.dlq.enqueue(
                                event,
                                reason=str(exc),
                                subscriber_id=sub.subscriber_id,
                                attempts=delivery.attempts,
                            )
                            self.metrics.on_failed()
                            errors.append(f"{sub.subscriber_id}:{exc}")
                            self.audit.log(
                                operation="delivery_failed",
                                publisher=event.source_service,
                                subscriber=sub.subscriber_id,
                                event_id=event.event_id,
                                payload_hash=event.payload_hash(),
                                delivery_result="dead",
                                result="error",
                            )
                            return
                self.retry.succeed(delivery, duration_ms=(time.time() - t0) * 1000)
                delivered += 1
                self.metrics.on_delivered((time.time() - t0) * 1000)
            except Exception as exc:
                self.metrics.on_failed()
                errors.append(str(exc))

        tasks = [asyncio.create_task(_deliver(sub)) for sub in matched]
        if wait or tasks:
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)

        duration_ms = (time.time() - started) * 1000
        return {
            "event_id": event.event_id,
            "status": "delivered" if not errors else "partial",
            "subscribers": len(matched),
            "delivered": delivered,
            "errors": errors,
            "duration_ms": round(duration_ms, 3),
        }

    async def _emit_live(self, event: EnterpriseEvent) -> None:
        for listener in list(self._live_listeners):
            try:
                result = listener(event)
                if asyncio.iscoroutine(result) or asyncio.isfuture(result):
                    await result  # type: ignore[misc]
            except Exception:
                logger.debug("live listener failed", exc_info=True)
        # Best-effort realtime channel broadcast
        try:
            from platform_realtime.models import RealtimeMessage
            from platform_realtime.realtime_hub import realtime_hub

            message = RealtimeMessage(
                type="event",
                channel="event_bus",
                event="event_bus.live",
                event_id=event.event_id,
                data=event.to_dict(),
            )
            await realtime_hub.broadcast_channel("event_bus", message)
        except Exception:
            logger.debug("realtime broadcast unavailable", exc_info=True)

    async def retry_dead_letter(self, dlq_id: str, *, actor: str = "system") -> dict[str, Any]:
        item = self.dlq.get(dlq_id)
        event = EnterpriseEvent.from_dict(item.event)
        event.metadata = {**event.metadata, "retried_from_dlq": dlq_id}
        event.event_id = f"evt_{uuid.uuid4().hex}"
        self.dlq.mark_retried(dlq_id)
        result = await self.publish(event, actor=actor)
        self.audit.log(operation="dlq_retry", actor=actor, dlq_id=dlq_id, result="ok")
        return {"dlq_id": dlq_id, "new_event_id": event.event_id, "result": result}

    def status(self) -> dict[str, Any]:
        return {
            "module": "platform_enterprise_event_bus",
            "sprint": "36.1",
            "sor": "events.event_bus.PlatformEventBus",
            "topics": len(self.topics.list_topics()),
            "subscriptions": len(self.subscriptions),
            "stored_events": self.store.statistics()["total"],
            "dlq": len(self.dlq.list_items()),
            "queued": len(self._scheduled),
            "metrics": self.metrics.snapshot(
                subscribers=len(self.subscriptions),
                retry_count=self.retry.retry_count,
            ),
        }


enterprise_event_bus = EnterpriseEventBus()
