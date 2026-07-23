"""SMS channel."""

from __future__ import annotations

from typing import Any

from applications.enterprise_hub.communications.channels.base import send_via_channel
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


class SMSChannel:
    name = "sms"

    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def send(
        self,
        *,
        recipient: str,
        subject: str = "",
        body: str = "",
        meta: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return send_via_channel(
            self.store,
            channel=self.name,
            recipient=recipient,
            subject=subject or "SMS",
            body=body[:320],
            meta=meta,
        )
