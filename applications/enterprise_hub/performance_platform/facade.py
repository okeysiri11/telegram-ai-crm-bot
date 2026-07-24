"""Performance Platform Suite facade — Sprint 21.7 / v6.0.0-rc7."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from platform_performance.facade import PerformanceLibrary

from applications.enterprise_hub.config import DEFAULT_CONFIG
from applications.enterprise_hub.shared.exceptions import NotFoundError, ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class PerformancePlatformSuite:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.library = PerformanceLibrary()

    def integrations(self) -> dict[str, Any]:
        return self.library.integrations()

    def bootstrap(self) -> dict[str, Any]:
        self.library = PerformanceLibrary()
        result = self.library.bootstrap()
        full = result.pop("full")
        bid = _id("epf_boot")
        record = {
            "bootstrap_id": bid,
            **result,
            "version": DEFAULT_CONFIG.application_version,
            "bootstrapped_at": _now(),
        }
        self.store.epf_bootstraps.save(bid, record)
        pid = _id("epf_prof")
        self.store.epf_profiles.save(pid, {"profile_id": pid, **full["profile"], "profiled_at": _now()})
        lid = _id("epf_load")
        self.store.epf_load_tests.save(lid, {"load_id": lid, **full["load"], "run_at": _now()})
        sid = _id("epf_stress")
        self.store.epf_stress_tests.save(sid, {"stress_id": sid, **full["stress"], "run_at": _now()})
        mid = _id("epf_mon")
        self.store.epf_monitoring.save(mid, {"monitor_id": mid, **full["monitor"], "captured_at": _now()})
        dash_id = _id("epf_dash")
        self.store.epf_dashboards.save(dash_id, {"dashboard_id": dash_id, **full["dashboard"], "rendered_at": _now()})
        cid = _id("epf_cert")
        self.store.epf_certifications.save(
            cid, {"certification_id": cid, **full["certification"], "certified_at": _now()}
        )
        record["dashboard_id"] = dash_id
        record["certification_id"] = cid
        record["profile_id"] = pid
        self.store.epf_bootstraps.save(bid, record)
        return record

    def profile(self, target: str | None = None) -> dict[str, Any]:
        try:
            result = self.library.profiler.profile(target)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        pid = _id("epf_prof")
        record = {"profile_id": pid, **result, "profiled_at": _now()}
        self.store.epf_profiles.save(pid, record)
        return record

    def load_test(self, *, concurrent_users: int = 500) -> dict[str, Any]:
        result = self.library.load.run(concurrent_users=concurrent_users)
        lid = _id("epf_load")
        record = {"load_id": lid, **result, "run_at": _now()}
        self.store.epf_load_tests.save(lid, record)
        return record

    def stress_test(self) -> dict[str, Any]:
        result = self.library.stress.run()
        sid = _id("epf_stress")
        record = {"stress_id": sid, **result, "run_at": _now()}
        self.store.epf_stress_tests.save(sid, record)
        return record

    def cache_put(self, *, key: str, value: Any, ttl: float = 60.0, backend: str = "redis") -> dict[str, Any]:
        try:
            return self.library.cache.put(key, value, ttl=ttl, backend=backend)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc

    def benchmark(self) -> dict[str, Any]:
        result = self.library.benchmark.run()
        bid = _id("epf_bench")
        record = {"benchmark_id": bid, **result, "run_at": _now()}
        self.store.epf_benchmarks.save(bid, record)
        return record

    def certify(self) -> dict[str, Any]:
        boot = self.bootstrap()
        items = self.store.epf_certifications.list_all()
        if not items:
            raise NotFoundError("certification not found")
        return items[-1]

    def dashboard(self) -> dict[str, Any]:
        items = self.store.epf_dashboards.list_all()
        if not items:
            raise NotFoundError("performance dashboard not found; bootstrap first")
        return items[-1]

    def status(self) -> dict[str, Any]:
        return {
            "library": self.library.status(),
            "bootstraps": len(self.store.epf_bootstraps.list_all()),
            "profiles": len(self.store.epf_profiles.list_all()),
            "load_tests": len(self.store.epf_load_tests.list_all()),
            "certifications": len(self.store.epf_certifications.list_all()),
        }


performance_platform = PerformancePlatformSuite()
