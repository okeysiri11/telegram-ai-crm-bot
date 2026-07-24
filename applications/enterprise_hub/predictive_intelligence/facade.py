"""Predictive Intelligence Suite — Sprint 24.3 / v7.3.0."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from platform_predictive_intelligence.facade import PredictiveIntelligenceLibrary

from applications.enterprise_hub.config import DEFAULT_CONFIG
from applications.enterprise_hub.shared.exceptions import ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class PredictiveIntelligenceSuite:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.library = PredictiveIntelligenceLibrary()

    def integrations(self) -> dict[str, Any]:
        return self.library.integrations.link()

    def bootstrap(self) -> dict[str, Any]:
        self.library = PredictiveIntelligenceLibrary()
        result = self.library.bootstrap()
        full = result.pop("full")
        bid = _id("pin_boot")
        record = {
            "bootstrap_id": bid,
            **result,
            "version": DEFAULT_CONFIG.application_version,
            "bootstrapped_at": _now(),
        }
        self.store.pin_bootstraps.save(bid, record)
        for m in full["models"]:
            self.store.pin_models.save(m["model_id"], {**m, "created_at": _now()})
        for key, attr, prefix in (
            ("business", "pin_forecasts", "pin_biz"),
            ("customer", "pin_customers", "pin_cu"),
            ("marketing", "pin_marketing", "pin_mkt"),
            ("operations", "pin_operations", "pin_ops"),
            ("risks", "pin_risks", "pin_risk"),
            ("opportunities", "pin_opportunities", "pin_opp"),
            ("scenarios", "pin_scenarios", "pin_scn"),
            ("dashboard", "pin_dashboards", "pin_dash"),
            ("learning", "pin_learning", "pin_learn"),
        ):
            rid = _id(prefix)
            getattr(self.store, attr).save(rid, {"record_id": rid, **full[key], "created_at": _now()})
        self.store.pin_bootstraps.save(bid, record)
        return record

    def register_model(self, **kwargs: Any) -> dict[str, Any]:
        try:
            model = self.library.registry.register(**kwargs)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        self.store.pin_models.save(model["model_id"], {**model, "created_at": _now()})
        return model

    def list_models(self) -> dict[str, Any]:
        stored = self.store.pin_models.list_all()
        if not stored:
            self.bootstrap()
            stored = self.store.pin_models.list_all()
        return {"models": stored, "count": len(stored)}

    def business_forecast(self, **kwargs: Any) -> dict[str, Any]:
        try:
            raw = self.library.business.forecast(**kwargs)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        # light enrichment from commerce when available
        try:
            from applications.enterprise_hub import enterprise_hub

            if hasattr(enterprise_hub, "commerce_core"):
                raw["data_hint"] = "commerce_core"
        except Exception:
            pass
        result = self.library.confidence.attach(prediction=raw, confidence=0.8, data_used=["commerce_core", "crm"])
        scenarios = self.library.scenarios.generate(baseline=result["forecast_value"], domain=result["domain"])
        rid = _id("pin_biz")
        record = {"forecast_id": rid, **result, "scenarios": scenarios, "created_at": _now()}
        self.store.pin_forecasts.save(rid, record)
        return record

    def customer_predict(self, **kwargs: Any) -> dict[str, Any]:
        try:
            raw = self.library.customer.predict(**kwargs)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        result = self.library.confidence.attach(prediction=raw, confidence=0.77, data_used=["crm"])
        rid = _id("pin_cu")
        record = {"prediction_id": rid, **result, "created_at": _now()}
        self.store.pin_customers.save(rid, record)
        return record

    def marketing_predict(self, **kwargs: Any) -> dict[str, Any]:
        raw = self.library.marketing.predict(**kwargs)
        result = self.library.confidence.attach(prediction=raw, confidence=0.78, data_used=["ai_marketing_os", "communications_hub"])
        rid = _id("pin_mkt")
        record = {"prediction_id": rid, **result, "created_at": _now()}
        self.store.pin_marketing.save(rid, record)
        return record

    def operations_predict(self, **kwargs: Any) -> dict[str, Any]:
        raw = self.library.operations.predict(**kwargs)
        result = self.library.confidence.attach(prediction=raw, confidence=0.74, data_used=["operations_center"])
        rid = _id("pin_ops")
        record = {"prediction_id": rid, **result, "created_at": _now()}
        self.store.pin_operations.save(rid, record)
        return record

    def assess_risks(self, **kwargs: Any) -> dict[str, Any]:
        result = self.library.risk.assess(**kwargs)
        rid = _id("pin_risk")
        record = {"risk_id": rid, **result, "created_at": _now()}
        self.store.pin_risks.save(rid, record)
        return record

    def detect_opportunities(self, **kwargs: Any) -> dict[str, Any]:
        result = self.library.opportunity.detect(**kwargs)
        rid = _id("pin_opp")
        record = {"opportunity_id": rid, **result, "created_at": _now()}
        self.store.pin_opportunities.save(rid, record)
        return record

    def learn(self, **kwargs: Any) -> dict[str, Any]:
        result = self.library.learning.compare(**kwargs)
        if result.get("learned") and kwargs.get("model_id"):
            try:
                self.library.registry.record_training(
                    kwargs["model_id"], note="confirmed_actual", accuracy=result.get("accuracy")
                )
                mid = kwargs["model_id"]
                if self.store.pin_models.get(mid):
                    m = dict(self.store.pin_models.get(mid))
                    m["accuracy"] = result.get("accuracy", m.get("accuracy"))
                    hist = list(m.get("training_history") or [])
                    hist.append({"note": "confirmed_actual", "accuracy": result.get("accuracy")})
                    m["training_history"] = hist
                    self.store.pin_models.save(mid, m)
            except ValueError:
                pass
        rid = _id("pin_learn")
        record = {"learning_id": rid, **result, "created_at": _now()}
        self.store.pin_learning.save(rid, record)
        return record

    def owner_dashboard(self) -> dict[str, Any]:
        forecasts = self.store.pin_forecasts.list_all()[-5:]
        risks = (self.store.pin_risks.list_all() or [{}])[-1]
        opps = (self.store.pin_opportunities.list_all() or [{}])[-1]
        if not forecasts:
            forecasts = [self.business_forecast(domain="revenue", baseline=5000)]
        if not risks or not risks.get("overall_risk"):
            risks = self.assess_risks()
        if not opps or not opps.get("opportunities"):
            opps = self.detect_opportunities(signals={"open_slots": 6})
        dash = self.library.dashboard.render(
            forecasts=forecasts,
            risks=risks,
            opportunities=opps,
            recommendations=["review_high_churn", "act_on_open_slots"],
        )
        rid = _id("pin_dash")
        record = {"dashboard_id": rid, **dash, "created_at": _now()}
        self.store.pin_dashboards.save(rid, record)
        return record

    def status(self) -> dict[str, Any]:
        return {
            "library": self.library.status(),
            "bootstraps": len(self.store.pin_bootstraps.list_all()),
            "models": len(self.store.pin_models.list_all()),
            "forecasts": len(self.store.pin_forecasts.list_all()),
            "shared_prediction_layer": True,
        }


predictive_intelligence = PredictiveIntelligenceSuite()
