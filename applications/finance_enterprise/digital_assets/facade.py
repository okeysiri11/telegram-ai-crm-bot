"""Digital Assets Suite facade — Sprint 18.4."""

from __future__ import annotations

from typing import Any

from applications.finance_enterprise.config import DEFAULT_CONFIG
from applications.finance_enterprise.digital_assets.accounting import DigitalAssetAccounting
from applications.finance_enterprise.digital_assets.ai_assets import AIDigitalAssetIntelligence
from applications.finance_enterprise.digital_assets.exchange import ExchangeIntegration
from applications.finance_enterprise.digital_assets.operations import DigitalAssetOperations
from applications.finance_enterprise.digital_assets.registry import DigitalAssetRegistry
from applications.finance_enterprise.digital_assets.services import (
    DigitalAssetDashboard,
    DigitalAssetKnowledge,
)
from applications.finance_enterprise.digital_assets.wallets import CryptoWalletManagement
from applications.finance_enterprise.shared.store import FinanceEnterpriseStore, finance_enterprise_store


class DigitalAssetsSuite:
    def __init__(self, store: FinanceEnterpriseStore | None = None) -> None:
        self.store = store or finance_enterprise_store
        self.registry = DigitalAssetRegistry(self.store)
        self.wallets = CryptoWalletManagement(self.store)
        self.accounting = DigitalAssetAccounting(self.store)
        self.operations = DigitalAssetOperations(self.store)
        self.exchange = ExchangeIntegration(self.store)
        self.ai = AIDigitalAssetIntelligence(self.store)
        self.knowledge = DigitalAssetKnowledge(self.store)
        self.dashboard = DigitalAssetDashboard(self.store)

    def bootstrap(self) -> dict[str, Any]:
        btc = self.registry.register_asset(symbol="BTC", name="Bitcoin", network="bitcoin")
        eth = self.registry.register_asset(symbol="ETH", name="Ethereum", network="ethereum")
        usdt = self.registry.register_token(
            symbol="USDT", contract="0xdac17f958d2ee523a2206206994597c13d831ec7", network="ethereum"
        )
        bc_eth = self.registry.register_blockchain(network="ethereum", chain_id="1", native_symbol="ETH")
        bc_btc = self.registry.register_blockchain(network="bitcoin", chain_id="btc", native_symbol="BTC")
        for net in ("tron", "bnb", "polygon", "solana", "evm"):
            self.registry.register_blockchain(network=net)
        ex_acct = self.registry.register_exchange_account(
            exchange="binance", account_ref="BX-1001", label="Primary Binance"
        )
        custody = self.registry.register_custody(provider="Fireblocks", vault_ref="VAULT-1")

        hot = self.wallets.create_wallet(label="Ops Hot", wallet_type="hot", network="ethereum")
        cold = self.wallets.create_wallet(label="Cold Vault", wallet_type="cold", network="bitcoin")
        multi = self.wallets.create_wallet(label="Treasury MultiSig", wallet_type="multisig", network="ethereum")
        hd = self.wallets.create_wallet(label="HD Treasury", wallet_type="hd", network="ethereum")
        addr = self.wallets.add_address(
            wallet_id=hot["wallet_id"],
            address="0xabc123",
            derivation_path="m/44'/60'/0'/0/0",
        )
        self.wallets.update_balance(wallet_id=hot["wallet_id"], balance=12.5, asset="ETH")
        self.wallets.update_balance(wallet_id=cold["wallet_id"], balance=2.0, asset="BTC")

        buy = self.accounting.post_ledger(
            asset_symbol="ETH", quantity=10, unit_cost=3000, side="buy", wallet_id=hot["wallet_id"]
        )
        self.accounting.post_ledger(
            asset_symbol="ETH", quantity=2.5, unit_cost=3200, side="buy", wallet_id=hot["wallet_id"]
        )
        cb = self.accounting.cost_basis(asset_symbol="ETH")
        rpnl = self.accounting.realized_pnl(
            asset_symbol="ETH",
            sell_quantity=1,
            sell_price=3500,
            average_cost=cb["average_cost"],
        )
        upnl = self.accounting.unrealized_pnl(
            asset_symbol="ETH",
            quantity=11.5,
            market_price=3400,
            average_cost=cb["average_cost"],
        )
        rev = self.accounting.revalue(asset_symbol="ETH", new_price=3400, quantity=11.5)
        pval = self.accounting.portfolio_valuation(
            holdings=[
                {"symbol": "ETH", "quantity": 11.5, "price": 3400},
                {"symbol": "BTC", "quantity": 2.0, "price": 65000},
            ]
        )

        dep = self.operations.operate(
            operation="deposit", asset_symbol="ETH", amount=5, to_ref=hot["wallet_id"]
        )
        wd = self.operations.operate(
            operation="withdrawal", asset_symbol="ETH", amount=1, from_ref=hot["wallet_id"]
        )
        xfer = self.operations.operate(
            operation="internal_transfer",
            asset_symbol="ETH",
            amount=0.5,
            from_ref=hot["wallet_id"],
            to_ref=multi["wallet_id"],
        )
        otc = self.operations.operate(
            operation="otc_settlement", asset_symbol="BTC", amount=0.1, detail="OTC desk"
        )
        xw = self.operations.operate(
            operation="cross_wallet",
            asset_symbol="ETH",
            amount=0.2,
            from_ref=hot["wallet_id"],
            to_ref=hd["wallet_id"],
        )
        reb = self.operations.operate(
            operation="rebalance", asset_symbol="USDT", amount=10000, detail="target weights"
        )

        link = self.exchange.link_account(exchange="binance", account_ref="BX-1001")
        sync = self.exchange.sync_balances(
            link_id=link["link_id"],
            balances=[{"symbol": "USDT", "balance": 50000}, {"symbol": "ETH", "balance": 3}],
        )
        trade = self.exchange.import_trade(
            link_id=link["link_id"], symbol="ETHUSDT", side="buy", quantity=1, price=3400, fee=3.4
        )
        xfer_imp = self.exchange.import_transfer(
            link_id=link["link_id"], asset="USDT", amount=10000, direction="in"
        )
        xrec = self.exchange.reconcile(link_id=link["link_id"], books_total=50000, exchange_total=50003.4)

        ai_port = self.ai.insight(insight_type="portfolio_risk", subject="treasury", score=0.42)
        ai_wal = self.ai.insight(insight_type="wallet_risk", subject=hot["wallet_id"], score=0.55)
        ai_exp = self.ai.insight(insight_type="market_exposure", subject="ETH", score=0.61)
        ai_opt = self.ai.insight(insight_type="treasury_optimization", subject="FY2026")
        ai_liq = self.ai.insight(insight_type="liquidity_recommendation", subject="USDT", score=0.7)
        ai_nl = self.ai.nl_report(audience="cfo")

        self.knowledge.publish(base="digital_asset", key=eth["asset_id"], payload={"symbol": "ETH"})
        self.knowledge.publish(base="wallet", key=hot["wallet_id"], payload={"type": "hot"})
        self.knowledge.publish(base="blockchain", key=bc_eth["blockchain_id"], payload={"network": "ethereum"})
        self.knowledge.publish(base="exchange", key=link["link_id"], payload={"exchange": "binance"})
        self.knowledge.publish(base="treasury", key=dep["operation_id"], payload={"operation": "deposit"})

        dash_da = self.dashboard.render(dashboard_type="digital_assets")
        dash_t = self.dashboard.render(dashboard_type="treasury")
        dash_p = self.dashboard.render(dashboard_type="portfolio")
        dash_w = self.dashboard.render(dashboard_type="wallets")
        dash_e = self.dashboard.render(dashboard_type="exchange")

        return {
            "bootstrap": True,
            "btc_id": btc["asset_id"],
            "eth_id": eth["asset_id"],
            "usdt_id": usdt["token_id"],
            "blockchain_eth_id": bc_eth["blockchain_id"],
            "blockchain_btc_id": bc_btc["blockchain_id"],
            "exchange_account_id": ex_acct["exchange_account_id"],
            "custody_id": custody["custody_id"],
            "hot_wallet_id": hot["wallet_id"],
            "cold_wallet_id": cold["wallet_id"],
            "multisig_wallet_id": multi["wallet_id"],
            "hd_wallet_id": hd["wallet_id"],
            "address_id": addr["address_id"],
            "ledger_id": buy["ledger_id"],
            "cost_basis_id": cb["cost_basis_id"],
            "realized_id": rpnl["realized_id"],
            "unrealized_id": upnl["unrealized_id"],
            "revaluation_id": rev["revaluation_id"],
            "portfolio_valuation_id": pval["valuation_id"],
            "deposit_id": dep["operation_id"],
            "withdrawal_id": wd["operation_id"],
            "internal_transfer_id": xfer["operation_id"],
            "otc_id": otc["operation_id"],
            "cross_wallet_id": xw["operation_id"],
            "rebalance_id": reb["operation_id"],
            "link_id": link["link_id"],
            "sync_id": sync["sync_id"],
            "trade_id": trade["trade_id"],
            "transfer_id": xfer_imp["transfer_id"],
            "exchange_recon_id": xrec["reconciliation_id"],
            "ai_portfolio_id": ai_port["insight_id"],
            "ai_wallet_id": ai_wal["insight_id"],
            "ai_exposure_id": ai_exp["insight_id"],
            "ai_optimization_id": ai_opt["insight_id"],
            "ai_liquidity_id": ai_liq["insight_id"],
            "ai_nl_id": ai_nl["insight_id"],
            "dashboard_digital_assets_id": dash_da["dashboard_id"],
            "dashboard_treasury_id": dash_t["dashboard_id"],
            "dashboard_portfolio_id": dash_p["dashboard_id"],
            "dashboard_wallets_id": dash_w["dashboard_id"],
            "dashboard_exchange_id": dash_e["dashboard_id"],
            "version": DEFAULT_CONFIG.application_version,
        }

    def status(self) -> dict[str, Any]:
        return {
            "registry": self.registry.status(),
            "wallets": self.wallets.status(),
            "accounting": self.accounting.status(),
            "operations": self.operations.status(),
            "exchange": self.exchange.status(),
            "ai": self.ai.status(),
            "knowledge": self.knowledge.status(),
            "dashboard": self.dashboard.status(),
        }


digital_assets = DigitalAssetsSuite()
