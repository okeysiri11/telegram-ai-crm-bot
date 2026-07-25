"""Production Readiness Suite — Sprint 25.6 / v8.6.0."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from platform_enterprise_production.facade import ProductionLibrary

from applications.enterprise_hub.config import DEFAULT_CONFIG
from applications.enterprise_hub.shared.exceptions import ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class ProductionReadinessSuite:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.library = ProductionLibrary()

    def integrations(self) -> dict[str, Any]:
        return self.library.integrations.link()

    def bootstrap(self) -> dict[str, Any]:
        self.library = ProductionLibrary()
        result = self.library.bootstrap()
        full = result.pop("full")
        bid = _id("epd_boot")
        record = {
            "bootstrap_id": bid,
            **result,
            "version": DEFAULT_CONFIG.application_version,
            "bootstrapped_at": _now(),
        }
        self.store.epd_bootstraps.save(bid, record)
        for key, attr, prefix in (
            ("services", "epd_services", "epd_svc"),
            ("health", "epd_health", "epd_hlth"),
            ("monitoring", "epd_monitoring", "epd_mon"),
            ("metrics", "epd_metrics", "epd_met"),
            ("logs", "epd_logs", "epd_log"),
            ("alerts", "epd_alerts", "epd_alrt"),
            ("scaling", "epd_scaling", "epd_scl"),
            ("deployment", "epd_deployments", "epd_dep"),
            ("reports", "epd_reports", "epd_rep"),
            ("dashboard", "epd_dashboards", "epd_dash"),
        ):
            rid = _id(prefix)
            getattr(self.store, attr).save(rid, {"record_id": rid, **full[key], "created_at": _now()})
        self.store.epd_bootstraps.save(bid, record)
        return record

    def run_gate(
        self,
        *,
        release: str | None = None,
        failed_health: list[str] | None = None,
        active_alerts: list[str] | None = None,
        failed_deployment: list[str] | None = None,
        monitoring_overrides: dict[str, float] | None = None,
    ) -> dict[str, Any]:
        release = release or DEFAULT_CONFIG.application_version
        plan = self.library.manager.plan(release=release)
        services = self.library.manager.register_services(version=release)
        try:
            health = self.library.health.check(failed=failed_health)
            monitoring = self.library.monitoring.sample(overrides=monitoring_overrides)
            metrics = self.library.metrics.collect()
            logs = self.library.logging.centralize()
            alerts = self.library.alerts.evaluate(active=active_alerts)
            scaling = self.library.scaling.prepare()
            deployment = self.library.deployment.validate(failed=failed_deployment)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        production_ready = (
            health["passed"]
            and monitoring["passed"]
            and alerts["critical_count"] == 0
            and scaling["passed"]
            and deployment["passed"]
        )
        release_blocked = not production_ready
        reports = self.library.reports.generate(
            run_id=_id("epd_run"),
            summary={
                "production_ready": production_ready,
                "release_blocked": release_blocked,
                "services": services["count"],
            },
        )
        dash = self.library.dashboard.render(
            system_health="healthy" if health["passed"] else "degraded",
            active_services=services["count"],
            infrastructure={"cloud_ready": True},
            monitoring=monitoring,
            alerts=alerts,
            logs={"centralized": True},
            metrics=metrics,
            deployments=deployment,
            capacity=scaling["capacity_planning"],
            availability=0.999 if production_ready else 0.95,
            production_ready=production_ready,
            recommendations=(
                ["production_gate_passed"] if production_ready else ["fix_blockers_before_production"]
            ),
        )
        rid = _id("epd_run")
        record = {
            "run_id": rid,
            "plan": plan,
            "services": services,
            "health": health,
            "monitoring": monitoring,
            "metrics": metrics,
            "logs": logs,
            "alerts": alerts,
            "scaling": scaling,
            "deployment": deployment,
            "reports": reports,
            "dashboard": dash,
            "production_ready": production_ready,
            "release_blocked": release_blocked,
            "production_allowed": production_ready,
            "created_at": _now(),
        }
        self.store.epd_runs.save(rid, record)
        did = _id("epd_dash")
        self.store.epd_dashboards.save(did, {"dashboard_id": did, **dash, "created_at": _now()})
        rep_id = _id("epd_rep")
        self.store.epd_reports.save(rep_id, {"report_id": rep_id, **reports, "created_at": _now()})
        return record

    def dashboard(self) -> dict[str, Any]:
        runs = self.store.epd_runs.list_all()
        if runs:
            return runs[-1].get("dashboard") or self.run_gate()["dashboard"]
        return self.run_gate()["dashboard"]

    def status(self) -> dict[str, Any]:
        return {
            "library": self.library.status(),
            "bootstraps": len(self.store.epd_bootstraps.list_all()),
            "runs": len(self.store.epd_runs.list_all()),
            "block_when_not_ready": True,
        }


production_readiness = ProductionReadinessSuite()
