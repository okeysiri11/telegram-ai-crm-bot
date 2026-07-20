# ValidationManager — unified validation and production readiness facade.

from __future__ import annotations

import logging
import time
from typing import Any

from events.publisher import publish
from platform_validation.certification_manager import CertificationManager, certification_manager
from platform_validation.compatibility_manager import CompatibilityManager, compatibility_manager
from platform_validation.config import DEFAULT_VALIDATION_CONFIG, ValidationConfig
from platform_validation.integration_test_manager import IntegrationTestManager, integration_test_manager
from platform_validation.models import (
    CertificationResult,
    PlatformHealthReport,
    ReadinessLevel,
    ValidationReport,
    ValidationStatus,
)
from platform_validation.performance_test_manager import PerformanceTestManager, performance_test_manager
from platform_validation.production_readiness_manager import ProductionReadinessManager, production_readiness_manager
from platform_validation.quality_manager import QualityManager, quality_manager
from platform_validation.stress_test_manager import StressTestManager, stress_test_manager
from platform_validation.validation_events import PlatformValidatedEvent, ProductionReadyEvent
from platform_validation.validation_metrics import ValidationMetrics, validation_metrics

logger = logging.getLogger(__name__)


class ValidationManager:
    """Complete platform validation, QA, and production readiness entry point."""

    def __init__(
        self,
        *,
        integration: IntegrationTestManager | None = None,
        performance: PerformanceTestManager | None = None,
        stress: StressTestManager | None = None,
        compatibility: CompatibilityManager | None = None,
        readiness: ProductionReadinessManager | None = None,
        quality: QualityManager | None = None,
        certification: CertificationManager | None = None,
        metrics: ValidationMetrics | None = None,
        config: ValidationConfig | None = None,
    ) -> None:
        self._integration = integration or integration_test_manager
        self._performance = performance or performance_test_manager
        self._stress = stress or stress_test_manager
        self._compatibility = compatibility or compatibility_manager
        self._readiness = readiness or production_readiness_manager
        self._quality = quality or quality_manager
        self._certification = certification or certification_manager
        self._metrics = metrics or validation_metrics
        self._config = config or DEFAULT_VALIDATION_CONFIG
        self._reports: dict[str, ValidationReport] = {}

    def reset(self) -> None:
        self._integration.reset()
        self._performance.reset()
        self._stress.reset()
        self._compatibility.reset()
        self._readiness.reset()
        self._quality.reset()
        self._certification.reset()
        self._metrics.reset()
        self._reports.clear()

    async def validate_integrations(self) -> ValidationReport:
        started = time.perf_counter()
        report = await self._integration.validate_all()
        self._metrics.record_validation(report, (time.perf_counter() - started) * 1000.0)
        self._reports["integration"] = report
        return report

    async def validate_performance(self) -> ValidationReport:
        started = time.perf_counter()
        report = await self._performance.run_all()
        self._metrics.record_validation(report, (time.perf_counter() - started) * 1000.0)
        self._reports["performance"] = report
        return report

    async def validate_stress(self) -> ValidationReport:
        started = time.perf_counter()
        report = await self._stress.run_all()
        self._metrics.record_validation(report, (time.perf_counter() - started) * 1000.0)
        self._reports["stress"] = report
        return report

    async def validate_compatibility(self) -> ValidationReport:
        started = time.perf_counter()
        report = await self._compatibility.validate_all()
        self._metrics.record_validation(report, (time.perf_counter() - started) * 1000.0)
        self._reports["compatibility"] = report
        return report

    async def validate_production_readiness(self) -> ValidationReport:
        started = time.perf_counter()
        report = await self._readiness.validate_all()
        self._metrics.record_validation(report, (time.perf_counter() - started) * 1000.0)
        self._reports["readiness"] = report
        return report

    async def validate_quality(self, *, include_regression: bool = False) -> ValidationReport:
        started = time.perf_counter()
        report = await self._quality.validate_all(include_regression=include_regression)
        self._metrics.record_validation(report, (time.perf_counter() - started) * 1000.0)
        self._reports["quality"] = report
        return report

    async def validate_platform(
        self,
        *,
        include_stress: bool = True,
        include_performance: bool = True,
        include_regression: bool = False,
    ) -> ValidationReport:
        """Run full platform validation suite."""
        started = time.perf_counter()
        master = ValidationReport(title="Platform Validation Report")

        suites = [
            await self.validate_integrations(),
            await self.validate_compatibility(),
            await self.validate_production_readiness(),
            await self.validate_quality(include_regression=include_regression),
        ]
        if include_performance:
            suites.append(await self.validate_performance())
        if include_stress:
            suites.append(await self.validate_stress())

        for suite in suites:
            master.checks.extend(suite.checks)

        master.summary["suites"] = [s.title for s in suites]
        master.finalize()
        duration_ms = (time.perf_counter() - started) * 1000.0
        self._metrics.record_validation(master, duration_ms)
        self._reports["platform"] = master

        await publish(
            PlatformValidatedEvent(
                report_id=master.report_id,
                status=master.status.value,
                check_count=len(master.checks),
                duration_ms=duration_ms,
            )
        )
        return master

    async def certify_platform(self, *, include_stress: bool = False) -> CertificationResult:
        """Run validation and issue production certification."""
        await self.validate_platform(include_stress=include_stress, include_performance=True)
        reports = {k: v for k, v in self._reports.items() if k != "platform"}
        if "platform" in self._reports:
            reports["platform"] = self._reports["platform"]

        result = await self._certification.run_certification(reports)
        self._metrics.record_certification(result)

        if result.certified:
            await publish(
                ProductionReadyEvent(
                    platform_version=result.platform_version,
                    platform_status=result.platform_status,
                    score=result.score,
                )
            )
        return result

    def build_health_report(self) -> PlatformHealthReport:
        readiness = self._reports.get("readiness")
        if readiness is None:
            return PlatformHealthReport(
                overall_status=ValidationStatus.WARN,
                readiness_level=ReadinessLevel.PARTIAL,
                components={},
                metrics={"message": "Run validate_production_readiness first"},
            )
        return self._readiness.build_health_report(readiness)

    def get_report(self, name: str) -> ValidationReport | None:
        return self._reports.get(name)

    def all_reports(self) -> dict[str, ValidationReport]:
        return dict(self._reports)

    def readiness_report(self) -> dict[str, Any]:
        platform = self._reports.get("platform")
        cert = self._certification.last_result
        return {
            "platform_validation": platform.to_dict() if platform else None,
            "certification": cert.to_dict() if cert else None,
            "health": self.build_health_report().to_dict(),
            "metrics": self._metrics.summary(),
        }

    def metrics_summary(self) -> dict[str, Any]:
        return self._metrics.summary()


validation_manager = ValidationManager()
