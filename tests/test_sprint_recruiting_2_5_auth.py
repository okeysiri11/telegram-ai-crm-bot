"""Sprint Recruiting 2.5 — recruiter API auth (JWT) without weakening HMAC ingest."""

from __future__ import annotations

import hashlib
import hmac
import json
import time
import uuid

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.platform_builder.api.middleware import auth_middleware as platform_builder_auth
from applications.recruiting_enterprise.api.register import register_recruiting_enterprise_routes
from platform_identity.jwt_service import jwt_service
from services.recruiting_ops import reset_recruiting_ops_for_tests
from services.recruiting_ops.ingest_auth import DEV_FALLBACK_SECRET

OPS = "/api/recruiting-ops/v1"
INGEST = f"{OPS}/vanguard/leads"


@pytest.fixture
def app() -> web.Application:
    application = web.Application(middlewares=[platform_builder_auth])
    register_recruiting_enterprise_routes(application)
    return application


@pytest.fixture
async def client(app: web.Application):
    async with TestClient(TestServer(app)) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def reset_ops(monkeypatch):
    monkeypatch.setenv("VANGUARD_INGEST_SECRET", DEV_FALLBACK_SECRET)
    monkeypatch.delenv("ALLOW_HEADER_AUTH", raising=False)
    _reload_security()
    reset_recruiting_ops_for_tests()
    yield
    monkeypatch.delenv("ALLOW_HEADER_AUTH", raising=False)
    _reload_security()
    reset_recruiting_ops_for_tests()


def _reload_security():
    from platform_configuration.configuration_center import configuration_center
    from platform_configuration.env_source import load_environment

    load_environment.cache_clear()
    configuration_center.reload()


def _strict_auth(monkeypatch):
    monkeypatch.setenv("ALLOW_HEADER_AUTH", "false")
    _reload_security()


def _owner_headers(org: str = "ados", extra: dict[str, str] | None = None) -> dict[str, str]:
    jwt_service.reset()
    tokens = jwt_service.issue_tokens(
        subject="owner@demo.corp",
        roles=["owner", "platform_admin"],
        permissions=["read", "write", "admin"],
        extra={"tenant_id": "demo-corp", "email": "owner@demo.corp"},
        session_id=f"sess_{uuid.uuid4().hex[:8]}",
    )
    headers = {
        "Authorization": f"Bearer {tokens.access_token}",
        "X-Organization-Id": org,
        "X-Tenant-Id": org,
        "X-Role": "platform_owner",
    }
    if extra:
        headers.update(extra)
    return headers


def _employee_headers(org: str, role: str = "observer") -> dict[str, str]:
    jwt_service.reset()
    tokens = jwt_service.issue_tokens(
        subject="recruiter@demo.corp",
        roles=["employee"],
        permissions=["read"],
        extra={"email": "recruiter@demo.corp"},
    )
    return {
        "Authorization": f"Bearer {tokens.access_token}",
        "X-Organization-Id": org,
        "X-Role": role,
    }


def _signed(body: dict, *, secret: str = DEV_FALLBACK_SECRET) -> tuple[bytes, dict[str, str]]:
    raw = json.dumps(body, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ts = str(time.time())
    nn = uuid.uuid4().hex
    msg = f"{ts}.{nn}.".encode("utf-8") + raw
    sig = hmac.new(secret.encode("utf-8"), msg, hashlib.sha256).hexdigest()
    return raw, {
        "Content-Type": "application/json",
        "X-Vanguard-Signature": sig,
        "X-Vanguard-Timestamp": ts,
        "X-Vanguard-Nonce": nn,
        "Idempotency-Key": str(uuid.uuid4()),
    }


async def test_authenticated_recruiter_gets_are_200(client: TestClient, monkeypatch):
    _strict_auth(monkeypatch)
    h = _owner_headers()
    for path in (
        "/leads",
        "/candidates",
        "/vacancies",
        "/projects",
        "/projects/vanguard",
        "/dashboard",
        "/analytics",
    ):
        res = await client.get(f"{OPS}{path}", headers=h)
        assert res.status == 200, path


async def test_missing_auth_is_401_not_header_auth_disabled(client: TestClient, monkeypatch):
    _strict_auth(monkeypatch)
    res = await client.get(
        f"{OPS}/leads",
        headers={"X-Organization-Id": "ados", "X-Role": "platform_owner"},
    )
    assert res.status == 401
    body = await res.json()
    assert body["error"] == "authentication_required"
    assert body["error"] != "header_auth_disabled"
    assert "войдите" in body["message_ru"].lower() or "вход" in body["message_ru"].lower()


async def test_invalid_jwt_is_401(client: TestClient, monkeypatch):
    _strict_auth(monkeypatch)
    res = await client.get(
        f"{OPS}/leads",
        headers={
            "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.e30.tampered",
            "X-Organization-Id": "ados",
            "X-Role": "platform_owner",
        },
    )
    assert res.status == 401
    body = await res.json()
    assert body["error"] == "invalid_token"


async def test_observer_cannot_create_lead(client: TestClient, monkeypatch):
    _strict_auth(monkeypatch)
    org = f"rec-obs-{uuid.uuid4().hex[:8]}"
    res = await client.post(
        f"{OPS}/leads",
        json={"name": "Наблюдатель", "email": "obs@example.com"},
        headers=_employee_headers(org, role="observer"),
    )
    assert res.status == 403
    body = await res.json()
    assert body["error"] == "forbidden"


async def test_vanguard_project_filters_leads(client: TestClient, monkeypatch):
    _strict_auth(monkeypatch)
    h = _owner_headers()
    created = await client.post(
        f"{OPS}/leads",
        json={
            "name": "Vanguard Lead",
            "email": "vg@example.com",
            "source": "vanguard-global",
            "project_key": "vanguard",
        },
        headers=h,
    )
    assert created.status == 201
    listed = await client.get(f"{OPS}/leads?project=vanguard", headers=h)
    assert listed.status == 200
    names = [x.get("name") for x in (await listed.json())["items"]]
    assert "Vanguard Lead" in names


async def test_tenant_isolation(client: TestClient, monkeypatch):
    _strict_auth(monkeypatch)
    org_a, org_b = f"org-a-{uuid.uuid4().hex[:6]}", f"org-b-{uuid.uuid4().hex[:6]}"
    created = await client.post(
        f"{OPS}/leads",
        json={"name": "Only A", "email": "a@example.com"},
        headers=_owner_headers(org_a),
    )
    assert created.status == 201
    listed_b = await client.get(f"{OPS}/leads", headers=_owner_headers(org_b))
    assert listed_b.status == 200
    names = [x.get("name") for x in (await listed_b.json())["items"]]
    assert "Only A" not in names


async def test_hmac_ingest_unchanged_without_jwt(client: TestClient, monkeypatch):
    _strict_auth(monkeypatch)
    raw, headers = _signed(
        {
            "first_name": "Ingest",
            "last_name": "Auth",
            "email": "ingest-auth@example.com",
            "source": "vanguard-global",
            "external_id": f"vg-auth-{uuid.uuid4().hex[:8]}",
        }
    )
    res = await client.post(INGEST, data=raw, headers=headers)
    assert res.status == 201
    item = (await res.json())["item"]
    assert item["source"] == "vanguard-global"
    assert item["project_key"] == "vanguard"


async def test_hmac_ingest_still_rejects_missing_signature(client: TestClient, monkeypatch):
    _strict_auth(monkeypatch)
    res = await client.post(
        INGEST,
        data=b'{"email":"x@example.com"}',
        headers={"Content-Type": "application/json"},
    )
    assert res.status == 401
    body = await res.json()
    assert body["error"] == "missing_signature"


async def test_health_remains_public(client: TestClient, monkeypatch):
    _strict_auth(monkeypatch)
    res = await client.get(f"{OPS}/health")
    assert res.status == 200
