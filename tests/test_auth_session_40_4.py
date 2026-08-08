"""Sprint 40.4 — opaque ISAM bearer must not hard-401 via platform_builder middleware."""

from __future__ import annotations

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.platform_builder.api.middleware import auth_middleware


async def _ok_handler(_request: web.Request) -> web.Response:
    return web.json_response({"ok": True})


@pytest.fixture
def app() -> web.Application:
    application = web.Application(middlewares=[auth_middleware])
    application.router.add_get("/ping", _ok_handler)
    return application


@pytest.fixture
async def client(app: web.Application):
    async with TestClient(TestServer(app)) as test_client:
        yield test_client


@pytest.mark.asyncio
async def test_opaque_isam_bearer_falls_through(client: TestClient):
    resp = await client.get("/ping", headers={"Authorization": "Bearer access_deadbeef"})
    assert resp.status == 200
    assert (await resp.json())["ok"] is True


@pytest.mark.asyncio
async def test_malformed_jwt_still_401(client: TestClient, monkeypatch):
    from platform_identity.identity_service import identity_service as iam

    async def _boom(_request):
        raise Exception("Not enough segments")

    monkeypatch.setattr(iam, "authenticate_request", _boom)
    # Three-segment token shape → treated as JWT → hard 401 on failure
    resp = await client.get(
        "/ping",
        headers={"Authorization": "Bearer aaa.bbb.ccc"},
    )
    assert resp.status == 401
    body = await resp.json()
    assert body.get("error") == "authentication_required"


@pytest.mark.asyncio
async def test_unauthenticated_still_allowed(client: TestClient):
    resp = await client.get("/ping")
    assert resp.status == 200


@pytest.mark.asyncio
async def test_full_app_crm_post_survives_principal_clobber():
    """Vertical middlewares wipe principal; innermost restore must keep CRM POST alive."""
    from api.server import create_app

    application = create_app()
    async with TestClient(TestServer(application)) as test_client:
        headers = {
            "Authorization": "Bearer access_sprint404",
            "Content-Type": "application/json",
        }
        resp = await test_client.post(
            "/api/auto/v1/crm/leads",
            headers=headers,
            json={"title": "40.4", "source": "web", "contact_name": "Auth"},
        )
        assert resp.status == 201, await resp.text()
        body = await resp.json()
        assert body.get("id") or body.get("lead_id") or "title" in body
