"""Enterprise Event Bus service façade — Sprint 36.1."""

from __future__ import annotations

from typing import Any

from platform_enterprise_event_bus.bus import EnterpriseEventBus, enterprise_event_bus
from platform_enterprise_event_bus.models import EnterpriseEvent, EventPriority


class EnterpriseEventBusService:
    """Ops façade over PlatformEventBus SoR + enterprise control plane."""

    def __init__(self, bus: EnterpriseEventBus | None = None) -> None:
        self.bus = bus or enterprise_event_bus

    def reset(self) -> None:
        self.bus.reset()

    def status(self) -> dict[str, Any]:
        return self.bus.status()

    # topics
    def list_topics(self) -> list[dict[str, Any]]:
        return [t.to_dict() for t in self.bus.topics.list_topics()]

    def create_topic(self, name: str, *, description: str = "") -> dict[str, Any]:
        return self.bus.topics.create(name, description=description).to_dict()

    # events
    def list_events(self, **filters: Any) -> list[dict[str, Any]]:
        return [e.to_dict() for e in self.bus.store.list_events(**filters)]

    def get_event(self, event_id: str) -> dict[str, Any]:
        return self.bus.store.get(event_id).to_dict()

    def inspect(self, event_id: str) -> dict[str, Any]:
        event = self.bus.store.get(event_id)
        deliveries = [
            d.to_dict()
            for d in self.bus.retry.list_deliveries()
            if d.event_id == event_id
        ]
        audits = [a for a in self.bus.audit.list_entries(limit=500) if a.get("event_id") == event_id]
        return {
            "event": event.to_dict(),
            "payload": event.payload,
            "headers": {
                "correlation_id": event.correlation_id,
                "causation_id": event.causation_id,
                "trace_id": event.trace_id,
                "signature": event.signature,
                "version": event.version,
            },
            "metadata": event.metadata,
            "routing": {
                "topic": event.topic,
                "category": event.category,
                "source_service": event.source_service,
                "target_service": event.target_service,
                "priority": event.priority_value.value,
            },
            "publisher": event.source_service,
            "subscribers": [
                s.to_dict()
                for s in self.bus.router.route(event)
            ],
            "deliveries": deliveries,
            "history": audits,
            "processing_time": next(
                (d.get("duration_ms") for d in deliveries if d.get("duration_ms") is not None),
                None,
            ),
        }

    async def publish(self, payload: dict[str, Any], *, actor: str = "system") -> dict[str, Any]:
        return await self.bus.publish(payload, actor=actor)

    def subscribe(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self.bus.subscribe(
            subscriber_id=str(payload.get("subscriber_id") or payload.get("subscriber") or "anonymous"),
            topic=payload.get("topic"),
            event_type=payload.get("event_type"),
            event_filter=payload.get("event_filter"),
            priority_min=payload.get("priority_min"),
            tenant_id=payload.get("tenant_id"),
            user_id=payload.get("user_id"),
            regex=payload.get("regex"),
            wildcard=payload.get("wildcard"),
            metadata=payload.get("metadata"),
        ).to_dict()

    def unsubscribe(self, subscription_id: str | None = None, *, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        payload = payload or {}
        sid = subscription_id or payload.get("subscription_id")
        if not sid:
            raise ValueError("subscription_id is required")
        ok = self.bus.unsubscribe(str(sid))
        return {"subscription_id": sid, "removed": ok}

    def list_subscribers(self) -> list[dict[str, Any]]:
        return [s.to_dict() for s in self.bus.subscriptions.values()]

    async def replay(self, payload: dict[str, Any], *, actor: str = "system") -> dict[str, Any]:
        return await self.bus.replay_engine.replay(
            event_id=payload.get("event_id"),
            event_ids=payload.get("event_ids"),
            topic=payload.get("topic"),
            since=payload.get("since"),
            until=payload.get("until"),
            event_type=payload.get("event_type"),
            limit=int(payload.get("limit") or 100),
            actor=actor,
        )

    def statistics(self) -> dict[str, Any]:
        return {
            **self.bus.store.statistics(),
            "metrics": self.bus.metrics.snapshot(
                subscribers=len(self.bus.subscriptions),
                retry_count=self.bus.retry.retry_count,
            ),
            "topics": self.list_topics(),
            "dlq_count": len(self.bus.dlq.list_items()),
        }

    def dead_letter(self, *, limit: int = 100) -> list[dict[str, Any]]:
        return [d.to_dict() for d in self.bus.dlq.list_items(limit=limit)]

    async def retry(self, payload: dict[str, Any], *, actor: str = "system") -> dict[str, Any]:
        dlq_id = payload.get("dlq_id")
        if not dlq_id:
            raise ValueError("dlq_id is required")
        return await self.bus.retry_dead_letter(str(dlq_id), actor=actor)

    def traffic(self) -> dict[str, Any]:
        return self.bus.metrics.snapshot(
            subscribers=len(self.bus.subscriptions),
            retry_count=self.bus.retry.retry_count,
        )


enterprise_event_bus_service = EnterpriseEventBusService()
