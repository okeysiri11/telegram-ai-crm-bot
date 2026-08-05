"""Sprint 37.5 — Production certification smoke tests."""

from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DOCS = [
    "FINAL_RELEASE_AUDIT.md",
    "PRODUCTION_CERTIFICATION.md",
    "ENTERPRISE_CERTIFICATE.md",
    "FINAL_TEST_REPORT.md",
    "FINAL_DEPLOYMENT_CHECKLIST.md",
    "SPRINT_37_5_RESULT.md",
]


@pytest.mark.asyncio
async def test_production_certification_report():
    from platform_validation.production_certification_37_5 import build_certification_report

    report = await build_certification_report()
    data = report.to_dict()
    assert data["blockers_p0"] == []
    assert data["overall_readiness_pct"] >= 99.0
    assert data["certified"] is True
    assert data["release_tag"] == "v1.0.0-rc1"
    for pillar in data["pillars"]:
        assert pillar["status"] == "READY", pillar


def test_certification_docs_present():
    for name in DOCS:
        path = ROOT / "docs" / name
        assert path.is_file(), name
        assert path.stat().st_size > 100


def test_prompt_firewall_abuse_reset():
    from applications.enterprise_hub.ai_provider_hub.prompt_firewall import (
        check_abuse,
        reset_abuse_state,
    )

    reset_abuse_state()
    for _ in range(5):
        abused, _ = check_abuse("cert_actor")
        assert abused is False
    reset_abuse_state()
