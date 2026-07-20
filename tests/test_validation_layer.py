"""Tests — Platform Validation & Production Readiness Layer (Sprint 5.5)."""

from __future__ import annotations

import asyncio

import pytest

from platform_validation.compatibility_manager import CompatibilityManager
from platform_validation.config import ValidationConfig
from platform_validation.integration_test_manager import IntegrationTestManager
from platform_validation.models import ValidationStatus
from platform_validation.performance_test_manager import PerformanceTestManager
from platform_validation.production_readiness_manager import ProductionReadinessManager
from platform_validation.quality_manager import QualityManager
from platform_validation.stress_test_manager import StressTestManager
from platform_validation.validation_manager import ValidationManager
from platform_validation.validation_metrics import ValidationMetrics


@pytest.fixture
def manager() -> ValidationManager:
    config = ValidationConfig(stress_operations=50, stress_concurrency=10, performance_benchmark_ops=20)
    mgr = ValidationManager(
        integration=IntegrationTestManager(),
        performance=PerformanceTestManager(config=config),
        stress=StressTestManager(config=config),
        compatibility=CompatibilityManager(),
        readiness=ProductionReadinessManager(),
        quality=QualityManager(),
        metrics=ValidationMetrics(),
        config=config,
    )
    yield mgr
    mgr.reset()


@pytest.mark.asyncio
async def test_integration_validation(manager: ValidationManager):
    report = await manager.validate_integrations()
    assert report.checks
    assert report.summary["total"] > 0


@pytest.mark.asyncio
async def test_performance_benchmarks(manager: ValidationManager):
    report = await manager.validate_performance()
    assert report.title == "Performance Report"
    assert len(manager._performance.benchmarks) >= 1


@pytest.mark.asyncio
async def test_stress_testing(manager: ValidationManager):
    report = await manager.validate_stress()
    assert report.title == "Stress Test Report"
    assert len(manager._stress.results) >= 1


@pytest.mark.asyncio
async def test_compatibility_validation(manager: ValidationManager):
    report = await manager.validate_compatibility()
    module_check = next(c for c in report.checks if c.check_id == "compatibility.modules")
    assert module_check.status in {ValidationStatus.PASS, ValidationStatus.WARN}


@pytest.mark.asyncio
async def test_production_readiness(manager: ValidationManager):
    report = await manager.validate_production_readiness()
    assert report.summary["total"] >= 8
    health = manager.build_health_report()
    assert health.readiness_level.value in {"production_ready", "partial", "not_ready"}


@pytest.mark.asyncio
async def test_quality_assurance(manager: ValidationManager):
    report = await manager.validate_quality(include_regression=False)
    assert any(c.check_id == "quality.architecture" for c in report.checks)


@pytest.mark.asyncio
async def test_full_platform_validation(manager: ValidationManager):
    report = await manager.validate_platform(include_stress=True, include_performance=True)
    assert report.status in {ValidationStatus.PASS, ValidationStatus.WARN}
    assert report.summary["suites"]


@pytest.mark.asyncio
async def test_certification(manager: ValidationManager):
    result = await manager.certify_platform(include_stress=False)
    assert result.platform_version == "3.0.0"
    assert result.gates_total >= 1


@pytest.mark.asyncio
async def test_readiness_report(manager: ValidationManager):
    await manager.validate_platform(include_stress=False)
    summary = manager.readiness_report()
    assert "platform_validation" in summary
    assert "metrics" in summary


@pytest.mark.asyncio
async def test_platform_validated_event(manager: ValidationManager):
    received: list = []

    from events import subscribe

    subscribe("PlatformValidatedEvent", lambda e: received.append(e))
    await manager.validate_platform(include_stress=False, include_performance=False)
    await asyncio.sleep(0.05)
    assert len(received) >= 1


def test_validation_metrics(manager: ValidationManager):
    assert manager.metrics_summary()["validation_runs"] == 0


@pytest.mark.asyncio
async def test_compatibility_version_check(manager: ValidationManager):
    report = await manager.validate_compatibility()
    version_check = next(c for c in report.checks if c.check_id == "compatibility.version")
    assert version_check.status == ValidationStatus.PASS
