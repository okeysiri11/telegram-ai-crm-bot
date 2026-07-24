"""Performance library facade — Sprint 21.7."""

from __future__ import annotations

from typing import Any

from platform_performance.autoscaling import Autoscaling
from platform_performance.benchmark import BenchmarkFramework
from platform_performance.caching import CacheLayer
from platform_performance.load_testing import LoadTesting
from platform_performance.models import INTEGRATION_TARGETS
from platform_performance.monitoring import PerformanceMonitoring
from platform_performance.optimization import (
    AIOptimization,
    DatabaseOptimization,
    EventBusOptimization,
    WorkflowOptimization,
)
from platform_performance.profiler import PerformanceProfiler
from platform_performance.reporting import PerformanceCertification, PerformanceDashboard
from platform_performance.scalability import ScalabilityValidation
from platform_performance.stress_testing import StressTesting
from platform_performance.tuning import TuningAdvisor


class PerformanceLibrary:
    def __init__(self) -> None:
        self.profiler = PerformanceProfiler()
        self.benchmark = BenchmarkFramework()
        self.cache = CacheLayer()
        self.database = DatabaseOptimization()
        self.ai_opt = AIOptimization()
        self.workflow_opt = WorkflowOptimization()
        self.event_bus_opt = EventBusOptimization()
        self.load = LoadTesting()
        self.stress = StressTesting()
        self.scalability = ScalabilityValidation()
        self.autoscaling = Autoscaling()
        self.monitoring = PerformanceMonitoring()
        self.tuning = TuningAdvisor()
        self.dashboard = PerformanceDashboard()
        self.certification = PerformanceCertification()

    def integrations(self) -> dict[str, Any]:
        return {"targets": list(INTEGRATION_TARGETS), "linked": True}

    def bootstrap(self) -> dict[str, Any]:
        self.__init__()
        profile = self.profiler.profile()
        bench = self.benchmark.run()
        warm = self.cache.warm({"session:default": {"ok": True}, "api:health": {"status": "ok"}}, ttl=300)
        db = self.database.optimize()
        ai = self.ai_opt.optimize()
        wf = self.workflow_opt.optimize()
        bus = self.event_bus_opt.optimize()
        load = self.load.run(concurrent_users=500)
        stress = self.stress.run()
        scale = self.scalability.validate()
        auto = self.autoscaling.policies()
        monitor = self.monitoring.snapshot()
        tuning = self.tuning.recommend()
        dash = self.dashboard.render(
            benchmark=bench, load=load, stress=stress, scale=scale, monitor=monitor
        )
        cert = self.certification.certify(
            dashboard=dash,
            tuning=tuning,
            optimizations=[db, ai, wf, bus],
        )
        return {
            "bootstrap": True,
            "profiles": profile["count"],
            "bottlenecks": len(profile["bottlenecks"]),
            "benchmark_passed": bench["passed"],
            "cache_warmed": warm["warmed"],
            "cache_backends": warm["backends"],
            "db_optimized": db["passed"],
            "ai_optimized": ai["passed"],
            "workflow_optimized": wf["passed"],
            "event_bus_tps": bus["throughput_tps"],
            "load_pass_rate": load["pass_rate"],
            "stress_max_users": stress["max_users"],
            "recovery_time_s": stress["recovery_time_s"],
            "hpa_enabled": scale["k8s_hpa"]["enabled"],
            "autoscaling_policies": len(auto["policies"]),
            "monitoring_passed": monitor["passed"],
            "certified": cert["certified"],
            "production_validated": cert["production_validated"],
            "status": dash["status"],
            "recommendations": cert["recommendations"],
            "integrations": self.integrations(),
            "full": {
                "profile": profile,
                "benchmark": bench,
                "load": load,
                "stress": stress,
                "scale": scale,
                "monitor": monitor,
                "dashboard": dash,
                "certification": cert,
            },
        }

    def status(self) -> dict[str, Any]:
        return {
            "cache": self.cache.status(),
            "components": [
                "profiler",
                "benchmark",
                "load",
                "stress",
                "scalability",
                "caching",
                "monitoring",
            ],
        }


performance_library = PerformanceLibrary()
