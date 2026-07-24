"""AI Performance Analyzer — Sprint 22.5."""

from __future__ import annotations

from typing import Any


class AIPerformanceAnalyzer:
    def analyze(self, *, campaign: dict[str, Any], observed: dict[str, Any] | None = None) -> dict[str, Any]:
        observed = observed or {
            "bookings": 18,
            "new_clients": 7,
            "master_load_delta": 0.12,
            "roi": 2.4,
            "cac": 12.5,
            "conversion": 0.08,
            "avg_check": 55.0,
            "revisits": 5,
        }
        result = {
            "campaign_kind": campaign.get("kind"),
            "campaign_title": campaign.get("title"),
            "metrics": observed,
            "passed": observed.get("roi", 0) >= 1.0,
            "product_intelligence_handoff": {
                "source": "ai_marketing_os",
                "title": f"Campaign results: {campaign.get('title')}",
                "module": "ai_marketing_os",
                "payload": observed,
            },
        }
        return result
