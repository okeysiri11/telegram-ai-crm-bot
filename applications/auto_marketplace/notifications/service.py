# NotificationService — customer and dealer notifications.

from __future__ import annotations

import logging
import time
from typing import Any

logger = logging.getLogger(__name__)


class NotificationService:
    def __init__(self) -> None:
        self._log: list[dict[str, Any]] = []

    def reset(self) -> None:
        self._log.clear()

    def send(self, *, channel: str, recipient: str, subject: str, body: str, metadata: dict | None = None) -> dict[str, Any]:
        entry = {
            "channel": channel,
            "recipient": recipient,
            "subject": subject,
            "body": body,
            "metadata": metadata or {},
            "sent_at": time.time(),
        }
        self._log.append(entry)
        logger.info("auto_marketplace_notification channel=%s recipient=%s subject=%s", channel, recipient, subject)
        return entry

    def notify_lead_created(self, lead_id: str, customer_email: str) -> dict[str, Any]:
        return self.send(
            channel="email",
            recipient=customer_email,
            subject="Lead received",
            body=f"Your inquiry {lead_id} has been received.",
            metadata={"lead_id": lead_id},
        )

    def notify_deal_update(self, deal_id: str, customer_email: str, status: str) -> dict[str, Any]:
        return self.send(
            channel="email",
            recipient=customer_email,
            subject="Deal update",
            body=f"Deal {deal_id} status: {status}",
            metadata={"deal_id": deal_id, "status": status},
        )

    def history(self) -> list[dict[str, Any]]:
        return list(self._log)


notification_service = NotificationService()
