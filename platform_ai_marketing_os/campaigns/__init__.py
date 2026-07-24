"""Campaign Manager — Sprint 22.5."""

from __future__ import annotations

from typing import Any

from platform_ai_marketing_os.models import CAMPAIGN_KINDS


class CampaignManager:
    def create(
        self,
        *,
        kind: str,
        title: str,
        budget: float = 0.0,
        channels: list[str] | None = None,
    ) -> dict[str, Any]:
        if kind not in CAMPAIGN_KINDS:
            raise ValueError(f"unknown campaign kind: {kind}")
        if not title:
            raise ValueError("campaign title is required")
        return {
            "kind": kind,
            "title": title.strip(),
            "budget": float(budget),
            "channels": list(channels or ["instagram", "telegram", "sms"]),
            "status": "draft",
            "published": False,
            "requires_owner_approval": True,
        }
