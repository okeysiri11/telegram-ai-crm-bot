# CryptoEnterpriseApplication — Sprint 16.0 foundation.

from __future__ import annotations

from typing import Any

from applications.crypto_enterprise.assets import AssetRegistry
from applications.crypto_enterprise.config import DEFAULT_CONFIG, CryptoEnterpriseConfig
from applications.crypto_enterprise.exchanges import ExchangeIntegration
from applications.crypto_enterprise.market_microstructure.facade import MarketMicrostructureSuite
from applications.crypto_enterprise.markets import MarketData
from applications.crypto_enterprise.portfolio import PortfolioManagement
from applications.crypto_enterprise.services import CryptoDashboard, CryptoKnowledge
from applications.crypto_enterprise.shared.store import CryptoEnterpriseStore, crypto_enterprise_store
from applications.crypto_enterprise.technical_analysis.facade import TechnicalAnalysisSuite


class CryptoEnterpriseApplication:
    def __init__(
        self,
        *,
        config: CryptoEnterpriseConfig | None = None,
        store: CryptoEnterpriseStore | None = None,
        technical_analysis_svc: TechnicalAnalysisSuite | None = None,
        market_microstructure_svc: MarketMicrostructureSuite | None = None,
    ) -> None:
        self.config = config or DEFAULT_CONFIG
        self.store = store or crypto_enterprise_store
        self.exchanges = ExchangeIntegration(self.store)
        self.markets = MarketData(self.store)
        self.assets = AssetRegistry(self.store)
        self.portfolio = PortfolioManagement(self.store)
        self.dashboard = CryptoDashboard(self.store)
        self.knowledge = CryptoKnowledge(self.store)
        self.technical_analysis = technical_analysis_svc or TechnicalAnalysisSuite(self.store)
        self.market_microstructure = market_microstructure_svc or MarketMicrostructureSuite(self.store)

    def reset(self) -> None:
        self.store.reset()

    def bootstrap(self) -> dict[str, Any]:
        binance = self.exchanges.integrate_binance()
        bybit = self.exchanges.integrate_bybit()
        okx = self.exchanges.integrate_okx()
        kraken = self.exchanges.integrate_kraken()
        htx = self.exchanges.integrate_htx()
        coinbase = self.exchanges.integrate_coinbase()

        eth = self.assets.register_blockchain(name="Ethereum", chain_id="1", native_symbol="ETH")
        btc_chain = self.assets.register_blockchain(name="Bitcoin", chain_id="bitcoin", native_symbol="BTC")
        btc = self.assets.register_coin(symbol="BTC", name="Bitcoin", blockchain_id=btc_chain["blockchain_id"])
        eth_coin = self.assets.register_coin(symbol="ETH", name="Ethereum", blockchain_id=eth["blockchain_id"])
        usdt = self.assets.register_stablecoin(
            symbol="USDT", name="Tether", peg="USD", blockchain_id=eth["blockchain_id"]
        )
        self.assets.register_token(
            symbol="UNI",
            name="Uniswap",
            blockchain_id=eth["blockchain_id"],
            contract="0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984",
        )
        pair = self.assets.register_pair(base="BTC", quote="USDT")

        spot = self.markets.register_spot(
            symbol="BTCUSDT",
            base="BTC",
            quote="USDT",
            exchange_id=binance["exchange"]["exchange_id"],
        )
        self.markets.register_futures(
            symbol="BTCUSDT-FQ",
            base="BTC",
            quote="USDT",
            exchange_id=binance["exchange"]["exchange_id"],
            expiry="2026-12-25",
        )
        self.markets.register_options(
            symbol="BTC-C-100000",
            base="BTC",
            quote="USDT",
            exchange_id=okx["exchange"]["exchange_id"],
            option_type="call",
        )
        perp = self.markets.register_perpetual(
            symbol="BTCUSDT-PERP",
            base="BTC",
            quote="USDT",
            exchange_id=bybit["exchange"]["exchange_id"],
        )
        ticker = self.markets.ticker(symbol="BTCUSDT", last=68000.0, bid=67990.0, ask=68010.0, volume=1200.5)
        self.markets.candle(
            symbol="BTCUSDT",
            interval="1h",
            open_=67500,
            high=68200,
            low=67400,
            close=68000,
            volume=350.2,
        )
        self.markets.historical(
            symbol="BTCUSDT",
            from_ts="2026-01-01T00:00:00Z",
            to_ts="2026-07-01T00:00:00Z",
            bars=4320,
        )
        stream = self.markets.stream(symbol="BTCUSDT", channel="trades")

        pf = self.portfolio.register_portfolio(name="Core Crypto", owner="treasury", base_currency="USD")
        wallet = self.portfolio.register_wallet(
            portfolio_id=pf["portfolio_id"],
            address="bc1qexample",
            blockchain_id=btc_chain["blockchain_id"],
            label="cold",
        )
        self.portfolio.allocate(portfolio_id=pf["portfolio_id"], asset="BTC", weight_pct=55, amount=1.5)
        self.portfolio.allocate(portfolio_id=pf["portfolio_id"], asset="ETH", weight_pct=30, amount=20)
        self.portfolio.allocate(portfolio_id=pf["portfolio_id"], asset="USDT", weight_pct=15, amount=50000)
        pnl = self.portfolio.track_pnl(portfolio_id=pf["portfolio_id"], realized=12000, unrealized=8500)
        bal = self.portfolio.balance_snapshot(
            portfolio_id=pf["portfolio_id"],
            balances={"BTC": 1.5, "ETH": 20, "USDT": 50000},
            total_value=185000,
        )

        for base, key in (
            ("crypto", pf["portfolio_id"]),
            ("exchange", binance["exchange"]["exchange_id"]),
            ("asset", btc["coin_id"]),
            ("market", spot["market_id"]),
        ):
            self.knowledge.publish(base=base, key=key, payload={"bootstrap": True})

        dash = self.dashboard.render(dashboard_type="market")
        return {
            "bootstrap": True,
            "binance_id": binance["exchange"]["exchange_id"],
            "bybit_id": bybit["exchange"]["exchange_id"],
            "okx_id": okx["exchange"]["exchange_id"],
            "kraken_id": kraken["exchange"]["exchange_id"],
            "htx_id": htx["exchange"]["exchange_id"],
            "coinbase_id": coinbase["exchange"]["exchange_id"],
            "btc_id": btc["coin_id"],
            "eth_id": eth_coin["coin_id"],
            "usdt_id": usdt["stablecoin_id"],
            "pair_id": pair["pair_id"],
            "spot_id": spot["market_id"],
            "perp_id": perp["market_id"],
            "ticker_id": ticker["ticker_id"],
            "stream_id": stream["stream_id"],
            "portfolio_id": pf["portfolio_id"],
            "wallet_id": wallet["wallet_id"],
            "pnl_id": pnl["pnl_id"],
            "balance_id": bal["balance_id"],
            "dashboard_id": dash["dashboard_id"],
            "version": self.config.application_version,
        }

    def health(self) -> dict[str, Any]:
        return {
            "status": "ok",
            "application": self.config.application,
            "application_name": self.config.application_name,
            "application_version": self.config.application_version,
            "release_status": self.config.release_status,
            "enterprise_foundation": self.config.enterprise_foundation,
            "platform_dependency": self.config.platform_dependency,
            "ecosystem_dependency": self.config.ecosystem_dependency,
            "api_prefix": self.config.api_prefix,
            "crypto_enterprise_foundation_ready": True,
            "exchange_integration_ready": True,
            "market_data_ready": True,
            "portfolio_platform_ready": True,
            "tradingview_integration_ready": True,
            "technical_analysis_ready": True,
            "pattern_recognition_ready": True,
            "ai_technical_intelligence_ready": True,
            "order_book_intelligence_ready": True,
            "trade_flow_analytics_ready": True,
            "derivatives_intelligence_ready": True,
            "liquidity_intelligence_ready": True,
            "ai_market_interpretation_ready": True,
            "engines": {
                "exchange_integration": self.config.exchange_integration,
                "market_data": self.config.market_data,
                "asset_registry": self.config.asset_registry,
                "portfolio_management": self.config.portfolio_management,
                "technical_analysis": self.config.technical_analysis,
                "market_microstructure": self.config.market_microstructure,
                "knowledge": self.config.knowledge,
                "analytics": self.config.analytics,
            },
            "exchanges": self.exchanges.status(),
            "markets": self.markets.status(),
            "assets": self.assets.status(),
            "portfolio": self.portfolio.status(),
            "knowledge": self.knowledge.status(),
            "dashboard": self.dashboard.status(),
            "technical_analysis": self.technical_analysis.status(),
            "market_microstructure": self.market_microstructure.status(),
        }


crypto_enterprise = CryptoEnterpriseApplication()
