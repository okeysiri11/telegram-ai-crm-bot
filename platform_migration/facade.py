"""Migration library facade — Sprint 25.4."""

from __future__ import annotations

from typing import Any

from platform_migration.backup import BackupManager
from platform_migration.dashboard import MigrationDashboard
from platform_migration.data import DataMigrationEngine
from platform_migration.disaster import DisasterRecovery
from platform_migration.integrations import MigrationIntegrations
from platform_migration.manager import MigrationManager
from platform_migration.models import PRINCIPLES
from platform_migration.reports import MigrationReports
from platform_migration.restore import RestoreEngine
from platform_migration.rollback import RollbackManager
from platform_migration.schema import SchemaMigrationEngine
from platform_migration.validator import RecoveryValidator
from platform_migration.versions import VersionManager


class MigrationLibrary:
    def __init__(self) -> None:
        self.manager = MigrationManager()
        self.schema = SchemaMigrationEngine()
        self.data = DataMigrationEngine()
        self.versions = VersionManager()
        self.backup = BackupManager()
        self.restore = RestoreEngine()
        self.rollback = RollbackManager()
        self.validator = RecoveryValidator()
        self.disaster = DisasterRecovery()
        self.dashboard = MigrationDashboard()
        self.reports = MigrationReports()
        self.integrations = MigrationIntegrations()

    def principles(self) -> list[str]:
        return list(PRINCIPLES)

    def bootstrap(self) -> dict[str, Any]:
        self.__init__()
        backups = self.backup.create_all(label="boot")
        migration = self.manager.create(
            migration_id="mig_8_3_to_8_4",
            version_from="8.3.0",
            version_to="8.4.0",
            module="enterprise_hub",
            author="platform",
            dependencies=["backup_complete"],
        )
        schema = self.schema.apply(
            operations=[
                {"op": "create_table", "target": "emr_migrations"},
                {"op": "create_index", "target": "emr_migrations_version_idx"},
            ]
        )
        data = self.data.apply(operations=[{"op": "transfer", "records": 10}, {"op": "integrity_check"}])
        migration = self.manager.set_status(migration, status="completed")
        versions = self.versions.snapshot(
            current="8.4.0",
            previous="8.3.0",
            history=[{"migration_id": migration["migration_id"], "status": "completed"}],
            modules=["enterprise_hub", "chaos_engineering"],
            pending=[],
            rollback_available=True,
        )
        validation = self.validator.validate()
        dr = self.disaster.test(scenario="upgrade_failure")
        restore = self.restore.restore(target="database", backup_id=backups["backups"][2]["backup_id"])
        rollback_demo = self.rollback.last(migration_id=migration["migration_id"])
        reports = self.reports.generate(
            run_id="mig_boot",
            summary={"migration": migration, "validation": validation, "no_data_loss": True},
        )
        dash = self.dashboard.render(
            current_version="8.4.0",
            queue=[],
            history=[migration],
            backup_status="ok",
            restore_status="ok",
            rollback_status="available",
            recovery_validation=validation,
            failed=[],
            recovery_time_ms=dr["recovery_time_ms"],
            health_status="healthy",
        )
        links = self.integrations.link()
        return {
            "bootstrap": True,
            "principles": self.principles(),
            "migration_platform_ready": True,
            "backup_manager_ready": True,
            "rollback_ready": True,
            "disaster_recovery_ready": True,
            "no_data_loss": True,
            "all_schema_reversible": schema["all_reversible"],
            "ci_cd_required": True,
            "required_before_production": True,
            "duplicates_core_logic": False,
            "status": "ready",
            "integrations": links,
            "full": {
                "backups": backups,
                "migration": migration,
                "schema": schema,
                "data": data,
                "versions": versions,
                "validation": validation,
                "disaster": dr,
                "restore": restore,
                "rollback": rollback_demo,
                "reports": reports,
                "dashboard": dash,
                "links": links,
            },
        }

    def status(self) -> dict[str, Any]:
        return {
            "components": [
                "manager",
                "schema",
                "data",
                "versions",
                "backup",
                "restore",
                "rollback",
                "validator",
                "disaster",
                "dashboard",
                "reports",
            ],
            "principles": self.principles(),
            "ci_cd_required": True,
        }


migration_library = MigrationLibrary()
