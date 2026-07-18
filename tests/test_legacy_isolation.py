"""Tests — legacy isolation boundary (platform_legacy adapters only)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from platform_legacy import legacy, legacy_registry, scan_legacy_import_violations
from platform_legacy.adapter import CRMAdapter, PermissionsAdapter, TracedAdapter
from platform_legacy.registry import LegacyRegistry

ROOT = Path(__file__).resolve().parents[1]


def test_registry_lists_default_adapters():
    names = legacy_registry.list_adapters()
    assert "crm" in names
    assert "telegram" in names
    assert "permissions" in names
    assert "notification" in names
    assert "audit" in names
    assert "scheduler" in names


def test_facade_routes_to_registry():
    assert legacy.crm.adapter_name == "crm"
    assert legacy.permissions.adapter_name == "permissions"


@pytest.mark.asyncio
async def test_permissions_adapter_traces_calls():
    registry = LegacyRegistry()
    registry.wire_defaults()
    adapter = registry.get("permissions")

    with patch(
        "services.pg_platform_permissions_engine.PlatformPermissionsEngineV1.user_has_permission",
        new_callable=AsyncMock,
        return_value=True,
    ):
        result = await adapter.user_has_permission(42, "admin.access")

    assert result is True
    assert registry.metrics.total_calls >= 1
    assert registry.metrics.calls_by_adapter.get("permissions", 0) >= 1


def test_traced_adapter_logs_failures():
    registry = LegacyRegistry()
    adapter = CRMAdapter(registry=registry)

    with patch.object(adapter, "_record") as record:
        with pytest.raises(RuntimeError):
            adapter._trace("boom", lambda: (_ for _ in ()).throw(RuntimeError("fail")))
        assert record.call_args.kwargs["success"] is False


def test_no_forbidden_legacy_imports_in_platform_modules():
    violations = scan_legacy_import_violations(ROOT)
    platform_violations = [
        v
        for v in violations
        if v.path.startswith(("platform_", "src/platform/", "src/verticals/", "startup.py", "events/"))
        and not v.path.startswith("platform_legacy/")
    ]
    assert platform_violations == [], _format_violations(platform_violations)


def test_scanner_detects_forbidden_import(tmp_path: Path):
    bad = tmp_path / "platform_foo" / "bad.py"
    bad.parent.mkdir(parents=True)
    bad.write_text("from handlers import router\n", encoding="utf-8")
    violations = scan_legacy_import_violations(tmp_path)
    assert any(v.module == "handlers" for v in violations)


def test_migration_report_structure():
    from platform_legacy.migrations import migration_report

    report = migration_report()
    assert "summary" in report
    assert "subsystems" in report
    assert report["summary"]["platform_default"] is True


def test_legacy_metrics_snapshot():
    snapshot = legacy.metrics()
    assert "metrics" in snapshot
    assert "migration" in snapshot
    assert "adapters" in snapshot


def test_events_facade_exposes_legacy_classes():
    assert legacy.events.legacy_platform_event_class().__name__ == "PlatformEvent"
    assert legacy.events.legacy_event_bus_class().__name__ == "EventBus"


def _format_violations(violations) -> str:
    if not violations:
        return ""
    lines = ["Forbidden legacy imports outside platform_legacy:"]
    for v in violations:
        lines.append(f"  {v.path}:{v.line} imports {v.module}")
    return "\n".join(lines)
