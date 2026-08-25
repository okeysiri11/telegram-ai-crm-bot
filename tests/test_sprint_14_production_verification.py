"""Sprint 14 — production runtime hardening (auth fail-closed, city SPA, persistence)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from api.web_static import prefers_html, register_web_static
from applications.auto_marketplace.integrations.platform_bridge import (
    _environment_is_production,
    platform_bridge,
)

ROOT = Path(__file__).resolve().parents[1]


def test_render_blueprint_is_the_production_path():
    blueprint = (ROOT / "render.yaml").read_text(encoding="utf-8")
    assert "ados-web" in blueprint
    assert "ados-postgres" in blueprint
    assert "ados-redis" in blueprint
    assert "autoDeployTrigger: checksPass" in blueprint
    assert "Dockerfile.web" in blueprint
    preview = (ROOT / "scripts" / "start_public_host.py").read_text(encoding="utf-8")
    assert "NOT production" in preview
    assert "trycloudflare" in preview.lower() or "quick tunnel" in preview.lower() or "PREVIEW" in preview


@pytest.mark.asyncio
async def test_unverified_bearer_rejected_in_production(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    assert _environment_is_production() is True
    principal = await platform_bridge.authenticate_request("Bearer not-a-real-token")
    assert principal is None


@pytest.mark.asyncio
async def test_dev_bearer_still_accepted_outside_production(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "development")
    principal = await platform_bridge.authenticate_request("Bearer test")
    assert principal is not None
    assert principal.get("authenticated") is True


def test_prefers_html_browser_vs_api():
    class _Req:
        def __init__(self, accept: str) -> None:
            self.headers = {"Accept": accept}

    assert prefers_html(_Req("text/html,application/xhtml+xml;q=0.9")) is True
    assert prefers_html(_Req("application/json")) is False
    assert prefers_html(_Req("application/json, text/html")) is False
    assert prefers_html(_Req("*/*")) is False


@pytest.mark.asyncio
async def test_city_html_navigation_serves_spa(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    dist = tmp_path / "dist"
    (dist / "assets").mkdir(parents=True)
    (dist / "index.html").write_text("<!doctype html><title>ADOS City</title>", encoding="utf-8")
    monkeypatch.setenv("ADOS_SERVE_WEB", "1")
    monkeypatch.setenv("ADOS_WEB_DIST", str(dist))

    async def city_api(_request: web.Request) -> web.Response:
        return web.json_response({"error": "Authentication required"}, status=401)

    app = web.Application()
    app.router.add_get("/city", city_api)
    register_web_static(app)
    async with TestClient(TestServer(app)) as client:
        html = await client.get(
            "/city",
            headers={"Accept": "text/html,application/xhtml+xml;q=0.9"},
        )
        assert html.status == 200
        assert "ADOS City" in await html.text()
        api = await client.get("/city", headers={"Accept": "application/json"})
        assert api.status == 401
        body = await api.json()
        assert body["error"] == "Authentication required"


def test_production_vite_config_does_not_default_to_localhost_services():
    src = (ROOT / "src" / "web" / "src" / "config" / "webConfig.ts").read_text(encoding="utf-8")
    assert 'import.meta.env.PROD ? ""' in src
    assert 'n8nUrl: import.meta.env.VITE_N8N_URL || "http://localhost:5678"' not in src
