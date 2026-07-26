"""Tests — Production Readiness & Launch Validation (Sprint 32.3.7)."""

from __future__ import annotations

from pathlib import Path

from applications.platform_builder import platform_builder


ROOT = Path(__file__).resolve().parents[1]

DOCS = [
    "PRODUCTION_READINESS_32_3_7.md",
    "RELEASE_NOTES_32_3_7.md",
]


def test_32_3_7_docs_exist():
    docs = ROOT / "docs"
    for name in DOCS:
        path = docs / name
        assert path.exists(), name
        assert "32.3.7" in path.read_text()
    index = (docs / "ARCHITECTURE_AUDIT_INDEX.md").read_text()
    assert "PRODUCTION_READINESS_32_3_7" in index
    report = (docs / "PRODUCTION_READINESS_32_3_7.md").read_text()
    assert "No new Engine" in report
    assert "92%" in report


def test_platform_version_32_3_7():
    health = platform_builder.health()
    assert health["application_version"] == "1.62.0"
    assert health["sprint"] == "33.6"
    assert "Enterprise Control Tower" in health["release_status"]


def test_launch_demo_routes_wired():
    app = (ROOT / "src" / "web" / "src" / "App.tsx").read_text()
    catalog = (ROOT / "src" / "web" / "src" / "launch" / "launchCatalog.ts").read_text()
    for token in (
        'path="/login"',
        'path="/onboarding/first-entry"',
        'path="/workspace"',
        'path="/dashboard"',
        'path="/platform-builder/mission-control"',
        'path="/enterprise-city"',
        'path="/platform-builder/ai-team"',
        'path="/settings"',
        'path="/auth/logout"',
    ):
        assert token in app
        assert token in catalog or token.replace('path="', "").replace('"', "") in catalog
    assert "EmptyState" in app
    assert "Страница не найдена" in app
    assert 'route: "/platform-builder/knowledge"' in (
        ROOT / "src" / "web" / "command-center" / "managers" / "quickActions.ts"
    ).read_text()
    assert "/platform-builder/knowledge" in (
        ROOT / "src" / "web" / "navigation" / "managers" / "searchIndex.ts"
    ).read_text()
    guard = (ROOT / "src" / "web" / "src" / "shell" / "PermissionGuard.tsx").read_text()
    assert "/auth/access-denied" in guard
    full = (ROOT / "src" / "web" / "src" / "layouts" / "FullLayout.tsx").read_text()
    assert "OfflineBanner" in full
    css = (ROOT / "src" / "web" / "src" / "index.css").read_text()
    assert "Sprint 32.3.7" in css
    assert "launch-offline" in css
    prod = (ROOT / "src" / "web" / "src" / "pages" / "ProductionReadinessPage.tsx").read_text()
    assert "LAUNCH_DEMO_STEPS" in prod


def test_config_manifest_32_3_7():
    cfg = (ROOT / "applications" / "platform_builder" / "config.py").read_text()
    assert 'application_version: str = "1.62.0"' in cfg
    assert 'sprint: str = "33.6"' in cfg
    manifest = (ROOT / "applications" / "platform_builder" / "manifest.json").read_text()
    assert '"application_version": "1.62.0"' in manifest
    assert '"sprint": "33.6"' in manifest
    web = (ROOT / "src" / "web" / "src" / "config" / "webConfig.ts").read_text()
    assert 'sprint: "33.6"' in web
    types = (ROOT / "src" / "web" / "platform-builder" / "types.ts").read_text()
    assert 'PLATFORM_BUILDER_VERSION = "1.62.0"' in types
    assert 'PLATFORM_BUILDER_SPRINT = "33.6"' in types
