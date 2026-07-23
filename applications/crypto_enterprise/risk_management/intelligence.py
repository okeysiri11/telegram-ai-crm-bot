"""AI risk intelligence, dashboards, and knowledge."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.crypto_enterprise.shared.exceptions import ValidationError
from applications.crypto_enterprise.shared.store import CryptoEnterpriseStore, crypto_enterprise_store

DASHBOARD_TYPES = ["risk", "portfolio", "exposure", "capital", "ai_risk"]
REGISTRY_TYPES = ["risk", "portfolio", "exposure", "risk_model"]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class AIRiskIntelligence:
    def __init__(self, store: CryptoEnterpriseStore | None = None) -> None:
        self.store = store or crypto_enterprise_store

    def market_risk_score(self, *, symbol: str, score: float) -> dict[str, Any]:
        score = float(score)
        if score < 0 or score > 100:
            raise ValidationError("score must be 0..100")
        sid = _id("rm_mrs")
        return self.store.rm_ai_market.save(
            sid,
            {
                "score_id": sid,
                "symbol": symbol.upper(),
                "score": score,
                "band": "high" if score >= 70 else "medium" if score >= 40 else "low",
                "at": _now(),
            },
        )

    def portfolio_health(self, *, portfolio_id: str, score: float) -> dict[str, Any]:
        score = float(score)
        if score < 0 or score > 100:
            raise ValidationError("score must be 0..100")
        hid = _id("rm_ph")
        return self.store.rm_ai_health.save(
            hid,
            {
                "health_id": hid,
                "portfolio_id": portfolio_id,
                "score": score,
                "status": "healthy" if score >= 70 else "watch" if score >= 40 else "critical",
                "at": _now(),
            },
        )

    def capital_preservation(self, *, portfolio_id: str, score: float) -> dict[str, Any]:
        score = float(score)
        if score < 0 or score > 100:
            raise ValidationError("score must be 0..100")
        cid = _id("rm_cp")
        return self.store.rm_ai_capital.save(
            cid,
            {
                "preservation_id": cid,
                "portfolio_id": portfolio_id,
                "score": score,
                "at": _now(),
            },
        )

    def exposure_recommendation(self, *, portfolio_id: str, action: str, rationale: str) -> dict[str, Any]:
        if action not in ("increase", "decrease", "hold", "hedge"):
            raise ValidationError("action must be increase|decrease|hold|hedge")
        eid = _id("rm_exp_rec")
        return self.store.rm_ai_exposure.save(
            eid,
            {
                "recommendation_id": eid,
                "portfolio_id": portfolio_id,
                "action": action,
                "rationale": rationale,
                "at": _now(),
            },
        )

    def leverage_recommendation(self, *, symbol: str, max_leverage: float, rationale: str) -> dict[str, Any]:
        if max_leverage <= 0:
            raise ValidationError("max_leverage must be > 0")
        lid = _id("rm_lev")
        return self.store.rm_ai_leverage.save(
            lid,
            {
                "recommendation_id": lid,
                "symbol": symbol.upper(),
                "max_leverage": float(max_leverage),
                "rationale": rationale,
                "at": _now(),
            },
        )

    def trade_approval(
        self,
        *,
        symbol: str,
        side: str,
        size: float,
        risk_pct: float,
        approved: bool = True,
    ) -> dict[str, Any]:
        if side not in ("long", "short"):
            raise ValidationError("side must be long|short")
        aid = _id("rm_appr")
        return self.store.rm_ai_approvals.save(
            aid,
            {
                "approval_id": aid,
                "symbol": symbol.upper(),
                "side": side,
                "size": float(size),
                "risk_pct": float(risk_pct),
                "approved": bool(approved),
                "at": _now(),
            },
        )

    def warning(self, *, portfolio_id: str, severity: str, message: str) -> dict[str, Any]:
        if severity not in ("info", "warning", "critical"):
            raise ValidationError("severity must be info|warning|critical")
        wid = _id("rm_warn")
        return self.store.rm_ai_warnings.save(
            wid,
            {
                "warning_id": wid,
                "portfolio_id": portfolio_id,
                "severity": severity,
                "message": message,
                "at": _now(),
            },
        )

    def report(self, *, portfolio_id: str, narrative: str) -> dict[str, Any]:
        if not narrative:
            raise ValidationError("narrative required")
        rid = _id("rm_rpt")
        return self.store.rm_ai_reports.save(
            rid,
            {
                "report_id": rid,
                "portfolio_id": portfolio_id,
                "narrative": narrative,
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "market_risk": self.store.rm_ai_market.count(),
            "health": self.store.rm_ai_health.count(),
            "approvals": self.store.rm_ai_approvals.count(),
            "warnings": self.store.rm_ai_warnings.count(),
        }


class RiskDashboard:
    def __init__(self, store: CryptoEnterpriseStore | None = None) -> None:
        self.store = store or crypto_enterprise_store
        self.types = list(DASHBOARD_TYPES)

    def render(self, *, dashboard_type: str = "risk") -> dict[str, Any]:
        if dashboard_type not in self.types:
            raise ValidationError(f"dashboard_type must be one of {self.types}")
        metrics = {
            "risk": {
                "sizing": self.store.rm_sizing.count(),
                "loss_limits": self.store.rm_loss_limits.count(),
            },
            "portfolio": {
                "allocations": self.store.rm_allocations.count(),
                "rebalances": self.store.rm_rebalances.count(),
            },
            "exposure": {
                "portfolio_risk": self.store.rm_portfolio_risk.count(),
                "heatmaps": self.store.rm_heatmaps.count(),
            },
            "capital": {
                "efficiency": self.store.rm_efficiency.count(),
                "preservation": self.store.rm_ai_capital.count(),
            },
            "ai_risk": {
                "approvals": self.store.rm_ai_approvals.count(),
                "warnings": self.store.rm_ai_warnings.count(),
            },
        }[dashboard_type]
        did = _id("rm_dash")
        return self.store.rm_dashboards.save(
            did,
            {"dashboard_id": did, "dashboard_type": dashboard_type, "metrics": metrics, "generated_at": _now()},
        )

    def status(self) -> dict[str, Any]:
        return {"dashboards": self.store.rm_dashboards.count(), "types": self.types}


class RiskKnowledge:
    def __init__(self, store: CryptoEnterpriseStore | None = None) -> None:
        self.store = store or crypto_enterprise_store
        self.types = list(REGISTRY_TYPES)

    def publish(self, *, registry_type: str, key: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        if registry_type not in self.types:
            raise ValidationError(f"registry_type must be one of {self.types}")
        if not key:
            raise ValidationError("key required")
        rid = _id("rm_reg")
        return self.store.rm_registries.save(
            rid,
            {
                "registry_id": rid,
                "registry_type": registry_type,
                "key": key,
                "payload": payload or {},
                "graph_node": f"rm:{registry_type}:{key}",
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"entries": self.store.rm_registries.count(), "types": self.types}
