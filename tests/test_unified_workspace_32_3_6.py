"""Tests — Unified Enterprise Workspace (Sprint 32.3.6)."""

from __future__ import annotations

from pathlib import Path

from applications.platform_builder import platform_builder


ROOT = Path(__file__).resolve().parents[1]

DOCS = [
    "UNIFIED_WORKSPACE_32_3_6.md",
    "RELEASE_NOTES_32_3_6.md",
]


def test_32_3_6_docs_exist():
    docs = ROOT / "docs"
    for name in DOCS:
        path = docs / name
        assert path.exists(), name
        assert "32.3.6" in path.read_text()
    index = (docs / "ARCHITECTURE_AUDIT_INDEX.md").read_text()
    assert "UNIFIED_WORKSPACE_32_3_6" in index


def test_platform_version_32_3_6():
    health = platform_builder.health()
    assert health["application_version"] == "1.56.0"
    assert health["sprint"] == "33.0"
    assert "Enterprise Digital Twin" in health["release_status"]


def test_unified_workspace_chrome():
    full = (ROOT / "src" / "web" / "src" / "layouts" / "FullLayout.tsx").read_text()
    assert "GlobalWorkspaceBar" in full
    assert "UnifiedToastStrip" in full
    assert "registerUnifiedWorkspaceSearch" in full
    ctx = (ROOT / "src" / "web" / "src" / "workspace-chrome" / "workspaceContext.ts").read_text()
    for token in ("Dashboard", "Mission Control", "Enterprise City", "CRM", "AI Team", "Knowledge"):
        assert token in ctx
    bar = (ROOT / "src" / "web" / "src" / "workspace-chrome" / "GlobalWorkspaceBar.tsx").read_text()
    assert "GLOBAL_QUICK_SWITCH" in bar
    assert "detectActiveEcosystem" in bar
    crumbs = (ROOT / "src" / "web" / "navigation" / "managers" / "breadcrumbEngine.ts").read_text()
    assert "labelForSegment" in crumbs
    assert "Enterprise" in crumbs
    search = (ROOT / "src" / "web" / "src" / "workspace-chrome" / "registerUnifiedSearch.ts").read_text()
    assert "searchIndex.upsert" in search
    cc = (ROOT / "src" / "web" / "command-center" / "components" / "CommandCenterProvider.tsx").read_text()
    assert 'e.key === "Escape"' in cc
    assert 'key === "/"' in cc
    qs = (ROOT / "src" / "web" / "navigation" / "managers" / "quickSwitcher.ts").read_text()
    assert "enterprise" in qs
    css = (ROOT / "src" / "web" / "src" / "index.css").read_text()
    assert "Sprint 32.3.6" in css
    assert "uws-chrome" in css


def test_config_manifest_32_3_6():
    cfg = (ROOT / "applications" / "platform_builder" / "config.py").read_text()
    assert 'application_version: str = "1.56.0"' in cfg
    assert 'sprint: str = "33.0"' in cfg
    manifest = (ROOT / "applications" / "platform_builder" / "manifest.json").read_text()
    assert '"application_version": "1.56.0"' in manifest
    assert '"sprint": "33.0"' in manifest
    web = (ROOT / "src" / "web" / "src" / "config" / "webConfig.ts").read_text()
    assert 'sprint: "33.0"' in web
    types = (ROOT / "src" / "web" / "platform-builder" / "types.ts").read_text()
    assert 'PLATFORM_BUILDER_VERSION = "1.56.0"' in types
    assert 'PLATFORM_BUILDER_SPRINT = "33.0"' in types
