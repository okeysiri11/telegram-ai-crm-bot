# Crypto Enterprise Platform — Sprint 16.4 Strategy Engine.

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class CryptoEnterpriseConfig:
    application_name: str = "Crypto Intelligence Platform"
    application: str = "crypto_enterprise"
    application_version: str = "4.7.4-enterprise"
    release_status: str = "Strategy Engine"
    platform_dependency: str = "AI Platform Core v3"
    enterprise_foundation: str = "Enterprise Platform v4.7.3-enterprise"
    ecosystem_dependency: str = "AI Ecosystem v1.5"
    api_version: str = "v1"
    api_prefix: str = "/api/crypto-enterprise/v1"
    technical_analysis_api_prefix: str = "/api/crypto-ta/v1"
    market_microstructure_api_prefix: str = "/api/crypto-mm/v1"
    market_intelligence_api_prefix: str = "/api/crypto-mi/v1"
    strategy_engine_api_prefix: str = "/api/crypto-se/v1"
    internal_prefix: str = "/internal/crypto-enterprise/v1"
    exchange_integration: str = "1.0"
    market_data: str = "1.0"
    asset_registry: str = "1.0"
    portfolio_management: str = "1.0"
    technical_analysis: str = "1.0"
    market_microstructure: str = "1.0"
    market_intelligence: str = "1.0"
    strategy_engine: str = "1.0"
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
