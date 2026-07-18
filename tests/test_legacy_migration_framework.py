"""Tests — deprecation framework, runtime monitoring, CI validation."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from platform_legacy.ci_validation import assert_legacy_ci_clean, validate_legacy_ci
from platform_legacy.compatibility_layer import compatibility_layer
from platform_legacy.coverage import migration_coverage
from platform_legacy.deprecation import deprecated, list_registered_deprecations
from platform_legacy.docs_generator import generate_legacy_migration_markdown
from platform_legacy.feature_flags import LegacyMigrationFlags
from platform_legacy.migration_manager import migration_manager
from platform_legacy.runtime_monitor import runtime_monitor


@pytest.fixture(autouse=True)
def _reset_monitors():
    migration_coverage.reset()
    runtime_monitor.reset()
    yield
    migration_coverage.reset()
    runtime_monitor.reset()


def test_deprecated_decorator_warns_and_registers():
    @deprecated(replacement="platform.new_fn", removal_version="3.0.0", subsystem="test")
    def old_fn() -> str:
        return "ok"

    with pytest.warns(DeprecationWarning):
        assert old_fn() == "ok"
    names = [d["name"] for d in list_registered_deprecations()]
    assert any("old_fn" in n for n in names)


@pytest.mark.asyncio
async def test_runtime_monitor_tracks_platform_and_legacy():
    runtime_monitor.record_platform("users", method="a", latency_ms=10)
    runtime_monitor.record_legacy("users", method="b", latency_ms=20)
    runtime_monitor.record_fallback("users", reason="flag")
    snap = runtime_monitor.snapshot()
    assert snap["platform_calls"] == 1
    assert snap["legacy_calls"] == 1
    assert snap["fallbacks"] == 1
    assert snap["migration_ratio"]["platform_percent"] == 50.0


@pytest.mark.asyncio
async def test_compatibility_fallback_increments_monitor():
    async def platform_fn() -> str:
        return "p"

    async def legacy_fn() -> str:
        return "l"

    flags = LegacyMigrationFlags(legacy_notifications=True)
    with patch("platform_legacy.migration_manager.load_legacy_migration_flags", return_value=flags):
        result = await compatibility_layer.dispatch_async(
            "notifications",
            platform_fn=platform_fn,
            legacy_fn=legacy_fn,
            method="notify",
        )
    assert result == "l"
    assert runtime_monitor.legacy_calls == 1
    assert runtime_monitor.fallbacks >= 1


def test_coverage_report_migrated_and_remaining():
    migration_coverage.record_platform("configuration")
    migration_coverage.record_legacy("telegram")
    report = migration_coverage.coverage_report()
    assert "configuration" in report["migrated_components"]
    assert "telegram" in report["remaining_legacy"]
    assert report["migration_percent"] == 50.0


def test_ci_validation_passes_on_clean_platform():
    result = validate_legacy_ci()
    platform_issues = [
        i for i in result["issues"] if "platform_" in i["path"] or i["path"].startswith("startup")
    ]
    assert platform_issues == []


def test_ci_validation_detects_forbidden_import(tmp_path):
    bad = tmp_path / "platform_foo" / "bad.py"
    bad.parent.mkdir(parents=True)
    bad.write_text("from handlers import router\n", encoding="utf-8")
    result = validate_legacy_ci(tmp_path)
    assert result["ok"] is False


def test_generate_legacy_migration_doc():
    md = generate_legacy_migration_markdown()
    assert "# Legacy Migration Guide" in md
    assert "Migration Matrix" in md
    assert "Compatibility Guarantees" in md
    assert "legacy_users" in md


def test_migration_report_has_runtime_section():
    from platform_legacy.migration_report import build_migration_report

    report = build_migration_report()
    assert "runtime" in report
    assert "coverage" in report
    assert "remaining_legacy" in report
