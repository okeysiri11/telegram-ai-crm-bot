"""Tests — Enterprise Marketplace & Solution Hub (Sprint 32.9)."""

from __future__ import annotations

from pathlib import Path

from applications.platform_builder import platform_builder


ROOT = Path(__file__).resolve().parents[1]

DOCS = [
    "ENTERPRISE_MARKETPLACE_32_9.md",
    "RELEASE_NOTES_32_9.md",
]


def test_32_9_docs_exist():
    docs = ROOT / "docs"
    for name in DOCS:
        path = docs / name
        assert path.exists(), name
        assert "32.9" in path.read_text()
    index = (docs / "ARCHITECTURE_AUDIT_INDEX.md").read_text()
    assert "ENTERPRISE_MARKETPLACE_32_9" in index
    report = (docs / "ENTERPRISE_MARKETPLACE_32_9.md").read_text()
    assert "No new Marketplace Engine" in report or "No new Marketplace" in report
    assert "One-Click Install" in report


def test_platform_version_32_9():
    health = platform_builder.health()
    assert health["application_version"] == "1.55.0"
    assert health["sprint"] == "32.9"
    assert "Enterprise Marketplace" in health["release_status"]


def test_marketplace_wired():
    app = (ROOT / "src" / "web" / "src" / "App.tsx").read_text()
    assert 'path="/platform-builder/solution-hub"' in app
    assert "EnterpriseMarketplacePage" in app
    full = (ROOT / "src" / "web" / "src" / "layouts" / "FullLayout.tsx").read_text()
    assert "MarketplaceStrip" in full
    catalog = (ROOT / "src" / "web" / "src" / "enterprise-marketplace" / "solutionCatalog.ts").read_text()
    for token in (
        "Beauty Enterprise Pack",
        "Legal Enterprise Pack",
        "Cafe Enterprise Pack",
        "Agriculture Enterprise Pack",
        "Automotive Enterprise Pack",
        "Drone Enterprise Pack",
        "Bidex Enterprise Pack",
        "MARKETPLACE_CATEGORIES",
        "ai_teams",
        "prompt_packs",
    ):
        assert token in catalog
    install = (ROOT / "src" / "web" / "src" / "enterprise-marketplace" / "installState.ts").read_text()
    assert "installSolution" in install
    assert "checkCompatibility" in install
    page = (
        ROOT / "src" / "web" / "src" / "enterprise-marketplace" / "EnterpriseMarketplacePage.tsx"
    ).read_text()
    for token in (
        "One-Click Install",
        "Solution Preview",
        "Compatibility",
        "Installed Solutions",
        "Enterprise Hub",
    ):
        assert token in page
    css = (ROOT / "src" / "web" / "src" / "index.css").read_text()
    assert "Sprint 32.9" in css
    assert "mkt-hub" in css or "mkt-strip" in css
    qa = (ROOT / "src" / "web" / "command-center" / "managers" / "quickActions.ts").read_text()
    assert "/platform-builder/solution-hub" in qa


def test_config_manifest_32_9():
    cfg = (ROOT / "applications" / "platform_builder" / "config.py").read_text()
    assert 'application_version: str = "1.55.0"' in cfg
    assert 'sprint: str = "32.9"' in cfg
    assert "Enterprise Marketplace & Solution Hub" in cfg
    manifest = (ROOT / "applications" / "platform_builder" / "manifest.json").read_text()
    assert '"application_version": "1.55.0"' in manifest
    assert '"sprint": "32.9"' in manifest
    web = (ROOT / "src" / "web" / "src" / "config" / "webConfig.ts").read_text()
    assert 'sprint: "32.9"' in web
    types = (ROOT / "src" / "web" / "platform-builder" / "types.ts").read_text()
    assert 'PLATFORM_BUILDER_VERSION = "1.55.0"' in types
    assert 'PLATFORM_BUILDER_SPRINT = "32.9"' in types
