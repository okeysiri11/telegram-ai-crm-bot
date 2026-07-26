"""Tests — Platform Control Center (Sprint 29.3)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.platform_builder import platform_builder
from applications.platform_builder.api.register import register_platform_builder_routes
from applications.platform_builder.control_center.catalogs import (
    ARCHITECTURE_GRAPHS,
    DIAGNOSTIC_CHECKS,
    EDITOR_FIELDS,
    HEALTH_METRICS,
    INSPECTOR_FIELDS,
    OVERVIEW_CATEGORIES,
    REGISTRY_ACTIONS,
    SEARCH_SCOPES,
)


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


def test_platform_control_catalog_coverage():
    health = platform_builder.health()
    assert health["application_version"] == "1.65.0"
    assert health["sprint"] == "33.9"
    assert health["platform_control_center_ready"] is True
    assert health["control_center"]["owner_gated"] is True

    catalog = platform_builder.control_center.catalog("owner")
    assert len(catalog["overview_categories"]) == len(OVERVIEW_CATEGORIES) == 12
    assert len(catalog["search_scopes"]) == len(SEARCH_SCOPES) == 9
    assert len(catalog["inspector_fields"]) == len(INSPECTOR_FIELDS) == 9
    assert len(catalog["editor_fields"]) == len(EDITOR_FIELDS) == 6
    assert len(catalog["registry_actions"]) == len(REGISTRY_ACTIONS) == 6
    assert len(catalog["health_metrics"]) == len(HEALTH_METRICS) == 7
    assert len(catalog["diagnostic_checks"]) == len(DIAGNOSTIC_CHECKS) == 5
    assert len(catalog["architecture_graphs"]) == len(ARCHITECTURE_GRAPHS) == 6


def test_search_scopes_and_registry_actions():
    cc = platform_builder.control_center
    for scope in SEARCH_SCOPES:
        result = cc.search("platform_owner", "", scope)
        assert "results" in result
        assert result["scope"] == scope

    for action in REGISTRY_ACTIONS:
        ops = cc.registries("platform_owner", action=action)
        assert ops["operation"]["status"] == "completed"


def test_architecture_explorer_and_rollback():
    cc = platform_builder.control_center
    arch = cc.architecture("platform_owner")
    assert arch["ready"] is True
    assert arch["module_relationships"]
    assert arch["ai_relationships"] is not None
    assert arch["knowledge_flow"]
    assert arch["workflow_graph"]
    assert arch["registry_graph"]
    assert arch["future_visual_layer_graph"]

    session = cc.start_session("platform_owner")
    created = cc.create("platform_owner", session["session_id"])
    versions = platform_builder.store.versions.list_all()
    assert versions
    rb = cc.rollback("platform_owner", versions[-1]["version_id"])
    assert rb["ok"] is True
    assert created["centers"]["health_center_id"]


@pytest.mark.asyncio
async def test_api_platform_control_endpoints(client):
    health = await client.get(f"{PREFIX}/health")
    body = await health.json()
    assert body["application_version"] == "1.65.0"
    assert body["platform_control_center_ready"] is True

    catalog = await client.get(f"{PREFIX}/god-mode/control/catalog", headers=OWNER)
    assert catalog.status == 200

    search = await client.get(
        f"{PREFIX}/god-mode/control/search?q=seed&scope=AI",
        headers=OWNER,
    )
    assert search.status == 200
    results = (await search.json())["results"]
    assert results
    oid = results[0]["internal_id"]

    inspect = await client.get(f"{PREFIX}/god-mode/control/objects/{oid}", headers=OWNER)
    assert inspect.status == 200

    edit = await client.patch(
        f"{PREFIX}/god-mode/control/objects/{oid}",
        headers=OWNER,
        json={"permissions": {"owner": "platform_owner"}},
    )
    assert edit.status == 200

    diag = await client.get(f"{PREFIX}/god-mode/control/diagnostics", headers=OWNER)
    assert diag.status == 200

    arch = await client.get(f"{PREFIX}/god-mode/control/architecture", headers=OWNER)
    assert arch.status == 200

    explain = await client.post(
        f"{PREFIX}/god-mode/control/explain",
        headers=OWNER,
        json={"recommendation": "Repair broken links"},
    )
    assert explain.status == 200
    explained = await explain.json()
    assert "business_impact" in explained


def test_docs_platform_control_28_7():
    docs = (ROOT / "docs" / "PLATFORM_CONTROL_CENTER.md").read_text()
    for key in (
        "Global Search",
        "Object Inspector",
        "System Health",
        "Architecture Explorer",
        "Explain Mode",
    ):
        assert key in docs
    assert (ROOT / "applications" / "platform_builder" / "control_center" / "control_center.py").exists()
    manifest = (ROOT / "applications" / "platform_builder" / "manifest.json").read_text()
    assert '"platform_control_center": "1.0"' in manifest
