"""Quality Assurance library facade — Sprint 21.5."""

from __future__ import annotations

from typing import Any

from platform_quality.ai import AITestFramework
from platform_quality.contract import ContractTestFramework
from platform_quality.coverage import CoverageEngine
from platform_quality.e2e import E2ETestFramework
from platform_quality.fixtures import TestDataPlatform
from platform_quality.integration import IntegrationTestFramework
from platform_quality.models import INTEGRATION_TARGETS, MIN_COVERAGE
from platform_quality.performance import PerformanceValidation
from platform_quality.regression import RegressionSuite
from platform_quality.reporting import QualityDashboard, QualityMetrics
from platform_quality.security import SecurityQaFramework
from platform_quality.unit import UnitTestFramework
from platform_quality.workflow import WorkflowTestFramework


class QualityLibrary:
    def __init__(self) -> None:
        self.unit = UnitTestFramework()
        self.integration = IntegrationTestFramework()
        self.e2e = E2ETestFramework()
        self.contract = ContractTestFramework()
        self.ai = AITestFramework()
        self.workflow = WorkflowTestFramework()
        self.regression = RegressionSuite()
        self.security = SecurityQaFramework()
        self.performance = PerformanceValidation()
        self.fixtures = TestDataPlatform()
        self.coverage = CoverageEngine()
        self.metrics = QualityMetrics()
        self.dashboard = QualityDashboard()

    def integrations(self) -> dict[str, Any]:
        return {"targets": list(INTEGRATION_TARGETS), "linked": True}

    def run_full_suite(self) -> dict[str, Any]:
        results = {
            "unit": self.unit.run(),
            "integration": self.integration.run(),
            "e2e": self.e2e.run(),
            "contract": self.contract.run(),
            "ai": self.ai.run(),
            "workflow": self.workflow.run(),
            "regression": self.regression.run(),
            "security_qa": self.security.run(),
            "performance": self.performance.run(),
        }
        coverage = self.coverage.measure()
        totals = sum(r["total"] for r in results.values())
        passed = sum(r["passed"] for r in results.values())
        pass_rate = round(passed / totals, 3) if totals else 0.0
        metrics = self.metrics.compute(pass_rate=pass_rate, coverage=coverage["overall"])
        dash = self.dashboard.render(suite_results=results, coverage=coverage, metrics=metrics)
        fixtures = self.fixtures.generate(kind="organization", count=5)
        return {
            "suites": results,
            "coverage": coverage,
            "pass_rate": pass_rate,
            "total_tests": totals,
            "passed_tests": passed,
            "metrics": metrics,
            "dashboard": dash,
            "fixtures": fixtures,
            "min_coverage": MIN_COVERAGE,
            "certified": dash["certified"],
        }

    def bootstrap(self) -> dict[str, Any]:
        self.__init__()
        full = self.run_full_suite()
        return {
            "bootstrap": True,
            "total_tests": full["total_tests"],
            "passed_tests": full["passed_tests"],
            "pass_rate": full["pass_rate"],
            "coverage": full["coverage"]["overall"],
            "meets_coverage_minimum": full["coverage"]["meets_minimum"],
            "regression_regressions": full["suites"]["regression"]["regressions_found"],
            "performance_passed": full["suites"]["performance"]["pass_rate"] == 1.0,
            "ai_decision_accuracy": full["suites"]["ai"]["decision_accuracy"],
            "e2e_steps": full["suites"]["e2e"]["total"],
            "contract_checks": full["suites"]["contract"]["total"],
            "fixture_id": full["fixtures"]["fixture_id"],
            "release_quality": full["dashboard"]["release_quality"],
            "certified": full["certified"],
            "integrations": self.integrations(),
            "full": full,
        }

    def status(self) -> dict[str, Any]:
        return {"frameworks": ["unit", "integration", "e2e", "contract", "ai", "workflow", "regression", "security", "performance"]}


quality_library = QualityLibrary()
