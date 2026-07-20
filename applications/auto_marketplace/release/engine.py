# Production release engine — validation, deployment, operations facade.

from __future__ import annotations

from typing import Any

from applications.auto_marketplace.backups.service import BackupService, backup_service
from applications.auto_marketplace.config import DEFAULT_CONFIG
from applications.auto_marketplace.deployment.service import DeploymentService, deployment_service
from applications.auto_marketplace.maintenance.service import MaintenanceService, maintenance_service
from applications.auto_marketplace.monitoring.service import MonitoringService, monitoring_service
from applications.auto_marketplace.operations.service import OperationsService, operations_service
from applications.auto_marketplace.quality_assurance.performance import PerformanceBenchmarks, performance_benchmarks
from applications.auto_marketplace.quality_assurance.security_audit import SecurityAuditor, security_auditor
from applications.auto_marketplace.quality_assurance.validator import ProductionValidator, production_validator
from applications.auto_marketplace.release.models import ReleaseReport, ValidationStatus
from applications.auto_marketplace.support.service import SupportService, support_service


class ProductionEngine:
    """Production release, validation, and operations entry point."""

    def __init__(
        self,
        validator: ProductionValidator | None = None,
        performance: PerformanceBenchmarks | None = None,
        security: SecurityAuditor | None = None,
        deployment: DeploymentService | None = None,
        monitoring: MonitoringService | None = None,
        backups: BackupService | None = None,
        support: SupportService | None = None,
        maintenance: MaintenanceService | None = None,
        operations: OperationsService | None = None,
    ) -> None:
        self.validator = validator or production_validator
        self.performance = performance or performance_benchmarks
        self.security = security or security_auditor
        self.deployment = deployment or deployment_service
        self.monitoring = monitoring or monitoring_service
        self.backups = backups or backup_service
        self.support = support or support_service
        self.maintenance = maintenance or maintenance_service
        self.operations = operations or operations_service

    async def generate_release_report(self, *, run_benchmarks: bool = True) -> ReleaseReport:
        validations = await self.validator.validate_all()
        security_audit = await self.security.run_audit()
        benchmarks = await self.performance.run_all(iterations=5) if run_benchmarks else []
        all_checks = validations + security_audit
        failed = [v for v in all_checks if v.status == ValidationStatus.FAILED]
        bench_failed = [b for b in benchmarks if not b.passed]
        production_ready = not failed and not bench_failed
        return ReleaseReport(
            application_version=DEFAULT_CONFIG.application_version,
            release_status=DEFAULT_CONFIG.release_status,
            platform_dependency=DEFAULT_CONFIG.platform_dependency,
            validations=validations,
            benchmarks=benchmarks,
            security_audit=security_audit,
            production_ready=production_ready,
        )

    def release_manifest(self) -> dict[str, Any]:
        import json
        from pathlib import Path

        manifest_path = Path(__file__).resolve().parent / "manifest.json"
        if manifest_path.exists():
            return json.loads(manifest_path.read_text(encoding="utf-8"))
        return {
            "application": "auto_marketplace",
            "application_version": DEFAULT_CONFIG.application_version,
            "release_status": DEFAULT_CONFIG.release_status,
            "platform_dependency": DEFAULT_CONFIG.platform_dependency,
        }

    def go_live_checklist(self) -> list[dict[str, Any]]:
        return self.deployment.checklist()

    def metrics(self) -> dict[str, Any]:
        return {
            "application_version": DEFAULT_CONFIG.application_version,
            "release_status": DEFAULT_CONFIG.release_status,
            "maintenance_mode": self.maintenance.enabled,
            "snapshots": len(self.backups.list_snapshots()),
        }


production_engine = ProductionEngine()
