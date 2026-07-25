"""Tests — Builder SDK foundation (Sprint 28.6)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.platform_builder import platform_builder
from applications.platform_builder.api.register import register_platform_builder_routes


ROOT = Path(__file__).resolve().parents[1]
PREFIX = "/api/platform-builder/v1"


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


def test_sdk_foundation_and_apis():
    sdk = platform_builder.ubf.sdk
    foundation = sdk.foundation()
    assert foundation["ready"] is True
    assert foundation["status"] == "architecture_only"
    assert "define_builder(schema)" in foundation["apis"]

    defined = sdk.define_builder(
        {
            "builder_type": "user",
            "name": "User Builder",
            "version": "0.1.0",
            "components": ["Wizard", "Forms"],
            "validation_rules": ["required_fields"],
        }
    )
    assert defined["builder_type"] == "user"
    assert defined["source"] == "builder_sdk"

    with_steps = sdk.register_steps("user", ["Identity", "Roles", "Summary", "Create"])
    assert with_steps["schema"]["steps"][0] == "Identity"

    with_rules = sdk.attach_validation("user", ["required_fields", "duplicate_detection"])
    assert "duplicate_detection" in with_rules["validation_rules"]

    with_components = sdk.attach_components("user", ["Wizard", "Cards", "Live Validation"])
    assert "Live Validation" in with_components["components"]

    template = sdk.save_template("user", {"name": "User Starter", "role": "admin"})
    assert template["builder_type"] == "user"

    cloned = sdk.clone_builder("user", new_type="user_v2")
    assert cloned["builder_type"] == "user_v2"

    lifecycle = sdk.run_lifecycle("user", {"name": "User Builder"})
    assert lifecycle["status"] == "finished"
    assert lifecycle["phase"] == "finish"
    assert len(lifecycle["history"]) == 8


@pytest.mark.asyncio
async def test_api_sdk(client):
    sdk = await client.get(f"{PREFIX}/ubf/sdk")
    assert sdk.status == 200
    body = await sdk.json()
    assert body["ready"] is True
    assert body["status"] == "architecture_only"

    defined = await client.post(
        f"{PREFIX}/ubf/sdk/define",
        json={
            "builder_type": "automation_ext",
            "name": "Automation Extension Builder",
            "components": ["Wizard"],
        },
    )
    assert defined.status == 201
    assert (await defined.json())["builder_type"] == "automation_ext"


def test_docs_sdk_28_5():
    assert (ROOT / "docs" / "BUILDER_SDK.md").exists()
    assert (ROOT / "knowledge" / "platform_builder" / "sdk" / "README.md").exists()
    docs = (ROOT / "docs" / "BUILDER_SDK.md").read_text()
    for key in ("define_builder", "clone_builder", "run_lifecycle", "minimal"):
        assert key in docs
