"""Transaction and stablecoin intelligence."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.crypto_enterprise.shared.exceptions import ValidationError
from applications.crypto_enterprise.onchain_intelligence.chains import CHAINS
from applications.crypto_enterprise.shared.store import CryptoEnterpriseStore, crypto_enterprise_store

STABLECOINS = ["USDT", "USDC", "DAI"]
FLOW_DIRECTIONS = ["inflow", "outflow"]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class TransactionIntelligence:
    def __init__(self, store: CryptoEnterpriseStore | None = None) -> None:
        self.store = store or crypto_enterprise_store

    def monitor(
        self,
        *,
        chain: str,
        tx_hash: str,
        from_addr: str,
        to_addr: str,
        amount_usd: float,
        asset: str = "ETH",
    ) -> dict[str, Any]:
        if chain not in CHAINS:
            raise ValidationError(f"chain must be one of {CHAINS}")
        if not tx_hash:
            raise ValidationError("tx_hash required")
        tid = _id("oc_tx")
        return self.store.oc_transactions.save(
            tid,
            {
                "tx_id": tid,
                "chain": chain,
                "tx_hash": tx_hash,
                "from_addr": from_addr,
                "to_addr": to_addr,
                "amount_usd": float(amount_usd),
                "asset": asset.upper(),
                "at": _now(),
            },
        )

    def large_transfer(self, *, chain: str, amount_usd: float, asset: str, threshold_usd: float = 1_000_000) -> dict[str, Any]:
        lid = _id("oc_large")
        return self.store.oc_large_transfers.save(
            lid,
            {
                "transfer_id": lid,
                "chain": chain,
                "amount_usd": float(amount_usd),
                "asset": asset.upper(),
                "threshold_usd": float(threshold_usd),
                "flagged": float(amount_usd) >= float(threshold_usd),
                "at": _now(),
            },
        )

    def cross_chain(self, *, from_chain: str, to_chain: str, amount_usd: float, asset: str) -> dict[str, Any]:
        cid = _id("oc_xchain")
        return self.store.oc_cross_chain.save(
            cid,
            {
                "transfer_id": cid,
                "from_chain": from_chain,
                "to_chain": to_chain,
                "amount_usd": float(amount_usd),
                "asset": asset.upper(),
                "at": _now(),
            },
        )

    def exchange_flow(self, *, direction: str, exchange: str, amount_usd: float, asset: str) -> dict[str, Any]:
        if direction not in FLOW_DIRECTIONS:
            raise ValidationError("direction must be inflow|outflow")
        fid = _id("oc_xflow")
        store = self.store.oc_exchange_inflow if direction == "inflow" else self.store.oc_exchange_outflow
        return store.save(
            fid,
            {
                "flow_id": fid,
                "direction": direction,
                "exchange": exchange.lower(),
                "amount_usd": float(amount_usd),
                "asset": asset.upper(),
                "at": _now(),
            },
        )

    def bridge(self, *, bridge: str, from_chain: str, to_chain: str, amount_usd: float) -> dict[str, Any]:
        bid = _id("oc_bridge")
        return self.store.oc_bridges.save(
            bid,
            {
                "bridge_id": bid,
                "bridge": bridge,
                "from_chain": from_chain,
                "to_chain": to_chain,
                "amount_usd": float(amount_usd),
                "at": _now(),
            },
        )

    def smart_contract(self, *, chain: str, contract: str, method: str, value_usd: float = 0.0) -> dict[str, Any]:
        sid = _id("oc_sc")
        return self.store.oc_contracts.save(
            sid,
            {
                "activity_id": sid,
                "chain": chain,
                "contract": contract,
                "method": method,
                "value_usd": float(value_usd),
                "at": _now(),
            },
        )

    def mint_burn(self, *, asset: str, action: str, amount: float, chain: str) -> dict[str, Any]:
        if action not in ("mint", "burn"):
            raise ValidationError("action must be mint|burn")
        mid = _id("oc_mb")
        return self.store.oc_mint_burn.save(
            mid,
            {
                "event_id": mid,
                "asset": asset.upper(),
                "action": action,
                "amount": float(amount),
                "chain": chain,
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "transactions": self.store.oc_transactions.count(),
            "large_transfers": self.store.oc_large_transfers.count(),
            "bridges": self.store.oc_bridges.count(),
            "mint_burn": self.store.oc_mint_burn.count(),
        }


class StablecoinIntelligence:
    def __init__(self, store: CryptoEnterpriseStore | None = None) -> None:
        self.store = store or crypto_enterprise_store

    def flow(self, *, stablecoin: str, direction: str, amount_usd: float, chain: str) -> dict[str, Any]:
        if stablecoin.upper() not in STABLECOINS:
            raise ValidationError(f"stablecoin must be one of {STABLECOINS}")
        if direction not in FLOW_DIRECTIONS:
            raise ValidationError("direction must be inflow|outflow")
        fid = _id("oc_sflow")
        return self.store.oc_stable_flows.save(
            fid,
            {
                "flow_id": fid,
                "stablecoin": stablecoin.upper(),
                "direction": direction,
                "amount_usd": float(amount_usd),
                "chain": chain,
                "at": _now(),
            },
        )

    def mint(self, *, stablecoin: str, amount: float, chain: str) -> dict[str, Any]:
        mid = _id("oc_smint")
        return self.store.oc_stable_mint.save(
            mid,
            {
                "event_id": mid,
                "stablecoin": stablecoin.upper(),
                "amount": float(amount),
                "chain": chain,
                "action": "mint",
                "at": _now(),
            },
        )

    def burn(self, *, stablecoin: str, amount: float, chain: str) -> dict[str, Any]:
        bid = _id("oc_sburn")
        return self.store.oc_stable_burn.save(
            bid,
            {
                "event_id": bid,
                "stablecoin": stablecoin.upper(),
                "amount": float(amount),
                "chain": chain,
                "action": "burn",
                "at": _now(),
            },
        )

    def liquidity_expansion(self, *, stablecoin: str, expansion_usd: float) -> dict[str, Any]:
        lid = _id("oc_sexp")
        return self.store.oc_stable_expansion.save(
            lid,
            {
                "expansion_id": lid,
                "stablecoin": stablecoin.upper(),
                "expansion_usd": float(expansion_usd),
                "detected": float(expansion_usd) > 0,
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "flows": self.store.oc_stable_flows.count(),
            "mints": self.store.oc_stable_mint.count(),
            "burns": self.store.oc_stable_burn.count(),
            "expansions": self.store.oc_stable_expansion.count(),
        }
