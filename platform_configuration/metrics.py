# Configuration & Deployment Layer — metrics.

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ConfigurationMetrics:
    configuration_load_count: int = 0
    configuration_load_time_ms: float = 0.0
    configuration_errors: int = 0
    deployment_count: int = 0
    deployment_duration_ms: float = 0.0
    migration_count: int = 0
    migration_duration_ms: float = 0.0
    rollback_count: int = 0
    environment_status: dict[str, str] = field(default_factory=dict)

    def reset(self) -> None:
        self.configuration_load_count = 0
        self.configuration_load_time_ms = 0.0
        self.configuration_errors = 0
        self.deployment_count = 0
        self.deployment_duration_ms = 0.0
        self.migration_count = 0
        self.migration_duration_ms = 0.0
        self.rollback_count = 0
        self.environment_status.clear()

    def record_load(self, duration_ms: float) -> None:
        self.configuration_load_count += 1
        self.configuration_load_time_ms += duration_ms

    def record_error(self) -> None:
        self.configuration_errors += 1

    def record_deployment(self, duration_ms: float) -> None:
        self.deployment_count += 1
        self.deployment_duration_ms += duration_ms

    def record_migration(self, duration_ms: float) -> None:
        self.migration_count += 1
        self.migration_duration_ms += duration_ms

    def record_rollback(self) -> None:
        self.rollback_count += 1

    def set_environment_status(self, environment: str, status: str) -> None:
        self.environment_status[environment] = status

    def summary(self) -> dict[str, Any]:
        avg_load = (
            self.configuration_load_time_ms / self.configuration_load_count
            if self.configuration_load_count
            else 0.0
        )
        avg_deploy = (
            self.deployment_duration_ms / self.deployment_count if self.deployment_count else 0.0
        )
        avg_migration = (
            self.migration_duration_ms / self.migration_count if self.migration_count else 0.0
        )
        return {
            "configuration_load_count": self.configuration_load_count,
            "configuration_load_time_avg_ms": round(avg_load, 2),
            "configuration_errors": self.configuration_errors,
            "deployment_count": self.deployment_count,
            "deployment_duration_avg_ms": round(avg_deploy, 2),
            "migration_count": self.migration_count,
            "migration_duration_avg_ms": round(avg_migration, 2),
            "rollback_count": self.rollback_count,
            "environment_status": dict(self.environment_status),
            "recorded_at": time.time(),
        }


configuration_metrics = ConfigurationMetrics()
