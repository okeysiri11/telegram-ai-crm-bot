"""Tests — Enterprise Digital Twin (Sprint 33.0)."""

from __future__ import annotations

from pathlib import Path

from applications.platform_builder import platform_builder


ROOT = Path(__file__).resolve().parents[1]

DOCS = [
    "ENTERPRISE_DIGITAL_TWIN_33_0.md",
    "RELEASE_NOTES_33_0.md",
]


def test_33_0_docs_exist():
    docs = ROOT / "docs"
    for name in DOCS:
        path = docs / name
        assert path.exists(), name
        assert "33.0" in path.read_text()
    index = (docs / "ARCHITECTURE_AUDIT_INDEX.md").read_text()
    assert "ENTERPRISE_DIGITAL_TWIN_33_0" in index
    report = (docs / "ENTERPRISE_DIGITAL_TWIN_33_0.md").read_text()
    assert "No new AI Core" in report
    assert "Organization Map" in report
    assert "Decision Impact" in report


def test_platform_version_33_0():
    health = platform_builder.health()
    assert health["application_version"] == "1.57.0"
    assert health["sprint"] == "33.1"
    assert "Enterprise Integration Hub" in health["release_status"]


def test_enterprise_twin_wired():
    app = (ROOT / "src" / "web" / "src" / "App.tsx").read_text()
    assert 'path="/enterprise-twin"' in app
    assert "EnterpriseTwinPage" in app
    full = (ROOT / "src" / "web" / "src" / "layouts" / "FullLayout.tsx").read_text()
    assert "EnterpriseTwinStrip" in full
    derive = (ROOT / "src" / "web" / "src" / "enterprise-twin" / "deriveTwin.ts").read_text()
    for token in (
        "deriveEnterpriseTwin",
        "Organization",
        "RELATIONSHIP_CHAIN",
        "heatmap",
        "DecisionImpact",
        "timeline",
        "executive",
        "useLiveEnterprise",
    ):
        assert token in derive or token in (
            ROOT / "src" / "web" / "src" / "enterprise-twin" / "EnterpriseTwinPage.tsx"
        ).read_text()
    page = (ROOT / "src" / "web" / "src" / "enterprise-twin" / "EnterpriseTwinPage.tsx").read_text()
    for token in (
        "Executive View",
        "Organization Map",
        "Relationship Graph",
        "Enterprise Heatmap",
        "Decision Impact",
        "Enterprise Timeline",
    ):
        assert token in page
    css = (ROOT / "src" / "web" / "src" / "enterprise-twin" / "enterprise-twin.css").read_text()
    assert "Sprint 33.0" in css
    assert "etwin-" in css
    idx = (ROOT / "src" / "web" / "src" / "index.css").read_text()
    assert "enterprise-twin.css" in idx
    qa = (ROOT / "src" / "web" / "command-center" / "managers" / "quickActions.ts").read_text()
    assert "/enterprise-twin" in qa
    hub = (ROOT / "src" / "web" / "platform-builder" / "pages" / "DigitalTwinPage.tsx").read_text()
    assert "EnterpriseTwinPage" in hub


def test_config_manifest_33_0():
    cfg = (ROOT / "applications" / "platform_builder" / "config.py").read_text()
    assert 'application_version: str = "1.57.0"' in cfg
    assert 'sprint: str = "33.1"' in cfg
    assert "Enterprise Integration Hub" in cfg
    manifest = (ROOT / "applications" / "platform_builder" / "manifest.json").read_text()
    assert '"application_version": "1.57.0"' in manifest
    assert '"sprint": "33.1"' in manifest
    web = (ROOT / "src" / "web" / "src" / "config" / "webConfig.ts").read_text()
    assert 'sprint: "33.1"' in web
    types = (ROOT / "src" / "web" / "platform-builder" / "types.ts").read_text()
    assert 'PLATFORM_BUILDER_VERSION = "1.57.0"' in types
    assert 'PLATFORM_BUILDER_SPRINT = "33.1"' in types
