"""Tests — AI Builder Studio (Sprint 32.8)."""

from __future__ import annotations

from pathlib import Path

from applications.platform_builder import platform_builder


ROOT = Path(__file__).resolve().parents[1]

DOCS = [
    "AI_BUILDER_STUDIO_32_8.md",
    "RELEASE_NOTES_32_8.md",
]


def test_32_8_docs_exist():
    docs = ROOT / "docs"
    for name in DOCS:
        path = docs / name
        assert path.exists(), name
        assert "32.8" in path.read_text()
    index = (docs / "ARCHITECTURE_AUDIT_INDEX.md").read_text()
    assert "AI_BUILDER_STUDIO_32_8" in index
    report = (docs / "AI_BUILDER_STUDIO_32_8.md").read_text()
    assert "No new Builder Engine" in report or "No new Builder" in report
    assert "Builder Home" in report or "Builder Dashboard" in report


def test_platform_version_32_8():
    health = platform_builder.health()
    assert health["application_version"] == "1.54.0"
    assert health["sprint"] == "32.8"
    assert health["release_status"] == "AI Builder Studio"


def test_ai_builder_studio_wired():
    app = (ROOT / "src" / "web" / "src" / "App.tsx").read_text()
    assert 'path="/platform-builder/builder-studio"' in app
    assert "AIBuilderStudioPage" in app
    full = (ROOT / "src" / "web" / "src" / "layouts" / "FullLayout.tsx").read_text()
    assert "AIBuilderStudioStrip" in full
    page = (ROOT / "src" / "web" / "platform-builder" / "pages" / "AIBuilderPage.tsx").read_text()
    assert "AIBuilderStudioPage" in page
    catalog = (ROOT / "src" / "web" / "src" / "ai-builder-studio" / "studioCatalog.ts").read_text()
    for token in (
        "STUDIO_HOME_CARDS",
        "DOMAIN_SKILL_PACKS",
        "PROMPT_LIBRARY",
        "ECOSYSTEM_TEMPLATES",
        "Beauty",
        "Bidex",
        "studioCatalogStats",
    ):
        assert token in catalog
    studio = (ROOT / "src" / "web" / "src" / "ai-builder-studio" / "AIBuilderStudioPage.tsx").read_text()
    for token in (
        "Builder Dashboard",
        "Визуальный редактор",
        "Skill Library",
        "Prompt Library",
        "Ecosystem Templates",
        "edit_agent",
        "BUSINESS_WORKFLOW_TEMPLATES",
        "AIBuilderWizard",
    ):
        assert token in studio
    wizard = (ROOT / "src" / "web" / "platform-builder" / "ai-builder" / "AIBuilderWizard.tsx").read_text()
    assert "embedded" in wizard
    css = (ROOT / "src" / "web" / "src" / "index.css").read_text()
    assert "Sprint 32.8" in css
    assert "abs-studio" in css or "abs-strip" in css
    qa = (ROOT / "src" / "web" / "command-center" / "managers" / "quickActions.ts").read_text()
    assert "act_open_builder_studio" in qa
    reg = (ROOT / "src" / "web" / "platform-builder" / "managers" / "builderRegistry.ts").read_text()
    assert "builder-studio" in reg


def test_config_manifest_32_8():
    cfg = (ROOT / "applications" / "platform_builder" / "config.py").read_text()
    assert 'application_version: str = "1.54.0"' in cfg
    assert 'sprint: str = "32.8"' in cfg
    assert "AI Builder Studio" in cfg
    manifest = (ROOT / "applications" / "platform_builder" / "manifest.json").read_text()
    assert '"application_version": "1.54.0"' in manifest
    assert '"sprint": "32.8"' in manifest
    web = (ROOT / "src" / "web" / "src" / "config" / "webConfig.ts").read_text()
    assert 'sprint: "32.8"' in web
    types = (ROOT / "src" / "web" / "platform-builder" / "types.ts").read_text()
    assert 'PLATFORM_BUILDER_VERSION = "1.54.0"' in types
    assert 'PLATFORM_BUILDER_SPRINT = "32.8"' in types
