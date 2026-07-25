"""Test Infrastructure library facade — Sprint 25.1."""

from __future__ import annotations

from typing import Any

from platform_testing.analytics import TestAnalytics
from platform_testing.contracts import APIContractEngine
from platform_testing.coverage import CoverageEngine
from platform_testing.dashboard import TestDashboard
from platform_testing.data_factory import TestDataFactory
from platform_testing.environment import TestEnvironmentManager
from platform_testing.integration import IntegrationEngine
from platform_testing.integrations import TestIntegrations
from platform_testing.models import PRINCIPLES
from platform_testing.pipeline import ExecutionPipeline
from platform_testing.registry import TestRegistry
from platform_testing.regression import RegressionEngine
from platform_testing.reports import TestReports
from platform_testing.runner import TestRunner
from platform_testing.smoke import SmokeEngine


class TestInfrastructureLibrary:
    def __init__(self) -> None:
        self.registry = TestRegistry()
        self.runner = TestRunner()
        self.pipeline = ExecutionPipeline()
        self.smoke = SmokeEngine()
        self.integration = IntegrationEngine()
        self.regression = RegressionEngine()
        self.contracts = APIContractEngine()
        self.coverage = CoverageEngine()
        self.environments = TestEnvironmentManager()
        self.data_factory = TestDataFactory()
        self.dashboard = TestDashboard()
        self.reports = TestReports()
        self.analytics = TestAnalytics()
        self.integrations = TestIntegrations()

    def principles(self) -> list[str]:
        return list(PRINCIPLES)

    def bootstrap(self) -> dict[str, Any]:
        self.__init__()
        t1 = self.registry.register(
            test_id="tst_hub_health",
            name="Hub health smoke",
            module="enterprise_hub",
            category="smoke",
            tags=["smoke", "hub"],
            estimated_duration_ms=40,
        )
        t2 = self.registry.register(
            test_id="tst_aph_route",
            name="AI Provider Hub route",
            module="ai_provider_hub",
            category="integration",
            tags=["ai", "integration"],
            estimated_duration_ms=80,
        )
        t3 = self.registry.register(
            test_id="tst_ees_public_api",
            name="Extension public API",
            module="extension_sdk",
            category="api",
            tags=["api", "sdk"],
            estimated_duration_ms=60,
        )
        catalog = [t1, t2, t3]
        env = self.environments.provision(environment="ci", run_id="run_boot")
        data = self.data_factory.generate(entity="companies", count=2)
        pipe = self.pipeline.run(run_id="run_boot", selected_count=len(catalog))
        selected = self.runner.select(catalog=catalog, full=True)
        execution = self.runner.execute(tests=selected)
        smoke = self.smoke.run(modules=["enterprise_hub", "ai_provider_hub"])
        integ = self.integration.run()
        reg = self.regression.run(baseline_pass_rate=1.0, current_pass_rate=1.0)
        contracts = self.contracts.validate(
            contracts=[{"contract_id": "health", "required_fields": ["status"], "payload": {"status": "ok"}}]
        )
        cov = self.coverage.measure(covered_lines=850, total_lines=1000)
        reports = self.reports.generate(run_id="run_boot", summary=execution)
        analytics = self.analytics.analyze(
            runs=[{
                "run_id": "run_boot",
                "duration_ms": sum(r["duration_ms"] for r in execution["results"]),
                "failed": execution["failed"],
                "success": execution["success"],
                "by_module": {"enterprise_hub": {"passed": 1, "failed": 0}},
            }]
        )
        dash = self.dashboard.render(
            active=len(catalog),
            passed=execution["passed"],
            failed=execution["failed"],
            skipped=0,
            coverage_pct=cov["coverage_pct"],
            duration_ms=sum(r["duration_ms"] for r in execution["results"]),
            history=[{"run_id": "run_boot", "success": True}],
            reports=list(reports["formats"]),
            trends=[{"metric": "pass_rate", "value": 1.0}],
            quality_score=0.95,
        )
        links = self.integrations.link()
        return {
            "bootstrap": True,
            "principles": self.principles(),
            "test_infrastructure_ready": True,
            "test_registry_ready": True,
            "test_runner_ready": True,
            "test_dashboard_ready": True,
            "isolated_environments": env["isolated"],
            "auto_reports": reports["auto_generated"],
            "duplicates_core_logic": False,
            "status": "ready",
            "integrations": links,
            "full": {
                "catalog": catalog,
                "environment": env,
                "data": data,
                "pipeline": pipe,
                "execution": execution,
                "smoke": smoke,
                "integration": integ,
                "regression": reg,
                "contracts": contracts,
                "coverage": cov,
                "reports": reports,
                "analytics": analytics,
                "dashboard": dash,
                "links": links,
            },
        }

    def status(self) -> dict[str, Any]:
        return {
            "components": [
                "registry",
                "runner",
                "pipeline",
                "smoke",
                "integration",
                "regression",
                "contracts",
                "coverage",
                "environments",
                "data_factory",
                "dashboard",
                "reports",
                "analytics",
            ],
            "principles": self.principles(),
            "single_test_center": True,
        }


test_infrastructure_library = TestInfrastructureLibrary()
