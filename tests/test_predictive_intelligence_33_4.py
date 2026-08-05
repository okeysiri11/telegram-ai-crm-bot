"""Tests — Predictive Intelligence & Scenario Simulator (Sprint 33.4)."""

from __future__ import annotations

from pathlib import Path

from applications.platform_builder import platform_builder


ROOT = Path(__file__).resolve().parents[1]

DOCS = [
    "PREDICTIVE_INTELLIGENCE_33_4.md",
    "RELEASE_NOTES_33_4.md",
]


def test_33_4_docs_exist():
    docs = ROOT / "docs"
    for name in DOCS:
        path = docs / name
        assert path.exists(), name
        assert "33.4" in path.read_text()
    index = (docs / "ARCHITECTURE_AUDIT_INDEX.md").read_text()
    assert "PREDICTIVE_INTELLIGENCE_33_4" in index
    report = (docs / "PREDICTIVE_INTELLIGENCE_33_4.md").read_text()
    assert "No new Prediction Engine" in report
    assert "Scenario Simulator" in report
    assert "What If" in report


def test_platform_version_33_4():
    health = platform_builder.health()
    assert health["application_version"] == "1.67.0"
    assert health["sprint"] == "1.1.1"
    assert "General Availability" in health["release_status"]


def test_predictive_wired():
    app = (ROOT / "src" / "web" / "src" / "App.tsx").read_text()
    assert 'path="/platform-builder/predictive"' in app
    assert "PredictiveIntelligencePage" in app
    full = (ROOT / "src" / "web" / "src" / "layouts" / "FullLayout.tsx").read_text()
    assert "PredictiveStrip" in full
    derive = (ROOT / "src" / "web" / "src" / "predictive-intelligence" / "derivePredictive.ts").read_text()
    for token in (
        "derivePredictive",
        "WHAT_IF_SCENARIOS",
        "grow_sales",
        "change_workflow",
        "disable_integration",
        "RiskSignal",
        "OpportunitySignal",
        "twinZones",
    ):
        assert token in derive
    page = (
        ROOT / "src" / "web" / "src" / "predictive-intelligence" / "PredictiveIntelligencePage.tsx"
    ).read_text()
    for token in (
        "Predictive Dashboard",
        "Scenario Simulator",
        "Risk Detection",
        "Opportunity Detection",
        "Executive Forecast",
        "PredictiveWidgetCompact",
    ):
        assert token in page
    css = (
        ROOT / "src" / "web" / "src" / "predictive-intelligence" / "predictive-intelligence.css"
    ).read_text()
    assert "Sprint 33.4" in css
    assert "pred-" in css
    idx = (ROOT / "src" / "web" / "src" / "index.css").read_text()
    assert "predictive-intelligence.css" in idx
    mc = (
        ROOT / "src" / "web" / "platform-builder" / "mission-control" / "MissionControlLivePanel.tsx"
    ).read_text()
    assert "PredictiveWidgetCompact" in mc
    twin = (ROOT / "src" / "web" / "src" / "enterprise-twin" / "EnterpriseTwinPage.tsx").read_text()
    assert "derivePredictive" in twin
    assert "Predictive Zones" in twin
    qa = (ROOT / "src" / "web" / "command-center" / "managers" / "quickActions.ts").read_text()
    assert "/platform-builder/predictive" in qa


def test_config_manifest_33_4():
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
