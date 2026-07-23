"""FinancePublisher."""

from __future__ import annotations

from typing import Any

from applications.enterprise_hub.event_platform.event_bus import EventBus
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


class FinancePublisher:
    source = "finance"

    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.bus = EventBus(store or enterprise_hub_store)

    def publish(self, *, event_type: str = "PaymentReceived", payload: dict[str, Any] | None = None, **kwargs: Any) -> dict[str, Any]:
        return self.bus.publish(event_type=event_type, source=self.source, payload=payload or {}, **kwargs)
