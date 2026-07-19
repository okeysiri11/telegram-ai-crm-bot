"""Tests — Platform SDK (Phase 1)."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiohttp.test_utils import TestClient, TestServer

from platform_sdk.base_vertical import PlatformVertical, ValidationPolicy
from platform_sdk.bootstrap import build_platform_verticals, register_platform_verticals
from platform_sdk.event_provider import EventProvider
from platform_sdk.exceptions import (
    ValidationError,
    VerticalAlreadyRegisteredError,
    VerticalNotFoundError,
)
from platform_sdk.manager_provider import ManagerProvider
from platform_sdk.notification_provider import NotificationProvider
from platform_sdk.validation_provider import ValidationProvider
from platform_sdk.vertical_builder import VerticalBuilder
from platform_sdk.vertical_registry import VerticalRegistry
from platform_sdk.verticals import AgroVertical, AutoVertical, BUILTIN_VERTICALS
from platform_sdk.verticals.agro_vertical import AgroVertical as AgroCls
from platform_sdk.workflow_loader import SdkWorkflowLoader


@pytest.fixture(autouse=True)
def _reset_vertical_registry():
    from platform_sdk.vertical_registry import VerticalRegistry

    VerticalRegistry.reset_singleton()
    yield
    VerticalRegistry.reset_singleton()


@pytest.fixture
def clean_registry():
    VerticalRegistry.reset_singleton()
    registry = VerticalRegistry()
    yield registry
    VerticalRegistry.reset_singleton()


def test_vertical_registry_register_get_list_remove(clean_registry):
    clean_registry.register(AgroVertical)
    assert clean_registry.get("agro") is AgroVertical
    assert "agro" in clean_registry.list_codes()
    assert clean_registry.list()[0]["workflow_name"] == "agro_post_create"
    clean_registry.remove("agro")
    with pytest.raises(VerticalNotFoundError):
        clean_registry.get("agro")


def test_vertical_registry_duplicate_raises(clean_registry):
    clean_registry.register(AgroVertical)
    with pytest.raises(VerticalAlreadyRegisteredError):
        clean_registry.register(AgroVertical)


def test_validation_vin_and_phone():
    assert ValidationProvider.validate_vin("1HGCM82633A004352") == "1HGCM82633A004352"
    with pytest.raises(ValidationError):
        ValidationProvider.validate_vin("BAD", required=True)
    assert ValidationProvider.validate_phone("+380991234567") == "+380991234567"
    with pytest.raises(ValidationError):
        ValidationProvider.validate_phone("123", required=True)


def test_validation_required_fields():
    with pytest.raises(ValidationError):
        ValidationProvider.validate_required({"a": 1}, ["a", "b"])


def test_workflow_loader_finds_definitions():
    loader = SdkWorkflowLoader()
    count = loader.ensure_loaded()
    assert count >= 4
    definition = loader.get_definition("auto_buy")
    assert definition.id == "auto_buy"
    assert loader.get_for_vertical("AGRO") is not None


def test_vertical_builder_wires_providers(clean_registry):
    clean_registry.register(AgroVertical)
    builder = VerticalBuilder(registry=clean_registry)
    vertical = builder.build(AgroVertical)
    assert vertical.context.manager is not None
    assert vertical.context.notifications is not None
    assert vertical.context.validation is not None
    assert vertical.context.events is not None
    assert vertical.context.workflows is not None
    assert clean_registry.get_built("agro") is vertical


def test_builtin_verticals_register(clean_registry):
    for cls in BUILTIN_VERTICALS:
        clean_registry.register(cls)
    assert len(clean_registry.list_codes()) == len(BUILTIN_VERTICALS)


@pytest.mark.asyncio
async def test_manager_provider_resolve_smart():
    provider = ManagerProvider(default_strategy="SMART")
    with patch(
        "services.smart_assignment_service.smart_assignment_service.assign_for_request",
        new=AsyncMock(return_value={"user_id": "u1", "telegram_id": 111}),
    ) as assign:
        mgr = await provider.resolve_manager("agro", {"request_type": "AGRO_GRAIN"})
        assert mgr["telegram_id"] == 111
        assign.assert_awaited_once()


@pytest.mark.asyncio
async def test_notification_provider_created():
    with patch(
        "services.notification_service.notification_service.notify_managers_new_request",
        new=AsyncMock(),
    ) as notify:
        await NotificationProvider.notify_created(
            vertical="agro",
            request_number="AGRO-00001",
            client_name="Test",
        )
        notify.assert_awaited_once()


@pytest.mark.asyncio
async def test_event_provider_publish():
    with patch("platform_sdk.event_provider.publish", new=AsyncMock(return_value={"handlers": 1})) as pub:
        await EventProvider.publish_request_created(
            request_id="1",
            request_number="AGRO-00001",
            vertical="agro",
            request_type="AGRO_REQUEST",
        )
        pub.assert_awaited_once()


@pytest.mark.asyncio
async def test_agro_vertical_create_request(clean_registry):
    clean_registry.register(AgroVertical)
    builder = VerticalBuilder(registry=clean_registry)
    vertical = builder.build(AgroVertical)

    mock_row = MagicMock()
    mock_row.id = "00000000-0000-0000-0000-000000000099"
    mock_row.request_number = "AGRO-00100"
    mock_row.request_type = "AGRO_REQUEST"
    mock_row.status = "NEW"
    mock_row.client_telegram_id = 123
    mock_row.client_first_name = "Client"
    mock_row.client_username = None
    mock_row.description = "wheat"
    mock_row.manager_id = None
    mock_row.created_at = None

    with patch.object(
        vertical.context.manager,
        "resolve_manager",
        new=AsyncMock(return_value={"user_id": "00000000-0000-0000-0000-000000000001", "telegram_id": 999}),
    ), patch(
        "services.request_service.RequestService.persist_crm_request",
        new=AsyncMock(
            return_value={
                "id": mock_row.id,
                "request_number": mock_row.request_number,
                "client_telegram_id": mock_row.client_telegram_id,
                "manager_id": mock_row.manager_id,
            }
        ),
    ), patch.object(
        vertical.context.events,
        "publish_request_created",
        new=AsyncMock(),
    ), patch.object(
        vertical.context.notifications,
        "notify_created",
        new=AsyncMock(),
    ), patch.object(
        vertical.context.workflows,
        "run_post_create",
        new=AsyncMock(),
    ):
        result = await vertical.create_request(
            client_telegram_id=123,
            client_name="Client",
            description="wheat",
        )

    assert result["request_number"] == "AGRO-00100"


@pytest.mark.asyncio
async def test_verticals_api_endpoint(monkeypatch, auth_headers):
    VerticalRegistry.reset_singleton()
    register_platform_verticals()
    from aiohttp import web
    from platform_management.management_router import register_management_routes
    from platform_management.permissions import ManagementRole

    async def _owner(_tid):
        return ManagementRole.OWNER

    monkeypatch.setattr("platform_management.permissions.resolve_role", _owner)

    app = web.Application()
    register_management_routes(app)
    with patch(
        "platform_management.management_service.management_service.log_request",
        new_callable=AsyncMock,
    ):
        async with TestClient(TestServer(app)) as client:
            resp = await client.get("/management/v1/verticals", headers=auth_headers)
            assert resp.status == 200
            body = await resp.json()
            verticals = body["data"]["verticals"]
            assert len(verticals) >= 6
            assert any(v["code"] == "agro" for v in verticals)
    VerticalRegistry.reset_singleton()


def test_auto_vertical_metadata():
    meta = AutoVertical.vertical_metadata()
    assert meta["code"] == "auto"
    assert meta["workflow_name"] == "auto_buy"
