# Configuration & Deployment Layer — exceptions.

from __future__ import annotations


class ConfigurationLayerError(Exception):
    """Base error for configuration layer."""


class ConfigurationValidationError(ConfigurationLayerError):
    def __init__(self, message: str, *, key: str | None = None) -> None:
        super().__init__(message)
        self.key = key


class EnvironmentNotFoundError(ConfigurationLayerError):
    def __init__(self, name: str) -> None:
        super().__init__(f"Environment profile not found: {name}")
        self.name = name


class DeploymentError(ConfigurationLayerError):
    def __init__(self, message: str, *, deployment_id: str | None = None) -> None:
        super().__init__(message)
        self.deployment_id = deployment_id


class MigrationError(ConfigurationLayerError):
    def __init__(self, message: str, *, migration_id: str | None = None) -> None:
        super().__init__(message)
        self.migration_id = migration_id


class VersionCompatibilityError(ConfigurationLayerError):
    def __init__(self, message: str, issues: list[str] | None = None) -> None:
        super().__init__(message)
        self.issues = issues or []


class SnapshotNotFoundError(ConfigurationLayerError):
    def __init__(self, snapshot_id: str) -> None:
        super().__init__(f"Configuration snapshot not found: {snapshot_id}")
        self.snapshot_id = snapshot_id
