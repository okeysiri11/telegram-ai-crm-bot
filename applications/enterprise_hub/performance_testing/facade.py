"""Performance Testing Suite — Sprint 25.2 / v8.2.0."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from platform_enterprise_performance_testing.facade import PerformanceTestingLibrary

from applications.enterprise_hub.config import DEFAULT_CONFIG
from applications.enterprise_hub.shared.exceptions import ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class PerformanceTestingSuite:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.library = PerformanceTestingLibrary()

    def integrations(self) -> dict[str, Any]:
        return self.library.integrations.link()

    def bootstrap(self) -> dict[str, Any]:
        self.library = PerformanceTestingLibrary()
        result = self.library.bootstrap()
        full = result.pop("full")
        bid = _id("epl_boot")
        record = {
            "bootstrap_id": bid,
            **result,
            "version": DEFAULT_CONFIG.application_version,
            "bootstrapped_at": _now(),
        }
        self.store.epl_bootstraps.save(bid, record)
        for key, attr, prefix in (
            ("load", "epl_loads", "epl_load"),
            ("stress", "epl_stress", "epl_str"),
            ("spike", "epl_spikes", "epl_spk"),
            ("soak", "epl_soaks", "epl_sok"),
            ("bottlenecks", "epl_bottlenecks", "epl_bn"),
            ("advice", "epl_advice", "epl_adv"),
            ("dashboard", "epl_dashboards", "epl_dash"),
        ):
            rid = _id(prefix)
            getattr(self.store, attr).save(rid, {"record_id": rid, **full[key], "created_at": _now()})
        self.store.epl_bootstraps.save(bid, record)
        return record

    def load_test(self, *, users: int) -> dict[str, Any]:
        try:
            result = self.library.load.run(users=users)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        rid = _id("epl_load")
        record = {"load_id": rid, **result, "created_at": _now()}
        self.store.epl_loads.save(rid, record)
        return record

    def stress_test(self, **kwargs: Any) -> dict[str, Any]:
        result = self.library.stress.run(**kwargs)
        rid = _id("epl_str")
        record = {"stress_id": rid, **result, "created_at": _now()}
        self.store.epl_stress.save(rid, record)
        return record

    def spike_test(self, *, pattern: list[int] | None = None) -> dict[str, Any]:
        result = self.library.spike.run(pattern=pattern)
        rid = _id("epl_spk")
        record = {"spike_id": rid, **result, "created_at": _now()}
        self.store.epl_spikes.save(rid, record)
        return record

    def soak_test(self, *, hours: int = 1, users: int = 100) -> dict[str, Any]:
        try:
            result = self.library.soak.run(hours=hours, users=users)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        rid = _id("epl_sok")
        record = {"soak_id": rid, **result, "created_at": _now()}
        self.store.epl_soaks.save(rid, record)
        return record

    def benchmark_api(self, **kwargs: Any) -> dict[str, Any]:
        result = self.library.benchmark.api(**kwargs)
        rid = _id("epl_bench")
        record = {"benchmark_id": rid, **result, "created_at": _now()}
        self.store.epl_benchmarks.save(rid, record)
        return record

    def benchmark_database(self, **kwargs: Any) -> dict[str, Any]:
        result = self.library.benchmark.database(**kwargs)
        rid = _id("epl_bench")
        record = {"benchmark_id": rid, **result, "created_at": _now()}
        self.store.epl_benchmarks.save(rid, record)
        return record

    def benchmark_ai(self, **kwargs: Any) -> dict[str, Any]:
        result = self.library.benchmark.ai(**kwargs)
        rid = _id("epl_bench")
        record = {"benchmark_id": rid, **result, "created_at": _now()}
        self.store.epl_benchmarks.save(rid, record)
        return record

    def benchmark_workflow(self, **kwargs: Any) -> dict[str, Any]:
        result = self.library.benchmark.workflow(**kwargs)
        rid = _id("epl_bench")
        record = {"benchmark_id": rid, **result, "created_at": _now()}
        self.store.epl_benchmarks.save(rid, record)
        return record

    def monitor(self, *, load_users: int = 0) -> dict[str, Any]:
        result = self.library.monitor.snapshot(load_users=load_users)
        rid = _id("epl_mon")
        record = {"monitor_id": rid, **result, "created_at": _now()}
        self.store.epl_monitors.save(rid, record)
        return record

    def analyze(self, *, load_users: int = 500, endpoint: str = "/api/enterprise-hub/v1/health") -> dict[str, Any]:
        resources = self.library.monitor.snapshot(load_users=load_users)
        api = self.library.benchmark.api(endpoint=endpoint)
        wf = self.library.benchmark.workflow()
        bottlenecks = self.library.bottleneck.analyze(resources=resources["metrics"], api=api, workflow=wf)
        advice = self.library.advisor.recommend(bottlenecks=bottlenecks["bottlenecks"])
        rid = _id("epl_bn")
        record = {
            "analysis_id": rid,
            "resources": resources,
            "api": api,
            "workflow": wf,
            "bottlenecks": bottlenecks,
            "advice": advice,
            "created_at": _now(),
        }
        self.store.epl_bottlenecks.save(rid, record)
        aid = _id("epl_adv")
        self.store.epl_advice.save(aid, {"advice_id": aid, **advice, "created_at": _now()})
        return record

    def dashboard(self) -> dict[str, Any]:
        loads = self.store.epl_loads.list_all()
        last = loads[-1] if loads else None
        analysis = self.analyze(load_users=int((last or {}).get("users", 100)))
        dash = self.library.dashboard.render(
            live_load=int((last or {}).get("users", 0)),
            active_users=int((last or {}).get("users", 0)),
            rps=float((last or {}).get("throughput_rps", 0)),
            api=analysis["api"],
            database=self.library.benchmark.database(),
            ai=self.library.benchmark.ai(),
            resources=analysis["resources"]["metrics"],
            errors=float((last or {}).get("error_rate", 0)),
            bottlenecks=analysis["bottlenecks"]["bottlenecks"],
            recommendations=analysis["advice"]["recommendations"],
        )
        rid = _id("epl_dash")
        record = {"dashboard_id": rid, **dash, "created_at": _now()}
        self.store.epl_dashboards.save(rid, record)
        return record

    def status(self) -> dict[str, Any]:
        return {
            "library": self.library.status(),
            "bootstraps": len(self.store.epl_bootstraps.list_all()),
            "loads": len(self.store.epl_loads.list_all()),
            "ci_cd_required": True,
        }


performance_testing = PerformanceTestingSuite()
