"""DeFi and NFT/token intelligence."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.crypto_enterprise.shared.exceptions import ValidationError
from applications.crypto_enterprise.shared.store import CryptoEnterpriseStore, crypto_enterprise_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class DeFiIntelligence:
    def __init__(self, store: CryptoEnterpriseStore | None = None) -> None:
        self.store = store or crypto_enterprise_store

    def tvl(self, *, protocol: str, chain: str, tvl_usd: float) -> dict[str, Any]:
        if not protocol:
            raise ValidationError("protocol required")
        tid = _id("oc_tvl")
        return self.store.oc_tvl.save(
            tid,
            {
                "tvl_id": tid,
                "protocol": protocol,
                "chain": chain,
                "tvl_usd": float(tvl_usd),
                "at": _now(),
            },
        )

    def liquidity_pool(self, *, protocol: str, pair: str, liquidity_usd: float) -> dict[str, Any]:
        lid = _id("oc_lp")
        return self.store.oc_pools.save(
            lid,
            {
                "pool_id": lid,
                "protocol": protocol,
                "pair": pair.upper(),
                "liquidity_usd": float(liquidity_usd),
                "at": _now(),
            },
        )

    def yield_protocol(self, *, protocol: str, apy: float, tvl_usd: float) -> dict[str, Any]:
        yid = _id("oc_yield")
        return self.store.oc_yields.save(
            yid,
            {
                "yield_id": yid,
                "protocol": protocol,
                "apy": float(apy),
                "tvl_usd": float(tvl_usd),
                "at": _now(),
            },
        )

    def dex_volume(self, *, dex: str, volume_usd: float, chain: str) -> dict[str, Any]:
        did = _id("oc_dexv")
        return self.store.oc_dex_volume.save(
            did,
            {
                "volume_id": did,
                "dex": dex,
                "volume_usd": float(volume_usd),
                "chain": chain,
                "at": _now(),
            },
        )

    def dex_whale(self, *, dex: str, wallet: str, volume_usd: float) -> dict[str, Any]:
        wid = _id("oc_dxw")
        return self.store.oc_dex_whales.save(
            wid,
            {
                "track_id": wid,
                "dex": dex,
                "wallet": wallet,
                "volume_usd": float(volume_usd),
                "at": _now(),
            },
        )

    def protocol_risk(self, *, protocol: str, risk_score: float) -> dict[str, Any]:
        risk_score = float(risk_score)
        if risk_score < 0 or risk_score > 100:
            raise ValidationError("risk_score must be 0..100")
        rid = _id("oc_prisk")
        return self.store.oc_protocol_risk.save(
            rid,
            {
                "risk_id": rid,
                "protocol": protocol,
                "risk_score": risk_score,
                "band": "high" if risk_score >= 70 else "medium" if risk_score >= 40 else "low",
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "tvl": self.store.oc_tvl.count(),
            "pools": self.store.oc_pools.count(),
            "dex_volume": self.store.oc_dex_volume.count(),
            "protocol_risk": self.store.oc_protocol_risk.count(),
        }


class NFTTokenIntelligence:
    def __init__(self, store: CryptoEnterpriseStore | None = None) -> None:
        self.store = store or crypto_enterprise_store

    def nft_activity(self, *, collection: str, volume_usd: float, sales: int) -> dict[str, Any]:
        nid = _id("oc_nft")
        return self.store.oc_nft.save(
            nid,
            {
                "activity_id": nid,
                "collection": collection,
                "volume_usd": float(volume_usd),
                "sales": int(sales),
                "at": _now(),
            },
        )

    def token_unlock(self, *, symbol: str, unlock_usd: float, unlock_at: str) -> dict[str, Any]:
        uid = _id("oc_unlk")
        return self.store.oc_unlocks.save(
            uid,
            {
                "unlock_id": uid,
                "symbol": symbol.upper(),
                "unlock_usd": float(unlock_usd),
                "unlock_at": unlock_at,
                "at": _now(),
            },
        )

    def vesting(self, *, symbol: str, schedule: list[dict[str, Any]]) -> dict[str, Any]:
        if not schedule:
            raise ValidationError("schedule required")
        vid = _id("oc_vest")
        return self.store.oc_vesting.save(
            vid,
            {
                "vesting_id": vid,
                "symbol": symbol.upper(),
                "schedule": schedule,
                "at": _now(),
            },
        )

    def governance(self, *, protocol: str, proposal: str, status: str = "active") -> dict[str, Any]:
        gid = _id("oc_gov")
        return self.store.oc_governance.save(
            gid,
            {
                "governance_id": gid,
                "protocol": protocol,
                "proposal": proposal,
                "status": status,
                "at": _now(),
            },
        )

    def treasury(self, *, protocol: str, balance_usd: float) -> dict[str, Any]:
        tid = _id("oc_treas")
        return self.store.oc_treasury.save(
            tid,
            {
                "treasury_id": tid,
                "protocol": protocol,
                "balance_usd": float(balance_usd),
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "nft": self.store.oc_nft.count(),
            "unlocks": self.store.oc_unlocks.count(),
            "governance": self.store.oc_governance.count(),
            "treasury": self.store.oc_treasury.count(),
        }
