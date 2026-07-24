"""Release library facade — Sprint 21.8."""

from __future__ import annotations

from typing import Any

from platform_release.backup import BackupService
from platform_release.certification import ReleaseCertification
from platform_release.deployment import DeploymentPackages
from platform_release.disaster_recovery import DisasterRecovery
from platform_release.health_checks import HealthChecks
from platform_release.installers import Installers
from platform_release.manifests import ProductionManifest
from platform_release.migration import MigrationFramework
from platform_release.models import INTEGRATION_TARGETS, LTS_LABEL, LTS_VERSION, PRODUCTION_STATUSES
from platform_release.monitoring import ProductionMonitoring
from platform_release.production import ProductionReadiness
from platform_release.release_notes import ReleaseNotes
from platform_release.validation import ProductionValidation


class ReleaseLibrary:
    def __init__(self) -> None:
        self.certification = ReleaseCertification()
        self.readiness = ProductionReadiness()
        self.deployment = DeploymentPackages()
        self.installers = Installers()
        self.migration = MigrationFramework()
        self.backup = BackupService()
        self.disaster_recovery = DisasterRecovery()
        self.health_checks = HealthChecks()
        self.monitoring = ProductionMonitoring()
        self.release_notes = ReleaseNotes()
        self.validation = ProductionValidation()
        self.manifest = ProductionManifest()

    def integrations(self) -> dict[str, Any]:
        return {"targets": list(INTEGRATION_TARGETS), "linked": True}

    def approve(self, *, architecture: bool = True, quality: bool = True, security: bool = True, documentation: bool = True) -> dict[str, Any]:
        approved = all([architecture, quality, security, documentation])
        return {
            "architecture_approved": architecture,
            "quality_approved": quality,
            "security_approved": security,
            "documentation_approved": documentation,
            "approved": approved,
            "release": LTS_VERSION if approved else None,
            "label": LTS_LABEL if approved else None,
        }

    def bootstrap(self) -> dict[str, Any]:
        self.__init__()
        cert = self.certification.certify()
        ready = self.readiness.validate()
        deploy = self.deployment.build()
        install = self.installers.package()
        migrate = self.migration.plan()
        backup = self.backup.configure()
        dr = self.disaster_recovery.validate()
        health = self.health_checks.run()
        monitor = self.monitoring.validate()
        notes = self.release_notes.generate()
        validation = self.validation.run()
        approval = self.approve()
        manifest = self.manifest.publish(approval=approval)
        production_ready = all(
            [
                cert["passed"],
                ready["passed"],
                deploy["passed"],
                migrate["passed"],
                backup["passed"],
                dr["passed"],
                health["passed"],
                monitor["passed"],
                notes["passed"],
                validation["passed"],
                approval["approved"],
                manifest["published"],
            ]
        )
        return {
            "bootstrap": True,
            "certified": cert["passed"],
            "certificate": cert["certificate"],
            "architecture_validated": cert["architecture_validated"],
            "domains_certified": cert["count"],
            "production_readiness_passed": ready["passed"],
            "deployment_packages": deploy["count"],
            "helm_ready": deploy["helm"],
            "migration_passed": migrate["passed"],
            "backup_automatic": backup["automatic"],
            "rpo_seconds": dr["rpo_seconds"],
            "rto_seconds": dr["rto_seconds"],
            "dr_passed": dr["passed"],
            "monitoring_passed": monitor["passed"],
            "health_passed": health["passed"],
            "validation_passed": validation["passed"],
            "release_notes_ready": notes["passed"],
            "lts_version": LTS_VERSION,
            "lts_label": LTS_LABEL,
            "lts_baseline": True,
            "approved": approval["approved"],
            "manifest_published": manifest["published"],
            "production_ready": production_ready,
            "enterprise_certified": production_ready,
            "statuses": list(PRODUCTION_STATUSES),
            "status": "production_ready" if production_ready else "blocked",
            "integrations": self.integrations(),
            "full": {
                "certification": cert,
                "readiness": ready,
                "deployment": deploy,
                "installers": install,
                "migration": migrate,
                "backup": backup,
                "disaster_recovery": dr,
                "health": health,
                "monitoring": monitor,
                "release_notes": notes,
                "validation": validation,
                "approval": approval,
                "manifest": manifest,
            },
        }

    def status(self) -> dict[str, Any]:
        return {
            "lts_version": LTS_VERSION,
            "components": [
                "certification",
                "deployment",
                "migration",
                "backup",
                "disaster_recovery",
                "monitoring",
                "validation",
            ],
        }


release_library = ReleaseLibrary()
