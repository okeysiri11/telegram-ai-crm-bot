"""Event serializer / deserializer / validator / filter — Sprint 36.1."""

from __future__ import annotations

import json
import re
from typing import Any

from platform_enterprise_event_bus.models import (
    PRIORITY_RANK,
    EnterpriseEvent,
    EventPriority,
    Subscription,
    match_wildcard,
    sign_payload,
)


class EventSerializer:
    def serialize(self, event: EnterpriseEvent) -> str:
        return json.dumps(event.to_dict(), default=str)

    def serialize_bytes(self, event: EnterpriseEvent) -> bytes:
        return self.serialize(event).encode("utf-8")


class EventDeserializer:
    def deserialize(self, data: str | bytes | dict[str, Any]) -> EnterpriseEvent:
        if isinstance(data, EnterpriseEvent):
            return data
        if isinstance(data, (bytes, bytearray)):
            data = data.decode("utf-8")
        if isinstance(data, str):
            data = json.loads(data)
        if not isinstance(data, dict):
            raise TypeError("unsupported event payload")
        return EnterpriseEvent.from_dict(data)


class EventValidator:
    REQUIRED = ("event_type", "category", "source_service")

    def __init__(self, *, signing_secret: str = "ados-event-bus-dev") -> None:
        self._secret = signing_secret

    def validate(self, event: EnterpriseEvent) -> list[str]:
        errors: list[str] = []
        for field in self.REQUIRED:
            if not getattr(event, field, None):
                errors.append(f"missing:{field}")
        if event.priority_value not in EventPriority:
            errors.append("invalid:priority")
        if not isinstance(event.payload, dict):
            errors.append("invalid:payload")
        if event.version and not str(event.version):
            errors.append("invalid:version")
        return errors

    def require_valid(self, event: EnterpriseEvent) -> EnterpriseEvent:
        errors = self.validate(event)
        if errors:
            raise ValueError(f"event validation failed: {', '.join(errors)}")
        return event

    def sign(self, event: EnterpriseEvent) -> EnterpriseEvent:
        event.signature = sign_payload(event.payload, secret=self._secret)
        return event

    def verify_signature(self, event: EnterpriseEvent) -> bool:
        if not event.signature:
            return False
        expected = sign_payload(event.payload, secret=self._secret)
        return hmac_compare(event.signature, expected)


def hmac_compare(a: str, b: str) -> bool:
    if len(a) != len(b):
        return False
    result = 0
    for x, y in zip(a.encode(), b.encode()):
        result |= x ^ y
    return result == 0


class EventFilter:
    def matches(self, event: EnterpriseEvent, subscription: Subscription) -> bool:
        if not subscription.active:
            return False
        if subscription.topic and not match_wildcard(subscription.topic, event.topic):
            return False
        if subscription.event_type and not match_wildcard(subscription.event_type, event.event_type):
            return False
        if subscription.wildcard and not match_wildcard(subscription.wildcard, event.event_type):
            return False
        if subscription.event_filter and not match_wildcard(subscription.event_filter, event.event_type):
            return False
        if subscription.regex:
            if re.search(subscription.regex, event.event_type) is None and re.search(
                subscription.regex, event.topic
            ) is None:
                return False
        if subscription.priority_min is not None:
            min_p = (
                subscription.priority_min
                if isinstance(subscription.priority_min, EventPriority)
                else EventPriority(subscription.priority_min)
            )
            if PRIORITY_RANK[event.priority_value] < PRIORITY_RANK[min_p]:
                return False
        if subscription.tenant_id and event.tenant_id != subscription.tenant_id:
            return False
        if subscription.user_id and event.user_id != subscription.user_id:
            return False
        return True
