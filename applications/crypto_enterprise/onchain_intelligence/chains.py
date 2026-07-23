"""Blockchain integration and wallet intelligence."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.crypto_enterprise.shared.exceptions import ValidationError
from applications.crypto_enterprise.shared.store import CryptoEnterpriseStore, crypto_enterprise_store

CHAINS = [
    "bitcoin",
    "ethereum",
    "bnb",
    "solana",
    "tron",
    "polygon",
    "arbitrum",
    "optimism",
    "avalanche",
]
WALLET_TYPES = ["whale", "exchange", "institutional", "smart_money", "government", "fund", "unknown"]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class BlockchainIntegration:
    def __init__(self, store: CryptoEnterpriseStore | None = None) -> None:
        self.store = store or crypto_enterprise_store
        self.supported = list(CHAINS)

    def connect(self, *, chain: str, rpc_ref: str = "", status: str = "connected") -> dict[str, Any]:
        if chain not in CHAINS:
            raise ValidationError(f"chain must be one of {CHAINS}")
        cid = _id("oc_chain")
        return self.store.oc_chains.save(
            cid,
            {
                "connection_id": cid,
                "chain": chain,
                "rpc_ref": rpc_ref or f"vault://rpc/{chain}",
                "status": status,
                "at": _now(),
            },
        )

    def multi_chain(self, *, chains: list[str] | None = None) -> dict[str, Any]:
        selected = chains or list(CHAINS)
        for chain in selected:
            if chain not in CHAINS:
                raise ValidationError(f"chain must be one of {CHAINS}")
            if not any(c.get("chain") == chain for c in self.store.oc_chains.list_all()):
                self.connect(chain=chain)
        mid = _id("oc_multi")
        return self.store.oc_multi_chain.save(
            mid,
            {
                "bundle_id": mid,
                "chains": selected,
                "count": len(selected),
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "connections": self.store.oc_chains.count(),
            "multi_chain": self.store.oc_multi_chain.count(),
            "supported": self.supported,
        }


class WalletIntelligence:
    def __init__(self, store: CryptoEnterpriseStore | None = None) -> None:
        self.store = store or crypto_enterprise_store
        self.wallet_types = list(WALLET_TYPES)

    def register(
        self,
        *,
        address: str,
        chain: str,
        wallet_type: str,
        label: str = "",
        balance_usd: float = 0.0,
    ) -> dict[str, Any]:
        if not address:
            raise ValidationError("address required")
        if chain not in CHAINS:
            raise ValidationError(f"chain must be one of {CHAINS}")
        if wallet_type not in WALLET_TYPES:
            raise ValidationError(f"wallet_type must be one of {WALLET_TYPES}")
        wid = _id("oc_wal")
        store_map = {
            "whale": self.store.oc_whale_wallets,
            "exchange": self.store.oc_exchange_wallets,
            "institutional": self.store.oc_inst_wallets,
            "smart_money": self.store.oc_smart_wallets,
            "government": self.store.oc_gov_wallets,
            "fund": self.store.oc_fund_wallets,
            "unknown": self.store.oc_wallets,
        }
        return store_map[wallet_type].save(
            wid,
            {
                "wallet_id": wid,
                "address": address,
                "chain": chain,
                "wallet_type": wallet_type,
                "label": label or wallet_type,
                "balance_usd": float(balance_usd),
                "at": _now(),
            },
        )

    def classify(self, *, address: str, wallet_type: str, confidence: float) -> dict[str, Any]:
        if wallet_type not in WALLET_TYPES:
            raise ValidationError(f"wallet_type must be one of {WALLET_TYPES}")
        confidence = float(confidence)
        if confidence < 0 or confidence > 1:
            raise ValidationError("confidence must be 0..1")
        cid = _id("oc_wcls")
        return self.store.oc_wallet_class.save(
            cid,
            {
                "classification_id": cid,
                "address": address,
                "wallet_type": wallet_type,
                "confidence": confidence,
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "whale": self.store.oc_whale_wallets.count(),
            "exchange": self.store.oc_exchange_wallets.count(),
            "institutional": self.store.oc_inst_wallets.count(),
            "smart_money": self.store.oc_smart_wallets.count(),
            "classifications": self.store.oc_wallet_class.count(),
        }
