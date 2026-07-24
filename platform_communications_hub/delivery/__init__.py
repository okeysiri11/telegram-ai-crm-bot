"""Campaign Delivery Manager — Sprint 22.6."""

from __future__ import annotations

from typing import Any


class CampaignDeliveryManager:
    def enqueue(
        self,
        *,
        campaign_id: str,
        recipients: list[str],
        channel: str,
        body: str,
        rate_limit_per_min: int = 120,
    ) -> dict[str, Any]:
        if not campaign_id or not recipients:
            raise ValueError("campaign_id and recipients are required")
        return {
            "campaign_id": campaign_id,
            "queue_size": len(recipients),
            "channel": channel,
            "body": body,
            "rate_limit_per_min": rate_limit_per_min,
            "retries": 3,
            "delivery_control": True,
            "status": "queued",
            "report": {"queued": len(recipients), "sent": 0, "failed": 0},
            "auto_sent_by_ai": False,
        }

    def report(self, delivery: dict[str, Any], *, delivered: int, failed: int = 0) -> dict[str, Any]:
        queued = int(delivery.get("queue_size", 0))
        return {
            **delivery,
            "status": "completed",
            "report": {
                "queued": queued,
                "sent": delivered,
                "failed": failed,
                "delivery_rate": round(delivered / max(queued, 1), 3),
            },
        }
