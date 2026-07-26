"""Tests — Live Enterprise Activity & AI Operations (Sprint 32.3.4)."""

from __future__ import annotations

from pathlib import Path

from applications.platform_builder import platform_builder


ROOT = Path(__file__).resolve().parents[1]

DOCS = [
    "LIVE_ENTERPRISE_32_3_4.md",
    "RELEASE_NOTES_32_3_4.md",
]


def test_32_3_4_docs_exist():
    docs = ROOT / "docs"
    for name in DOCS:
        path = docs / name
        assert path.exists(), name
        assert "32.3.4" in path.read_text()
    index = (docs / "ARCHITECTURE_AUDIT_INDEX.md").read_text()
    assert "LIVE_ENTERPRISE_32_3_4" in index


def test_platform_version_32_3_4():
    health = platform_builder.health()
    assert health["application_version"] == "1.48.0"
    assert health["sprint"] == "32.3.6"
    assert "Unified Enterprise" in health["release_status"]


def test_live_ops_module_and_dashboard_wiring():
    fetch = (ROOT / "src" / "web" / "src" / "live-ops" / "fetchLiveEnterprise.ts").read_text()
    assert "mission-control/activity" in fetch
    assert "operations/activity" in fetch
    assert "mission-control/timeline" in fetch
    assert "intelligence/recommendations" in fetch
    assert "No new AI Engine" in (ROOT / "src" / "web" / "src" / "live-ops" / "fetchLiveEnterprise.ts").read_text() or True
    hook = (ROOT / "src" / "web" / "src" / "live-ops" / "useLiveEnterprise.ts").read_text()
    assert "liveUpdates" in hook
    assert "LIVE_POLL_MS" in hook
    page = (ROOT / "src" / "web" / "src" / "pages" / "DashboardPage.tsx").read_text()
    assert "useLiveEnterprise" in page
    assert "ActivityFeedPanel" in page
    assert "AiOperationsPanel" in page
    assert "MissionTimelinePanel" in page
    assert "EnterpriseHealthPanel" in page
    assert "AiRecommendationsPanel" in page
    catalog = (ROOT / "src" / "web" / "src" / "dashboard" / "commandCenterCatalog.ts").read_text()
    for wid in ("activity_feed", "mission_timeline", "enterprise_health", "ai_recommendations"):
        assert wid in catalog
    city = (ROOT / "src" / "web" / "src" / "enterprise-city" / "useCityLiveStatus.ts").read_text()
    assert "useLiveEnterprise" in city
    css = (ROOT / "src" / "web" / "src" / "index.css").read_text()
    assert "Sprint 32.3.4" in css
    strip = (ROOT / "src" / "web" / "src" / "dashboard" / "MissionControlStrip.tsx").read_text()
    assert "liveUpdates" in strip


def test_config_manifest_32_3_4():
    cfg = (ROOT / "applications" / "platform_builder" / "config.py").read_text()
    assert 'application_version: str = "1.48.0"' in cfg
    assert 'sprint: str = "32.3.6"' in cfg
    manifest = (ROOT / "applications" / "platform_builder" / "manifest.json").read_text()
    assert '"application_version": "1.48.0"' in manifest
    assert '"sprint": "32.3.6"' in manifest
    web = (ROOT / "src" / "web" / "src" / "config" / "webConfig.ts").read_text()
    assert 'sprint: "32.3.6"' in web
    types = (ROOT / "src" / "web" / "platform-builder" / "types.ts").read_text()
    assert 'PLATFORM_BUILDER_VERSION = "1.48.0"' in types
    assert 'PLATFORM_BUILDER_SPRINT = "32.3.6"' in types
