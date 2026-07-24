"""Communications Analytics — Sprint 22.6."""

from __future__ import annotations

from typing import Any


class CommunicationsAnalytics:
    def summarize(self, *, delivered: int, opened: int, clicks: int, conversions: int, bookings: int, sales: float) -> dict[str, Any]:
        return {
            "delivered": delivered,
            "opened": opened,
            "ctr": round(clicks / max(opened, 1), 3),
            "conversion": round(conversions / max(delivered, 1), 3),
            "bookings_after_messages": bookings,
            "sales_after_campaigns": sales,
            "open_rate": round(opened / max(delivered, 1), 3),
        }
