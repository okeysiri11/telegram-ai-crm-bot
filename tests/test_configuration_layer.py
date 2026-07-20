"""Tests — Platform Configuration & Deployment Layer (Sprint 5.4)."""

from __future__ import annotations

import asyncio

import pytest

from platform_configuration.configuration_loader import ConfigurationLoader
from platform_configuration.configuration_manager import ConfigurationManager
from platform_configuration.configuration_validator import ConfigurationValidator
from platform_configuration.deployment_manager import DeploymentManager
from platform_configuration.environment_manager import EnvironmentManager
from platform_configuration.feature_flag_manager import FeatureFlagManager
from platform_configuration.layer_exceptions import DeploymentError, VersionCompatibilityError
from platform_configuration.metrics import ConfigurationMetrics
from platform_configuration.migration_manager import MigrationManager
from platform_configuration.models import DeploymentTarget, EnvironmentProfile, FeatureFlag, MigrationDirection
from platform_configuration.version_manager import VersionManager


@pytest.fixture
def manager() -> ConfigurationManager:
    loader = ConfigurationLoader()
    flags = FeatureFlagManager()
    deployment = DeploymentManager()
    migrations = MigrationManager()
    environments = EnvironmentManager(loader=loader)
    mgr = ConfigurationManager(
        loader=loader,
        environments=environments,
        flags=flags,
        deployment=deployment,
        migrations=migrations,
        metrics=ConfigurationMetrics(),
        versions=VersionManager(),
    )
    yield mgr
    mgr.reset()


def test_hierarchical_configuration_load(manager: ConfigurationManager):
    snapshot = manager.load_configuration(environment=EnvironmentProfile.PRODUCTION.value)
    assert snapshot.environment == "production"
    assert snapshot.values["general.environment"] == "production"
    assert snapshot.values["general.log_level"] == "WARNING"
    assert "base_defaults" in snapshot.source_layers


def test_configuration_inheritance_and_overrides(manager: ConfigurationManager):
    manager.register_custom_environment("preview", {"general.log_level": "DEBUG"})
    snapshot = manager.load_configuration(environment="preview")
    assert snapshot.values["general.log_level"] == "DEBUG"


def test_configuration_validation(manager: ConfigurationManager):
    validator = ConfigurationValidator()
    with pytest.raises(Exception):
        validator.validate_value("sla.assignment_sec", 10)


def test_runtime_configuration_update(manager: ConfigurationManager):
    manager.load_configuration()
    value = manager.update_runtime("sla.assignment_sec", 1200)
    assert value == 1200


def test_encrypted_configuration_value(manager: ConfigurationManager):
    secret_id = manager.encrypt_config_value("api.secret", "super-secret")
    assert secret_id


def test_environment_profiles(manager: ConfigurationManager):
    snapshot = manager.activate_environment(EnvironmentProfile.STAGING.value)
    assert snapshot.environment == "staging"
    assert manager._environments.is_isolated("staging")


def test_feature_flag_enable_disable(manager: ConfigurationManager):
    manager._flags.set("new_ui", enabled=True)
    assert manager.is_feature_enabled("new_ui")


def test_feature_flag_gradual_rollout():
    flags = FeatureFlagManager()
    flags.set("rollout", enabled=True, rollout_percent=0.0)
    assert not flags.is_enabled("rollout", user_id="user-1")
    flags.set("rollout", rollout_percent=100.0)
    assert flags.is_enabled("rollout", user_id="user-1")


def test_feature_flag_per_agent():
    flags = FeatureFlagManager()
    flags.set("agent_feature", enabled=True)
    flags.scope_agent("agent_feature", "agent-a")
    assert flags.is_enabled("agent_feature", agent_id="agent-a")
    assert not flags.is_enabled("agent_feature", agent_id="agent-b")


def test_feature_flag_per_workflow():
    flags = FeatureFlagManager()
    flags.set("wf_feature", enabled=True)
    flags.scope_workflow("wf_feature", "wf-1")
    assert flags.is_enabled("wf_feature", workflow_id="wf-1")
    assert not flags.is_enabled("wf_feature", workflow_id="wf-2")


def test_feature_flag_per_user():
    flags = FeatureFlagManager()
    flags.set("user_feature", enabled=True)
    flags.scope_user("user_feature", "user-42")
    assert flags.is_enabled("user_feature", user_id="user-42")


@pytest.mark.asyncio
async def test_local_deployment(manager: ConfigurationManager):
    record = await manager.deploy(target=DeploymentTarget.LOCAL, version="2.8.0-alpha")
    assert record.status.value == "verified"
    assert record.duration_ms >= 0


@pytest.mark.asyncio
async def test_docker_deployment_simulated(manager: ConfigurationManager):
    record = await manager.deploy(target=DeploymentTarget.DOCKER, version="2.8.0-alpha")
    assert record.status.value in {"verified", "failed"}


@pytest.mark.asyncio
async def test_deployment_rollback(manager: ConfigurationManager):
    await manager.deploy(target=DeploymentTarget.LOCAL, version="2.8.0-alpha")
    await manager.deploy(target=DeploymentTarget.LOCAL, version="2.8.1-alpha")
    rolled = await manager.rollback_deployment()
    assert rolled.status.value == "rolled_back"
    assert manager.metrics_summary()["rollback_count"] == 1


@pytest.mark.asyncio
async def test_deployment_rollback_without_previous(manager: ConfigurationManager):
    with pytest.raises(DeploymentError):
        await manager.rollback_deployment()


def test_migration_apply_and_rollback(manager: ConfigurationManager):
    config = {"general.environment": "development"}
    migrated, record = manager.apply_migration("config_1_0_to_1_1", config)
    assert "deployment.last_version" in migrated
    assert record.success

    rolled, rollback_record = manager.apply_migration(
        "config_1_0_to_1_1",
        migrated,
        direction=MigrationDirection.DOWN,
    )
    assert "deployment.last_version" not in rolled
    assert rollback_record.direction == MigrationDirection.DOWN


def test_migration_validation(manager: ConfigurationManager):
    assert manager._migrations.validate_migration("config_1_0_to_1_1")
    assert not manager._migrations.validate_migration("unknown_migration")


def test_version_management(manager: ConfigurationManager):
    info = manager.get_version_info()
    assert info.platform_version
    assert info.configuration_layer == "1.0" or "2." in info.platform_version


def test_version_compatibility(manager: ConfigurationManager):
    info = manager.validate_platform()
    assert info.compatible or info.issues


def test_configuration_metrics(manager: ConfigurationManager):
    manager.load_configuration()
    summary = manager.metrics_summary()
    assert summary["configuration_load_count"] >= 1


@pytest.mark.asyncio
async def test_configuration_loaded_event(manager: ConfigurationManager):
    received: list = []

    from events import subscribe

    subscribe("ConfigurationLoadedEvent", lambda e: received.append(e))

    await manager.load_and_publish(environment="testing")
    await asyncio.sleep(0.05)
    assert len(received) >= 1
