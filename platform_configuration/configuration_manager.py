# ConfigurationManager — unified configuration and deployment entry point.

from __future__ import annotations

import logging
import time
from typing import Any

from events.publisher import publish
from platform_configuration.configuration_events import (
    ConfigurationLoadedEvent,
    DeploymentCompletedEvent,
    EnvironmentActivatedEvent,
    FeatureFlagChangedEvent,
    MigrationAppliedEvent,
)
from platform_configuration.configuration_loader import ConfigurationLoader, configuration_loader
from platform_configuration.configuration_provider import ConfigurationProvider, configuration_provider
from platform_configuration.configuration_validator import ConfigurationValidator, configuration_validator
from platform_configuration.deployment_manager import DeploymentManager, deployment_manager
from platform_configuration.environment_manager import EnvironmentManager, environment_manager
from platform_configuration.feature_flag_manager import FeatureFlagManager, feature_flag_manager
from platform_configuration.integrations import ConfigurationIntegrations, configuration_integrations
from platform_configuration.layer_config import DEFAULT_LAYER_CONFIG, ConfigurationLayerConfig
from platform_configuration.layer_exceptions import ConfigurationValidationError
from platform_configuration.metrics import ConfigurationMetrics, configuration_metrics
from platform_configuration.migration_manager import MigrationManager, migration_manager
from platform_configuration.models import (
    ConfigurationSnapshot,
    DeploymentTarget,
    EnvironmentProfile,
    FeatureFlag,
    MigrationDirection,
    VersionInfo,
)
from platform_configuration.version_manager import VersionManager, version_manager

logger = logging.getLogger(__name__)


class ConfigurationManager:
    """Centralized configuration, deployment, and version management facade."""

    def __init__(
        self,
        *,
        loader: ConfigurationLoader | None = None,
        provider: ConfigurationProvider | None = None,
        validator: ConfigurationValidator | None = None,
        environments: EnvironmentManager | None = None,
        flags: FeatureFlagManager | None = None,
        deployment: DeploymentManager | None = None,
        versions: VersionManager | None = None,
        migrations: MigrationManager | None = None,
        metrics: ConfigurationMetrics | None = None,
        integrations: ConfigurationIntegrations | None = None,
        config: ConfigurationLayerConfig | None = None,
    ) -> None:
        self._loader = loader or configuration_loader
        self._provider = provider or configuration_provider
        self._validator = validator or configuration_validator
        self._environments = environments or environment_manager
        self._flags = flags or feature_flag_manager
        self._deployment = deployment or deployment_manager
        self._versions = versions or version_manager
        self._migrations = migrations or migration_manager
        self._metrics = metrics or configuration_metrics
        self._integrations = integrations or configuration_integrations
        self._config = config or DEFAULT_LAYER_CONFIG
        self._snapshots: dict[str, ConfigurationSnapshot] = {}

    def reset(self) -> None:
        self._loader.reset()
        self._environments.reset()
        self._flags.reset()
        self._deployment.reset()
        self._versions.reset()
        self._migrations.reset()
        self._metrics.reset()
        self._snapshots.clear()

    def load_configuration(
        self,
        *,
        environment: str = "development",
        overrides: dict[str, Any] | None = None,
    ) -> ConfigurationSnapshot:
        try:
            snapshot = self._loader.load(environment=environment, overrides=overrides)
            if self._config.enable_encryption:
                snapshot = self._loader.load_encrypted_values(
                    snapshot,
                    decrypt_fn=self._integrations.decrypt_value,
                )
            self._validator.validate_snapshot(snapshot)
            self._provider.apply_snapshot(snapshot)
            self._snapshots[snapshot.snapshot_id] = snapshot
            self._metrics.record_load(self._loader.last_load_ms)
            self._metrics.set_environment_status(environment, "loaded")
        except ConfigurationValidationError:
            self._metrics.record_error()
            raise

        return snapshot

    async def load_and_publish(
        self,
        *,
        environment: str = "development",
        overrides: dict[str, Any] | None = None,
    ) -> ConfigurationSnapshot:
        snapshot = self.load_configuration(environment=environment, overrides=overrides)
        await publish(
            ConfigurationLoadedEvent(
                environment=environment,
                key_count=len(snapshot.values),
                duration_ms=self._loader.last_load_ms,
            )
        )
        await self._integrations.observability_log_load(snapshot, self._loader.last_load_ms)
        return snapshot

    def activate_environment(
        self,
        name: str,
        *,
        overrides: dict[str, Any] | None = None,
    ) -> ConfigurationSnapshot:
        snapshot = self._environments.activate(name, overrides=overrides)
        self._provider.apply_snapshot(snapshot)
        self._metrics.set_environment_status(name, "active")
        return snapshot

    async def activate_and_publish(self, name: str, **kwargs: Any) -> ConfigurationSnapshot:
        snapshot = self.activate_environment(name, **kwargs)
        await publish(
            EnvironmentActivatedEvent(
                environment=name,
                isolated=self._environments.is_isolated(name),
            )
        )
        self._integrations.memory_store_profile(name, snapshot.to_dict())
        return snapshot

    def update_runtime(self, key: str, value: Any) -> Any:
        if not self._config.enable_runtime_updates:
            raise ConfigurationValidationError("Runtime updates disabled")
        validated = self._validator.validate_value(key, value)
        self._provider.set(key, validated)
        return validated

    def encrypt_config_value(self, key: str, value: str) -> str:
        secret_id = self._integrations.encrypt_value(key, value)
        self._provider.set(key, secret_id)
        return secret_id

    def is_feature_enabled(
        self,
        key: str,
        *,
        agent_id: str | None = None,
        workflow_id: str | None = None,
        user_id: str | None = None,
        default: bool = False,
    ) -> bool:
        return self._flags.is_enabled(
            key,
            agent_id=agent_id,
            workflow_id=workflow_id,
            user_id=user_id,
            default=default,
        )

    async def set_feature_flag(self, flag: FeatureFlag) -> FeatureFlag:
        registered = self._flags.register(flag)
        await publish(
            FeatureFlagChangedEvent(
                flag_key=flag.key,
                enabled=flag.enabled,
                metadata=flag.metadata,
            )
        )
        return registered

    async def deploy(
        self,
        *,
        target: DeploymentTarget = DeploymentTarget.LOCAL,
        environment: str | None = None,
        version: str = "",
    ) -> Any:
        env = environment or self._environments.active_environment
        version_info = self._versions.get_version_info()
        ver = version or version_info.platform_version
        started = time.perf_counter()
        record = await self._deployment.deploy(target=target, environment=env, version=ver)
        duration_ms = (time.perf_counter() - started) * 1000.0
        self._metrics.record_deployment(record.duration_ms or duration_ms)
        await publish(
            DeploymentCompletedEvent(
                deployment_id=record.deployment_id,
                target=record.target.value,
                status=record.status.value,
                duration_ms=record.duration_ms,
            )
        )
        await self._integrations.record_deployment_metrics(record)
        await self._integrations.reliability_checkpoint_config(
            ConfigurationSnapshot(environment=env, values={"deployment_id": record.deployment_id})
        )
        return record

    async def rollback_deployment(self) -> Any:
        record = await self._deployment.rollback()
        self._metrics.record_rollback()
        return record

    def apply_migration(
        self,
        migration_id: str,
        config: dict[str, Any],
        *,
        direction: MigrationDirection = MigrationDirection.UP,
    ) -> tuple[dict[str, Any], Any]:
        started = time.perf_counter()
        migrated, record = self._migrations.apply(migration_id, config, direction=direction)
        self._metrics.record_migration((time.perf_counter() - started) * 1000.0)
        return migrated, record

    async def apply_migration_and_publish(
        self,
        migration_id: str,
        config: dict[str, Any],
        *,
        direction: MigrationDirection = MigrationDirection.UP,
    ) -> tuple[dict[str, Any], Any]:
        migrated, record = self.apply_migration(migration_id, config, direction=direction)
        await publish(
            MigrationAppliedEvent(
                migration_id=migration_id,
                direction=direction.value,
                version_to=record.version_to,
            )
        )
        return migrated, record

    def get_version_info(self) -> VersionInfo:
        return self._versions.get_version_info()

    def validate_platform(self) -> VersionInfo:
        return self._versions.validate_dependencies()

    def metrics_summary(self) -> dict[str, Any]:
        return self._metrics.summary()

    def register_custom_environment(self, name: str, overrides: dict[str, Any]) -> None:
        normalized = self._validator.validate_environment_name(name)
        self._loader.register_profile(normalized, overrides)
        self._environments.register_custom(normalized, overrides)

    def get_snapshot(self, snapshot_id: str) -> ConfigurationSnapshot | None:
        return self._snapshots.get(snapshot_id)


configuration_manager = ConfigurationManager()
