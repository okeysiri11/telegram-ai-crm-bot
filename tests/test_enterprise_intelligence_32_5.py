"""Tests — Enterprise Intelligence Layer (Sprint 32.5)."""

from __future__ import annotations

from pathlib import Path

from applications.platform_builder import platform_builder


ROOT = Path(__file__).resolve().parents[1]

DOCS = [
    "ENTERPRISE_INTELLIGENCE_32_5.md",
    "RELEASE_NOTES_32_5.md",
]


def test_32_5_docs_exist():
    docs = ROOT / "docs"
    for name in DOCS:
        path = docs / name
        assert path.exists(), name
        assert "32.5" in path.read_text()
    index = (docs / "ARCHITECTURE_AUDIT_INDEX.md").read_text()
    assert "ENTERPRISE_INTELLIGENCE_32_5" in index
    report = (docs / "ENTERPRISE_INTELLIGENCE_32_5.md").read_text()
    assert "No new Engine" in report
    assert "Daily Brief" in report
    assert "deriveIntelligence" in report or "live-ops" in report


def test_platform_version_32_5():
    health = platform_builder.health()
    assert health["application_version"] == "1.67.0"
    assert health["sprint"] == "1.1.1"
    assert health["release_status"] == "Enterprise Platform v1.1 General Availability"


def test_enterprise_intelligence_wired():
    full = (ROOT / "src" / "web" / "src" / "layouts" / "FullLayout.tsx").read_text()
    assert "EnterpriseIntelligenceLayer" in full
    assert "AiOsExperienceChrome" in full
    dash = (ROOT / "src" / "web" / "src" / "pages" / "DashboardPage.tsx").read_text()
    assert "EnterpriseIntelligenceDashboard" in dash
    derive = (ROOT / "src" / "web" / "src" / "enterprise-intelligence" / "deriveIntelligence.ts").read_text()
    for token in (
        "deriveIntelligence",
        "deriveDailyBrief",
        "derivePriorities",
        "deriveCrossModule",
        "CRM → Finance",
        "Knowledge",
        "knowledgeSignal",
    ):
        assert token in derive
    panels = (
        ROOT / "src" / "web" / "src" / "enterprise-intelligence" / "EnterpriseIntelligencePanels.tsx"
    ).read_text()
    for token in (
        "Enterprise Insights",
        "Daily Brief",
        "Smart Priorities",
        "Cross-Module Intelligence",
        "Executive Decision Panel",
        "useLiveEnterprise",
    ):
        assert token in panels
    suggestions = (ROOT / "src" / "web" / "src" / "ai-os-chrome" / "smartSuggestions.ts").read_text()
    assert "kb_aware" in suggestions
    assert "knowledgeAwareFromSnapshot" in suggestions
    css = (ROOT / "src" / "web" / "src" / "index.css").read_text()
    assert "Sprint 32.5" in css
    assert "ei-layer" in css
    assert "ei-decision" in css


def test_config_manifest_32_5():
    cfg = (ROOT / "applications" / "platform_builder" / "config.py").read_text()
    assert 'application_version: str = "1.67.0"' in cfg
    assert 'sprint: str = "1.1.1"' in cfg
    assert "General Availability" in cfg
    manifest = (ROOT / "applications" / "platform_builder" / "manifest.json").read_text()
    assert '"application_version": "1.67.0"' in manifest
    assert '"sprint": "1.1.1"' in manifest
    assert "General Availability" in manifest
    web = (ROOT / "src" / "web" / "src" / "config" / "webConfig.ts").read_text()
    assert 'sprint: "1.1.1"' in web
    types = (ROOT / "src" / "web" / "platform-builder" / "types.ts").read_text()
    assert 'PLATFORM_BUILDER_VERSION = "1.67.0"' in types
    assert 'PLATFORM_BUILDER_SPRINT = "1.1.1"' in types
