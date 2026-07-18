"""Tests — legacy migration manager, compatibility layer, feature flags."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from platform_legacy.compatibility_layer import compatibility_layer
from platform_legacy.coverage import MigrationCoverage
from platform_legacy.feature_flags import LegacyMigrationFlags, load_legacy_migration_flags
from platform_legacy.migration_manager import MigrationState, migration_manager
from platform_legacy.migration_report import build_migration_report


@pytest.fixture(autouse=True)
def _reset_migration_state():
    from platform_legacy.migration_manager import MigrationState, migration_manager

    snapshots = {name: migration_manager.get(name).state for name in migration_manager.list_subsystems()}
    yield
    for name, state in snapshots.items():
        migration_manager.set_state(name, state, notes="test_reset")


@pytest.fixture(autouse=True)
def _reset_coverage():
    from platform_legacy.coverage import migration_coverage

    migration_coverage.reset()
    yield
    migration_coverage.reset()


def test_migration_manager_default_states():
    assert migration_manager.state("configuration") == MigrationState.PLATFORM
    assert migration_manager.state("telegram") == MigrationState.LEGACY
    assert migration_manager.state("users") == MigrationState.MIGRATING


def test_platform_default_route_in_migrating_subsystem():
    flags = LegacyMigrationFlags()
    with patch("platform_legacy.migration_manager.load_legacy_migration_flags", return_value=flags):
        assert migration_manager.should_route_to_legacy("users") is False


def test_legacy_flag_enables_compatibility_path():
    flags = LegacyMigrationFlags(legacy_users=True)
    with patch("platform_legacy.migration_manager.load_legacy_migration_flags", return_value=flags):
        assert migration_manager.should_route_to_legacy("users") is True


def test_legacy_state_always_routes_legacy():
    flags = LegacyMigrationFlags()
    migration_manager.set_state("requests", MigrationState.LEGACY)
    with patch("platform_legacy.migration_manager.load_legacy_migration_flags", return_value=flags):
        assert migration_manager.should_route_to_legacy("requests") is True
    migration_manager.set_state("requests", MigrationState.MIGRATING)


def test_rollback_is_reversible():
    migration_manager.set_state("workflow", MigrationState.PLATFORM)
    migration_manager.rollback("workflow")
    assert migration_manager.state("workflow") == MigrationState.LEGACY
    migration_manager.set_state("workflow", MigrationState.MIGRATING)


@pytest.mark.asyncio
async def test_compatibility_layer_records_coverage():
    from platform_legacy.coverage import migration_coverage

    async def platform_fn() -> str:
        return "platform"

    async def legacy_fn() -> str:
        return "legacy"

    flags = LegacyMigrationFlags()
    with patch("platform_legacy.migration_manager.load_legacy_migration_flags", return_value=flags):
        result = await compatibility_layer.dispatch_async(
            "notifications",
            platform_fn=platform_fn,
            legacy_fn=legacy_fn,
            method="test",
        )
    assert result == "platform"
    assert migration_coverage.platform_hits.get("notifications", 0) == 1


@pytest.mark.asyncio
async def test_compatibility_layer_legacy_path():
    from platform_legacy.coverage import migration_coverage

    async def platform_fn() -> str:
        return "platform"

    async def legacy_fn() -> str:
        return "legacy"

    flags = LegacyMigrationFlags(legacy_notifications=True)
    with patch("platform_legacy.migration_manager.load_legacy_migration_flags", return_value=flags):
        result = await compatibility_layer.dispatch_async(
            "notifications",
            platform_fn=platform_fn,
            legacy_fn=legacy_fn,
            method="test",
        )
    assert result == "legacy"
    assert migration_coverage.legacy_hits.get("notifications", 0) == 1


def test_migration_report_includes_subsystems():
    report = build_migration_report()
    assert "summary" in report
    assert "subsystems" in report
    assert "feature_flags" in report
    assert "coverage" in report
    assert "deprecated_apis" in report
    assert "health" in report
    assert "telegram" in report["subsystems"]


def test_feature_flags_load_defaults():
    flags = load_legacy_migration_flags()
    assert flags.legacy_users is False
    assert flags.legacy_handlers is False


def test_coverage_subsystem_percent():
    cov = MigrationCoverage()
    cov.record_platform("users", method="a")
    cov.record_platform("users", method="b")
    cov.record_legacy("users", method="c")
    stats = cov.subsystem_coverage("users")
    assert stats["platform_percent"] == pytest.approx(66.7, abs=0.1)
