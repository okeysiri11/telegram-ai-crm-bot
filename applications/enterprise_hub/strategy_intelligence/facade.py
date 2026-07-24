"""Strategy Intelligence Suite — Sprint 24.7 / v7.7.0."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from platform_enterprise_strategy_intelligence.facade import StrategyIntelligenceLibrary

from applications.enterprise_hub.config import DEFAULT_CONFIG
from applications.enterprise_hub.shared.exceptions import NotFoundError, ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class StrategyIntelligenceSuite:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.library = StrategyIntelligenceLibrary()

    def integrations(self) -> dict[str, Any]:
        return self.library.integrations.link()

    def bootstrap(self) -> dict[str, Any]:
        self.library = StrategyIntelligenceLibrary()
        result = self.library.bootstrap()
        full = result.pop("full")
        bid = _id("est_boot")
        record = {
            "bootstrap_id": bid,
            **result,
            "version": DEFAULT_CONFIG.application_version,
            "bootstrapped_at": _now(),
        }
        self.store.est_bootstraps.save(bid, record)
        sid = full["strategy"]["strategy_id"]
        self.store.est_strategies.save(sid, {**full["strategy"], "created_at": _now()})
        for key, attr, prefix in (
            ("forecast", "est_forecasts", "est_fc"),
            ("scenarios", "est_scenarios", "est_sc"),
            ("investment", "est_investments", "est_inv"),
            ("risk", "est_risks", "est_risk"),
            ("council", "est_council", "est_cnc"),
            ("decision", "est_owner", "est_own"),
            ("dashboard", "est_dashboards", "est_dash"),
        ):
            rid = _id(prefix)
            getattr(self.store, attr).save(rid, {"record_id": rid, **full[key], "created_at": _now()})
        record["strategy_id"] = sid
        self.store.est_bootstraps.save(bid, record)
        return record

    def create_strategy(self, **kwargs: Any) -> dict[str, Any]:
        try:
            strategy = self.library.registry.create(**kwargs)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        self.store.est_strategies.save(strategy["strategy_id"], {**strategy, "created_at": _now()})
        return strategy

    def define_goal(self, **kwargs: Any) -> dict[str, Any]:
        try:
            return self.library.goals.define(**kwargs)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc

    def forecast(self, **kwargs: Any) -> dict[str, Any]:
        try:
            # light hooks to PIN / Twin / ESL / EKG
            try:
                from applications.enterprise_hub import enterprise_hub

                kwargs.setdefault("from_pin", hasattr(enterprise_hub, "predictive_intelligence"))
            except Exception:
                pass
            result = self.library.forecast.project(**{k: v for k, v in kwargs.items() if k in ("baseline", "growth_rate", "horizon")})
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        rid = _id("est_fc")
        record = {"forecast_id": rid, **result, "created_at": _now()}
        self.store.est_forecasts.save(rid, record)
        return record

    def build_scenarios(self, *, baseline_value: float, strategy_id: str = "") -> dict[str, Any]:
        result = self.library.scenarios.build(baseline_value=baseline_value, strategy_id=strategy_id)
        rid = _id("est_sc")
        record = {"scenario_id": rid, **result, "created_at": _now()}
        self.store.est_scenarios.save(rid, record)
        return record

    def analyze_investment(self, **kwargs: Any) -> dict[str, Any]:
        result = self.library.investment.analyze(**kwargs)
        rid = _id("est_inv")
        record = {"investment_id": rid, **result, "created_at": _now()}
        self.store.est_investments.save(rid, record)
        return record

    def plan_expansion(self, *, items: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        result = self.library.expansion.plan(items=items)
        rid = _id("est_exp")
        record = {"expansion_id": rid, **result, "created_at": _now()}
        self.store.est_expansions.save(rid, record)
        return record

    def assess_risk(self, *, scores: dict[str, float] | None = None) -> dict[str, Any]:
        result = self.library.risk.assess(scores=scores)
        rid = _id("est_risk")
        record = {"risk_id": rid, **result, "created_at": _now()}
        self.store.est_risks.save(rid, record)
        return record

    def council_review(self, *, strategy_id: str, risk_score: float = 0.3) -> dict[str, Any]:
        strategy = self.store.est_strategies.get(strategy_id)
        if not strategy:
            raise NotFoundError(f"strategy not found: {strategy_id}")
        review = self.library.council.review(strategy=strategy, risk_score=risk_score)
        try:
            from applications.enterprise_hub import enterprise_hub

            if hasattr(enterprise_hub, "enterprise_ai_orchestrator"):
                review["orchestrator_available"] = True
        except Exception:
            pass
        updated = self.library.registry.set_status(strategy, status="awaiting_owner")
        self.store.est_strategies.save(strategy_id, {**updated, "council": review, "updated_at": _now()})
        cid = _id("est_cnc")
        record = {"council_id": cid, **review, "created_at": _now()}
        self.store.est_council.save(cid, record)
        return record

    def owner_decide(self, **kwargs: Any) -> dict[str, Any]:
        try:
            result = self.library.owner.decide(**kwargs)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        sid = kwargs.get("strategy_id", "")
        strategy = self.store.est_strategies.get(sid)
        if not strategy:
            raise NotFoundError(f"strategy not found: {sid}")
        status = result["status"]
        if result.get("execution_workflow"):
            status = "in_execution"
        updated = self.library.registry.set_status(strategy, status=status)
        updated = self.library.registry.record_change(updated, note=f"owner_{kwargs.get('action')}", actor="platform_owner")
        if kwargs.get("action") == "modify" and kwargs.get("modifications"):
            updated = {**updated, **(kwargs.get("modifications") or {})}
            updated["status"] = "modified"
        self.store.est_strategies.save(sid, {**updated, "owner_decision": result, "updated_at": _now()})
        rid = _id("est_own")
        record = {"owner_id": rid, **result, "created_at": _now()}
        self.store.est_owner.save(rid, record)
        return record

    def list_strategies(self) -> dict[str, Any]:
        items = self.store.est_strategies.list_all()
        return {"strategies": items, "count": len(items)}

    def owner_dashboard(self, *, strategy_id: str | None = None) -> dict[str, Any]:
        strategies = self.store.est_strategies.list_all()
        strategy = None
        if strategy_id:
            strategy = self.store.est_strategies.get(strategy_id)
            if not strategy:
                raise NotFoundError(f"strategy not found: {strategy_id}")
        elif strategies:
            strategy = strategies[0]
        scenarios = self.store.est_scenarios.list_all()
        alternatives = []
        if scenarios:
            alternatives = scenarios[-1].get("scenarios") or []
        dash = self.library.dashboard.render(
            strategy=strategy or {},
            deviations=[],
            kpi_forecast={"probability": 0.7},
            ai_recommendations=["review_top_scenario"],
            alternatives=alternatives,
        )
        rid = _id("est_dash")
        record = {"dashboard_id": rid, **dash, "created_at": _now()}
        self.store.est_dashboards.save(rid, record)
        return record

    def status(self) -> dict[str, Any]:
        return {
            "library": self.library.status(),
            "bootstraps": len(self.store.est_bootstraps.list_all()),
            "strategies": len(self.store.est_strategies.list_all()),
            "autonomous_decide": False,
        }


strategy_intelligence = StrategyIntelligenceSuite()
