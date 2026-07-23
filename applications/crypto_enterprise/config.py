# Crypto Enterprise Platform — Sprint 16.0 Foundation.

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class CryptoEnterpriseConfig:
    application_name: str = "Crypto Intelligence Platform"
    application: str = "crypto_enterprise"
    application_version: str = "4.7.0-enterprise"
    release_status: str = "Crypto Enterprise Foundation"
    platform_dependency: str = "AI Platform Core v3"
    enterprise_foundation: str = "Enterprise Platform v4.6.0-enterprise"
    ecosystem_dependency: str = "AI Ecosystem v1.5"
    api_version: str = "v1"
    api_prefix: str = "/api/crypto-enterprise/v1"
    internal_prefix: str = "/internal/crypto-enterprise/v1"
    exchange_integration: str = "1.0"
    market_data: str = "1.0"
    asset_registry: str = "1.0"
    portfolio_management: str = "1.0"
    knowledge: str = "1.0"
    analytics: str = "1.0"
    supported_exchanges: list[str] = field(
        default_factory=lambda: ["binance", "bybit", "okx", "kraken", "htx", "coinbase"]
    )
    market_types: list[str] = field(
        default_factory=lambda: ["spot", "futures", "options", "perpetual"]
    )
    dashboard_types: list[str] = field(
        default_factory=lambda: ["exchange", "portfolio", "market", "asset"]
    )
    knowledge_bases: list[str] = field(
        default_factory=lambda: ["crypto", "exchange", "asset", "market"]
    )


DEFAULT_CONFIG = CryptoEnterpriseConfig()
