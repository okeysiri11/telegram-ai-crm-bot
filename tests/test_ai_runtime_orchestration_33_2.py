"""Tests — AI Runtime & Orchestration Center (Sprint 33.2)."""

from __future__ import annotations

from pathlib import Path

from applications.platform_builder import platform_builder


ROOT = Path(__file__).resolve().parents[1]

DOCS = [
    "AI_RUNTIME_ORCHESTRATION_33_2.md",
    "RELEASE_NOTES_33_2.md",
]


def test_33_2_docs_exist():
    docs = ROOT / "docs"
    for name in DOCS:
        path = docs / name
        assert path.exists(), name
        assert "33.2" in path.read_text()
    index = (docs / "ARCHITECTURE_AUDIT_INDEX.md").read_text()
    assert "AI_RUNTIME_ORCHESTRATION_33_2" in index
    report = (docs / "AI_RUNTIME_ORCHESTRATION_33_2.md").read_text()
    assert "No new AI Core" in report
    assert "Runtime Engine" in report
    assert "Live AI Queue" in report


def test_platform_version_33_2():
    health = platform_builder.health()
    assert health["application_version"] == "1.65.0"
    assert health["sprint"] == "33.9"
    assert "Governance" in health["release_status"]


def test_runtime_wired():
    app = (ROOT / "src" / "web" / "src" / "App.tsx").read_text()
    assert 'path="/platform-builder/runtime"' in app
    assert "AIRuntimePage" in app
    full = (ROOT / "src" / "web" / "src" / "layouts" / "FullLayout.tsx").read_text()
    assert "AIRuntimeStrip" in full
    derive = (ROOT / "src" / "web" / "src" / "ai-runtime" / "deriveRuntime.ts").read_text()
    for token in (
        "deriveRuntime",
        "ORCH_CHAIN",
        "active",
        "waiting",
        "completed",
        "failed",
        "paused",
        "RuntimeHealth",
    ):
        assert token in derive
    page = (ROOT / "src" / "web" / "src" / "ai-runtime" / "AIRuntimePage.tsx").read_text()
    for token in (
        "Runtime Dashboard",
        "Live AI Queue",
        "Orchestration Timeline",
        "Execution Monitor",
        "Runtime Health",
        "RuntimeMonitorCompact",
    ):
        assert token in page
    css = (ROOT / "src" / "web" / "src" / "ai-runtime" / "ai-runtime.css").read_text()
    assert "Sprint 33.2" in css
    assert "art-" in css
    idx = (ROOT / "src" / "web" / "src" / "index.css").read_text()
    assert "ai-runtime.css" in idx
    mc = (
        ROOT / "src" / "web" / "platform-builder" / "mission-control" / "MissionControlLivePanel.tsx"
    ).read_text()
    assert "RuntimeMonitorCompact" in mc
    twin = (ROOT / "src" / "web" / "src" / "enterprise-twin" / "EnterpriseTwinPage.tsx").read_text()
    assert "deriveRuntime" in twin
    assert "Live Runtime" in twin
    qa = (ROOT / "src" / "web" / "command-center" / "managers" / "quickActions.ts").read_text()
    assert "/platform-builder/runtime" in qa


def test_config_manifest_33_2():
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
