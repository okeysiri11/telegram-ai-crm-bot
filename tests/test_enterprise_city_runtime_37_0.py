"""Tests — Enterprise City Runtime (Sprint 37.0)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from platform_orchestrator.city_runtime_router import register_enterprise_city_runtime_routes
from platform_orchestrator.city_runtime_service import enterprise_city_runtime_service as crs
from platform_management.permissions import ManagementRole


@pytest.fixture
def engine():
    crs.reset()
    crs.ensure_ready()
    yield crs
    crs.reset()


def test_kernel_registry_navigation_palette(engine):
    services = engine.list_services()
    assert len(services) >= 12
    ids = {s["service_id"] for s in services}
    assert "svc_enterprise_city" in ids
    assert "svc_creative_factory" in ids
    assert "svc_multi_agent_runtime" in ids

    nav = engine.navigation()
    labels = {n["label"] for n in nav}
    assert "Enterprise Dashboard" in labels
    assert "Command Center" in labels

    palette = engine.command_palette("creative")
    assert any("Creative" in c["label"] for c in palette)

    routed = engine.route_to("creative_factory")
    assert routed["route"] == "/platform-builder/creative"


def test_workspace_and_shared_session(engine):
    modules = engine.workspace()
    names = {m["module"] for m in modules}
    assert {
        "crm",
        "erp",
        "ai_runtime",
        "multi_agent_runtime",
        "project_memory",
        "context_engine",
        "workflow_runtime",
        "creative_factory",
        "voice_runtime",
        "analytics",
        "knowledge_base",
    } <= names

    session = engine.create_session({"user_id": "exec_1", "roles": ["owner"]})
    updated = engine.update_shared(
        session["session_id"],
        {
            "shared_context": {"focus": "q3"},
            "shared_memory": {"brief": "growth"},
            "permissions": ["platform.read", "platform.execute"],
        },
    )
    assert updated["shared_context"]["focus"] == "q3"
    assert updated["shared_memory"]["brief"] == "growth"
    assert "platform.execute" in updated["permissions"]

    event = engine.publish_event({"type": "platform.test", "ok": True})
    assert event["type"] == "platform.test"
    assert engine.list_events()


def test_dashboard_search_notifications(engine):
    dash = engine.dashboard()
    assert dash["active_agents"] >= 1
    assert dash["recommendations"]
    assert dash["platform_health"]["overall"] in ("healthy", "warning", "critical", "offline")
    assert dash["business_analytics"]

    hits = engine.search("creative")
    assert hits
    kinds = {h["kind"] for h in engine.search("agent")}
    assert "agents" in kinds or hits

    note = engine.notify({"title": "Alert", "body": "demo", "level": "warning"})
    assert note["notification_id"]
    unread = engine.list_notifications(unread_only=True)
    assert any(n["notification_id"] == note["notification_id"] for n in unread)
    engine.mark_read(note["notification_id"])


@pytest.mark.asyncio
async def test_command_center(engine):
    search_cmd = await engine.execute_command({"text": "search agents", "kind": "natural_language"})
    assert search_cmd["intent"] == "search"
    assert search_cmd["result"]["hits"] is not None

    open_cmd = await engine.execute_command({"text": "open multi agent", "kind": "natural_language"})
    assert open_cmd["intent"] == "open_module"

    wf = await engine.execute_command({"text": "run workflow launch", "kind": "workflow_execution"})
    assert wf["intent"] == "workflow"

    ai = await engine.execute_command({"text": "ask ai recommend next action", "kind": "ai_execution"})
    assert ai["intent"] == "ai"


@pytest.mark.asyncio
async def test_integrations_and_readiness(engine):
    from platform_service_builder.service import service_builder

    service_builder.reset()
    service_builder.ensure_seed()

    probe = await engine.probe_integrations()
    assert probe["count"] >= 8
    assert "creative_factory" in probe["integrations"]
    assert "multi_agent_runtime" in probe["integrations"]

    ai = await engine.for_ai_runtime({})
    assert ai["consumer"] == "ai_runtime"
    ma = await engine.for_multi_agent({})
    assert ma["consumer"] == "multi_agent_runtime"
    mem = await engine.for_project_memory({})
    assert mem["consumer"] == "project_memory"
    ctx = await engine.for_context_engine({})
    assert ctx["consumer"] == "context_engine"
    creative = await engine.for_creative({})
    assert creative["consumer"] == "creative_factory"
    voice = await engine.for_voice({"transcript": "open platform dashboard"})
    assert voice["consumer"] == "voice_runtime"
    skills = await engine.for_skills({})
    assert skills["consumer"] == "skills_sdk"
    wf = await engine.for_workflow({})
    assert wf["consumer"] == "workflow_runtime"
    eb = await engine.for_event_bus({})
    assert eb["consumer"] == "event_bus"

    ready = engine.production_readiness()
    assert ready["ready"] is True
    assert ready["score"] == 100.0
    check_ids = {c["id"] for c in ready["checks"]}
    assert {"integration", "smoke", "load", "regression", "security", "api"} <= check_ids

    svc = service_builder.get("svc_enterprise_city")
    assert svc.id == "svc_enterprise_city"
    assert svc.manifest.name == "enterprise_city_runtime"
    assert "/api/platform" in svc.manifest.api
    service_builder.reset()


@pytest.mark.asyncio
async def test_rest_api(engine, auth_headers, monkeypatch):
    async def _admin(_tid):
        return ManagementRole.ADMINISTRATOR

    monkeypatch.setattr("platform_management.permissions.resolve_role", _admin)
    app = web.Application()
    register_enterprise_city_runtime_routes(app)

    with patch(
        "platform_management.management_service.management_service.log_request",
        new_callable=AsyncMock,
    ):
        async with TestClient(TestServer(app)) as client:
            res = await client.get("/api/platform/status", headers=auth_headers)
            assert res.status == 200
            body = await res.json()
            assert body["data"]["sprint"] == "37.0"

            res = await client.get("/api/dashboard", headers=auth_headers)
            assert res.status == 200
            assert (await res.json())["data"]["recommendations"]

            res = await client.get("/api/search?q=memory", headers=auth_headers)
            assert res.status == 200
            assert (await res.json())["data"]["count"] >= 1

            res = await client.post(
                "/api/platform/command",
                headers=auth_headers,
                json={"text": "search workflows"},
            )
            assert res.status == 201

            res = await client.get("/api/platform/services", headers=auth_headers)
            assert res.status == 200
            assert (await res.json())["data"]["count"] >= 10

            res = await client.get("/api/platform/readiness", headers=auth_headers)
            assert res.status == 200
            assert (await res.json())["data"]["ready"] is True

            res = await client.get("/management/v1/platform/status", headers=auth_headers)
            assert res.status == 200
            assert (await res.json())["data"]["service"] == "enterprise_city_runtime"

            res = await client.get("/city/simulate", headers=auth_headers)
            assert res.status == 200

    crs.reset()


def test_ui_present():
    page = Path(__file__).resolve().parents[1] / "src/web/src/platform-console/EnterpriseCityRuntimePage.tsx"
    text = page.read_text(encoding="utf-8")
    for label in (
        "Enterprise Dashboard",
        "Global Search",
        "Platform Health",
        "Service Registry",
        "Activity Center",
        "Command Center",
        "Platform Settings",
    ):
        assert label in text


def test_orm_and_migration():
    from database.models.enterprise_city_runtime import (
        PlatformConfigurationRow,
        PlatformHealthRow,
        PlatformMetricRow,
        PlatformRegistryRow,
        PlatformSessionRow,
        PlatformUsageRow,
    )

    assert PlatformRegistryRow.__tablename__ == "platform_registry"
    assert PlatformSessionRow.__tablename__ == "platform_sessions"
    assert PlatformMetricRow.__tablename__ == "platform_metrics"
    assert PlatformHealthRow.__tablename__ == "platform_health"
    assert PlatformUsageRow.__tablename__ == "platform_usage"
    assert PlatformConfigurationRow.__tablename__ == "platform_configuration"

    mig = Path(__file__).resolve().parents[1] / "migrations/versions/t3n456789012_enterprise_city_runtime_v1.py"
    text = mig.read_text(encoding="utf-8")
    for table in (
        "platform_registry",
        "platform_sessions",
        "platform_metrics",
        "platform_health",
        "platform_usage",
        "platform_configuration",
    ):
        assert table in text
    assert 'revision: str = "t3n456789012"' in text
    assert 'down_revision: Union[str, None] = "s2m345678901"' in text


def test_exports_and_docs():
    from platform_orchestrator import enterprise_city_runtime_engine, enterprise_city_runtime_service

    assert enterprise_city_runtime_engine and enterprise_city_runtime_service
    root = Path(__file__).resolve().parents[1]
    assert (root / "docs/ENTERPRISE_CITY_RUNTIME.md").is_file()
    assert (root / "docs/PLATFORM_ARCHITECTURE.md").is_file()
    assert (root / "docs/SPRINT_37_0_RESULT.md").is_file()
