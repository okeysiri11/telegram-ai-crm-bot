"""Agricultural finance, crop insurance, risk and market intelligence."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.agro_enterprise.shared.exceptions import NotFoundError, ValidationError
from applications.agro_enterprise.shared.store import AgroEnterpriseStore, agro_enterprise_store

RISK_TYPES = [
    "weather",
    "market",
    "production",
    "supply_chain",
    "financial",
    "operational",
]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class AgriculturalFinance:
    def __init__(self, store: AgroEnterpriseStore | None = None) -> None:
        self.store = store or agro_enterprise_store

    def create_budget(self, *, farm_id: str, year: int, revenue: float, costs: float) -> dict[str, Any]:
        if not farm_id:
            raise ValidationError("farm_id required")
        bid = _id("af_bud")
        return self.store.af_budgets.save(
            bid,
            {
                "budget_id": bid,
                "farm_id": farm_id,
                "year": int(year),
                "revenue": float(revenue),
                "costs": float(costs),
                "profit": round(float(revenue) - float(costs), 2),
                "at": _now(),
            },
        )

    def cash_flow(self, *, farm_id: str, inflow: float, outflow: float) -> dict[str, Any]:
        cid = _id("af_cf")
        return self.store.af_cashflows.save(
            cid,
            {
                "cashflow_id": cid,
                "farm_id": farm_id,
                "inflow": float(inflow),
                "outflow": float(outflow),
                "net": round(float(inflow) - float(outflow), 2),
                "at": _now(),
            },
        )

    def cost_entry(self, *, farm_id: str, category: str, amount: float) -> dict[str, Any]:
        cid = _id("af_cost")
        return self.store.af_costs.save(
            cid,
            {
                "cost_id": cid,
                "farm_id": farm_id,
                "category": category,
                "amount": float(amount),
                "at": _now(),
            },
        )

    def profitability(self, farm_id: str) -> dict[str, Any]:
        budgets = [b for b in self.store.af_budgets.list_all() if b.get("farm_id") == farm_id]
        costs = [c for c in self.store.af_costs.list_all() if c.get("farm_id") == farm_id]
        revenue = sum(float(b.get("revenue") or 0) for b in budgets)
        total_costs = sum(float(b.get("costs") or 0) for b in budgets) + sum(
            float(c.get("amount") or 0) for c in costs
        )
        return {
            "farm_id": farm_id,
            "revenue": round(revenue, 2),
            "costs": round(total_costs, 2),
            "margin": round(revenue - total_costs, 2),
            "margin_pct": round((revenue - total_costs) / revenue * 100, 2) if revenue else 0.0,
        }

    def credit(self, *, farm_id: str, limit: float, utilized: float = 0.0) -> dict[str, Any]:
        cid = _id("af_crd")
        return self.store.af_credit.save(
            cid,
            {
                "credit_id": cid,
                "farm_id": farm_id,
                "limit": float(limit),
                "utilized": float(utilized),
                "available": round(float(limit) - float(utilized), 2),
                "at": _now(),
            },
        )

    def loan(self, *, farm_id: str, principal: float, rate_pct: float, term_months: int) -> dict[str, Any]:
        lid = _id("af_loan")
        return self.store.af_loans.save(
            lid,
            {
                "loan_id": lid,
                "farm_id": farm_id,
                "principal": float(principal),
                "rate_pct": float(rate_pct),
                "term_months": int(term_months),
                "status": "active",
                "at": _now(),
            },
        )

    def subsidy(self, *, farm_id: str, program: str, amount: float) -> dict[str, Any]:
        sid = _id("af_sub")
        return self.store.af_subsidies.save(
            sid,
            {
                "subsidy_id": sid,
                "farm_id": farm_id,
                "program": program,
                "amount": float(amount),
                "kind": "subsidy",
                "at": _now(),
            },
        )

    def grant(self, *, farm_id: str, program: str, amount: float) -> dict[str, Any]:
        gid = _id("af_grn")
        return self.store.af_grants.save(
            gid,
            {
                "grant_id": gid,
                "farm_id": farm_id,
                "program": program,
                "amount": float(amount),
                "kind": "grant",
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "budgets": self.store.af_budgets.count(),
            "loans": self.store.af_loans.count(),
            "subsidies": self.store.af_subsidies.count(),
            "grants": self.store.af_grants.count(),
        }


class CropInsurance:
    def __init__(self, store: AgroEnterpriseStore | None = None) -> None:
        self.store = store or agro_enterprise_store

    def register_insurer(self, *, name: str) -> dict[str, Any]:
        if not name:
            raise ValidationError("insurer name required")
        iid = _id("af_ins")
        return self.store.af_insurers.save(
            iid, {"insurer_id": iid, "name": name, "created_at": _now()}
        )

    def create_policy(
        self,
        *,
        insurer_id: str,
        farm_id: str,
        crop: str,
        coverage: float,
        premium: float,
    ) -> dict[str, Any]:
        if self.store.af_insurers.get(insurer_id) is None:
            raise NotFoundError("insurer", insurer_id)
        pid = _id("af_pol")
        return self.store.af_policies.save(
            pid,
            {
                "policy_id": pid,
                "insurer_id": insurer_id,
                "farm_id": farm_id,
                "crop": crop,
                "coverage": float(coverage),
                "premium": float(premium),
                "status": "active",
                "at": _now(),
            },
        )

    def coverage_calc(self, *, hectares: float, yield_t_ha: float, price: float, coverage_pct: float = 0.7) -> dict[str, Any]:
        insured = float(hectares) * float(yield_t_ha) * float(price) * float(coverage_pct)
        premium = round(insured * 0.04, 2)
        cid = _id("af_cov")
        return self.store.af_coverage.save(
            cid,
            {
                "calc_id": cid,
                "hectares": float(hectares),
                "yield_t_ha": float(yield_t_ha),
                "price": float(price),
                "coverage_pct": float(coverage_pct),
                "insured_value": round(insured, 2),
                "estimated_premium": premium,
                "at": _now(),
            },
        )

    def risk_score(self, *, farm_id: str, weather: float = 0.3, market: float = 0.2, production: float = 0.25) -> dict[str, Any]:
        score = round(min(1.0, (weather + market + production) / 3), 3)
        rid = _id("af_rsk")
        return self.store.af_ins_risk.save(
            rid,
            {
                "score_id": rid,
                "farm_id": farm_id,
                "weather": float(weather),
                "market": float(market),
                "production": float(production),
                "composite": score,
                "band": "high" if score > 0.6 else "medium" if score > 0.35 else "low",
                "at": _now(),
            },
        )

    def claim(self, *, policy_id: str, amount: float, damage_pct: float) -> dict[str, Any]:
        if self.store.af_policies.get(policy_id) is None:
            raise NotFoundError("policy", policy_id)
        cid = _id("af_clm")
        return self.store.af_claims.save(
            cid,
            {
                "claim_id": cid,
                "policy_id": policy_id,
                "amount": float(amount),
                "damage_pct": float(damage_pct),
                "assessment": "severe" if damage_pct > 50 else "moderate" if damage_pct > 20 else "minor",
                "status": "open",
                "at": _now(),
            },
        )

    def premium_analytics(self) -> dict[str, Any]:
        policies = self.store.af_policies.list_all()
        claims = self.store.af_claims.list_all()
        premiums = sum(float(p.get("premium") or 0) for p in policies)
        claim_amt = sum(float(c.get("amount") or 0) for c in claims)
        return {
            "policies": len(policies),
            "total_premiums": round(premiums, 2),
            "total_claims": round(claim_amt, 2),
            "loss_ratio": round(claim_amt / premiums, 3) if premiums else 0.0,
        }

    def status(self) -> dict[str, Any]:
        return {
            "insurers": self.store.af_insurers.count(),
            "policies": self.store.af_policies.count(),
            "claims": self.store.af_claims.count(),
        }


class RiskIntelligence:
    def __init__(self, store: AgroEnterpriseStore | None = None) -> None:
        self.store = store or agro_enterprise_store

    def assess(self, *, risk_type: str, entity_id: str, severity: float) -> dict[str, Any]:
        if risk_type not in RISK_TYPES:
            raise ValidationError(f"risk_type must be one of {RISK_TYPES}")
        severity = float(severity)
        if severity < 0 or severity > 1:
            raise ValidationError("severity must be 0..1")
        rid = _id("af_risk")
        return self.store.af_risks.save(
            rid,
            {
                "risk_id": rid,
                "risk_type": risk_type,
                "entity_id": entity_id,
                "severity": severity,
                "ai_score": round(severity * 0.85 + 0.05, 3),
                "level": "critical" if severity >= 0.75 else "elevated" if severity >= 0.45 else "normal",
                "at": _now(),
            },
        )

    def early_warning(self, *, entity_id: str, signal: str, severity: float = 0.6) -> dict[str, Any]:
        wid = _id("af_warn")
        return self.store.af_warnings.save(
            wid,
            {
                "warning_id": wid,
                "entity_id": entity_id,
                "signal": signal,
                "severity": float(severity),
                "status": "active",
                "at": _now(),
            },
        )

    def portfolio_score(self, entity_id: str) -> dict[str, Any]:
        risks = [r for r in self.store.af_risks.list_all() if r.get("entity_id") == entity_id]
        if not risks:
            return {"entity_id": entity_id, "ai_risk_score": 0.0, "risk_count": 0}
        avg = sum(float(r.get("ai_score") or 0) for r in risks) / len(risks)
        return {
            "entity_id": entity_id,
            "ai_risk_score": round(avg, 3),
            "risk_count": len(risks),
            "highest": max(risks, key=lambda r: float(r.get("severity") or 0))["risk_type"],
        }

    def status(self) -> dict[str, Any]:
        return {
            "risks": self.store.af_risks.count(),
            "warnings": self.store.af_warnings.count(),
        }


class MarketIntelligence:
    def __init__(self, store: AgroEnterpriseStore | None = None) -> None:
        self.store = store or agro_enterprise_store

    def publish_price(self, *, commodity: str, price: float, market: str = "local") -> dict[str, Any]:
        if not commodity:
            raise ValidationError("commodity required")
        pid = _id("af_px")
        return self.store.af_prices.save(
            pid,
            {
                "price_id": pid,
                "commodity": commodity,
                "price": float(price),
                "market": market,
                "at": _now(),
            },
        )

    def trend(self, commodity: str) -> dict[str, Any]:
        prices = [p for p in self.store.af_prices.list_all() if p.get("commodity") == commodity]
        if len(prices) < 2:
            direction = "flat"
            delta = 0.0
        else:
            ordered = prices[-2:]
            delta = float(ordered[-1]["price"]) - float(ordered[-2]["price"])
            direction = "up" if delta > 0 else "down" if delta < 0 else "flat"
        tid = _id("af_trd_an")
        return self.store.af_trends.save(
            tid,
            {
                "trend_id": tid,
                "commodity": commodity,
                "samples": len(prices),
                "direction": direction,
                "delta": round(delta, 2),
                "at": _now(),
            },
        )

    def supply_demand(self, *, commodity: str, supply_t: float, demand_t: float) -> dict[str, Any]:
        sid = _id("af_sd")
        balance = float(supply_t) - float(demand_t)
        return self.store.af_supply_demand.save(
            sid,
            {
                "analysis_id": sid,
                "commodity": commodity,
                "supply_t": float(supply_t),
                "demand_t": float(demand_t),
                "balance_t": round(balance, 2),
                "signal": "surplus" if balance > 0 else "deficit" if balance < 0 else "balanced",
                "at": _now(),
            },
        )

    def forecast(self, *, commodity: str, horizon_days: int = 30) -> dict[str, Any]:
        prices = [p for p in self.store.af_prices.list_all() if p.get("commodity") == commodity]
        last = float(prices[-1]["price"]) if prices else 220.0
        forecast = round(last * (1 + 0.002 * horizon_days), 2)
        fid = _id("af_fc")
        return self.store.af_forecasts.save(
            fid,
            {
                "forecast_id": fid,
                "commodity": commodity,
                "horizon_days": int(horizon_days),
                "price_forecast": forecast,
                "confidence": 0.72,
                "at": _now(),
            },
        )

    def export_analytics(self, *, region: str, commodity: str, tons: float, value: float) -> dict[str, Any]:
        eid = _id("af_exp")
        return self.store.af_export_analytics.save(
            eid,
            {
                "analytics_id": eid,
                "region": region,
                "commodity": commodity,
                "tons": float(tons),
                "value": float(value),
                "at": _now(),
            },
        )

    def trading_insight(self, *, commodity: str) -> dict[str, Any]:
        trend = self.trend(commodity)
        fc = self.forecast(commodity=commodity, horizon_days=14)
        iid = _id("af_ins")
        action = "accumulate" if trend["direction"] == "up" else "hedge" if trend["direction"] == "down" else "hold"
        return self.store.af_insights.save(
            iid,
            {
                "insight_id": iid,
                "commodity": commodity,
                "action": action,
                "trend": trend["direction"],
                "forecast_price": fc["price_forecast"],
                "ai_confidence": 0.68,
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "prices": self.store.af_prices.count(),
            "forecasts": self.store.af_forecasts.count(),
            "insights": self.store.af_insights.count(),
        }
