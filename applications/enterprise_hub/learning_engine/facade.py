"""Learning Engine Suite — Sprint 24.8 / v7.8.0."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from platform_enterprise_learning_engine.facade import LearningEngineLibrary

from applications.enterprise_hub.config import DEFAULT_CONFIG
from applications.enterprise_hub.shared.exceptions import NotFoundError, ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class LearningEngineSuite:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.library = LearningEngineLibrary()

    def integrations(self) -> dict[str, Any]:
        return self.library.integrations.link()

    def bootstrap(self) -> dict[str, Any]:
        self.library = LearningEngineLibrary()
        result = self.library.bootstrap()
        full = result.pop("full")
        bid = _id("ele_boot")
        record = {
            "bootstrap_id": bid,
            **result,
            "version": DEFAULT_CONFIG.application_version,
            "bootstrapped_at": _now(),
        }
        self.store.ele_bootstraps.save(bid, record)
        lid = full["record"]["learning_id"]
        self.store.ele_learnings.save(lid, {**full["record"], "created_at": _now()})
        for key, attr, prefix in (
            ("collected", "ele_collections", "ele_col"),
            ("patterns", "ele_patterns", "ele_pat"),
            ("cross_tenant", "ele_cross_tenant", "ele_xt"),
            ("evolution", "ele_evolution", "ele_evo"),
            ("score", "ele_scores", "ele_scr"),
            ("decision", "ele_owner", "ele_own"),
            ("product", "ele_product", "ele_prd"),
            ("dashboard", "ele_dashboards", "ele_dash"),
        ):
            rid = _id(prefix)
            getattr(self.store, attr).save(rid, {"record_id": rid, **full[key], "created_at": _now()})
        record["learning_id"] = lid
        self.store.ele_bootstraps.save(bid, record)
        return record

    def collect(self, *, events: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        result = self.library.collector.collect(events=events)
        rid = _id("ele_col")
        record = {"collection_id": rid, **result, "created_at": _now()}
        self.store.ele_collections.save(rid, record)
        return record

    def register(self, **kwargs: Any) -> dict[str, Any]:
        try:
            kwargs.setdefault("timestamp", _now())
            record = self.library.registry.create(**kwargs)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        self.store.ele_learnings.save(record["learning_id"], {**record, "created_at": _now()})
        return record

    def classify_feedback(self, *, text: str) -> dict[str, Any]:
        return self.library.feedback.classify(text=text)

    def detect_patterns(self, *, items: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        result = self.library.patterns.detect(items=items)
        rid = _id("ele_pat")
        record = {"pattern_id": rid, **result, "created_at": _now()}
        self.store.ele_patterns.save(rid, record)
        return record

    def cross_tenant(self, *, anonymized_signals: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        try:
            result = self.library.cross_tenant.aggregate(anonymized_signals=anonymized_signals)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        rid = _id("ele_xt")
        record = {"cross_id": rid, **result, "created_at": _now()}
        self.store.ele_cross_tenant.save(rid, record)
        return record

    def evolve(self, **kwargs: Any) -> dict[str, Any]:
        result = self.library.evolution.evolve(**kwargs)
        rid = _id("ele_evo")
        record = {"evolution_id": rid, **result, "created_at": _now()}
        self.store.ele_evolution.save(rid, record)
        return record

    def score_agent(self, **kwargs: Any) -> dict[str, Any]:
        try:
            result = self.library.score.score(**kwargs)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        rid = _id("ele_scr")
        record = {"score_id": rid, **result, "created_at": _now()}
        self.store.ele_scores.save(rid, record)
        return record

    def owner_decide(self, **kwargs: Any) -> dict[str, Any]:
        try:
            result = self.library.owner.decide(**kwargs)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        lid = kwargs.get("learning_id", "")
        learning = self.store.ele_learnings.get(lid)
        if not learning:
            raise NotFoundError(f"learning not found: {lid}")
        updated = self.library.registry.set_status(learning, status=result["status"])
        self.store.ele_learnings.save(lid, {**updated, "owner_decision": result, "updated_at": _now()})
        rid = _id("ele_own")
        record = {"owner_id": rid, **result, "created_at": _now()}
        self.store.ele_owner.save(rid, record)
        return record

    def product_push(self, *, improvement: str, confirmed: bool = False) -> dict[str, Any]:
        try:
            result = self.library.product.push(improvement=improvement, confirmed=confirmed)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        # optional EPI hook
        try:
            from applications.enterprise_hub import enterprise_hub

            if hasattr(enterprise_hub, "product_intelligence"):
                result["product_intelligence_available"] = True
        except Exception:
            pass
        rid = _id("ele_prd")
        record = {"product_id": rid, **result, "created_at": _now()}
        self.store.ele_product.save(rid, record)
        return record

    def safety_check(self, *, intent: str) -> dict[str, Any]:
        return self.library.safety.enforce(intent=intent)

    def list_learnings(self) -> dict[str, Any]:
        items = self.store.ele_learnings.list_all()
        return {"learnings": items, "count": len(items)}

    def owner_dashboard(self) -> dict[str, Any]:
        items = self.store.ele_learnings.list_all()
        awaiting = [i["learning_id"] for i in items if i.get("verification_status") in ("pending", "awaiting_owner")]
        approved = [i["learning_id"] for i in items if i.get("verification_status") in ("approved", "policy_trusted")]
        rejected = [i["learning_id"] for i in items if i.get("verification_status") == "rejected"]
        dash = self.library.dashboard.render(
            learned=approved[:10],
            improved=["recommendation_weights"],
            degraded=[],
            awaiting_confirmation=awaiting[:10],
            rejected=rejected[:10],
        )
        rid = _id("ele_dash")
        record = {"dashboard_id": rid, **dash, "created_at": _now()}
        self.store.ele_dashboards.save(rid, record)
        return record

    def status(self) -> dict[str, Any]:
        return {
            "library": self.library.status(),
            "bootstraps": len(self.store.ele_bootstraps.list_all()),
            "learnings": len(self.store.ele_learnings.list_all()),
            "autonomous_learn": False,
        }


learning_engine = LearningEngineSuite()
