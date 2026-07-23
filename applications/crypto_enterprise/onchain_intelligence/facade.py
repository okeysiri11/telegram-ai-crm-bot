"""On-Chain Intelligence Suite facade — Sprint 16.6."""

from __future__ import annotations

from typing import Any

from applications.crypto_enterprise.config import DEFAULT_CONFIG
from applications.crypto_enterprise.onchain_intelligence.chains import BlockchainIntegration, WalletIntelligence
from applications.crypto_enterprise.onchain_intelligence.defi import DeFiIntelligence, NFTTokenIntelligence
from applications.crypto_enterprise.onchain_intelligence.intelligence import (
    AIOnChainIntelligence,
    OnChainDashboard,
    OnChainKnowledge,
)
from applications.crypto_enterprise.onchain_intelligence.transactions import (
    StablecoinIntelligence,
    TransactionIntelligence,
)
from applications.crypto_enterprise.shared.store import CryptoEnterpriseStore, crypto_enterprise_store


class OnChainIntelligenceSuite:
    def __init__(self, store: CryptoEnterpriseStore | None = None) -> None:
        self.store = store or crypto_enterprise_store
        self.chains = BlockchainIntegration(self.store)
        self.wallets = WalletIntelligence(self.store)
        self.transactions = TransactionIntelligence(self.store)
        self.stablecoins = StablecoinIntelligence(self.store)
        self.defi = DeFiIntelligence(self.store)
        self.nft = NFTTokenIntelligence(self.store)
        self.ai = AIOnChainIntelligence(self.store)
        self.dashboard = OnChainDashboard(self.store)
        self.knowledge = OnChainKnowledge(self.store)

    def bootstrap(self) -> dict[str, Any]:
        eth = self.chains.connect(chain="ethereum")
        for chain in (
            "bitcoin",
            "bnb",
            "solana",
            "tron",
            "polygon",
            "arbitrum",
            "optimism",
            "avalanche",
        ):
            self.chains.connect(chain=chain)
        multi = self.chains.multi_chain()

        whale = self.wallets.register(
            address="0xwhale0001",
            chain="ethereum",
            wallet_type="whale",
            label="Mega Whale",
            balance_usd=420_000_000,
        )
        self.wallets.register(
            address="0xbinancehot",
            chain="ethereum",
            wallet_type="exchange",
            label="Binance Hot",
            balance_usd=1_200_000_000,
        )
        inst = self.wallets.register(
            address="0xblackrock01",
            chain="ethereum",
            wallet_type="institutional",
            label="IBIT Custodian",
            balance_usd=8_500_000_000,
        )
        self.wallets.register(
            address="0xsmartmoney1",
            chain="ethereum",
            wallet_type="smart_money",
            label="Smart Money Desk",
            balance_usd=85_000_000,
        )
        self.wallets.register(
            address="0xgovreserve",
            chain="bitcoin",
            wallet_type="government",
            label="Sovereign Reserve",
            balance_usd=2_100_000_000,
        )
        self.wallets.register(
            address="0xfundalpha",
            chain="ethereum",
            wallet_type="fund",
            label="Crypto Macro Fund",
            balance_usd=650_000_000,
        )
        self.wallets.classify(address="0xwhale0001", wallet_type="whale", confidence=0.94)

        tx = self.transactions.monitor(
            chain="ethereum",
            tx_hash="0xtxbootstrap01",
            from_addr="0xwhale0001",
            to_addr="0xbinancehot",
            amount_usd=48_000_000,
            asset="ETH",
        )
        large = self.transactions.large_transfer(chain="ethereum", amount_usd=48_000_000, asset="ETH")
        self.transactions.cross_chain(from_chain="ethereum", to_chain="arbitrum", amount_usd=12_000_000, asset="ETH")
        self.transactions.exchange_flow(direction="inflow", exchange="binance", amount_usd=48_000_000, asset="ETH")
        self.transactions.exchange_flow(direction="outflow", exchange="coinbase", amount_usd=22_000_000, asset="BTC")
        self.transactions.bridge(bridge="stargate", from_chain="ethereum", to_chain="optimism", amount_usd=5_000_000)
        self.transactions.smart_contract(chain="ethereum", contract="0xuniswapv3", method="swap", value_usd=2_400_000)
        self.transactions.mint_burn(asset="ETH", action="burn", amount=1200, chain="ethereum")

        stable = self.stablecoins.flow(stablecoin="USDT", direction="inflow", amount_usd=320_000_000, chain="tron")
        self.stablecoins.flow(stablecoin="USDC", direction="outflow", amount_usd=95_000_000, chain="ethereum")
        self.stablecoins.flow(stablecoin="DAI", direction="inflow", amount_usd=18_000_000, chain="ethereum")
        self.stablecoins.mint(stablecoin="USDT", amount=500_000_000, chain="ethereum")
        self.stablecoins.burn(stablecoin="USDC", amount=80_000_000, chain="ethereum")
        self.stablecoins.liquidity_expansion(stablecoin="USDT", expansion_usd=420_000_000)

        tvl = self.defi.tvl(protocol="Aave", chain="ethereum", tvl_usd=12_500_000_000)
        self.defi.liquidity_pool(protocol="Uniswap", pair="ETH/USDC", liquidity_usd=480_000_000)
        self.defi.yield_protocol(protocol="Lido", apy=3.2, tvl_usd=28_000_000_000)
        self.defi.dex_volume(dex="Uniswap", volume_usd=1_800_000_000, chain="ethereum")
        self.defi.dex_whale(dex="Uniswap", wallet="0xwhale0001", volume_usd=65_000_000)
        self.defi.protocol_risk(protocol="Aave", risk_score=28)

        self.nft.nft_activity(collection="CryptoPunks", volume_usd=12_500_000, sales=84)
        self.nft.token_unlock(symbol="ARB", unlock_usd=95_000_000, unlock_at="2026-08-15T00:00:00Z")
        self.nft.vesting(symbol="OP", schedule=[{"date": "2026-09-01", "amount_usd": 40_000_000}])
        self.nft.governance(protocol="Uniswap", proposal="Fee Switch v2", status="active")
        self.nft.treasury(protocol="ENS", balance_usd=820_000_000)

        whale_ai = self.ai.whale_activity(chain="ethereum", intensity=0.81, side="distribute")
        self.ai.institutional_accumulation(asset="BTC", amount_usd=1_200_000_000)
        self.ai.distribution(asset="ETH", amount_usd=48_000_000)
        self.ai.smart_money(wallet="0xsmartmoney1", action="buy", asset="SOL")
        self.ai.capital_rotation(from_asset="ETH", to_asset="BTC", amount_usd=210_000_000)
        health = self.ai.network_health(chain="ethereum", score=84)
        self.ai.blockchain_risk(chain="ethereum", score=22)
        self.ai.market_impact_forecast(asset="ETH", impact_pct=-1.8, horizon="3d")
        report = self.ai.report(
            title="Whale Distribution Alert",
            narrative="Large ETH transfer into Binance coincides with elevated stablecoin inflows on Tron.",
        )

        for rtype, key in (
            ("blockchain", eth["connection_id"]),
            ("wallet", whale["wallet_id"]),
            ("transaction", tx["tx_id"]),
            ("institution", inst["wallet_id"]),
            ("onchain_event", large["transfer_id"]),
        ):
            self.knowledge.publish(registry_type=rtype, key=key, payload={"bootstrap": True})

        dash = self.dashboard.render(dashboard_type="onchain")
        return {
            "bootstrap": True,
            "eth_connection_id": eth["connection_id"],
            "multi_chain_id": multi["bundle_id"],
            "whale_wallet_id": whale["wallet_id"],
            "institution_wallet_id": inst["wallet_id"],
            "tx_id": tx["tx_id"],
            "large_transfer_id": large["transfer_id"],
            "stable_flow_id": stable["flow_id"],
            "tvl_id": tvl["tvl_id"],
            "whale_ai_id": whale_ai["detection_id"],
            "health_id": health["health_id"],
            "report_id": report["report_id"],
            "dashboard_id": dash["dashboard_id"],
            "version": DEFAULT_CONFIG.application_version,
        }

    def status(self) -> dict[str, Any]:
        return {
            "chains": self.chains.status(),
            "wallets": self.wallets.status(),
            "transactions": self.transactions.status(),
            "stablecoins": self.stablecoins.status(),
            "defi": self.defi.status(),
            "nft": self.nft.status(),
            "ai": self.ai.status(),
            "dashboard": self.dashboard.status(),
            "knowledge": self.knowledge.status(),
        }


onchain_intelligence = OnChainIntelligenceSuite()
