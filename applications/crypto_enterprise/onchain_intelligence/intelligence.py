"""AI on-chain intelligence, dashboards, and knowledge."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.crypto_enterprise.shared.exceptions import ValidationError
from applications.crypto_enterprise.shared.store import CryptoEnterpriseStore, crypto_enterprise_store

DASHBOARD_TYPES = ["onchain", "whale", "stablecoin", "defi", "institution", "ai_blockchain"]
REGISTRY_TYPES = ["blockchain", "wallet", "transaction", "institution", "onchain_event"]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class AIOnChainIntelligence:
    def __init__(self, store: CryptoEnterpriseStore | None = None) -> None:
        self.store = store or crypto_enterprise_store

    def whale_activity(self, *, chain: str, intensity: float, side: str = "accumulate") -> dict[str, Any]:
        intensity = float(intensity)
        if intensity < 0 or intensity > 1:
            raise ValidationError("intensity must be 0..1")
        wid = _id("oc_awhale")
        return self.store.oc_ai_whale.save(
            wid,
            {
                "detection_id": wid,
                "chain": chain,
                "intensity": intensity,
                "side": side,
                "detected": intensity >= 0.55,
                "at": _now(),
            },
        )

    def institutional_accumulation(self, *, asset: str, amount_usd: float) -> dict[str, Any]:
        iid = _id("oc_ainst")
        return self.store.oc_ai_institutional.save(
            iid,
            {
                "detection_id": iid,
                "asset": asset.upper(),
                "amount_usd": float(amount_usd),
                "signal": "accumulation",
                "at": _now(),
            },
        )

    def distribution(self, *, asset: str, amount_usd: float) -> dict[str, Any]:
        did = _id("oc_adist")
        return self.store.oc_ai_distribution.save(
            did,
            {
                "detection_id": did,
                "asset": asset.upper(),
                "amount_usd": float(amount_usd),
                "signal": "distribution",
                "at": _now(),
            },
        )

    def smart_money(self, *, wallet: str, action: str, asset: str) -> dict[str, Any]:
        sid = _id("oc_asm")
        return self.store.oc_ai_smart_money.save(
            sid,
            {
                "track_id": sid,
                "wallet": wallet,
                "action": action,
                "asset": asset.upper(),
                "at": _now(),
            },
        )

    def capital_rotation(self, *, from_asset: str, to_asset: str, amount_usd: float) -> dict[str, Any]:
        cid = _id("oc_arot")
        return self.store.oc_ai_rotation.save(
            cid,
            {
                "rotation_id": cid,
                "from_asset": from_asset.upper(),
                "to_asset": to_asset.upper(),
                "amount_usd": float(amount_usd),
                "at": _now(),
            },
        )

    def network_health(self, *, chain: str, score: float) -> dict[str, Any]:
        score = float(score)
        if score < 0 or score > 100:
            raise ValidationError("score must be 0..100")
        nid = _id("oc_ahealth")
        return self.store.oc_ai_health.save(
            nid,
            {
                "health_id": nid,
                "chain": chain,
                "score": score,
                "status": "healthy" if score >= 70 else "watch" if score >= 40 else "stressed",
                "at": _now(),
            },
        )

    def blockchain_risk(self, *, chain: str, score: float) -> dict[str, Any]:
        score = float(score)
        if score < 0 or score > 100:
            raise ValidationError("score must be 0..100")
        rid = _id("oc_arisk")
        return self.store.oc_ai_risk.save(
            rid,
            {
                "risk_id": rid,
                "chain": chain,
                "score": score,
                "band": "high" if score >= 70 else "medium" if score >= 40 else "low",
                "at": _now(),
            },
        )

    def market_impact_forecast(self, *, asset: str, impact_pct: float, horizon: str = "7d") -> dict[str, Any]:
        fid = _id("oc_aimp")
        return self.store.oc_ai_impact.save(
            fid,
            {
                "forecast_id": fid,
                "asset": asset.upper(),
                "impact_pct": float(impact_pct),
                "horizon": horizon,
                "at": _now(),
            },
        )

    def report(self, *, title: str, narrative: str) -> dict[str, Any]:
        if not narrative:
            raise ValidationError("narrative required")
        rid = _id("oc_arpt")
        return self.store.oc_ai_reports.save(
            rid,
            {
                "report_id": rid,
                "title": title,
                "narrative": narrative,
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "whale": self.store.oc_ai_whale.count(),
            "institutional": self.store.oc_ai_institutional.count(),
            "health": self.store.oc_ai_health.count(),
            "reports": self.store.oc_ai_reports.count(),
        }


class OnChainDashboard:
    def __init__(self, store: CryptoEnterpriseStore | None = None) -> None:
        self.store = store or crypto_enterprise_store
        self.types = list(DASHBOARD_TYPES)

    def render(self, *, dashboard_type: str = "onchain") -> dict[str, Any]:
        if dashboard_type not in self.types:
            raise ValidationError(f"dashboard_type must be one of {self.types}")
        metrics = {
            "onchain": {
                "chains": self.store.oc_chains.count(),
                "transactions": self.store.oc_transactions.count(),
            },
            "whale": {
                "wallets": self.store.oc_whale_wallets.count(),
                "large_transfers": self.store.oc_large_transfers.count(),
            },
            "stablecoin": {
                "flows": self.store.oc_stable_flows.count(),
                "mints": self.store.oc_stable_mint.count(),
            },
            "defi": {
                "tvl": self.store.oc_tvl.count(),
                "pools": self.store.oc_pools.count(),
            },
            "institution": {
                "wallets": self.store.oc_inst_wallets.count(),
                "funds": self.store.oc_fund_wallets.count(),
            },
            "ai_blockchain": {
                "whale_signals": self.store.oc_ai_whale.count(),
                "reports": self.store.oc_ai_reports.count(),
            },
        }[dashboard_type]
        did = _id("oc_dash")
        return self.store.oc_dashboards.save(
            did,
            {"dashboard_id": did, "dashboard_type": dashboard_type, "metrics": metrics, "generated_at": _now()},
        )

    def status(self) -> dict[str, Any]:
        return {"dashboards": self.store.oc_dashboards.count(), "types": self.types}


class OnChainKnowledge:
    def __init__(self, store: CryptoEnterpriseStore | None = None) -> None:
        self.store = store or crypto_enterprise_store
        self.types = list(REGISTRY_TYPES)

    def publish(self, *, registry_type: str, key: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        if registry_type not in self.types:
            raise ValidationError(f"registry_type must be one of {self.types}")
        if not key:
            raise ValidationError("key required")
        rid = _id("oc_reg")
        return self.store.oc_registries.save(
            rid,
            {
                "registry_id": rid,
                "registry_type": registry_type,
                "key": key,
                "payload": payload or {},
                "graph_node": f"oc:{registry_type}:{key}",
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"entries": self.store.oc_registries.count(), "types": self.types}
