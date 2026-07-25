"""Test Infrastructure Suite — Sprint 25.1 / v8.1.0."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from platform_testing.facade import TestInfrastructureLibrary

from applications.enterprise_hub.config import DEFAULT_CONFIG
from applications.enterprise_hub.shared.exceptions import NotFoundError, ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class TestInfrastructureSuite:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.library = TestInfrastructureLibrary()

    def integrations(self) -> dict[str, Any]:
        return self.library.integrations.link()

    def bootstrap(self) -> dict[str, Any]:
        self.library = TestInfrastructureLibrary()
        result = self.library.bootstrap()
        full = result.pop("full")
        bid = _id("eti_boot")
        record = {
            "bootstrap_id": bid,
            **result,
            "version": DEFAULT_CONFIG.application_version,
            "bootstrapped_at": _now(),
        }
        self.store.eti_bootstraps.save(bid, record)
        for t in full["catalog"]:
            self.store.eti_tests.save(t["test_id"], {**t, "created_at": _now()})
        for key, attr, prefix in (
            ("execution", "eti_runs", "eti_run"),
            ("reports", "eti_reports", "eti_rep"),
            ("analytics", "eti_analytics", "eti_an"),
            ("dashboard", "eti_dashboards", "eti_dash"),
            ("coverage", "eti_coverage", "eti_cov"),
        ):
            rid = _id(prefix)
            getattr(self.store, attr).save(rid, {"record_id": rid, **full[key], "created_at": _now()})
        self.store.eti_bootstraps.save(bid, record)
        return record

    def register_test(self, **kwargs: Any) -> dict[str, Any]:
        try:
            test = self.library.registry.register(**kwargs)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        self.store.eti_tests.save(test["test_id"], {**test, "created_at": _now()})
        return test

    def list_tests(self) -> dict[str, Any]:
        items = self.store.eti_tests.list_all()
        return {"tests": items, "count": len(items)}

    def run(
        self,
        *,
        test_id: str | None = None,
        group: list[str] | None = None,
        module: str | None = None,
        tag: str | None = None,
        changed_files: list[str] | None = None,
        full: bool = False,
        environment: str = "ci",
        fail_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        catalog = self.store.eti_tests.list_all()
        if not catalog:
            raise ValidationError("no tests registered")
        try:
            selected = self.library.runner.select(
                catalog=catalog,
                test_id=test_id,
                group=group,
                module=module,
                tag=tag,
                changed_files=changed_files,
                full=full,
            )
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        run_id = _id("eti_run")
        try:
            env = self.library.environments.provision(environment=environment, run_id=run_id)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        pipe = self.library.pipeline.run(run_id=run_id, selected_count=len(selected))
        execution = self.library.runner.execute(tests=selected, fail_ids=fail_ids)
        now = _now()
        for r in execution["results"]:
            test = self.store.eti_tests.get(r["test_id"])
            if test:
                updated = self.library.registry.update_result(test, result=r["status"], executed_at=now)
                self.store.eti_tests.save(r["test_id"], updated)
        reports = self.library.reports.generate(run_id=run_id, summary=execution)
        cov = self.library.coverage.measure(
            covered_lines=max(1, execution["passed"] * 100),
            total_lines=max(1, execution["total"] * 120),
        )
        analytics = self.library.analytics.analyze(
            runs=[{
                "run_id": run_id,
                "duration_ms": sum(r["duration_ms"] for r in execution["results"]),
                "failed": execution["failed"],
                "success": execution["success"],
                "by_module": {},
            }]
        )
        record = {
            "run_id": run_id,
            "environment": env,
            "pipeline": pipe,
            "execution": execution,
            "reports": reports,
            "coverage": cov,
            "analytics": analytics,
            "created_at": now,
        }
        self.store.eti_runs.save(run_id, record)
        rid = _id("eti_rep")
        self.store.eti_reports.save(rid, {"report_id": rid, **reports, "created_at": now})
        return record

    def smoke(self, *, modules: list[str] | None = None) -> dict[str, Any]:
        return self.library.smoke.run(modules=modules)

    def integration_check(self, *, pairs: list[list[str]] | None = None) -> dict[str, Any]:
        tup = [(p[0], p[1]) for p in (pairs or []) if len(p) >= 2] or None
        return self.library.integration.run(pairs=tup)

    def regression(self, **kwargs: Any) -> dict[str, Any]:
        return self.library.regression.run(**kwargs)

    def validate_contracts(self, *, contracts: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        return self.library.contracts.validate(contracts=contracts)

    def coverage(self, *, covered_lines: int, total_lines: int) -> dict[str, Any]:
        result = self.library.coverage.measure(covered_lines=covered_lines, total_lines=total_lines)
        rid = _id("eti_cov")
        record = {"coverage_id": rid, **result, "created_at": _now()}
        self.store.eti_coverage.save(rid, record)
        return record

    def generate_data(self, *, entity: str, count: int = 1) -> dict[str, Any]:
        try:
            result = self.library.data_factory.generate(entity=entity, count=count)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        rid = _id("eti_data")
        record = {"data_id": rid, **result, "created_at": _now()}
        self.store.eti_data.save(rid, record)
        return record

    def provision_env(self, *, environment: str) -> dict[str, Any]:
        try:
            return self.library.environments.provision(environment=environment, run_id=_id("eti_env"))
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc

    def dashboard(self) -> dict[str, Any]:
        tests = self.store.eti_tests.list_all()
        runs = self.store.eti_runs.list_all()
        last = runs[-1] if runs else None
        execution = (last or {}).get("execution") or {"passed": 0, "failed": 0, "skipped": 0, "results": []}
        cov = (last or {}).get("coverage") or {"coverage_pct": 0.0}
        dash = self.library.dashboard.render(
            active=len(tests),
            passed=execution.get("passed", 0),
            failed=execution.get("failed", 0),
            skipped=execution.get("skipped", 0),
            coverage_pct=cov.get("coverage_pct", 0.0),
            duration_ms=sum(r.get("duration_ms", 0) for r in execution.get("results") or []),
            history=[{"run_id": r.get("run_id"), "success": (r.get("execution") or {}).get("success")} for r in runs[-10:]],
            reports=["html", "json", "xml", "console"],
            trends=[{"metric": "runs", "value": len(runs)}],
            quality_score=round(execution.get("passed", 0) / max(execution.get("total", 1), 1), 3),
        )
        rid = _id("eti_dash")
        record = {"dashboard_id": rid, **dash, "created_at": _now()}
        self.store.eti_dashboards.save(rid, record)
        return record

    def analytics(self) -> dict[str, Any]:
        runs = self.store.eti_runs.list_all()
        payload = []
        for r in runs:
            ex = r.get("execution") or {}
            payload.append({
                "run_id": r.get("run_id"),
                "duration_ms": sum(x.get("duration_ms", 0) for x in ex.get("results") or []),
                "failed": ex.get("failed", 0),
                "success": ex.get("success"),
                "by_module": {},
            })
        result = self.library.analytics.analyze(runs=payload)
        rid = _id("eti_an")
        record = {"analytics_id": rid, **result, "created_at": _now()}
        self.store.eti_analytics.save(rid, record)
        return record

    def status(self) -> dict[str, Any]:
        return {
            "library": self.library.status(),
            "bootstraps": len(self.store.eti_bootstraps.list_all()),
            "tests": len(self.store.eti_tests.list_all()),
            "runs": len(self.store.eti_runs.list_all()),
            "single_test_center": True,
        }


test_infrastructure = TestInfrastructureSuite()
