"""Performance Testing library facade — Sprint 25.2."""

from __future__ import annotations

from typing import Any

from platform_enterprise_performance_testing.advisor import OptimizationAdvisor
from platform_enterprise_performance_testing.benchmark import BenchmarkEngine
from platform_enterprise_performance_testing.bottleneck import BottleneckAnalyzer
from platform_enterprise_performance_testing.dashboard import PerformanceTestingDashboard
from platform_enterprise_performance_testing.integrations import PerformanceTestingIntegrations
from platform_enterprise_performance_testing.load import LoadTestEngine
from platform_enterprise_performance_testing.models import PRINCIPLES
from platform_enterprise_performance_testing.monitor import ResourceMonitor
from platform_enterprise_performance_testing.soak import SoakTestEngine
from platform_enterprise_performance_testing.spike import SpikeTestEngine
from platform_enterprise_performance_testing.stress import StressTestEngine


class PerformanceTestingLibrary:
    def __init__(self) -> None:
        self.load = LoadTestEngine()
        self.stress = StressTestEngine()
        self.spike = SpikeTestEngine()
        self.soak = SoakTestEngine()
        self.benchmark = BenchmarkEngine()
        self.monitor = ResourceMonitor()
        self.bottleneck = BottleneckAnalyzer()
        self.advisor = OptimizationAdvisor()
        self.dashboard = PerformanceTestingDashboard()
        self.integrations = PerformanceTestingIntegrations()

    def principles(self) -> list[str]:
        return list(PRINCIPLES)

    def bootstrap(self) -> dict[str, Any]:
        self.__init__()
        load = self.load.run(users=500)
        stress = self.stress.run(start_users=100, step=400, max_users=3000)
        spike = self.spike.run()
        soak = self.soak.run(hours=1, users=100)
        api = self.benchmark.api(endpoint="/api/enterprise-hub/v1/health")
        db = self.benchmark.database()
        ai = self.benchmark.ai()
        wf = self.benchmark.workflow()
        resources = self.monitor.snapshot(load_users=500)
        bottlenecks = self.bottleneck.analyze(resources=resources["metrics"], api=api, workflow=wf)
        advice = self.advisor.recommend(bottlenecks=bottlenecks["bottlenecks"])
        dash = self.dashboard.render(
            live_load=500,
            active_users=500,
            rps=load["throughput_rps"],
            api=api,
            database=db,
            ai=ai,
            resources=resources["metrics"],
            errors=load["error_rate"],
            bottlenecks=bottlenecks["bottlenecks"],
            recommendations=advice["recommendations"],
        )
        links = self.integrations.link()
        return {
            "bootstrap": True,
            "principles": self.principles(),
            "performance_testing_ready": True,
            "load_testing_ready": True,
            "stress_testing_ready": True,
            "bottleneck_advisor_ready": True,
            "ci_cd_required": True,
            "required_before_production": True,
            "duplicates_core_logic": False,
            "duplicates_epf_logic": False,
            "status": "ready",
            "integrations": links,
            "full": {
                "load": load,
                "stress": stress,
                "spike": spike,
                "soak": soak,
                "api": api,
                "database": db,
                "ai": ai,
                "workflow": wf,
                "resources": resources,
                "bottlenecks": bottlenecks,
                "advice": advice,
                "dashboard": dash,
                "links": links,
            },
        }

    def status(self) -> dict[str, Any]:
        return {
            "components": [
                "load",
                "stress",
                "spike",
                "soak",
                "benchmark",
                "monitor",
                "bottleneck",
                "advisor",
                "dashboard",
            ],
            "principles": self.principles(),
            "ci_cd_required": True,
        }


performance_testing_library = PerformanceTestingLibrary()
