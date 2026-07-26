"""Tests — AI Team Collaboration & Multi-Agent Workspace (Sprint 32.6)."""

from __future__ import annotations

from pathlib import Path

from applications.platform_builder import platform_builder


ROOT = Path(__file__).resolve().parents[1]

DOCS = [
    "AI_TEAM_COLLABORATION_32_6.md",
    "RELEASE_NOTES_32_6.md",
]


def test_32_6_docs_exist():
    docs = ROOT / "docs"
    for name in DOCS:
        path = docs / name
        assert path.exists(), name
        assert "32.6" in path.read_text()
    index = (docs / "ARCHITECTURE_AUDIT_INDEX.md").read_text()
    assert "AI_TEAM_COLLABORATION_32_6" in index
    report = (docs / "AI_TEAM_COLLABORATION_32_6.md").read_text()
    assert "No new AI Engine" in report or "No new" in report
    assert "AI Team Workspace" in report


def test_platform_version_32_6():
    health = platform_builder.health()
    assert health["application_version"] == "1.64.0"
    assert health["sprint"] == "33.8"
    assert "OKR Intelligence" in health["release_status"]


def test_ai_team_collaboration_wired():
    page = (ROOT / "src" / "web" / "platform-builder" / "ai-team" / "AITeamCenterPage.tsx").read_text()
    assert "AITeamCollaborationWorkspace" in page
    full = (ROOT / "src" / "web" / "src" / "layouts" / "FullLayout.tsx").read_text()
    assert "AITeamCollaborationWorkspace" in full
    derive = (
        ROOT / "src" / "web" / "src" / "ai-team-collaboration" / "deriveTeamCollaboration.ts"
    ).read_text()
    for token in (
        "deriveTeamCollaboration",
        "Marketing AI",
        "Sales AI",
        "Legal AI",
        "Analytics AI",
        "buildConversation",
        "KnowledgeContribution",
        "TeamHealthMetrics",
    ):
        assert token in derive
    panels = (
        ROOT / "src" / "web" / "src" / "ai-team-collaboration" / "AITeamCollaborationPanels.tsx"
    ).read_text()
    for token in (
        "AI Team Workspace",
        "Task Distribution",
        "AI Collaboration Timeline",
        "Team Health",
        "AI Conversation",
        "Knowledge Contribution",
        "Executive Overview",
        "useLiveEnterprise",
    ):
        assert token in panels
    css = (ROOT / "src" / "web" / "src" / "index.css").read_text()
    assert "Sprint 32.6" in css
    assert "atc-collab" in css
    assert "atc-strip" in css


def test_config_manifest_32_6():
    cfg = (ROOT / "applications" / "platform_builder" / "config.py").read_text()
    assert 'application_version: str = "1.64.0"' in cfg
    assert 'sprint: str = "33.8"' in cfg
    assert "OKR Intelligence" in cfg
    manifest = (ROOT / "applications" / "platform_builder" / "manifest.json").read_text()
    assert '"application_version": "1.64.0"' in manifest
    assert '"sprint": "33.8"' in manifest
    web = (ROOT / "src" / "web" / "src" / "config" / "webConfig.ts").read_text()
    assert 'sprint: "33.8"' in web
    types = (ROOT / "src" / "web" / "platform-builder" / "types.ts").read_text()
    assert 'PLATFORM_BUILDER_VERSION = "1.64.0"' in types
    assert 'PLATFORM_BUILDER_SPRINT = "33.8"' in types
