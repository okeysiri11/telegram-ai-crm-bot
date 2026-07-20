# Operations facade — deployment, monitoring, backups, maintenance, incidents.

from __future__ import annotations

from typing import Any

from applications.auto_marketplace.backups.service import BackupService, backup_service
from applications.auto_marketplace.deployment.service import DeploymentService, deployment_service
from applications.auto_marketplace.maintenance.service import MaintenanceService, maintenance_service
from applications.auto_marketplace.monitoring.service import MonitoringService, monitoring_service
from applications.auto_marketplace.support.service import SupportService, support_service


class OperationsService:
    """Unified operations entry point for go-live and day-2 operations."""

    def __init__(
        self,
        deployment: DeploymentService | None = None,
        monitoring: MonitoringService | None = None,
        backups: BackupService | None = None,
        maintenance: MaintenanceService | None = None,
        support: SupportService | None = None,
    ) -> None:
        self.deployment = deployment or deployment_service
        self.monitoring = monitoring or monitoring_service
        self.backups = backups or backup_service
        self.maintenance = maintenance or maintenance_service
        self.support = support or support_service

    def deployment_checklist(self) -> list[dict[str, Any]]:
        return self.deployment.checklist()

    def rollback_procedure(self) -> dict[str, Any]:
        return self.deployment.rollback_procedure()

    def backup_procedures(self) -> dict[str, Any]:
        return {
            "backup": self.backups.backup_procedure(),
            "restore": self.backups.restore_procedure(),
        }

    async def monitoring_integration(self) -> dict[str, Any]:
        return await self.monitoring.integrate_observability()

    def incident_guide(self) -> dict[str, Any]:
        return self.monitoring.incident_guide()

    def maintenance_status(self) -> dict[str, Any]:
        return self.maintenance.status()

    def operations_guide(self) -> dict[str, Any]:
        return {
            "deployment_checklist": self.deployment_checklist(),
            "rollback": self.rollback_procedure(),
            "backups": self.backup_procedures(),
            "incidents": self.incident_guide(),
            "maintenance": self.maintenance_status(),
            "support": self.support.guide(),
        }


operations_service = OperationsService()
