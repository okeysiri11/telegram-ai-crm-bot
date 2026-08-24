"""
Sprint 47.0 — server-side AI-command scoping (CC-3).

Before this sprint, /management/v1/ai-command/chat trusted whatever role/vertical
the client claimed in the request body (the web frontend hardcoded role: "owner").
cmd_chat now resolves the caller's real active_vertical/active_persona/
authenticated_role from the same server-side vertical_role_registry the Telegram bot
uses, and a real tenant_id from TenantContextService, instead of trusting the client.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from platform_ai_command.api.router import _resolve_server_side_scope, register_ai_command_routes
from services.vertical_role_registry import VerticalSession


@pytest.mark.asyncio
async def test_resolve_server_side_scope_no_telegram_identity():
    ctx = MagicMock(actor_telegram_id=None)
    result = await _resolve_server_side_scope(ctx)
    assert result == (None, None, None, None)


@pytest.mark.asyncio
async def test_resolve_server_side_scope_uses_real_vertical_session(monkeypatch):
    ctx = MagicMock(actor_telegram_id=4700001)
    sess = VerticalSession(
        user_id=4700001,
        authenticated_role="platform_owner",
        active_vertical="auto",
        active_persona="dealer",
    )
    monkeypatch.setattr(
        "services.vertical_role_registry.vertical_role_registry.get",
        MagicMock(return_value=sess),
    )
    monkeypatch.setattr(
        "services.tenant_context.TenantContextService.resolve_for_user",
        AsyncMock(return_value=None),
    )
    active_vertical, active_persona, authenticated_role, tenant_id = await _resolve_server_side_scope(ctx)
    assert active_vertical == "auto"
    assert active_persona == "dealer"
    assert authenticated_role == "platform_owner"
    assert tenant_id is None


@pytest.mark.asyncio
async def test_resolve_server_side_scope_resolves_tenant_id(monkeypatch):
    ctx = MagicMock(actor_telegram_id=4700002)
    monkeypatch.setattr(
        "services.vertical_role_registry.vertical_role_registry.get",
        MagicMock(return_value=VerticalSession(user_id=4700002)),
    )
    tenant_ctx = MagicMock()
    tenant_ctx.tenant_id = "11111111-1111-1111-1111-111111111111"
    monkeypatch.setattr(
        "services.tenant_context.TenantContextService.resolve_for_user",
        AsyncMock(return_value=tenant_ctx),
    )
    _, _, _, tenant_id = await _resolve_server_side_scope(ctx)
    assert tenant_id == "11111111-1111-1111-1111-111111111111"


@pytest.mark.asyncio
async def test_resolve_server_side_scope_survives_lookup_failure(monkeypatch):
    """A DB/lookup failure must not break AI chat — degrade to no server-side scope."""
    ctx = MagicMock(actor_telegram_id=4700003)
    monkeypatch.setattr(
        "services.vertical_role_registry.vertical_role_registry.get",
        MagicMock(side_effect=RuntimeError("boom")),
    )
    monkeypatch.setattr(
        "services.tenant_context.TenantContextService.resolve_for_user",
        AsyncMock(side_effect=RuntimeError("boom")),
    )
    result = await _resolve_server_side_scope(ctx)
    assert result == (None, None, None, None)


@pytest.fixture
def ai_command_app() -> web.Application:
    app = web.Application()
    register_ai_command_routes(app)
    return app


@pytest.mark.asyncio
async def test_cmd_chat_uses_server_resolved_scope_not_client_body(monkeypatch, ai_command_app, auth_headers):
    """The client sends role: "client" and no vertical — the server must still use
    the real, server-side platform_owner/auto/dealer session, not the client claim."""
    sess = VerticalSession(
        user_id=42,
        authenticated_role="platform_owner",
        active_vertical="auto",
        active_persona="dealer",
    )
    monkeypatch.setattr(
        "services.vertical_role_registry.vertical_role_registry.get",
        MagicMock(return_value=sess),
    )
    monkeypatch.setattr(
        "services.tenant_context.TenantContextService.resolve_for_user",
        AsyncMock(return_value=None),
    )
    handle_mock = AsyncMock(return_value={"status": "completed", "reply_ru": "ok", "plan_id": "p1"})
    monkeypatch.setattr("platform_ai_command.core.command_center.ai_command_center.handle", handle_mock)

    async with TestClient(TestServer(ai_command_app)) as client:
        resp = await client.post(
            "/management/v1/ai-command/chat",
            json={"text": "hello", "role": "client", "vertical": "beauty"},
            headers=auth_headers,
        )
        assert resp.status == 201

    assert handle_mock.await_count == 1
    _, kwargs = handle_mock.await_args
    assert kwargs["role"] == "platform_owner"
    assert kwargs["active_vertical"] == "auto"
    assert kwargs["active_persona"] == "dealer"
    assert kwargs["authenticated_role"] == "platform_owner"
