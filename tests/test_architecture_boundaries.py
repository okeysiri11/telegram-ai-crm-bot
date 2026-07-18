"""Architecture boundary tests — fail on layer violations."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.platform.layers.architecture_policy import (
    BoundaryViolation,
    scan_layer,
    scan_file,
)

ROOT = Path(__file__).resolve().parents[1]

# Legacy Telegram handlers with known DB/repository leaks — must not grow.
LEGACY_HANDLER_VIOLATIONS_ALLOWLIST: frozenset[str] = frozenset({
    "handler_no_database|auto_vertical_handlers.py|imports database layer",
    "handler_no_database|automotive_partner_handlers.py|imports database layer",
    "handler_no_database|dealer_onboarding_handlers.py|imports database layer",
    "handler_no_database|handlers.py|imports database layer",
})


def _keys(violations: list[BoundaryViolation]) -> set[str]:
    return {v.key() for v in violations}


def test_management_layer_has_no_boundary_violations():
    violations = scan_layer("management", ROOT)
    assert violations == [], _format_violations("management", violations)


def test_plugins_use_sdk_only():
    violations = scan_layer("plugins", ROOT)
    assert violations == [], _format_violations("plugins", violations)


def test_event_handlers_have_no_boundary_violations():
    violations: list[BoundaryViolation] = []
    handlers_dir = ROOT / "events" / "handlers"
    for path in handlers_dir.rglob("*.py"):
        if path.name == "__init__.py":
            continue
        violations.extend(scan_file(path, root=ROOT))
    assert violations == [], _format_violations("events/handlers", violations)


def test_legacy_handler_violations_do_not_increase():
    violations = scan_layer("handlers", ROOT)
    current = _keys(violations)
    unknown = current - LEGACY_HANDLER_VIOLATIONS_ALLOWLIST
    assert not unknown, (
        "New handler boundary violations detected (handlers must call services, not DB/repos):\n"
        + "\n".join(f"  + {item}" for item in sorted(unknown))
        + "\nFix the violation or update LEGACY_HANDLER_VIOLATIONS_ALLOWLIST only when migrating."
    )


def test_legacy_handler_allowlist_tracks_remaining_debt():
    violations = scan_layer("handlers", ROOT)
    current = _keys(violations)
    stale = LEGACY_HANDLER_VIOLATIONS_ALLOWLIST - current
    assert not stale, (
        "Remove fixed violations from LEGACY_HANDLER_VIOLATIONS_ALLOWLIST:\n"
        + "\n".join(f"  - {item}" for item in sorted(stale))
    )


def test_architecture_policy_detects_management_db_import(tmp_path: Path):
    bad = tmp_path / "platform_management" / "bad_module.py"
    bad.parent.mkdir(parents=True)
    bad.write_text("from database.session import get_session\n", encoding="utf-8")
    violations = scan_file(bad, root=tmp_path)
    assert any(v.rule == "management_no_database" for v in violations)


def test_architecture_policy_detects_plugin_repository_import(tmp_path: Path):
    bad = tmp_path / "plugins" / "demo" / "plugin.py"
    bad.parent.mkdir(parents=True)
    bad.write_text("from repositories.user_repository import UserRepository\n", encoding="utf-8")
    violations = scan_file(bad, root=tmp_path)
    assert any(v.rule == "plugin_no_repository" for v in violations)


def _format_violations(layer: str, violations: list[BoundaryViolation]) -> str:
    if not violations:
        return ""
    lines = [f"{layer} boundary violations:"]
    for v in violations:
        lines.append(f"  [{v.rule}] {v.path} — {v.detail}")
    return "\n".join(lines)
