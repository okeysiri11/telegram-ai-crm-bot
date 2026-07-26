"""Tests — Enterprise Dashboard & Mission Control (Sprint 32.3.2)."""

from __future__ import annotations

from pathlib import Path

from applications.platform_builder import platform_builder


ROOT = Path(__file__).resolve().parents[1]

DOCS = [
    "ENTERPRISE_COMMAND_CENTER_32_3_2.md",
    "RELEASE_NOTES_32_3_2.md",
]


def test_32_3_2_docs_exist():
    docs = ROOT / "docs"
    for name in DOCS:
        path = docs / name
        assert path.exists(), name
        assert "32.3.2" in path.read_text()
    index = (docs / "ARCHITECTURE_AUDIT_INDEX.md").read_text()
    assert "ENTERPRISE_COMMAND_CENTER_32_3_2" in index


def test_platform_version_32_3_2():
    health = platform_builder.health()
    assert health["application_version"] == "1.46.0"
    assert health["sprint"] == "32.3.4"
    assert "Live Enterprise" in health["release_status"]


def test_command_center_dashboard_reuses_existing():
    page = (ROOT / "src" / "web" / "src" / "pages" / "DashboardPage.tsx").read_text()
    assert "Enterprise Command Center" in page
    assert "MissionControlStrip" in page
    assert "commandCenterCatalog" in page
    assert "personalizationEngine" in page
    assert "widgetManager" in page
    assert "NotificationsPanel" in page
    assert "searchProvider" in page
    for section in (
        "Mission Control",
        "Today",
        "Business KPI",
        "Quick Actions",
        "AI Operations",
        "Business Modules",
        "Personal Dashboard",
    ):
        assert section in page
    catalog = (ROOT / "src" / "web" / "src" / "dashboard" / "commandCenterCatalog.ts").read_text()
    assert "ewp_command_center_layout_v2" in catalog or "ewp_command_center_layout_v1" in catalog
    assert "QUICK_ACTIONS" in catalog
    assert "BUSINESS_MODULES" in catalog
    strip = (ROOT / "src" / "web" / "src" / "dashboard" / "MissionControlStrip.tsx").read_text()
    assert "mission-control/status" in strip
    assert "/platform-builder/mission-control" in strip
    css = (ROOT / "src" / "web" / "src" / "index.css").read_text()
    assert "command-center" in css
    assert "Sprint 32.3.2" in css


def test_config_manifest_32_3_2():
    cfg = (ROOT / "applications" / "platform_builder" / "config.py").read_text()
    assert 'application_version: str = "1.46.0"' in cfg
    assert 'sprint: str = "32.3.4"' in cfg
    manifest = (ROOT / "applications" / "platform_builder" / "manifest.json").read_text()
    assert '"application_version": "1.46.0"' in manifest
    assert '"sprint": "32.3.4"' in manifest
    web = (ROOT / "src" / "web" / "src" / "config" / "webConfig.ts").read_text()
    assert 'sprint: "32.3.4"' in web
    types = (ROOT / "src" / "web" / "platform-builder" / "types.ts").read_text()
    assert 'PLATFORM_BUILDER_VERSION = "1.46.0"' in types
    assert 'PLATFORM_BUILDER_SPRINT = "32.3.4"' in types
