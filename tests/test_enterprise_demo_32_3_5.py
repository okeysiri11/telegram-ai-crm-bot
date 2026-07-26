"""Tests — Enterprise Demo Polish & Executive Experience (Sprint 32.3.5)."""

from __future__ import annotations

from pathlib import Path

from applications.platform_builder import platform_builder


ROOT = Path(__file__).resolve().parents[1]

DOCS = [
    "ENTERPRISE_DEMO_32_3_5.md",
    "RELEASE_NOTES_32_3_5.md",
]


def test_32_3_5_docs_exist():
    docs = ROOT / "docs"
    for name in DOCS:
        path = docs / name
        assert path.exists(), name
        assert "32.3.5" in path.read_text()
    index = (docs / "ARCHITECTURE_AUDIT_INDEX.md").read_text()
    assert "ENTERPRISE_DEMO_32_3_5" in index


def test_platform_version_32_3_5():
    health = platform_builder.health()
    assert health["application_version"] == "1.66.0"
    assert health["sprint"] == "34.0"
    assert "Release Candidate" in health["release_status"]


def test_executive_mode_and_demo_scenario():
    app = (ROOT / "src" / "web" / "src" / "App.tsx").read_text()
    assert 'path="/demo/scenario"' in app
    assert "DemoScenarioPage" in app
    exec_mode = (ROOT / "src" / "web" / "src" / "demo" / "executiveMode.ts").read_text()
    assert "EXECUTIVE_LAYOUT" in exec_mode
    assert "resolveExecutiveMode" in exec_mode
    dash = (ROOT / "src" / "web" / "src" / "pages" / "DashboardPage.tsx").read_text()
    assert "resolveExecutiveMode" in dash
    assert "Executive Mode" in dash
    assert "mode=executive" in dash or "setExecutive" in dash
    roles = (ROOT / "src" / "web" / "src" / "onboarding" / "firstEntryRoles.ts").read_text()
    assert 'id: "executive"' in roles
    ui = (ROOT / "src" / "web" / "src" / "ui" / "ExperienceStates.tsx").read_text()
    assert "Skeleton" in ui
    assert "SuccessState" in ui
    empty = (ROOT / "src" / "web" / "src" / "ui" / "EmptyState.tsx").read_text()
    assert "illustration" in empty
    nav = (ROOT / "src" / "web" / "src" / "navigation" / "TopNavigation.tsx").read_text()
    assert "/demo/scenario" in nav
    assert "mode=executive" in nav
    css = (ROOT / "src" / "web" / "src" / "index.css").read_text()
    assert "Sprint 32.3.5" in css
    assert "demo-scenario" in css
    shared = (ROOT / "src" / "web" / "src" / "ui" / "sharedUi.ts").read_text()
    assert "Skeleton" in shared
    steps = (ROOT / "src" / "web" / "src" / "demo" / "demoScenarioCatalog.ts").read_text()
    for token in ("first_entry", "dashboard", "mission_control", "city", "crm"):
        assert token in steps


def test_config_manifest_32_3_5():
    cfg = (ROOT / "applications" / "platform_builder" / "config.py").read_text()
    assert 'application_version: str = "1.66.0"' in cfg
    assert 'sprint: str = "34.0"' in cfg
    manifest = (ROOT / "applications" / "platform_builder" / "manifest.json").read_text()
    assert '"application_version": "1.66.0"' in manifest
    assert '"sprint": "34.0"' in manifest
    web = (ROOT / "src" / "web" / "src" / "config" / "webConfig.ts").read_text()
    assert 'sprint: "34.0"' in web
    types = (ROOT / "src" / "web" / "platform-builder" / "types.ts").read_text()
    assert 'PLATFORM_BUILDER_VERSION = "1.66.0"' in types
    assert 'PLATFORM_BUILDER_SPRINT = "34.0"' in types
