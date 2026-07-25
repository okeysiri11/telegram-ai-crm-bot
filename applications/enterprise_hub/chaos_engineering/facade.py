"""Chaos Engineering Suite — Sprint 25.3 / v8.3.0."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from platform_chaos.facade import ChaosLibrary

from applications.enterprise_hub.config import DEFAULT_CONFIG
from applications.enterprise_hub.shared.exceptions import NotFoundError, ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class ChaosEngineeringSuite:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.library = ChaosLibrary()

    def integrations(self) -> dict[str, Any]:
        return self.library.integrations.link()

    def bootstrap(self) -> dict[str, Any]:
        self.library = ChaosLibrary()
        result = self.library.bootstrap()
        full = result.pop("full")
        bid = _id("ece_boot")
        record = {
            "bootstrap_id": bid,
            **result,
            "version": DEFAULT_CONFIG.application_version,
            "bootstrapped_at": _now(),
        }
        self.store.ece_bootstraps.save(bid, record)
        sid = full["scenario"]["scenario_id"]
        self.store.ece_scenarios.save(sid, {**full["scenario"], "created_at": _now()})
        for key, attr, prefix in (
            ("injection", "ece_injections", "ece_inj"),
            ("recovery", "ece_recoveries", "ece_rec"),
            ("circuit", "ece_circuits", "ece_cb"),
            ("retry", "ece_retries", "ece_rty"),
            ("fallback", "ece_fallbacks", "ece_fb"),
            ("reports", "ece_reports", "ece_rep"),
            ("dashboard", "ece_dashboards", "ece_dash"),
        ):
            rid = _id(prefix)
            getattr(self.store, attr).save(rid, {"record_id": rid, **full[key], "created_at": _now()})
        # incident history
        iid = _id("ece_inc")
        self.store.ece_incidents.save(
            iid,
            {
                "incident_id": iid,
                "scenario_id": sid,
                "failure_type": full["scenario"]["failure_type"],
                "recovered": full["recovery"]["recovered"],
                "created_at": _now(),
            },
        )
        record["scenario_id"] = sid
        self.store.ece_bootstraps.save(bid, record)
        return record

    def create_scenario(self, **kwargs: Any) -> dict[str, Any]:
        try:
            scenario = self.library.controller.create_scenario(**kwargs)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        self.store.ece_scenarios.save(scenario["scenario_id"], {**scenario, "created_at": _now()})
        return scenario

    def list_scenarios(self) -> dict[str, Any]:
        items = self.store.ece_scenarios.list_all()
        return {"scenarios": items, "count": len(items)}

    def run_scenario(self, *, scenario_id: str, retry_strategy: str = "exponential_backoff", fallback: str = "degraded_mode") -> dict[str, Any]:
        scenario = self.store.ece_scenarios.get(scenario_id)
        if not scenario:
            raise NotFoundError(f"scenario not found: {scenario_id}")
        try:
            injection = self.library.injector.inject(scenario=scenario)
            recovery = self.library.recovery.verify(scenario=scenario, injection=injection)
            circuit = self.library.circuit.evaluate(failure_count=5, success_after_open=3)
            retry = self.library.retry.run(strategy=retry_strategy, max_attempts=3)
            fb = self.library.fallback.activate(preferred=fallback)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        deps = self.library.dependencies.map(failed_service=scenario["target_service"])
        health = self.library.health.snapshot(
            services=deps["chain"][:6],
            incidents={scenario["target_service"]: 1},
        )
        run_id = _id("ece_run")
        reports = self.library.reports.generate(
            run_id=run_id,
            summary={
                "incidents": [{"service": scenario["target_service"], "type": scenario["failure_type"]}],
                "recovery_events": [{"event": k, "ok": v} for k, v in recovery["checks"].items()],
                "root_cause": f"injected_{scenario['failure_type']}",
                "recommendations": ["confirm_circuit_breaker", "validate_fallback_path"],
            },
        )
        iid = _id("ece_inc")
        incident = {
            "incident_id": iid,
            "run_id": run_id,
            "scenario_id": scenario_id,
            "failure_type": scenario["failure_type"],
            "target_service": scenario["target_service"],
            "recovered": recovery["recovered"],
            "recovery_time_ms": recovery["recovery_time_ms"],
            "no_data_loss": recovery["checks"]["no_data_loss"],
            "created_at": _now(),
        }
        self.store.ece_incidents.save(iid, incident)
        record = {
            "run_id": run_id,
            "scenario": scenario,
            "injection": injection,
            "recovery": recovery,
            "circuit": circuit,
            "retry": retry,
            "fallback": fb,
            "dependencies": deps,
            "health": health,
            "reports": reports,
            "incident_id": iid,
            "created_at": _now(),
        }
        self.store.ece_runs.save(run_id, record)
        rid = _id("ece_rep")
        self.store.ece_reports.save(rid, {"report_id": rid, **reports, "created_at": _now()})
        return record

    def circuit_check(self, **kwargs: Any) -> dict[str, Any]:
        result = self.library.circuit.evaluate(**kwargs)
        rid = _id("ece_cb")
        record = {"circuit_id": rid, **result, "created_at": _now()}
        self.store.ece_circuits.save(rid, record)
        return record

    def retry_check(self, **kwargs: Any) -> dict[str, Any]:
        try:
            result = self.library.retry.run(**kwargs)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        rid = _id("ece_rty")
        record = {"retry_id": rid, **result, "created_at": _now()}
        self.store.ece_retries.save(rid, record)
        return record

    def fallback_check(self, **kwargs: Any) -> dict[str, Any]:
        try:
            result = self.library.fallback.activate(**kwargs)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        rid = _id("ece_fb")
        record = {"fallback_id": rid, **result, "created_at": _now()}
        self.store.ece_fallbacks.save(rid, record)
        return record

    def health_monitor(self, **kwargs: Any) -> dict[str, Any]:
        return self.library.health.snapshot(**kwargs)

    def dependency_map(self, *, failed_service: str | None = None) -> dict[str, Any]:
        return self.library.dependencies.map(failed_service=failed_service)

    def list_incidents(self) -> dict[str, Any]:
        items = self.store.ece_incidents.list_all()
        return {"incidents": items, "count": len(items)}

    def dashboard(self) -> dict[str, Any]:
        runs = self.store.ece_runs.list_all()
        last = runs[-1] if runs else None
        incidents = self.store.ece_incidents.list_all()
        dash = self.library.dashboard.render(
            active_tests=[(last or {}).get("scenario", {}).get("scenario_id")] if last else [],
            health=(last or {}).get("health") or {},
            incidents=incidents[-10:],
            recovery=(last or {}).get("recovery") or {},
            circuit=(last or {}).get("circuit") or {},
            retry=(last or {}).get("retry") or {},
            fallback=(last or {}).get("fallback") or {},
            availability=0.98 if not last else 0.96,
            recovery_time_ms=int(((last or {}).get("recovery") or {}).get("recovery_time_ms", 0)),
            recommendations=["keep_chaos_in_ci", "review_blast_radius"],
        )
        rid = _id("ece_dash")
        record = {"dashboard_id": rid, **dash, "created_at": _now()}
        self.store.ece_dashboards.save(rid, record)
        return record

    def status(self) -> dict[str, Any]:
        return {
            "library": self.library.status(),
            "bootstraps": len(self.store.ece_bootstraps.list_all()),
            "scenarios": len(self.store.ece_scenarios.list_all()),
            "incidents": len(self.store.ece_incidents.list_all()),
            "ci_cd_required": True,
        }


chaos_engineering = ChaosEngineeringSuite()
