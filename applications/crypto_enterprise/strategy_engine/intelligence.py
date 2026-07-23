"""AI strategy intelligence, dashboards, and knowledge."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.crypto_enterprise.shared.exceptions import ValidationError
from applications.crypto_enterprise.shared.store import CryptoEnterpriseStore, crypto_enterprise_store

REGIMES = ["trending", "ranging", "volatile", "quiet"]
DASHBOARD_TYPES = ["strategy", "backtesting", "signal", "performance", "ai_strategy"]
REGISTRY_TYPES = ["strategy", "backtesting", "signal", "performance"]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class AIStrategyIntelligence:
    def __init__(self, store: CryptoEnterpriseStore | None = None) -> None:
        self.store = store or crypto_enterprise_store

    def evaluate(self, *, strategy_id: str, score: float) -> dict[str, Any]:
        score = float(score)
        if score < 0 or score > 100:
            raise ValidationError("score must be 0..100")
        eid = _id("se_eval")
        return self.store.se_evaluations.save(
            eid,
            {
                "evaluation_id": eid,
                "strategy_id": strategy_id,
                "score": score,
                "grade": "A" if score >= 80 else "B" if score >= 65 else "C" if score >= 50 else "D",
                "at": _now(),
            },
        )

    def detect_regime(self, *, symbol: str, regime: str, confidence: float) -> dict[str, Any]:
        if regime not in REGIMES:
            raise ValidationError(f"regime must be one of {REGIMES}")
        rid = _id("se_regm")
        return self.store.se_regimes.save(
            rid,
            {
                "regime_id": rid,
                "symbol": symbol.upper(),
                "regime": regime,
                "confidence": float(confidence),
                "at": _now(),
            },
        )

    def adaptive_select(self, *, symbol: str, strategy_ids: list[str], selected_id: str) -> dict[str, Any]:
        if selected_id not in strategy_ids:
            raise ValidationError("selected_id must be in strategy_ids")
        aid = _id("se_adapt")
        return self.store.se_adaptive.save(
            aid,
            {
                "selection_id": aid,
                "symbol": symbol.upper(),
                "candidates": strategy_ids,
                "selected_id": selected_id,
                "at": _now(),
            },
        )

    def optimize_strategy(self, *, strategy_id: str, improvement: float) -> dict[str, Any]:
        oid = _id("se_aiopt")
        return self.store.se_ai_optimize.save(
            oid,
            {
                "optimization_id": oid,
                "strategy_id": strategy_id,
                "improvement": float(improvement),
                "at": _now(),
            },
        )

    def scenario(self, *, strategy_id: str, name: str, outcome: str) -> dict[str, Any]:
        sid = _id("se_scen")
        return self.store.se_scenarios.save(
            sid,
            {
                "scenario_id": sid,
                "strategy_id": strategy_id,
                "name": name,
                "outcome": outcome,
                "at": _now(),
            },
        )

    def recommend(self, *, symbol: str, action: str, rationale: str) -> dict[str, Any]:
        if action not in ("long", "short", "hold", "reduce"):
            raise ValidationError("action must be long|short|hold|reduce")
        rid = _id("se_rec")
        return self.store.se_recommendations.save(
            rid,
            {
                "recommendation_id": rid,
                "symbol": symbol.upper(),
                "action": action,
                "rationale": rationale,
                "at": _now(),
            },
        )

    def explain(self, *, strategy_id: str, explanation: str) -> dict[str, Any]:
        if not explanation:
            raise ValidationError("explanation required")
        eid = _id("se_expl")
        return self.store.se_explanations.save(
            eid,
            {
                "explanation_id": eid,
                "strategy_id": strategy_id,
                "explanation": explanation,
                "at": _now(),
            },
        )

    def report(self, *, strategy_id: str, narrative: str) -> dict[str, Any]:
        if not narrative:
            raise ValidationError("narrative required")
        rid = _id("se_rpt")
        return self.store.se_reports.save(
            rid,
            {
                "report_id": rid,
                "strategy_id": strategy_id,
                "narrative": narrative,
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "evaluations": self.store.se_evaluations.count(),
            "regimes": self.store.se_regimes.count(),
            "recommendations": self.store.se_recommendations.count(),
            "reports": self.store.se_reports.count(),
        }


class StrategyDashboard:
    def __init__(self, store: CryptoEnterpriseStore | None = None) -> None:
        self.store = store or crypto_enterprise_store
        self.types = list(DASHBOARD_TYPES)

    def render(self, *, dashboard_type: str = "strategy") -> dict[str, Any]:
        if dashboard_type not in self.types:
            raise ValidationError(f"dashboard_type must be one of {self.types}")
        metrics = {
            "strategy": {
                "strategies": self.store.se_strategies.count(),
                "rules": self.store.se_rules.count(),
            },
            "backtesting": {
                "backtests": self.store.se_backtests.count(),
                "optimizations": self.store.se_optimizations.count(),
            },
            "signal": {
                "entries": self.store.se_entries.count(),
                "exits": self.store.se_exits.count(),
            },
            "performance": {
                "reports": self.store.se_performance.count(),
            },
            "ai_strategy": {
                "evaluations": self.store.se_evaluations.count(),
                "recommendations": self.store.se_recommendations.count(),
            },
        }[dashboard_type]
        did = _id("se_dash")
        return self.store.se_dashboards.save(
            did,
            {"dashboard_id": did, "dashboard_type": dashboard_type, "metrics": metrics, "generated_at": _now()},
        )

    def status(self) -> dict[str, Any]:
        return {"dashboards": self.store.se_dashboards.count(), "types": self.types}


class StrategyKnowledge:
    def __init__(self, store: CryptoEnterpriseStore | None = None) -> None:
        self.store = store or crypto_enterprise_store
        self.types = list(REGISTRY_TYPES)

    def publish(self, *, registry_type: str, key: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        if registry_type not in self.types:
            raise ValidationError(f"registry_type must be one of {self.types}")
        if not key:
            raise ValidationError("key required")
        rid = _id("se_reg")
        return self.store.se_registries.save(
            rid,
            {
                "registry_id": rid,
                "registry_type": registry_type,
                "key": key,
                "payload": payload or {},
                "graph_node": f"se:{registry_type}:{key}",
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"entries": self.store.se_registries.count(), "types": self.types}
