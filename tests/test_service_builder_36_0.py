"""Tests — Enterprise Service Builder (Sprint 36.0)."""

from __future__ import annotations

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from platform_service_builder.lifecycle import LifecycleError
from platform_service_builder.models import ServiceState, compare_semver, parse_semver
from platform_service_builder.permissions import ServicePermissionDenied
from platform_service_builder.router import register_service_builder_routes
from platform_service_builder.service import ServiceBuilderService, service_builder


@pytest.fixture
def builder() -> ServiceBuilderService:
    service_builder.reset()
    service_builder.ensure_seed()
    yield service_builder
    service_builder.reset()


@pytest.mark.asyncio
async def test_registration(builder: ServiceBuilderService):
    svc = builder.create(
        {
            "id": "svc_test_alpha",
            "name": "test_alpha",
            "display_name": "Test Alpha",
            "version": "1.2.3",
            "owner": "qa",
            "category": "runtime",
            "dependencies": ["svc_event_bus"],
            "permissions": {
                "allowed_apis": ["test.*"],
                "allowed_events": ["test.*"],
                "allowed_storage": ["tmp"],
                "allowed_ai_tools": [],
                "allowed_integrations": [],
            },
        },
        actor="tester",
    )
    assert svc.id == "svc_test_alpha"
    assert svc.state == ServiceState.DRAFT
    assert svc.manifest.version == "1.2.3"
    assert builder.get("svc_test_alpha").manifest.owner == "qa"


@pytest.mark.asyncio
async def test_installation_startup_shutdown(builder: ServiceBuilderService):
    builder.install("svc_event_bus", actor="tester")
    assert builder.get("svc_event_bus").state == ServiceState.INSTALLED

    builder.load("svc_event_bus", actor="tester")
    assert builder.get("svc_event_bus").state == ServiceState.LOADED

    builder.start("svc_event_bus", actor="tester")
    running = builder.get("svc_event_bus")
    assert running.state == ServiceState.RUNNING
    assert running.started_at is not None

    builder.stop("svc_event_bus", actor="tester")
    assert builder.get("svc_event_bus").state == ServiceState.LOADED


@pytest.mark.asyncio
async def test_reload_restart(builder: ServiceBuilderService):
    builder.start("svc_event_bus", actor="tester")
    builder.reload("svc_event_bus", actor="tester")
    assert builder.get("svc_event_bus").state == ServiceState.RUNNING

    before = builder.get("svc_event_bus").restart_count
    builder.restart("svc_event_bus", actor="tester")
    assert builder.get("svc_event_bus").restart_count == before + 1
    assert builder.get("svc_event_bus").state == ServiceState.RUNNING


@pytest.mark.asyncio
async def test_health(builder: ServiceBuilderService):
    builder.start("svc_event_bus", actor="tester")
    snap = builder.health_of("svc_event_bus")
    assert snap["service_id"] == "svc_event_bus"
    assert snap["healthy"] is True
    assert "response_time_ms" in snap
    assert "availability_pct" in snap
    monitor = builder.health_monitor()
    assert any(h["service_id"] == "svc_event_bus" for h in monitor)


@pytest.mark.asyncio
async def test_permissions(builder: ServiceBuilderService):
    svc = builder.get("svc_ai_runtime")
    assert builder.permissions.check_api(svc, "ai.invoke") is True
    assert builder.permissions.check_ai_tool(svc, "anything") is True
    assert builder.permissions.check_storage(svc, "ai_memory") is True
    assert builder.permissions.check_storage(svc, "forbidden_bucket") is False

    with pytest.raises(ServicePermissionDenied):
        builder.permissions.require(svc, "storage", "forbidden_bucket")

    result = builder.check_permission("svc_ai_runtime", api="ai.chat", storage="ai_memory")
    assert result["allowed"] is True


@pytest.mark.asyncio
async def test_dependency_resolver(builder: ServiceBuilderService):
    order = builder.dependencies.resolve_startup_order(
        ["svc_enterprise_city", "svc_multi_agent_runtime", "svc_event_bus"]
    )
    assert order.index("svc_event_bus") < order.index("svc_multi_agent_runtime")
    assert order.index("svc_multi_agent_runtime") < order.index("svc_enterprise_city")

    shutdown = builder.dependencies.resolve_shutdown_order(["svc_workflow_runtime", "svc_event_bus"])
    assert shutdown.index("svc_workflow_runtime") < shutdown.index("svc_event_bus")

    graph = builder.dependency_graph("svc_workflow_runtime")
    assert graph["root"] == "svc_workflow_runtime"
    assert graph["graph"]["service_id"] == "svc_workflow_runtime"
    assert graph["graph"]["children"][0]["service_id"] == "svc_event_bus"

    # cycle detection
    builder.create(
        {
            "id": "svc_cycle_a",
            "name": "cycle_a",
            "display_name": "Cycle A",
            "version": "1.0.0",
            "dependencies": ["svc_cycle_b"],
        }
    )
    builder.create(
        {
            "id": "svc_cycle_b",
            "name": "cycle_b",
            "display_name": "Cycle B",
            "version": "1.0.0",
            "dependencies": ["svc_cycle_a"],
        }
    )
    cycles = builder.dependencies.detect_cycles()
    assert cycles
    assert builder.dependencies.has_cycle_involving("svc_cycle_a")


def test_version_resolver(builder: ServiceBuilderService):
    assert parse_semver("1.2.3") == (1, 2, 3)
    assert compare_semver("1.2.0", "1.1.9") > 0
    assert compare_semver("2.0.0", "2.0.0") == 0

    builder.update(
        "svc_event_bus",
        {"version": "1.1.0", "changelog": "minor bump"},
        actor="tester",
    )
    versions = builder.versions("svc_event_bus")
    assert any(v["version"] == "1.1.0" and v["is_active"] for v in versions)
    assert any(v["version"] == "1.0.0" for v in versions)

    active = builder.registry.resolve_version("svc_event_bus")
    assert active is not None
    assert active.version == "1.1.0"


@pytest.mark.asyncio
async def test_start_resolves_dependencies(builder: ServiceBuilderService):
    builder.start("svc_workflow_runtime", actor="tester")
    assert builder.get("svc_event_bus").state == ServiceState.RUNNING
    assert builder.get("svc_workflow_runtime").state == ServiceState.RUNNING


@pytest.mark.asyncio
async def test_disable_blocks_start(builder: ServiceBuilderService):
    builder.install("svc_event_bus")
    builder.disable("svc_event_bus")
    assert builder.get("svc_event_bus").state == ServiceState.DISABLED
    with pytest.raises(LifecycleError):
        builder.start("svc_event_bus")


@pytest.mark.asyncio
async def test_audit_logging(builder: ServiceBuilderService):
    builder.install("svc_event_bus", actor="auditor")
    builder.start("svc_event_bus", actor="auditor")
    logs = builder.logs("svc_event_bus")
    ops = {e["operation"] for e in logs}
    assert "install" in ops
    assert "start" in ops
    assert all("actor" in e and "result" in e for e in logs)


@pytest.mark.asyncio
async def test_api_routes(auth_headers, monkeypatch):
    from unittest.mock import AsyncMock, patch

    from platform_management.permissions import ManagementRole

    service_builder.reset()
    service_builder.ensure_seed()

    async def _admin(_tid):
        return ManagementRole.ADMINISTRATOR

    monkeypatch.setattr("platform_management.permissions.resolve_role", _admin)

    app = web.Application()
    register_service_builder_routes(app)

    with patch(
        "platform_management.management_service.management_service.log_request",
        new_callable=AsyncMock,
    ):
        async with TestClient(TestServer(app)) as client:
            res = await client.get("/api/service-builder/services", headers=auth_headers)
            assert res.status == 200
            body = await res.json()
            assert body["success"] is True
            assert body["data"]["count"] >= 6

            sid = "svc_event_bus"
            res = await client.post(
                f"/api/service-builder/services/{sid}/install",
                headers=auth_headers,
            )
            assert res.status == 200

            res = await client.post(
                f"/api/service-builder/services/{sid}/start",
                headers=auth_headers,
            )
            assert res.status == 200
            data = (await res.json())["data"]
            assert data["state"] == "running"

            res = await client.get(
                f"/api/service-builder/services/{sid}/health",
                headers=auth_headers,
            )
            assert res.status == 200
            assert (await res.json())["data"]["healthy"] is True

            res = await client.get(
                f"/api/service-builder/services/{sid}/logs",
                headers=auth_headers,
            )
            assert res.status == 200
            assert (await res.json())["data"]["count"] >= 1

            res = await client.post(
                f"/api/service-builder/services/{sid}/stop",
                headers=auth_headers,
            )
            assert res.status == 200

            res = await client.get(
                "/management/v1/service-builder/services",
                headers=auth_headers,
            )
            assert res.status == 200

    service_builder.reset()


def test_ui_module_present():
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    page = root / "src/web/src/service-builder/ServiceBuilderPage.tsx"
    index = root / "src/web/src/service-builder/index.ts"
    assert page.exists()
    assert index.exists()
    text = page.read_text(encoding="utf-8")
    for label in (
        "Service Catalog",
        "Installed",
        "Running",
        "Dependencies",
        "Health Monitor",
        "Configuration",
        "Permissions",
        "Logs",
        "Versions",
        "Start",
        "Stop",
        "Restart",
        "Reload",
    ):
        assert label in text


def test_package_exports():
    from platform_service_builder import (
        ServiceBuilderService,
        ServiceDefinition,
        ServiceDependencyResolver,
        ServiceHealthChecker,
        ServiceLifecycleManager,
        ServiceLoader,
        ServiceManifest,
        ServicePermissionResolver,
        ServiceRegistry,
        ServiceSandbox,
        ServiceState,
        ServiceVersion,
        service_builder as sb,
    )

    assert ServiceBuilderService is not None
    assert ServiceRegistry is not None
    assert ServiceDefinition is not None
    assert ServiceManifest is not None
    assert ServiceVersion is not None
    assert ServiceState.RUNNING.value == "running"
    assert ServiceLifecycleManager is not None
    assert ServiceDependencyResolver is not None
    assert ServiceLoader is not None
    assert ServiceSandbox is not None
    assert ServiceHealthChecker is not None
    assert ServicePermissionResolver is not None
    assert sb is not None


def test_canonical_registration():
    from platform_architecture.canonical_services import CANONICAL_SERVICES

    assert "service_builder" in CANONICAL_SERVICES
    assert "platform_service_builder" in CANONICAL_SERVICES["service_builder"]["canonical"]


def test_orm_tables_defined():
    from database.models.service_builder import (
        ServiceDependencyRow,
        ServiceHealthRow,
        ServiceLogRow,
        ServicePermissionRow,
        ServiceRegistryRow,
        ServiceVersionRow,
    )

    assert ServiceRegistryRow.__tablename__ == "service_registry"
    assert ServiceVersionRow.__tablename__ == "service_versions"
    assert ServiceDependencyRow.__tablename__ == "service_dependencies"
    assert ServiceHealthRow.__tablename__ == "service_health"
    assert ServiceLogRow.__tablename__ == "service_logs"
    assert ServicePermissionRow.__tablename__ == "service_permissions"
