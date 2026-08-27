"""Advertising control-center foundation — no live provider APIs.

Future: Meta Ads, Google Ads, TikTok Ads.
This sprint defines provider-neutral entities mapped to Recruiting project Vanguard.
"""

from __future__ import annotations

from typing import Any

ADS_PROVIDERS = ("meta", "google", "tiktok")

ENTITY_TYPES = (
    "AdAccount",
    "Campaign",
    "AdSet",
    "AdGroup",
    "Creative",
    "Audience",
    "Spend",
    "Impressions",
    "Clicks",
    "CTR",
    "CPC",
    "Applications",
    "Leads",
    "Candidates",
    "CPL",
    "CostPerCandidate",
)


def ads_foundation(*, project_key: str = "vanguard") -> dict[str, Any]:
    providers = {
        name: {
            "provider": name,
            "status": "not_connected",
            "label_ru": "Провайдер не подключен",
            "accounts": [],
            "campaigns": [],
            "metrics": None,
        }
        for name in ADS_PROVIDERS
    }
    return {
        "ok": True,
        "project_key": project_key,
        "connected": False,
        "providers": providers,
        "entity_types": list(ENTITY_TYPES),
        "mapping": {"recruiting_project": project_key},
        "message_ru": "Провайдер не подключен",
        "fake_data": False,
    }
