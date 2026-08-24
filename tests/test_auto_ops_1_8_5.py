"""Sprint AUTO 1.8.5 — remote HTTPS access, CORS, bind/PORT, health."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from api.bind import resolve_api_host, resolve_api_port
from api.cors_middleware import cors_middleware, origin_allowed
from api.web_static import register_web_static
from applications.auto_enterprise.api.register import register_auto_enterprise_routes
from services.auto_ops import reset_auto_ops_for_tests

OPS = "/api/auto-ops/v1"


@pytest.fixture
def app() -> web.Application:
    application = web.Application(middlewares=[cors_middleware])
    register_auto_enterprise_routes(application)
    return application


@pytest.fixture
async def client(app: web.Application):
    async with TestClient(TestServer(app)) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def reset_ops():
    reset_auto_ops_for_tests()
    yield
    reset_auto_ops_for_tests()


async def test_auto_ops_1_8_5_health_version_and_no_secrets(client: TestClient):
    res = await client.get(f"{OPS}/health")
    assert res.status == 200
    body = await res.json()
    assert body["sprint"] == "AUTO_1.8.5"
    assert body["application_version"] == "1.8.5"
    assert body["status"] == "ok"
    assert body["private"] is True
    assert body["public"] is False
    assert "database" in body
    assert "engine" in body["database"]
    dumped = str(body)
    assert "BOT_TOKEN" not in dumped
    assert "postgresql+" not in dumped
    assert "password" not in dumped.lower()
    assert "Новый бот не строится" in body["telegram"]["message_ru"]


async def test_cors_allows_localhost_and_rejects_star(client: TestClient):
    res = await client.get(
        f"{OPS}/health",
        headers={"Origin": "http://127.0.0.1:5180"},
    )
    assert res.status == 200
    assert res.headers.get("Access-Control-Allow-Origin") == "http://127.0.0.1:5180"
    assert res.headers.get("Access-Control-Allow-Credentials") == "true"

    preflight = await client.options(
        f"{OPS}/health",
        headers={
            "Origin": "http://localhost:5180",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert preflight.status == 204
    assert preflight.headers.get("Access-Control-Allow-Origin") == "http://localhost:5180"

    blocked = await client.get(f"{OPS}/health", headers={"Origin": "https://evil.example"})
    assert blocked.status == 200
    assert "Access-Control-Allow-Origin" not in blocked.headers
    assert not origin_allowed("*")

    lan = await client.get(
        f"{OPS}/health",
        headers={"Origin": "http://192.168.20.103:5180"},
    )
    assert lan.headers.get("Access-Control-Allow-Origin") == "http://192.168.20.103:5180"


async def test_cors_allows_trycloudflare_https(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("ADOS_CORS_ORIGINS", "https://ados-example.vercel.app")
    res = await client.get(
        f"{OPS}/health",
        headers={"Origin": "https://ados-example.vercel.app"},
    )
    assert res.headers.get("Access-Control-Allow-Origin") == "https://ados-example.vercel.app"
    tun = await client.get(
        f"{OPS}/health",
        headers={"Origin": "https://random-name.trycloudflare.com"},
    )
    assert tun.headers.get("Access-Control-Allow-Origin") == "https://random-name.trycloudflare.com"


def test_bind_honors_platform_port(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("API_PORT", raising=False)
    monkeypatch.setenv("PORT", "9099")
    assert resolve_api_port() == 9099
    monkeypatch.setenv("API_PORT", "8080")
    monkeypatch.setenv("PORT", "9099")
    assert resolve_api_port() == 8080
    assert resolve_api_host("127.0.0.1") in {"127.0.0.1", os.environ.get("API_HOST", "127.0.0.1")}


async def test_spa_serves_existing_frontend_build(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    dist = tmp_path / "dist"
    (dist / "assets").mkdir(parents=True)
    (dist / "index.html").write_text("<!doctype html><title>ADOS</title>", encoding="utf-8")
    (dist / "assets" / "app.js").write_text("console.log('ados')", encoding="utf-8")
    monkeypatch.setenv("ADOS_SERVE_WEB", "1")
    monkeypatch.setenv("ADOS_WEB_DIST", str(dist))
    app = web.Application()
    register_auto_enterprise_routes(app)
    register_web_static(app)
    async with TestClient(TestServer(app)) as spa_client:
        root = await spa_client.get("/")
        assert root.status == 200
        assert "ADOS" in await root.text()
        spa = await spa_client.get("/workspace/auto")
        assert spa.status == 200
        assert "ADOS" in await spa.text()
        health = await spa_client.get(f"{OPS}/health")
        assert health.status == 200
        body = await health.json()
        assert body["sprint"] == "AUTO_1.8.5"


def test_vite_dev_server_binds_all_interfaces_and_allows_tunnel_hosts():
    src = (Path(__file__).resolve().parents[1] / "src" / "web" / "vite.config.ts").read_text(
        encoding="utf-8"
    )
    assert 'host: process.env.VITE_DEV_HOST || "0.0.0.0"' in src
    assert '".trycloudflare.com"' in src
    assert 'host: process.env.VITE_DEV_HOST || "127.0.0.1"' not in src
