"""Tests — God Mode Expansion (Sprint 29.3)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.platform_builder import platform_builder
from applications.platform_builder.api.register import register_platform_builder_routes
from applications.platform_builder.control_center.catalogs import WIZARD_STEPS
from applications.platform_builder.shared.exceptions import ForbiddenError


ROOT = Path(__file__).resolve().parents[1]
PREFIX = "/api/platform-builder/v1"
OWNER = {"X-Platform-Role": "platform_owner"}


@pytest.fixture
def app() -> web.Application:
    application = web.Application()
    register_platform_builder_routes(application)
    return application


@pytest.fixture
async def client(app: web.Application):
    async with TestClient(TestServer(app)) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def reset_store():
    platform_builder.reset()
    yield
    platform_builder.reset()


def test_god_mode_expansion_ready():
    health = platform_builder.health()
    assert health["application_version"] == "1.47.0"
    assert health["sprint"] == "32.3.5"
    assert health["god_mode_ready"] is True
    assert health["god_mode_expansion_ready"] is True
    assert health["platform_control_center_ready"] is True
    assert health["architecture_explorer_ready"] is True
    assert health["audit_center_ready"] is True
    assert health["platform_diagnostics_ready"] is True
    assert health["system_health_center_ready"] is True
    assert health["engines"]["god_mode"] == "2.0"
    assert health["engines"]["platform_control_center"] == "1.0"

    status = platform_builder.god_mode.status("platform_owner")
    assert status["version"] == "2.0.0"
    assert status["sprint"] == "32.3.5"
    assert status["expansion_ready"] is True
    assert status["platform_control_center_ready"] is True
    assert status["diagnostics"]["control_center_online"] is True

    with pytest.raises(ForbiddenError):
        platform_builder.god_mode.status("member")


def test_control_center_owner_gate_and_flow():
    cc = platform_builder.control_center
    with pytest.raises(ForbiddenError):
        cc.catalog("admin")

    catalog = cc.catalog("platform_owner")
    assert catalog["operational"] is True
    assert catalog["god_mode_expansion"] is True
    assert len(catalog["steps"]) == 11
    assert len(WIZARD_STEPS) == 11

    overview = cc.overview("platform_owner")
    assert overview["ready"] is True
    assert "Organizations" in overview["categories"]
    assert "AI Specialists" in overview["categories"]
    assert "Visual Layer" in overview["categories"]

    search = cc.search("platform_owner", "seed", "AI")
    assert search["count"] >= 1
    oid = search["results"][0]["internal_id"]

    inspected = cc.inspect("platform_owner", oid)
    for field in (
        "internal_id",
        "visual_id",
        "object_type",
        "owner",
        "dependencies",
        "relationships",
        "lifecycle",
        "status",
        "history",
    ):
        assert field in inspected

    edited = cc.edit("platform_owner", oid, {"metadata": {"note": "sprint-29.3"}, "properties": {"x": 1}})
    assert edited["ok"] is True

    regs = cc.registries("platform_owner", action="Synchronize")
    assert regs["operation"]["action"] == "synchronize"
    assert regs["count"] >= 1

    health = cc.health("platform_owner")
    assert "Services" in health["metrics"]
    assert "Memory Usage" in health["metrics"]

    diag = cc.diagnostics("platform_owner")
    assert diag["findings"]
    assert "Broken Links" in diag["checks"]

    arch = cc.architecture("platform_owner")
    assert arch["nodes"] and arch["edges"]
    assert "Module Relationships" in arch["graphs"]

    explain = cc.explain("platform_owner", "Rebuild registry graph")
    for key in (
        "reason",
        "expected_benefit",
        "business_impact",
        "alternative_options",
        "estimated_effect",
    ):
        assert key in explain

    session = cc.start_session("platform_owner")
    cc.update_session(
        "platform_owner",
        session["session_id"],
        {"step": 11, "draft": {"recommendation": "Synchronize registries", "focus_object_id": oid}},
    )
    summary = cc.summary("platform_owner", session["session_id"])
    assert summary["title"] == "Platform Control Center Summary"

    created = cc.create("platform_owner", session["session_id"])
    assert created["ok"] is True
    assert created["centers"]["diagnostics_center_id"]
    assert created["centers"]["audit_center_id"]
    assert created["centers"]["architecture_snapshot_id"]
    assert created["centers"]["health_center_id"]

    audit = cc.audit_center("platform_owner")
    assert audit["rollback_support"] is True
    assert audit["count"] >= 1


@pytest.mark.asyncio
async def test_api_god_mode_control(client):
    denied = await client.get(f"{PREFIX}/god-mode/control/overview")
    assert denied.status == 403

    overview = await client.get(f"{PREFIX}/god-mode/control/overview", headers=OWNER)
    assert overview.status == 200

    session = await client.post(f"{PREFIX}/god-mode/control/sessions", headers=OWNER, json={})
    assert session.status == 201
    sid = (await session.json())["session_id"]

    create = await client.post(
        f"{PREFIX}/god-mode/control/sessions/{sid}/create",
        headers=OWNER,
        json={},
    )
    assert create.status == 201
    body = await create.json()
    assert body["ok"] is True
    assert "centers" in body


def test_docs_god_mode_28_7():
    assert (ROOT / "docs" / "GOD_MODE.md").exists()
    assert (ROOT / "docs" / "PLATFORM_CONTROL_CENTER.md").exists()
    assert (ROOT / "knowledge" / "platform_builder" / "god_mode" / "README.md").exists()
    assert (ROOT / "knowledge" / "platform_builder" / "control_center" / "README.md").exists()
    assert (ROOT / "src" / "web" / "platform-builder" / "god-mode" / "ControlCenterStudio.tsx").exists()
    docs = (ROOT / "docs" / "GOD_MODE.md").read_text()
    for key in ("Platform Owner", "Object Inspector", "Architecture View", "Explain Mode"):
        assert key in docs
    manifest = (ROOT / "applications" / "platform_builder" / "manifest.json").read_text()
    assert '"application_version": "1.47.0"' in manifest
    assert "32.3.5" in manifest
