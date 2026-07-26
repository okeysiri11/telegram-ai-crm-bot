"""Tests — Architecture Audit & Production Readiness (Sprint 30.3).

Validates audit deliverables exist and existing platform remains compatible.
Does not introduce new subsystems.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from applications.platform_builder import platform_builder


ROOT = Path(__file__).resolve().parents[1]

AUDIT_DOCS = [
    "ARCHITECTURE_AUDIT_INDEX.md",
    "ARCHITECTURE_INVENTORY.md",
    "TECHNICAL_DEBT_REPORT.md",
    "API_CORE_AUDIT.md",
    "ROUTING_AUDIT.md",
    "BUSINESS_ECOSYSTEM_AUDIT.md",
    "AI_PLATFORM_AUDIT.md",
    "PRODUCTION_READINESS_AUDIT.md",
    "WEB_READINESS_AUDIT.md",
    "IMPLEMENTATION_BACKLOG_30_2.md",
]


@pytest.fixture(autouse=True)
def reset_store():
    platform_builder.reset()
    yield
    platform_builder.reset()


def test_architecture_audit_docs_exist():
    docs = ROOT / "docs"
    for name in AUDIT_DOCS:
        path = docs / name
        assert path.exists(), f"Missing audit deliverable: {name}"
        text = path.read_text()
        # Historical 30.2 audit docs remain; index references 30.3 consolidation / 30.4 web
        assert "30.2" in text or "30.3" in text or "30.4" in text
        assert len(text) > 200


def test_architecture_audit_knowledge_exists():
    knowledge = ROOT / "knowledge" / "architecture_audit" / "README.md"
    assert knowledge.exists()
    assert "ARCHITECTURE_AUDIT_INDEX" in knowledge.read_text()


def test_existing_platform_compatible_after_audit():
    """Audit must not break prior foundation."""
    health = platform_builder.health()
    assert health["application_version"] == "1.36.0"
    assert health["sprint"] == "31.1"
    assert health["platform_builder_ready"] is True
    assert health["business_ecosystem_foundation_ready"] is True
    assert health["mission_control_ready"] is True
    assert health["digital_twin_ready"] is True
    assert health["strategy_engine_ready"] is True
    assert health["workflow_intelligence_ready"] is True
    assert health["workspace_os_ready"] is True

    # No redesign — engines still read-only / non-replacing where applicable
    assert health["mission_control"]["replaces_existing_modules"] is False
    assert health["business_ecosystem"]["does_not_replace_existing_modules"] is True
    assert health["business_ecosystem"]["does_not_break_existing_apis"] is True


def test_audit_index_links_all_reports():
    index = (ROOT / "docs" / "ARCHITECTURE_AUDIT_INDEX.md").read_text()
    for name in AUDIT_DOCS:
        if name == "ARCHITECTURE_AUDIT_INDEX.md":
            continue
        assert name in index, f"Index missing link to {name}"


def test_backlog_prefers_extension():
    backlog = (ROOT / "docs" / "IMPLEMENTATION_BACKLOG_30_2.md").read_text()
    assert "Prefer extension" in backlog or "Prefer extension" in backlog.replace("·", "")
    assert "No architecture redesign" in backlog or "no architecture redesign" in backlog.lower()
    assert "Automotive" in backlog
    assert "Do not" in backlog or "do not" in backlog.lower()
