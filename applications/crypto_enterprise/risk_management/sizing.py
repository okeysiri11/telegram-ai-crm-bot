"""Position sizing and risk analytics."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.crypto_enterprise.shared.exceptions import ValidationError
from applications.crypto_enterprise.shared.store import CryptoEnterpriseStore, crypto_enterprise_store

SIZING_METHODS = ["fixed", "percentage", "atr", "kelly", "volatility", "max_exposure", "dynamic"]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class PositionSizing:
    def __init__(self, store: CryptoEnterpriseStore | None = None) -> None:
        self.store = store or crypto_enterprise_store
        self.methods = list(SIZING_METHODS)

    def size(
        self,
        *,
        method: str,
        symbol: str,
        capital: float,
        risk_pct: float = 1.0,
        stop_distance: float = 0.0,
        atr: float = 0.0,
        win_rate: float = 0.55,
        payoff: float = 1.5,
        volatility: float = 0.0,
        max_exposure_pct: float = 10.0,
    ) -> dict[str, Any]:
        if method not in SIZING_METHODS:
            raise ValidationError(f"method must be one of {SIZING_METHODS}")
        if capital <= 0:
            raise ValidationError("capital must be > 0")
        capital = float(capital)
        risk_amount = capital * (float(risk_pct) / 100.0)
        if method == "fixed":
            qty = risk_amount / max(stop_distance, 1e-9)
        elif method == "percentage":
            qty = (capital * float(risk_pct) / 100.0) / max(stop_distance, 1e-9)
        elif method == "atr":
            qty = risk_amount / max(float(atr) * 1.5, 1e-9)
        elif method == "kelly":
            p = float(win_rate)
            b = float(payoff)
            kelly = max(0.0, p - (1 - p) / max(b, 1e-9))
            qty = (capital * kelly) / max(stop_distance or 1.0, 1e-9)
        elif method == "volatility":
            qty = risk_amount / max(float(volatility) * capital * 0.01, 1e-9)
        elif method == "max_exposure":
            qty = (capital * float(max_exposure_pct) / 100.0) / max(stop_distance or 1.0, 1e-9)
        else:  # dynamic
            base = risk_amount / max(stop_distance or atr or 1.0, 1e-9)
            qty = base * (1.0 if float(volatility) < 3 else 0.7)
        sid = _id("rm_size")
        return self.store.rm_sizing.save(
            sid,
            {
                "sizing_id": sid,
                "method": method,
                "symbol": symbol.upper(),
                "capital": capital,
                "risk_pct": float(risk_pct),
                "quantity": round(float(qty), 8),
                "risk_amount": round(risk_amount, 4),
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"sizes": self.store.rm_sizing.count(), "methods": self.methods}


class RiskAnalytics:
    def __init__(self, store: CryptoEnterpriseStore | None = None) -> None:
        self.store = store or crypto_enterprise_store

    def risk_per_trade(self, *, symbol: str, risk_amount: float, capital: float) -> dict[str, Any]:
        if capital <= 0:
            raise ValidationError("capital must be > 0")
        rid = _id("rm_rpt")
        return self.store.rm_risk_trade.save(
            rid,
            {
                "risk_id": rid,
                "symbol": symbol.upper(),
                "risk_amount": float(risk_amount),
                "capital": float(capital),
                "risk_pct": round(float(risk_amount) / float(capital) * 100, 4),
                "at": _now(),
            },
        )

    def portfolio_risk(self, *, portfolio_id: str, var_pct: float, exposure_pct: float) -> dict[str, Any]:
        pid = _id("rm_prisk")
        return self.store.rm_portfolio_risk.save(
            pid,
            {
                "analysis_id": pid,
                "portfolio_id": portfolio_id,
                "var_pct": float(var_pct),
                "exposure_pct": float(exposure_pct),
                "at": _now(),
            },
        )

    def drawdown(self, *, portfolio_id: str, current_dd: float, max_dd: float) -> dict[str, Any]:
        did = _id("rm_dd")
        return self.store.rm_drawdown.save(
            did,
            {
                "monitor_id": did,
                "portfolio_id": portfolio_id,
                "current_dd": float(current_dd),
                "max_dd": float(max_dd),
                "breached": float(current_dd) >= float(max_dd),
                "at": _now(),
            },
        )

    def loss_limit(self, *, period: str, limit_pct: float, realized_pct: float) -> dict[str, Any]:
        if period not in ("daily", "weekly", "monthly"):
            raise ValidationError("period must be daily|weekly|monthly")
        lid = _id("rm_llim")
        return self.store.rm_loss_limits.save(
            lid,
            {
                "limit_id": lid,
                "period": period,
                "limit_pct": float(limit_pct),
                "realized_pct": float(realized_pct),
                "breached": float(realized_pct) >= float(limit_pct),
                "at": _now(),
            },
        )

    def heatmap(self, *, portfolio_id: str, cells: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        hid = _id("rm_heat")
        return self.store.rm_heatmaps.save(
            hid,
            {
                "heatmap_id": hid,
                "portfolio_id": portfolio_id,
                "cells": cells or [{"asset": "BTC", "risk": 0.4}, {"asset": "ETH", "risk": 0.3}],
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "trade_risk": self.store.rm_risk_trade.count(),
            "portfolio_risk": self.store.rm_portfolio_risk.count(),
            "loss_limits": self.store.rm_loss_limits.count(),
            "heatmaps": self.store.rm_heatmaps.count(),
        }
