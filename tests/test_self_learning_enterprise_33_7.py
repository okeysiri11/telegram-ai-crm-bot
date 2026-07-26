"""Tests — Self-Learning Enterprise (Sprint 33.7)."""

from __future__ import annotations

from pathlib import Path

from applications.platform_builder import platform_builder


ROOT = Path(__file__).resolve().parents[1]

DOCS = [
    "SELF_LEARNING_ENTERPRISE_33_7.md",
    "RELEASE_NOTES_33_7.md",
]


def test_33_7_docs_exist():
    docs = ROOT / "docs"
    for name in DOCS:
        path = docs / name
        assert path.exists(), name
        assert "33.7" in path.read_text()
    index = (docs / "ARCHITECTURE_AUDIT_INDEX.md").read_text()
    assert "SELF_LEARNING_ENTERPRISE_33_7" in index
    report = (docs / "SELF_LEARNING_ENTERPRISE_33_7.md").read_text()
    assert "No new Learning Engine" in report
    assert "Learning Dashboard" in report
    assert "Recommendation Center" in report
    assert "Executive Learning Report" in report


def test_platform_version_33_7():
    health = platform_builder.health()
    assert health["application_version"] == "1.66.0"
    assert health["sprint"] == "34.0"
    assert "Release Candidate" in health["release_status"]


def test_learning_wired():
    app = (ROOT / "src" / "web" / "src" / "App.tsx").read_text()
    assert 'path="/platform-builder/learning"' in app
    assert "SelfLearningEnterprisePage" in app
    full = (ROOT / "src" / "web" / "src" / "layouts" / "FullLayout.tsx").read_text()
    assert "LearningStrip" in full
    derive = (ROOT / "src" / "web" / "src" / "self-learning-enterprise" / "deriveLearning.ts").read_text()
    for token in (
        "deriveLearning",
        "workflowOpts",
        "aiReview",
        "KnowledgeEvolution",
        "recommendations",
        "ExecutiveLearningReport",
        "deriveRuntime",
        "derivePredictive",
        "deriveIntelligence",
        "deriveDataFabric",
    ):
        assert token in derive
    page = (
        ROOT / "src" / "web" / "src" / "self-learning-enterprise" / "SelfLearningEnterprisePage.tsx"
    ).read_text()
    for token in (
        "Learning Dashboard",
        "Workflow Optimization",
        "AI Performance Review",
        "Knowledge Evolution",
        "Recommendation Center",
        "Executive Learning Report",
        "LearningWidgetCompact",
    ):
        assert token in page
    css = (
        ROOT / "src" / "web" / "src" / "self-learning-enterprise" / "self-learning-enterprise.css"
    ).read_text()
    assert "Sprint 33.7" in css
    assert "sle-" in css
    idx = (ROOT / "src" / "web" / "src" / "index.css").read_text()
    assert "self-learning-enterprise.css" in idx
    search = (ROOT / "src" / "web" / "navigation" / "managers" / "searchIndex.ts").read_text()
    assert "idx_learning" in search
    qa = (ROOT / "src" / "web" / "command-center" / "managers" / "quickActions.ts").read_text()
    assert "/platform-builder/learning" in qa
    mc = (
        ROOT / "src" / "web" / "platform-builder" / "mission-control" / "MissionControlLivePanel.tsx"
    ).read_text()
    assert "LearningWidgetCompact" in mc
    assert "learning" in mc


def test_config_manifest_33_7():
    cfg = (ROOT / "applications" / "platform_builder" / "config.py").read_text()
    assert 'application_version: str = "1.66.0"' in cfg
    assert 'sprint: str = "34.0"' in cfg
    assert "Release Candidate" in cfg
    manifest = (ROOT / "applications" / "platform_builder" / "manifest.json").read_text()
    assert '"application_version": "1.66.0"' in manifest
    assert '"sprint": "34.0"' in manifest
    web = (ROOT / "src" / "web" / "src" / "config" / "webConfig.ts").read_text()
    assert 'sprint: "34.0"' in web
    types = (ROOT / "src" / "web" / "platform-builder" / "types.ts").read_text()
    assert 'PLATFORM_BUILDER_VERSION = "1.66.0"' in types
    assert 'PLATFORM_BUILDER_SPRINT = "34.0"' in types
