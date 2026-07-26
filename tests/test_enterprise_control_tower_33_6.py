"""Tests — Enterprise Control Tower (Sprint 33.6)."""

from __future__ import annotations

from pathlib import Path

from applications.platform_builder import platform_builder


ROOT = Path(__file__).resolve().parents[1]

DOCS = [
    "ENTERPRISE_CONTROL_TOWER_33_6.md",
    "RELEASE_NOTES_33_6.md",
]


def test_33_6_docs_exist():
    docs = ROOT / "docs"
    for name in DOCS:
        path = docs / name
        assert path.exists(), name
        assert "33.6" in path.read_text()
    index = (docs / "ARCHITECTURE_AUDIT_INDEX.md").read_text()
    assert "ENTERPRISE_CONTROL_TOWER_33_6" in index
    report = (docs / "ENTERPRISE_CONTROL_TOWER_33_6.md").read_text()
    assert "No new Dashboard Engine" in report
    assert "Operations Wall" in report
    assert "Executive Cockpit" in report


def test_platform_version_33_6():
    health = platform_builder.health()
    assert health["application_version"] == "1.66.0"
    assert health["sprint"] == "34.0"
    assert "Release Candidate" in health["release_status"]


def test_control_tower_wired():
    app = (ROOT / "src" / "web" / "src" / "App.tsx").read_text()
    assert 'path="/platform-builder/control-tower"' in app
    assert "EnterpriseControlTowerPage" in app
    full = (ROOT / "src" / "web" / "src" / "layouts" / "FullLayout.tsx").read_text()
    assert "ControlTowerStrip" in full
    derive = (ROOT / "src" / "web" / "src" / "enterprise-control-tower" / "deriveControlTower.ts").read_text()
    for token in (
        "deriveControlTower",
        "Beauty",
        "Legal",
        "Cafe",
        "Agriculture",
        "Automotive",
        "Drone",
        "Bidex",
        "CONTROL_TOWER_COMMANDS",
    ):
        assert token in derive
    page = (
        ROOT / "src" / "web" / "src" / "enterprise-control-tower" / "EnterpriseControlTowerPage.tsx"
    ).read_text()
    for token in (
        "Global Overview",
        "Operations Wall",
        "Executive Cockpit",
        "Cross Ecosystem Monitor",
        "Global Search",
        "Incident Center",
        "Command Actions",
        "RuntimeMonitorCompact",
        "AutonomousWidgetCompact",
    ):
        assert token in page
    css = (
        ROOT / "src" / "web" / "src" / "enterprise-control-tower" / "enterprise-control-tower.css"
    ).read_text()
    assert "Sprint 33.6" in css
    assert "ect-" in css
    idx = (ROOT / "src" / "web" / "src" / "index.css").read_text()
    assert "enterprise-control-tower.css" in idx
    search = (ROOT / "src" / "web" / "navigation" / "managers" / "searchIndex.ts").read_text()
    assert "idx_control_tower" in search
    assert "idx_ai_team" in search
    assert "idx_crm_clients" in search
    qa = (ROOT / "src" / "web" / "command-center" / "managers" / "quickActions.ts").read_text()
    assert "/platform-builder/control-tower" in qa
    mc = (
        ROOT / "src" / "web" / "platform-builder" / "mission-control" / "MissionControlLivePanel.tsx"
    ).read_text()
    assert "control-tower" in mc


def test_config_manifest_33_6():
    cfg = (ROOT / "applications" / "platform_builder" / "config.py").read_text()
    assert 'application_version: str = "1.66.0"' in cfg
    assert 'sprint: str = "34.0"' in cfg
    assert "Release Candidate" in cfg
    manifest = (ROOT / "applications" / "platform_builder" / "manifest.json").read_text()
    assert '"application_version": "1.66.0"' in manifest
    assert '"sprint": "34.0"' in manifest
    web = (ROOT / "src" / "web" / "src" / "config" / "webConfig.ts").read_text()
    assert 'sprint: "34.0"' in web
    types = (ROOT / "src" / "web" / "platform-builder" / "types.ts").read_text()
    assert 'PLATFORM_BUILDER_VERSION = "1.66.0"' in types
    assert 'PLATFORM_BUILDER_SPRINT = "34.0"' in types
