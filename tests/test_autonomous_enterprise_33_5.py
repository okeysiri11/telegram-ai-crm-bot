"""Tests — Autonomous Enterprise & Human-in-the-Loop (Sprint 33.5)."""

from __future__ import annotations

from pathlib import Path

from applications.platform_builder import platform_builder


ROOT = Path(__file__).resolve().parents[1]

DOCS = [
    "AUTONOMOUS_ENTERPRISE_33_5.md",
    "RELEASE_NOTES_33_5.md",
]


def test_33_5_docs_exist():
    docs = ROOT / "docs"
    for name in DOCS:
        path = docs / name
        assert path.exists(), name
        assert "33.5" in path.read_text()
    index = (docs / "ARCHITECTURE_AUDIT_INDEX.md").read_text()
    assert "AUTONOMOUS_ENTERPRISE_33_5" in index
    report = (docs / "AUTONOMOUS_ENTERPRISE_33_5.md").read_text()
    assert "No new AI Core" in report
    assert "Approval Center" in report
    assert "Human-in-the-Loop" in report or "Human-in-the-loop" in report


def test_platform_version_33_5():
    health = platform_builder.health()
    assert health["application_version"] == "1.64.0"
    assert health["sprint"] == "33.8"
    assert "OKR Intelligence" in health["release_status"]


def test_autonomy_wired():
    app = (ROOT / "src" / "web" / "src" / "App.tsx").read_text()
    assert 'path="/platform-builder/autonomy"' in app
    assert "AutonomousEnterprisePage" in app
    full = (ROOT / "src" / "web" / "src" / "layouts" / "FullLayout.tsx").read_text()
    assert "AutonomyStrip" in full
    catalog = (ROOT / "src" / "web" / "src" / "autonomous-enterprise" / "autonomyCatalog.ts").read_text()
    for token in (
        "Manual Only",
        "AI Suggests",
        "AI Executes Low Risk",
        "AI Executes + Approval For Critical",
        "Enterprise Autonomous",
        "CRITICAL_ACTIONS",
    ):
        assert token in catalog
    page = (
        ROOT / "src" / "web" / "src" / "autonomous-enterprise" / "AutonomousEnterprisePage.tsx"
    ).read_text()
    for token in (
        "Autonomy Center",
        "Approval Center",
        "Autonomy Levels",
        "Decision Journal",
        "Executive Governance",
        "Approve",
        "Reject",
        "Edit",
        "AutonomousWidgetCompact",
    ):
        assert token in page
    css = (
        ROOT / "src" / "web" / "src" / "autonomous-enterprise" / "autonomous-enterprise.css"
    ).read_text()
    assert "Sprint 33.5" in css
    assert "auto-" in css
    idx = (ROOT / "src" / "web" / "src" / "index.css").read_text()
    assert "autonomous-enterprise.css" in idx
    mc = (
        ROOT / "src" / "web" / "platform-builder" / "mission-control" / "MissionControlLivePanel.tsx"
    ).read_text()
    assert "AutonomousWidgetCompact" in mc
    twin = (ROOT / "src" / "web" / "src" / "enterprise-twin" / "EnterpriseTwinPage.tsx").read_text()
    assert "deriveAutonomy" in twin
    qa = (ROOT / "src" / "web" / "command-center" / "managers" / "quickActions.ts").read_text()
    assert "/platform-builder/autonomy" in qa


def test_config_manifest_33_5():
    cfg = (ROOT / "applications" / "platform_builder" / "config.py").read_text()
    assert 'application_version: str = "1.64.0"' in cfg
    assert 'sprint: str = "33.8"' in cfg
    assert "OKR Intelligence" in cfg
    manifest = (ROOT / "applications" / "platform_builder" / "manifest.json").read_text()
    assert '"application_version": "1.64.0"' in manifest
    assert '"sprint": "33.8"' in manifest
    web = (ROOT / "src" / "web" / "src" / "config" / "webConfig.ts").read_text()
    assert 'sprint: "33.8"' in web
    types = (ROOT / "src" / "web" / "platform-builder" / "types.ts").read_text()
    assert 'PLATFORM_BUILDER_VERSION = "1.64.0"' in types
    assert 'PLATFORM_BUILDER_SPRINT = "33.8"' in types
