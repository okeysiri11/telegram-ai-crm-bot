"""Tests — AI Skills & SDK (Sprint 36.8)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from platform_ai.skills_sdk_router import register_skills_sdk_routes
from platform_ai.skills_sdk_service import skills_sdk_service as sss
from platform_management.permissions import ManagementRole


@pytest.fixture
def engine():
    sss.reset()
    sss.ensure_ready()
    yield sss
    sss.reset()


def test_skills_registry(engine):
    skills = engine.list_skills()
    assert len(skills) >= 4
    ids = {s["skill_id"] for s in skills}
    assert "skill.summarize_report" in ids
    created = engine.register(
        {
            "skill_id": "skill.custom_demo",
            "name": "Custom Demo",
            "category": "analysis",
            "permissions": ["skill.execute"],
            "visibility": "enterprise",
            "dependencies": [],
        }
    )
    assert created["signature"]
    assert engine.get_skill("skill.custom_demo")["name"] == "Custom Demo"
    versions = engine.list_versions("skill.custom_demo")
    assert versions


@pytest.mark.asyncio
async def test_install_runtime_sandbox(engine):
    inst = engine.install("skill.summarize_report", {"principal": "tester"})
    assert inst["state"] == "enabled"
    assert inst["sandbox"] is True
    assert "timeout_sec" in inst["resource_limits"]

    exe = await engine.execute(
        {"skill_id": "skill.summarize_report", "input": {"doc": "hello"}, "agent_id": "agent_test"}
    )
    assert exe["success"] is True
    assert exe["sandboxed"] is True

    engine.disable("skill.summarize_report")
    disabled_run = await engine.execute(
        {"skill_id": "skill.summarize_report", "auto_install": False, "input": {}}
    )
    assert disabled_run["success"] is False

    engine.enable("skill.summarize_report")
    engine.uninstall("skill.summarize_report")
    assert not any(i["skill_id"] == "skill.summarize_report" for i in engine.list_installed())


def test_dependencies_and_versions(engine):
    # crm_enrich depends on summarize_report — install cascades
    inst = engine.install("skill.crm_enrich")
    assert inst["skill_id"] == "skill.crm_enrich"
    installed_ids = {i["skill_id"] for i in engine.list_installed()}
    assert "skill.summarize_report" in installed_ids

    ver = engine.publish_version(
        "skill.summarize_report",
        {"version": "1.1.0", "notes": "Better summaries"},
    )
    assert ver["version"] == "1.1.0"
    updates = engine.updates("skill.summarize_report")
    assert updates["latest_version"] == "1.1.0"
    assert updates["update_available"] is True


def test_marketplace_and_ratings(engine):
    listings = engine.marketplace()
    assert len(listings) >= 4
    repos = {l["repository"] for l in listings}
    assert {"public", "enterprise", "private", "local"} <= repos

    private = engine.marketplace(repository="private")
    assert private and private[0]["repository"] == "private"

    rated = engine.rate("skill.summarize_report", {"score": 5, "comment": "great"})
    assert rated["ratings_count"] >= 1
    assert rated["rating"] > 0


def test_sdk_templates(engine):
    manifest = engine.sdk_manifest()
    assert set(manifest["sdks"]) >= {"python", "typescript", "rest", "mcp"}
    templates = engine.templates()
    kinds = {t["kind"] for t in templates}
    assert kinds >= {"python", "typescript", "rest", "mcp"}
    py = engine.get_template("tpl_python")
    assert "skill.py" in py["files"]
    assert engine.templates(kind="mcp")


@pytest.mark.asyncio
async def test_integrations(engine):
    from platform_service_builder.service import service_builder

    service_builder.reset()
    service_builder.ensure_seed()

    ai = await engine.for_ai_runtime({"skill_id": "skill.summarize_report"})
    assert ai["consumer"] == "ai_runtime"
    assert ai["execution"]["success"] is True

    ma = await engine.for_multi_agent({})
    assert ma["consumer"] == "multi_agent_runtime"

    mem = await engine.for_project_memory({})
    assert mem["consumer"] == "project_memory"

    ctx = await engine.for_context_engine({})
    assert ctx["consumer"] == "context_engine"

    wf = await engine.for_workflow({})
    assert wf["consumer"] == "workflow"

    voice = await engine.for_voice({"transcript": "generate report about skills"})
    assert voice["consumer"] == "voice_runtime"

    svc = service_builder.get("svc_skills_sdk")
    assert svc.id == "svc_skills_sdk"
    assert svc.manifest.name == "skills_sdk"
    service_builder.reset()


@pytest.mark.asyncio
async def test_agent_dynamic_install_execute(engine):
    installed = {i["skill_id"] for i in engine.list_installed()}
    if "skill.local_draft" in installed:
        engine.uninstall("skill.local_draft")
    exe = await engine.execute(
        {
            "skill_id": "skill.local_draft",
            "agent_id": "agent_worker",
            "auto_install": True,
            "input": {"task": "draft"},
        }
    )
    assert exe["success"] is True
    assert any(i["skill_id"] == "skill.local_draft" for i in engine.list_installed())


@pytest.mark.asyncio
async def test_rest_api(engine, auth_headers, monkeypatch):
    async def _admin(_tid):
        return ManagementRole.ADMINISTRATOR

    monkeypatch.setattr("platform_management.permissions.resolve_role", _admin)
    app = web.Application()
    register_skills_sdk_routes(app)

    with patch(
        "platform_management.management_service.management_service.log_request",
        new_callable=AsyncMock,
    ):
        async with TestClient(TestServer(app)) as client:
            res = await client.get("/api/skills/skills", headers=auth_headers)
            assert res.status == 200
            assert (await res.json())["data"]["count"] >= 4

            res = await client.get("/api/sdk/templates", headers=auth_headers)
            assert res.status == 200
            assert (await res.json())["data"]["count"] >= 4

            res = await client.post(
                "/api/skills/execute",
                headers=auth_headers,
                json={"skill_id": "skill.summarize_report", "input": {"x": 1}},
            )
            assert res.status == 200
            assert (await res.json())["data"]["success"] is True

            res = await client.get("/api/skills/marketplace", headers=auth_headers)
            assert res.status == 200

            res = await client.get("/management/v1/skills/status", headers=auth_headers)
            assert res.status == 200
            assert (await res.json())["data"]["sprint"] == "36.8"

    sss.reset()


def test_ui_present():
    page = Path(__file__).resolve().parents[1] / "src/web/src/skills-sdk-console/SkillsSdkPage.tsx"
    text = page.read_text(encoding="utf-8")
    for label in (
        "Skills Dashboard",
        "Marketplace",
        "Installed Skills",
        "SDK Explorer",
        "Templates",
        "Version Manager",
    ):
        assert label in text


def test_orm_and_migration():
    from database.models.skills_sdk import (
        InstalledSkillRow,
        SkillDependencyRow,
        SkillMarketplaceRow,
        SkillPermissionRow,
        SkillRow,
        SkillStatisticsRow,
        SkillVersionRow,
    )

    assert SkillRow.__tablename__ == "skills"
    assert SkillVersionRow.__tablename__ == "skill_versions"
    assert SkillDependencyRow.__tablename__ == "skill_dependencies"
    assert SkillPermissionRow.__tablename__ == "skill_permissions"
    assert InstalledSkillRow.__tablename__ == "installed_skills"
    assert SkillStatisticsRow.__tablename__ == "skill_statistics"
    assert SkillMarketplaceRow.__tablename__ == "skill_marketplace"

    mig = Path(__file__).resolve().parents[1] / "migrations/versions/r1l234567890_ai_skills_sdk_v1.py"
    text = mig.read_text(encoding="utf-8")
    for table in (
        "skills",
        "skill_versions",
        "skill_dependencies",
        "skill_permissions",
        "installed_skills",
        "skill_statistics",
        "skill_marketplace",
    ):
        assert table in text


def test_exports():
    from platform_ai import skills_sdk_engine, skills_sdk_service

    assert skills_sdk_engine and skills_sdk_service
