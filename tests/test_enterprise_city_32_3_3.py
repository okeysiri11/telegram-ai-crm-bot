"""Tests — Enterprise City Navigation (Sprint 32.3.3)."""

from __future__ import annotations

from pathlib import Path

from applications.platform_builder import platform_builder


ROOT = Path(__file__).resolve().parents[1]

DOCS = [
    "ENTERPRISE_CITY_32_3_3.md",
    "RELEASE_NOTES_32_3_3.md",
]


def test_32_3_3_docs_exist():
    docs = ROOT / "docs"
    for name in DOCS:
        path = docs / name
        assert path.exists(), name
        assert "32.3.3" in path.read_text()
    index = (docs / "ARCHITECTURE_AUDIT_INDEX.md").read_text()
    assert "ENTERPRISE_CITY_32_3_3" in index


def test_platform_version_32_3_3():
    health = platform_builder.health()
    assert health["application_version"] == "1.58.0"
    assert health["sprint"] == "33.2"
    assert "AI Runtime & Orchestration Center" in health["release_status"]


def test_enterprise_city_page_and_catalog():
    app = (ROOT / "src" / "web" / "src" / "App.tsx").read_text()
    assert 'path="/enterprise-city"' in app
    assert "EnterpriseCityPage" in app
    page = (ROOT / "src" / "web" / "src" / "enterprise-city" / "EnterpriseCityPage.tsx").read_text()
    assert "searchProvider" in page
    assert "searchIndex" in page
    assert "CityMinimap" in page or "ec-minimap" in page
    assert "navigate(b.route)" in page
    catalog = (ROOT / "src" / "web" / "src" / "enterprise-city" / "cityCatalog.ts").read_text()
    for token in ("CRM Center", "Analytics Center", "AI Team Center", "Knowledge Center", "Finance", "HR"):
        assert token in catalog
    assert "/workspace/crm" in catalog
    assert "/platform-builder/ai-team" in catalog
    assert "/dashboard" in catalog
    css = (ROOT / "src" / "web" / "src" / "index.css").read_text()
    assert "enterprise-city" in css
    assert "Sprint 32.3.3" in css
    # Does not replace dashboard
    dash = (ROOT / "src" / "web" / "src" / "pages" / "DashboardPage.tsx").read_text()
    assert "Enterprise Command Center" in dash
    cc = (ROOT / "src" / "web" / "src" / "dashboard" / "commandCenterCatalog.ts").read_text()
    assert 'route: "/enterprise-city"' in cc


def test_config_manifest_32_3_3():
    cfg = (ROOT / "applications" / "platform_builder" / "config.py").read_text()
    assert 'application_version: str = "1.58.0"' in cfg
    assert 'sprint: str = "33.2"' in cfg
    manifest = (ROOT / "applications" / "platform_builder" / "manifest.json").read_text()
    assert '"application_version": "1.58.0"' in manifest
    assert '"sprint": "33.2"' in manifest
    web = (ROOT / "src" / "web" / "src" / "config" / "webConfig.ts").read_text()
    assert 'sprint: "33.2"' in web
    types = (ROOT / "src" / "web" / "platform-builder" / "types.ts").read_text()
    assert 'PLATFORM_BUILDER_VERSION = "1.58.0"' in types
    assert 'PLATFORM_BUILDER_SPRINT = "33.2"' in types
