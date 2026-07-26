"""Tests — Enterprise Strategy & OKR Intelligence (Sprint 33.8)."""

from __future__ import annotations

from pathlib import Path

from applications.platform_builder import platform_builder


ROOT = Path(__file__).resolve().parents[1]

DOCS = [
    "ENTERPRISE_STRATEGY_OKR_33_8.md",
    "RELEASE_NOTES_33_8.md",
]


def test_33_8_docs_exist():
    docs = ROOT / "docs"
    for name in DOCS:
        path = docs / name
        assert path.exists(), name
        assert "33.8" in path.read_text()
    index = (docs / "ARCHITECTURE_AUDIT_INDEX.md").read_text()
    assert "ENTERPRISE_STRATEGY_OKR_33_8" in index
    report = (docs / "ENTERPRISE_STRATEGY_OKR_33_8.md").read_text()
    assert "No new Strategy Engine" in report
    assert "Enterprise Goals" in report
    assert "OKR Dashboard" in report
    assert "Scenario Impact" in report


def test_platform_version_33_8():
    health = platform_builder.health()
    assert health["application_version"] == "1.65.0"
    assert health["sprint"] == "33.9"
    assert "Governance" in health["release_status"]


def test_okr_wired():
    app = (ROOT / "src" / "web" / "src" / "App.tsx").read_text()
    assert 'path="/platform-builder/okr"' in app
    assert "EnterpriseOkrPage" in app
    full = (ROOT / "src" / "web" / "src" / "layouts" / "FullLayout.tsx").read_text()
    assert "OkrStrip" in full
    derive = (ROOT / "src" / "web" / "src" / "enterprise-okr" / "deriveOkr.ts").read_text()
    for token in (
        "deriveOkr",
        "alignRecommendation",
        "ENTERPRISE_GOALS",
        "scenarioImpacts",
        "ExecutiveHorizon",
        "deriveLearning",
        "derivePredictive",
        "deriveIntelligence",
    ):
        assert token in derive
    catalog = (ROOT / "src" / "web" / "src" / "enterprise-okr" / "goalsCatalog.ts").read_text()
    for token in (
        "revenue",
        "profit",
        "sales",
        "marketing",
        "production",
        "customer_success",
        "hr",
        "operations",
    ):
        assert token in catalog
    page = (ROOT / "src" / "web" / "src" / "enterprise-okr" / "EnterpriseOkrPage.tsx").read_text()
    for token in (
        "Enterprise Goals",
        "OKR Dashboard",
        "AI Goal Alignment",
        "Executive Cockpit",
        "Scenario Impact",
        "Strategy Timeline",
        "EnterpriseGoalsWidgetCompact",
    ):
        assert token in page
    css = (ROOT / "src" / "web" / "src" / "enterprise-okr" / "enterprise-okr.css").read_text()
    assert "Sprint 33.8" in css
    assert "okr-" in css
    idx = (ROOT / "src" / "web" / "src" / "index.css").read_text()
    assert "enterprise-okr.css" in idx
    search = (ROOT / "src" / "web" / "navigation" / "managers" / "searchIndex.ts").read_text()
    assert "idx_okr" in search
    qa = (ROOT / "src" / "web" / "command-center" / "managers" / "quickActions.ts").read_text()
    assert "/platform-builder/okr" in qa
    mc = (
        ROOT / "src" / "web" / "platform-builder" / "mission-control" / "MissionControlLivePanel.tsx"
    ).read_text()
    assert "EnterpriseGoalsWidgetCompact" in mc
    panels = (ROOT / "src" / "web" / "src" / "live-ops" / "LivePanels.tsx").read_text()
    assert "alignRecommendation" in panels
    # Existing Strategy Engine route preserved
    assert 'path="/platform-builder/strategy"' in app


def test_config_manifest_33_8():
    cfg = (ROOT / "applications" / "platform_builder" / "config.py").read_text()
    assert 'application_version: str = "1.65.0"' in cfg
    assert 'sprint: str = "33.9"' in cfg
    assert "Governance" in cfg
    manifest = (ROOT / "applications" / "platform_builder" / "manifest.json").read_text()
    assert '"application_version": "1.65.0"' in manifest
    assert '"sprint": "33.9"' in manifest
    web = (ROOT / "src" / "web" / "src" / "config" / "webConfig.ts").read_text()
    assert 'sprint: "33.9"' in web
    types = (ROOT / "src" / "web" / "platform-builder" / "types.ts").read_text()
    assert 'PLATFORM_BUILDER_VERSION = "1.65.0"' in types
    assert 'PLATFORM_BUILDER_SPRINT = "33.9"' in types
