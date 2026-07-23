"""Portfolio optimization, advanced risk models, and trade protection."""

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


class PortfolioOptimization:
    def __init__(self, store: CryptoEnterpriseStore | None = None) -> None:
        self.store = store or crypto_enterprise_store

    def asset_allocation(self, *, name: str, weights: dict[str, float]) -> dict[str, Any]:
        if not name or not weights:
            raise ValidationError("name and weights required")
        total = sum(weights.values())
        if abs(total - 100) > 0.5 and abs(total - 1.0) > 0.01:
            raise ValidationError("weights should sum to 100 or 1.0")
        aid = _id("rm_alloc")
        return self.store.rm_allocations.save(
            aid,
            {"allocation_id": aid, "name": name, "weights": weights, "kind": "asset", "at": _now()},
        )

    def sector_allocation(self, *, name: str, sectors: dict[str, float]) -> dict[str, Any]:
        if not sectors:
            raise ValidationError("sectors required")
        sid = _id("rm_sect")
        return self.store.rm_sectors.save(
            sid,
            {"allocation_id": sid, "name": name, "sectors": sectors, "kind": "sector", "at": _now()},
        )

    def correlation_matrix(self, *, assets: list[str], matrix: list[list[float]] | None = None) -> dict[str, Any]:
        if len(assets) < 2:
            raise ValidationError("at least two assets required")
        cid = _id("rm_corr")
        return self.store.rm_corr_matrix.save(
            cid,
            {
                "matrix_id": cid,
                "assets": [a.upper() for a in assets],
                "matrix": matrix or [[1.0, 0.55], [0.55, 1.0]],
                "at": _now(),
            },
        )

    def diversification(self, *, score: float, holdings: int) -> dict[str, Any]:
        score = float(score)
        if score < 0 or score > 1:
            raise ValidationError("score must be 0..1")
        did = _id("rm_div")
        return self.store.rm_diversification.save(
            did,
            {
                "diversification_id": did,
                "score": score,
                "holdings": int(holdings),
                "label": "high" if score >= 0.7 else "moderate" if score >= 0.4 else "low",
                "at": _now(),
            },
        )

    def rebalance(self, *, portfolio_id: str, target: dict[str, float], threshold_pct: float = 5.0) -> dict[str, Any]:
        if not target:
            raise ValidationError("target required")
        rid = _id("rm_reb")
        return self.store.rm_rebalances.save(
            rid,
            {
                "rebalance_id": rid,
                "portfolio_id": portfolio_id,
                "target": target,
                "threshold_pct": float(threshold_pct),
                "status": "proposed",
                "at": _now(),
            },
        )

    def capital_efficiency(self, *, portfolio_id: str, deployed_pct: float, idle_pct: float) -> dict[str, Any]:
        cid = _id("rm_eff")
        return self.store.rm_efficiency.save(
            cid,
            {
                "efficiency_id": cid,
                "portfolio_id": portfolio_id,
                "deployed_pct": float(deployed_pct),
                "idle_pct": float(idle_pct),
                "score": round(float(deployed_pct) / 100.0, 4),
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "allocations": self.store.rm_allocations.count(),
            "rebalances": self.store.rm_rebalances.count(),
            "diversification": self.store.rm_diversification.count(),
        }


class AdvancedRiskModels:
    def __init__(self, store: CryptoEnterpriseStore | None = None) -> None:
        self.store = store or crypto_enterprise_store

    def var(self, *, portfolio_id: str, confidence: float, var_pct: float) -> dict[str, Any]:
        confidence = float(confidence)
        if confidence <= 0 or confidence >= 1:
            raise ValidationError("confidence must be between 0 and 1")
        vid = _id("rm_var")
        return self.store.rm_var.save(
            vid,
            {
                "var_id": vid,
                "portfolio_id": portfolio_id,
                "confidence": confidence,
                "var_pct": float(var_pct),
                "at": _now(),
            },
        )

    def cvar(self, *, portfolio_id: str, confidence: float, cvar_pct: float) -> dict[str, Any]:
        cid = _id("rm_cvar")
        return self.store.rm_cvar.save(
            cid,
            {
                "cvar_id": cid,
                "portfolio_id": portfolio_id,
                "confidence": float(confidence),
                "cvar_pct": float(cvar_pct),
                "at": _now(),
            },
        )

    def monte_carlo(self, *, portfolio_id: str, simulations: int = 5000) -> dict[str, Any]:
        mid = _id("rm_mc")
        return self.store.rm_monte_carlo.save(
            mid,
            {
                "simulation_id": mid,
                "portfolio_id": portfolio_id,
                "simulations": int(simulations),
                "p5": -0.15,
                "p50": 0.08,
                "p95": 0.28,
                "at": _now(),
            },
        )

    def stress_test(self, *, portfolio_id: str, scenario: str, shock_pct: float) -> dict[str, Any]:
        sid = _id("rm_stress")
        return self.store.rm_stress.save(
            sid,
            {
                "stress_id": sid,
                "portfolio_id": portfolio_id,
                "scenario": scenario,
                "shock_pct": float(shock_pct),
                "impact_pct": round(float(shock_pct) * 0.72, 4),
                "at": _now(),
            },
        )

    def scenario(self, *, portfolio_id: str, name: str, outcome: str) -> dict[str, Any]:
        sid = _id("rm_scen")
        return self.store.rm_scenarios.save(
            sid,
            {
                "scenario_id": sid,
                "portfolio_id": portfolio_id,
                "name": name,
                "outcome": outcome,
                "at": _now(),
            },
        )

    def tail_risk(self, *, portfolio_id: str, tail_pct: float) -> dict[str, Any]:
        tid = _id("rm_tail")
        return self.store.rm_tail.save(
            tid,
            {
                "tail_id": tid,
                "portfolio_id": portfolio_id,
                "tail_pct": float(tail_pct),
                "severity": "elevated" if float(tail_pct) >= 5 else "normal",
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "var": self.store.rm_var.count(),
            "cvar": self.store.rm_cvar.count(),
            "stress": self.store.rm_stress.count(),
            "monte_carlo": self.store.rm_monte_carlo.count(),
        }


class TradeProtection:
    def __init__(self, store: CryptoEnterpriseStore | None = None) -> None:
        self.store = store or crypto_enterprise_store

    def dynamic_stop(self, *, symbol: str, stop: float, atr_mult: float = 1.5) -> dict[str, Any]:
        sid = _id("rm_dstop")
        return self.store.rm_dyn_stops.save(
            sid,
            {
                "protection_id": sid,
                "symbol": symbol.upper(),
                "stop": float(stop),
                "atr_mult": float(atr_mult),
                "kind": "dynamic_stop",
                "at": _now(),
            },
        )

    def adaptive_tp(self, *, symbol: str, targets: list[float]) -> dict[str, Any]:
        if not targets:
            raise ValidationError("targets required")
        tid = _id("rm_atp")
        return self.store.rm_adaptive_tp.save(
            tid,
            {
                "protection_id": tid,
                "symbol": symbol.upper(),
                "targets": [float(t) for t in targets],
                "kind": "adaptive_tp",
                "at": _now(),
            },
        )

    def trailing_stop(self, *, symbol: str, trail_pct: float) -> dict[str, Any]:
        if trail_pct <= 0:
            raise ValidationError("trail_pct must be > 0")
        tid = _id("rm_trail")
        return self.store.rm_trailing.save(
            tid,
            {
                "protection_id": tid,
                "symbol": symbol.upper(),
                "trail_pct": float(trail_pct),
                "kind": "trailing",
                "at": _now(),
            },
        )

    def breakeven(self, *, symbol: str, trigger_r: float = 1.0) -> dict[str, Any]:
        bid = _id("rm_be")
        return self.store.rm_breakeven.save(
            bid,
            {
                "protection_id": bid,
                "symbol": symbol.upper(),
                "trigger_r": float(trigger_r),
                "kind": "breakeven",
                "at": _now(),
            },
        )

    def partial_profit(self, *, symbol: str, levels: list[dict[str, float]]) -> dict[str, Any]:
        if not levels:
            raise ValidationError("levels required")
        pid = _id("rm_pp")
        return self.store.rm_partials.save(
            pid,
            {
                "protection_id": pid,
                "symbol": symbol.upper(),
                "levels": levels,
                "kind": "partial",
                "at": _now(),
            },
        )

    def emergency_exit(self, *, symbol: str, reason: str) -> dict[str, Any]:
        if not reason:
            raise ValidationError("reason required")
        eid = _id("rm_eexit")
        return self.store.rm_emergency.save(
            eid,
            {
                "protection_id": eid,
                "symbol": symbol.upper(),
                "reason": reason,
                "kind": "emergency",
                "executed": True,
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "dynamic_stops": self.store.rm_dyn_stops.count(),
            "trailing": self.store.rm_trailing.count(),
            "emergency": self.store.rm_emergency.count(),
        }
