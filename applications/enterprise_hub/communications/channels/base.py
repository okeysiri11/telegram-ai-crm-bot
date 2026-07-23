"""Base channel send helper and registry."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Callable

from applications.enterprise_hub.shared.exceptions import ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def send_via_channel(
    store: EnterpriseHubStore,
    *,
    channel: str,
    recipient: str,
    subject: str,
    body: str,
    meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if not channel or not recipient:
        raise ValidationError("channel and recipient required")
    mid = _id("comm_msg")
    return store.comm_messages.save(
        mid,
        {
            "message_id": mid,
            "channel": channel,
            "recipient": recipient,
            "subject": subject,
            "body": body,
            "meta": meta or {},
            "status": "sent",
            "at": _now(),
        },
    )


class ChannelRegistry:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self._handlers: dict[str, Callable[..., dict[str, Any]]] = {}

    def register(self, channel: str, handler: Callable[..., dict[str, Any]]) -> None:
        self._handlers[channel] = handler

    def send(
        self,
        *,
        channel: str,
        recipient: str,
        subject: str = "",
        body: str = "",
        meta: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        handler = self._handlers.get(channel)
        if handler is None:
            return send_via_channel(
                self.store,
                channel=channel,
                recipient=recipient,
                subject=subject,
                body=body,
                meta=meta,
            )
        return handler(recipient=recipient, subject=subject, body=body, meta=meta or {})

    def status(self) -> dict[str, Any]:
        return {
            "messages": self.store.comm_messages.count(),
            "registered_channels": sorted(self._handlers.keys()),
        }
