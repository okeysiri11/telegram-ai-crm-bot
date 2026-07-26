"""Tests — AI Operating System Experience (Sprint 32.4)."""

from __future__ import annotations

from pathlib import Path

from applications.platform_builder import platform_builder


ROOT = Path(__file__).resolve().parents[1]

DOCS = [
    "AI_OS_EXPERIENCE_32_4.md",
    "RELEASE_NOTES_32_4.md",
]


def test_32_4_docs_exist():
    docs = ROOT / "docs"
    for name in DOCS:
        path = docs / name
        assert path.exists(), name
        assert "32.4" in path.read_text()
    index = (docs / "ARCHITECTURE_AUDIT_INDEX.md").read_text()
    assert "AI_OS_EXPERIENCE_32_4" in index
    report = (docs / "AI_OS_EXPERIENCE_32_4.md").read_text()
    assert "No new Engine" in report
    assert "AiOsExperienceChrome" in report or "Global AI Concierge" in report


def test_platform_version_32_4():
    health = platform_builder.health()
    assert health["application_version"] == "1.58.0"
    assert health["sprint"] == "33.2"
    assert health["release_status"] == "AI Runtime & Orchestration Center"


def test_ai_os_chrome_wired():
    full = (ROOT / "src" / "web" / "src" / "layouts" / "FullLayout.tsx").read_text()
    assert "AiOsExperienceChrome" in full
    assert "GlobalWorkspaceBar" in full
    chrome = (ROOT / "src" / "web" / "src" / "ai-os-chrome" / "AiOsExperienceChrome.tsx").read_text()
    for token in (
        "AI Concierge",
        "Workspace Pulse",
        "Executive Snapshot",
        "useLiveEnterprise",
        "suggestionsForPath",
        "openPalette",
        "openAi",
    ):
        assert token in chrome
    suggestions = (ROOT / "src" / "web" / "src" / "ai-os-chrome" / "smartSuggestions.ts").read_text()
    for token in ("crm_create", "kb_new", "city_prod", "an_kpi", "sectionKeyFromPath"):
        assert token in suggestions
    providers = (ROOT / "src" / "web" / "src" / "shell" / "Providers.tsx").read_text()
    assert "contextEngine.patch" in providers
    assert "sectionKeyFromPath" in providers
    qa = (ROOT / "src" / "web" / "command-center" / "managers" / "quickActions.ts").read_text()
    assert "act_open_mission_control" in qa
    assert "act_open_enterprise_city" in qa
    assert "act_open_concierge" in qa
    assert "ai_recommendations" in qa
    ai = (ROOT / "src" / "web" / "command-center" / "managers" / "aiCommands.ts").read_text()
    assert "open_mission_control" in ai
    assert "open_enterprise_city" in ai
    assert "ai_recommendations" in ai
    css = (ROOT / "src" / "web" / "src" / "index.css").read_text()
    assert "Sprint 32.4" in css
    assert "aios-dock" in css
    assert "aios-pulse" in css
    assert "aios-snapshot" in css


def test_config_manifest_32_4():
    cfg = (ROOT / "applications" / "platform_builder" / "config.py").read_text()
    assert 'application_version: str = "1.58.0"' in cfg
    assert 'sprint: str = "33.2"' in cfg
    assert "AI Runtime & Orchestration Center" in cfg
    manifest = (ROOT / "applications" / "platform_builder" / "manifest.json").read_text()
    assert '"application_version": "1.58.0"' in manifest
    assert '"sprint": "33.2"' in manifest
    assert "AI Runtime & Orchestration Center" in manifest
    web = (ROOT / "src" / "web" / "src" / "config" / "webConfig.ts").read_text()
    assert 'sprint: "33.2"' in web
    types = (ROOT / "src" / "web" / "platform-builder" / "types.ts").read_text()
    assert 'PLATFORM_BUILDER_VERSION = "1.58.0"' in types
    assert 'PLATFORM_BUILDER_SPRINT = "33.2"' in types
