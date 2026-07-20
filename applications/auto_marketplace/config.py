# Auto Marketplace configuration.

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class AutoMarketplaceConfig:
    api_version: str = "v1"
    api_prefix: str = "/api/auto/v1"
    internal_prefix: str = "/internal/auto/v1"
    webhook_prefix: str = "/webhooks/auto/v1"
    default_currency: str = "USD"
    enable_ai_recommendations: bool = True
    enable_auctions: bool = True


DEFAULT_CONFIG = AutoMarketplaceConfig()
