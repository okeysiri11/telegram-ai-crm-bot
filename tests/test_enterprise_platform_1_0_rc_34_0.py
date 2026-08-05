"""Tests — Enterprise Platform v1.0 Release Candidate (Sprint 34.0)."""

from __future__ import annotations

from pathlib import Path

from applications.platform_builder import platform_builder


ROOT = Path(__file__).resolve().parents[1]

DOCS = [
    "ENTERPRISE_PLATFORM_1_0.md",
    "ARCHITECTURE_AUDIT_34_0.md",
    "EXECUTIVE_DEMO_34_0.md",
    "RELEASE_NOTES_34_0.md",
    "KNOWN_LIMITATIONS_1_0.md",
    "ROADMAP_2_0.md",
]


def test_34_0_docs_exist():
    docs = ROOT / "docs"
    for name in DOCS:
        path = docs / name
        assert path.exists(), name
        text = path.read_text()
        assert "34.0" in text or "1.0" in text
    index = (docs / "ARCHITECTURE_AUDIT_INDEX.md").read_text()
    assert "ENTERPRISE_PLATFORM_1_0" in index
    platform = (docs / "ENTERPRISE_PLATFORM_1_0.md").read_text()
    assert "General Availability" in platform or "Release Candidate" in platform
    assert "No new Engine" in platform or "Без новых Engine" in platform
    assert (docs / "ENTERPRISE_PLATFORM_V1_GA.md").exists()
    assert (docs / "GA_READINESS_REPORT.md").exists()
    assert (docs / "FINAL_EQI_REPORT.md").exists()
    assert (docs / "PILOT_CHECKLIST.md").exists()
    assert "READY FOR GENERAL AVAILABILITY" in (docs / "GA_READINESS_REPORT.md").read_text()
    demo = (docs / "EXECUTIVE_DEMO_34_0.md").read_text()
    for route in (
        "/login",
        "/dashboard",
        "/platform-builder/mission-control",
        "/enterprise-city",
        "/platform-builder/governance",
        "/platform-builder/control-tower",
    ):
        assert route in demo


def test_platform_version_34_0():
    health = platform_builder.health()
    assert health["application_version"] == "1.67.0"
    assert health["sprint"] == "1.1.1"
    assert "General Availability" in health["release_status"]


def test_34_0_rc_stabilizations():
    app = (ROOT / "src" / "web" / "src" / "App.tsx").read_text()
    assert "lazy(" in app
    assert "Suspense" in app
    assert "LoadingScreen" in app
    full = (ROOT / "src" / "web" / "src" / "layouts" / "FullLayout.tsx").read_text()
    assert "eds-ops-chrome" in full or "opsOpen" in full
    assert "ControlTowerStrip" in full
    assert "GovernanceStrip" in full
    assert "Show platform strips" in full
    menu = (ROOT / "src" / "web" / "navigation" / "managers" / "menuEngine.ts").read_text()
    assert "/platform-builder/workflow-center" in menu
    assert "/enterprise-city" in menu
    assert "/platform-builder/builder-studio" in menu
    search = (ROOT / "src" / "web" / "navigation" / "managers" / "searchIndex.ts").read_text()
    assert "idx_mission_control" in search
    assert "idx_enterprise_city" in search
    assert 'path="/dashboard"' in search or 'path: "/dashboard"' in search
    registry = (ROOT / "src" / "web" / "platform-builder" / "managers" / "builderRegistry.ts").read_text()
    assert "workflow_center" in registry
    assert "enterprise_city" in registry
    # No new Engine packages invented in 34.0
    gov = ROOT / "src" / "web" / "src" / "enterprise-governance"
    assert gov.exists()
    # Demo route still present
    assert 'path="/platform-builder/control-tower"' in app
    assert 'path="/platform-builder/governance"' in app


def test_config_manifest_34_0():
    cfg = (ROOT / "applications" / "platform_builder" / "config.py").read_text()
    assert 'application_version: str = "1.67.0"' in cfg
    assert 'sprint: str = "1.1.1"' in cfg
    assert "General Availability" in cfg
    manifest = (ROOT / "applications" / "platform_builder" / "manifest.json").read_text()
    assert '"application_version": "1.67.0"' in manifest
    assert '"sprint": "1.1.1"' in manifest
    web = (ROOT / "src" / "web" / "src" / "config" / "webConfig.ts").read_text()
    assert 'sprint: "1.1.1"' in web
    types = (ROOT / "src" / "web" / "platform-builder" / "types.ts").read_text()
    assert 'PLATFORM_BUILDER_VERSION = "1.67.0"' in types
    assert 'PLATFORM_BUILDER_SPRINT = "1.1.1"' in types
