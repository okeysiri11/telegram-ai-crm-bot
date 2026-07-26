"""Tests — First User Experience / Platform Entry (Sprint 32.3.1)."""

from __future__ import annotations

from pathlib import Path

from applications.platform_builder import platform_builder


ROOT = Path(__file__).resolve().parents[1]

DOCS = [
    "FIRST_ENTRY_32_3_1.md",
    "RELEASE_NOTES_32_3_1.md",
]


def test_32_3_1_docs_exist():
    docs = ROOT / "docs"
    for name in DOCS:
        path = docs / name
        assert path.exists(), name
        assert "32.3.1" in path.read_text()


def test_platform_version_32_3_1():
    health = platform_builder.health()
    assert health["application_version"] == "1.43.0"
    assert health["sprint"] == "32.3.1"
    assert "First User Experience" in health["release_status"]


def test_first_entry_page_and_route():
    app_tsx = (ROOT / "src" / "web" / "src" / "App.tsx").read_text()
    assert 'path="/onboarding/first-entry"' in app_tsx
    assert "FirstEntryPage" in app_tsx
    page = (ROOT / "src" / "web" / "src" / "onboarding" / "FirstEntryPage.tsx").read_text()
    for token in ("welcome", "role", "workspace", "ai_team", "concierge", "dashboard"):
        assert token in page
    assert "hubIntegrations.tenancy" in page
    assert "platform-builder/ai-team" in page
    assert "platform-builder/concierge" in page
    roles = (ROOT / "src" / "web" / "src" / "onboarding" / "firstEntryRoles.ts").read_text()
    assert "register" in roles
    assert "beauty_salon" in roles
    login = (ROOT / "src" / "web" / "auth" / "pages" / "LoginPage.tsx").read_text()
    assert "isFirstEntryComplete" in login
    assert "/onboarding/first-entry" in login
    settings = (ROOT / "src" / "web" / "src" / "pages" / "SettingsPage.tsx").read_text()
    assert "Personalization (scaffold)" in settings


def test_config_manifest_32_3_1():
    cfg = (ROOT / "applications" / "platform_builder" / "config.py").read_text()
    assert 'application_version: str = "1.43.0"' in cfg
    assert 'sprint: str = "32.3.1"' in cfg
    manifest = (ROOT / "applications" / "platform_builder" / "manifest.json").read_text()
    assert '"application_version": "1.43.0"' in manifest
    assert '"sprint": "32.3.1"' in manifest
