"""Topic manager, store, DLQ, retry, audit, metrics — Sprint 36.1."""

from __future__ import annotations

import time
import uuid
from collections import defaultdict
from typing import Any

from platform_enterprise_event_bus.models import (
    DEFAULT_TOPICS,
    DeadLetterRecord,
    DeliveryRecord,
    EnterpriseEvent,
    TopicInfo,
)


class TopicManager:
    def __init__(self) -> None:
        self._topics: dict[str, TopicInfo] = {}
        for name in DEFAULT_TOPICS:
            self._topics[name] = TopicInfo(name=name, description=f"Default topic: {name}")

    def reset(self) -> None:
        self.__init__()

    def list_topics(self) -> list[TopicInfo]:
        return sorted(self._topics.values(), key=lambda t: t.name)

    def get(self, name: str) -> TopicInfo:
        topic = self._topics.get(name)
        if topic is None:
            raise KeyError(f"topic not found: {name}")
        return topic

    def create(self, name: str, *, description: str = "", metadata: dict[str, Any] | None = None) -> TopicInfo:
        if name in self._topics:
            raise ValueError(f"topic already exists: {name}")
        info = TopicInfo(name=name, description=description, metadata=metadata or {})
        self._topics[name] = info
        return info

    def ensure(self, name: str) -> TopicInfo:
        if name not in self._topics:
            return self.create(name, description=f"Auto-created topic: {name}")
        return self._topics[name]

    def bump_event(self, name: str) -> None:
        topic = self.ensure(name)
        topic.event_count += 1

    def set_subscriber_count(self, name: str, count: int) -> None:
        if name in self._topics:
            self._topics[name].subscriber_count = count


class EventStore:
    """In-memory durable event log for enterprise ops (replay/search/audit)."""

    def __init__(self, *, retention: int = 50_000) -> None:
        self._events: list[EnterpriseEvent] = []
        self._by_id: dict[str, EnterpriseEvent] = {}
        self._retention = retention

    def reset(self) -> None:
        self._events.clear()
        self._by_id.clear()

    def append(self, event: EnterpriseEvent) -> EnterpriseEvent:
        self._events.append(event)
        self._by_id[event.event_id] = event
        if len(self._events) > self._retention:
            drop = self._events[: -self._retention]
            self._events = self._events[-self._retention :]
            for e in drop:
                self._by_id.pop(e.event_id, None)
        return event

    def get(self, event_id: str) -> EnterpriseEvent:
        event = self._by_id.get(event_id)
        if event is None:
            raise KeyError(f"event not found: {event_id}")
        return event

    def list_events(
        self,
        *,
        topic: str | None = None,
        event_type: str | None = None,
        tenant_id: str | None = None,
        source_service: str | None = None,
        since: float | None = None,
        until: float | None = None,
        limit: int = 100,
    ) -> list[EnterpriseEvent]:
        rows = self._events
        if topic:
            rows = [e for e in rows if e.topic == topic]
        if event_type:
            rows = [e for e in rows if e.event_type == event_type]
        if tenant_id:
            rows = [e for e in rows if e.tenant_id == tenant_id]
        if source_service:
            rows = [e for e in rows if e.source_service == source_service]
        if since is not None:
            rows = [e for e in rows if e.timestamp >= since]
        if until is not None:
            rows = [e for e in rows if e.timestamp <= until]
        return rows[-limit:]

    def search(self, query: str, *, limit: int = 50) -> list[EnterpriseEvent]:
        q = query.lower()
        hits = []
        for e in reversed(self._events):
            blob = f"{e.event_type} {e.topic} {e.source_service} {e.payload}".lower()
            if q in blob:
                hits.append(e)
            if len(hits) >= limit:
                break
        return list(reversed(hits))

    def statistics(self) -> dict[str, Any]:
        by_topic: dict[str, int] = defaultdict(int)
        by_type: dict[str, int] = defaultdict(int)
        for e in self._events:
            by_topic[e.topic] += 1
            by_type[e.event_type] += 1
        return {
            "total": len(self._events),
            "by_topic": dict(by_topic),
            "by_type": dict(sorted(by_type.items(), key=lambda kv: -kv[1])[:50]),
        }


class DeadLetterQueue:
    def __init__(self) -> None:
        self._items: list[DeadLetterRecord] = []

    def reset(self) -> None:
        self._items.clear()

    def enqueue(
        self,
        event: EnterpriseEvent | dict[str, Any],
        *,
        reason: str,
        subscriber_id: str | None = None,
        attempts: int = 0,
    ) -> DeadLetterRecord:
        payload = event.to_dict() if isinstance(event, EnterpriseEvent) else dict(event)
        record = DeadLetterRecord(
            dlq_id=f"dlq_{uuid.uuid4().hex[:12]}",
            event=payload,
            reason=reason,
            subscriber_id=subscriber_id,
            attempts=attempts,
        )
        self._items.append(record)
        return record

    def list_items(self, *, limit: int = 100) -> list[DeadLetterRecord]:
        return self._items[-limit:]

    def get(self, dlq_id: str) -> DeadLetterRecord:
        for item in self._items:
            if item.dlq_id == dlq_id:
                return item
        raise KeyError(f"dlq item not found: {dlq_id}")

    def mark_retried(self, dlq_id: str) -> DeadLetterRecord:
        item = self.get(dlq_id)
        item.retried = True
        return item


class RetryManager:
    def __init__(self, *, max_attempts: int = 3, base_delay_sec: float = 0.05) -> None:
        self.max_attempts = max_attempts
        self.base_delay_sec = base_delay_sec
        self._deliveries: dict[str, DeliveryRecord] = {}
        self._retry_count = 0

    def reset(self) -> None:
        self._deliveries.clear()
        self._retry_count = 0

    def begin(self, event_id: str, subscriber_id: str) -> DeliveryRecord:
        rec = DeliveryRecord(
            delivery_id=f"dlv_{uuid.uuid4().hex[:12]}",
            event_id=event_id,
            subscriber_id=subscriber_id,
            status="pending",
        )
        self._deliveries[rec.delivery_id] = rec
        return rec

    def succeed(self, delivery: DeliveryRecord, *, duration_ms: float) -> DeliveryRecord:
        delivery.status = "delivered"
        delivery.duration_ms = duration_ms
        delivery.updated_at = time.time()
        return delivery

    def fail(self, delivery: DeliveryRecord, *, error: str) -> DeliveryRecord:
        delivery.attempts += 1
        delivery.last_error = error
        delivery.updated_at = time.time()
        if delivery.attempts >= self.max_attempts:
            delivery.status = "dead"
        else:
            delivery.status = "retrying"
            self._retry_count += 1
        return delivery

    def should_retry(self, delivery: DeliveryRecord) -> bool:
        return delivery.status == "retrying" and delivery.attempts < self.max_attempts

    def delay_for(self, delivery: DeliveryRecord) -> float:
        return self.base_delay_sec * (2 ** max(0, delivery.attempts - 1))

    @property
    def retry_count(self) -> int:
        return self._retry_count

    def list_deliveries(self, *, limit: int = 200) -> list[DeliveryRecord]:
        return list(self._deliveries.values())[-limit:]


class EventAuditLogger:
    def __init__(self) -> None:
        self._rows: list[dict[str, Any]] = []

    def reset(self) -> None:
        self._rows.clear()

    def log(self, **fields: Any) -> dict[str, Any]:
        row = {"audit_id": f"aud_{uuid.uuid4().hex[:10]}", "timestamp": time.time(), **fields}
        self._rows.append(row)
        self._rows = self._rows[-20_000:]
        return row

    def list_entries(self, *, limit: int = 100) -> list[dict[str, Any]]:
        return self._rows[-limit:]


class EventMetrics:
    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        self.published = 0
        self.delivered = 0
        self.failed = 0
        self.queued = 0
        self.latency_total_ms = 0.0
        self.latency_samples = 0
        self._window: list[tuple[float, int]] = []

    def on_publish(self) -> None:
        now = time.time()
        self.published += 1
        self._window.append((now, 1))
        self._window = [(t, n) for t, n in self._window if now - t < 1.0]

    def on_delivered(self, latency_ms: float) -> None:
        self.delivered += 1
        self.latency_total_ms += latency_ms
        self.latency_samples += 1

    def on_failed(self) -> None:
        self.failed += 1

    def set_queued(self, n: int) -> None:
        self.queued = n

    def events_per_sec(self) -> float:
        now = time.time()
        return float(sum(n for t, n in self._window if now - t < 1.0))

    def avg_latency_ms(self) -> float:
        if self.latency_samples == 0:
            return 0.0
        return self.latency_total_ms / self.latency_samples

    def snapshot(self, *, subscribers: int = 0, retry_count: int = 0) -> dict[str, Any]:
        import resource

        try:
            mem_mb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0 / 1024.0
            # macOS reports bytes; Linux KB — normalize roughly
            if mem_mb > 10_000:
                mem_mb = mem_mb / 1024.0
        except Exception:
            mem_mb = 0.0
        return {
            "events_per_sec": self.events_per_sec(),
            "active_subscribers": subscribers,
            "queued_events": self.queued,
            "failed_events": self.failed,
            "retry_count": retry_count,
            "latency_ms": round(self.avg_latency_ms(), 3),
            "throughput": self.delivered,
            "published": self.published,
            "delivered": self.delivered,
            "memory_usage_mb": round(mem_mb, 2),
        }
