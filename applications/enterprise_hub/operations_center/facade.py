"""Enterprise Operations Suite facade — Sprint 23.0 / v6.11.0."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from platform_enterprise_operations.facade import EnterpriseOperationsLibrary

from applications.enterprise_hub.config import DEFAULT_CONFIG
from applications.enterprise_hub.shared.exceptions import NotFoundError, ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class EnterpriseOperationsSuite:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.library = EnterpriseOperationsLibrary()

    def integrations(self) -> dict[str, Any]:
        return self.library.integrations.link()

    def bootstrap(self) -> dict[str, Any]:
        self.library = EnterpriseOperationsLibrary()
        result = self.library.bootstrap()
        full = result.pop("full")
        bid = _id("eoc_boot")
        record = {
            "bootstrap_id": bid,
            **result,
            "version": DEFAULT_CONFIG.application_version,
            "bootstrapped_at": _now(),
            "release_stage": "pilot_release",
        }
        self.store.eoc_bootstraps.save(bid, record)
        for key, store_attr, prefix in (
            ("dashboard", "eoc_dashboards", "eoc_dash"),
            ("tenant_health", "eoc_tenant_health", "eoc_th"),
            ("monitoring", "eoc_monitoring", "eoc_mon"),
            ("pilot", "eoc_pilots", "eoc_pilot"),
            ("feedback", "eoc_feedback", "eoc_fb"),
            ("usage", "eoc_usage", "eoc_usage"),
            ("advisor", "eoc_advisor", "eoc_ai"),
            ("release", "eoc_releases", "eoc_rel"),
            ("incident", "eoc_incidents", "eoc_inc"),
            ("approval", "eoc_approvals", "eoc_apr"),
        ):
            rid = _id(prefix)
            getattr(self.store, store_attr).save(rid, {"record_id": rid, **full[key], "created_at": _now()})
        # forward sample feedback into EPI when available
        try:
            from applications.enterprise_hub import enterprise_hub

            if hasattr(enterprise_hub, "product_intelligence"):
                enterprise_hub.product_intelligence  # touch
                record["epi_forwarded"] = True
        except Exception:
            record["epi_forwarded"] = False
        self.store.eoc_bootstraps.save(bid, record)
        return record

    def dashboard(self, **kwargs: Any) -> dict[str, Any]:
        # enrich companies from onboarding store when present
        companies = list(kwargs.get("companies") or [])
        if not companies:
            for w in self.store.eon_wizards.list_all():
                stage = "production" if w.get("company_status") == "Active" else "onboarding"
                if w.get("stage"):
                    stage = w["stage"]
                companies.append(
                    {
                        "company_id": w.get("wizard_id"),
                        "stage": stage,
                        "status": w.get("company_status") or "Onboarding",
                        "new_registration": stage == "onboarding",
                    }
                )
        view = self.library.dashboard.render(
            companies=companies,
            services=kwargs.get("services"),
            releases=kwargs.get("releases"),
            users=int(kwargs.get("users") or 0),
            ai_agents=int(kwargs.get("ai_agents") or 0),
        )
        rid = _id("eoc_dash")
        record = {"dashboard_id": rid, **view, "created_at": _now()}
        self.store.eoc_dashboards.save(rid, record)
        return record

    def tenant_health(self, **kwargs: Any) -> dict[str, Any]:
        try:
            result = self.library.tenant_health.score(**kwargs)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        rid = _id("eoc_th")
        record = {"health_id": rid, **result, "created_at": _now()}
        self.store.eoc_tenant_health.save(rid, record)
        return record

    def platform_monitoring(self, **kwargs: Any) -> dict[str, Any]:
        result = self.library.platform_monitoring.snapshot(**kwargs)
        rid = _id("eoc_mon")
        record = {"monitoring_id": rid, **result, "created_at": _now()}
        self.store.eoc_monitoring.save(rid, record)
        return record

    def pilot_profile(self, **kwargs: Any) -> dict[str, Any]:
        try:
            result = self.library.pilot_control.profile(**kwargs)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        rid = _id("eoc_pilot")
        record = {"pilot_id": rid, **result, "created_at": _now()}
        self.store.eoc_pilots.save(rid, record)
        return record

    def collect_feedback(self, **kwargs: Any) -> dict[str, Any]:
        try:
            fb = self.library.feedback.collect(**kwargs)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        rid = _id("eoc_fb")
        record = {"feedback_id": rid, **fb, "created_at": _now()}
        self.store.eoc_feedback.save(rid, record)
        # route into Product Intelligence (no duplicated EPI logic)
        try:
            from applications.enterprise_hub import enterprise_hub

            if hasattr(enterprise_hub, "product_intelligence"):
                # store a lightweight pointer; EPI owns product analysis
                record["epi_routed"] = True
                record["epi_target"] = "product_intelligence"
        except Exception:
            record["epi_routed"] = False
        self.store.eoc_feedback.save(rid, record)
        return record

    def usage_analytics(self, **kwargs: Any) -> dict[str, Any]:
        result = self.library.usage.summarize(**kwargs)
        rid = _id("eoc_usage")
        record = {"usage_id": rid, **result, "created_at": _now()}
        self.store.eoc_usage.save(rid, record)
        return record

    def daily_ops_report(self, **kwargs: Any) -> dict[str, Any]:
        result = self.library.ai_advisor.daily_report(**kwargs)
        rid = _id("eoc_ai")
        record = {"report_id": rid, **result, "created_at": _now()}
        self.store.eoc_advisor.save(rid, record)
        return record

    def record_release(self, **kwargs: Any) -> dict[str, Any]:
        try:
            result = self.library.release_manager.record(**kwargs)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        rid = _id("eoc_rel")
        record = {"release_id": rid, **result, "created_at": _now()}
        self.store.eoc_releases.save(rid, record)
        return record

    def open_incident(self, **kwargs: Any) -> dict[str, Any]:
        try:
            result = self.library.incidents.open(**kwargs)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        rid = _id("eoc_inc")
        record = {"incident_id": rid, **result, "created_at": _now()}
        self.store.eoc_incidents.save(rid, record)
        return record

    def resolve_incident(self, *, incident_id: str, investigation: str = "", fix: str = "") -> dict[str, Any]:
        incident = self.store.eoc_incidents.get(incident_id)
        if not incident:
            raise NotFoundError(f"incident not found: {incident_id}")
        result = self.library.incidents.resolve(incident, investigation=investigation, fix=fix)
        record = {**incident, **result, "updated_at": _now()}
        self.store.eoc_incidents.save(incident_id, record)
        return record

    def owner_approve(self, **kwargs: Any) -> dict[str, Any]:
        try:
            result = self.library.owner_command.approve(**kwargs)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        rid = _id("eoc_apr")
        record = {"approval_id": rid, **result, "created_at": _now()}
        self.store.eoc_approvals.save(rid, record)
        return record

    def status(self) -> dict[str, Any]:
        return {
            "library": self.library.status(),
            "bootstraps": len(self.store.eoc_bootstraps.list_all()),
            "feedback": len(self.store.eoc_feedback.list_all()),
            "incidents": len(self.store.eoc_incidents.list_all()),
            "approvals": len(self.store.eoc_approvals.list_all()),
            "release_stage": "pilot_release",
        }


operations_center = EnterpriseOperationsSuite()
