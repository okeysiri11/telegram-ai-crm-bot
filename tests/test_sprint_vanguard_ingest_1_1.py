"""Sprint Recruiting 1.1 — signed Vanguard ingest + production fail-closed persistence."""

from __future__ import annotations

import json
import time
import uuid
from unittest.mock import AsyncMock, patch

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.recruiting_enterprise.api.register import register_recruiting_enterprise_routes
from services.recruiting_ops import reset_recruiting_ops_for_tests
from services.recruiting_ops.ingest_auth import DEV_FALLBACK_SECRET, sign_ingest_body
from services.recruiting_ops.shared_store import SharedStore, set_store_for_tests
from services.recruiting_ops.service import PersistUnavailable

OPS = "/api/recruiting-ops/v1"
INGEST = f"{OPS}/vanguard/leads"


@pytest.fixture
def app() -> web.Application:
    application = web.Application()
    register_recruiting_enterprise_routes(application)
    return application


@pytest.fixture
async def client(app: web.Application):
    async with TestClient(TestServer(app)) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def reset_ops(monkeypatch):
    monkeypatch.delenv("ENVIRONMENT", raising=False)
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("VANGUARD_INGEST_SECRET", DEV_FALLBACK_SECRET)
    reset_recruiting_ops_for_tests()
    yield
    reset_recruiting_ops_for_tests()


def _signed(body: dict, *, secret: str = DEV_FALLBACK_SECRET, timestamp: str | None = None, nonce: str | None = None) -> tuple[bytes, dict[str, str]]:
    raw = json.dumps(body, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ts = timestamp if timestamp is not None else str(time.time())
    nn = nonce or uuid.uuid4().hex
    sig = sign_ingest_body(body=raw, timestamp=ts, nonce=nn, secret=secret)
    return raw, {
        "Content-Type": "application/json",
        "X-Vanguard-Signature": sig,
        "X-Vanguard-Timestamp": ts,
        "X-Vanguard-Nonce": nn,
    }


async def _post_signed(client: TestClient, body: dict, **sign_kw):
    raw, headers = _signed(body, **sign_kw)
    return await client.post(INGEST, data=raw, headers=headers)


async def test_valid_signed_request_accepted(client: TestClient):
    res = await _post_signed(
        client,
        {
            "first_name": "Анна",
            "email": f"anna.{uuid.uuid4().hex[:8]}@example.com",
            "source": "vanguard",
            "vacancy_id": "vac-ops",
            "external_id": f"vg-ok-{uuid.uuid4().hex[:8]}",
            "utm_source": "vanguard",
            "utm_campaign": "career",
        },
    )
    assert res.status == 201
    payload = await res.json()
    assert payload["ok"] is True
    assert payload["item"]["source"] == "vanguard"
    assert payload["item"]["name"] == "Анна"


async def test_missing_signature_rejected(client: TestClient):
    res = await client.post(
        INGEST,
        json={"first_name": "Анна", "email": "a@example.com"},
        headers={"Content-Type": "application/json"},
    )
    assert res.status == 401
    body = await res.json()
    assert body["error"] == "missing_signature"
    assert body["ok"] is False


async def test_bad_signature_rejected(client: TestClient):
    raw, headers = _signed({"first_name": "Анна", "email": "a@example.com"})
    headers["X-Vanguard-Signature"] = "deadbeef"
    res = await client.post(INGEST, data=raw, headers=headers)
    assert res.status == 401
    assert (await res.json())["error"] == "bad_signature"


async def test_expired_signature_rejected(client: TestClient):
    raw, headers = _signed(
        {"first_name": "Анна", "email": "a@example.com"},
        timestamp=str(time.time() - 10_000),
    )
    res = await client.post(INGEST, data=raw, headers=headers)
    assert res.status == 401
    assert (await res.json())["error"] == "expired_signature"


async def test_replayed_nonce_rejected(client: TestClient):
    nonce = f"nonce-{uuid.uuid4().hex}"
    body = {"first_name": "Replay", "email": f"replay.{uuid.uuid4().hex[:8]}@example.com", "vacancy_id": "vac-r"}
    first = await _post_signed(client, body, nonce=nonce)
    assert first.status == 201
    second = await _post_signed(client, body, nonce=nonce)
    assert second.status == 401
    assert (await second.json())["error"] == "bad_signature"


async def test_malformed_lead_rejected(client: TestClient):
    res = await _post_signed(client, {"email": "no-name@example.com"})
    assert res.status == 400
    assert (await res.json())["error"] == "validation"
    res2 = await _post_signed(client, {"first_name": "ТолькоИмя"})
    assert res2.status == 400


async def test_valid_lead_persisted_with_attribution_and_activity(client: TestClient):
    org = "ados"
    res = await _post_signed(
        client,
        {
            "first_name": "E2E_TEST",
            "email": f"e2e.{uuid.uuid4().hex[:8]}@example.com",
            "phone": "+380500000001",
            "source": "vanguard",
            "vacancy_id": "vac-frontend",
            "external_id": f"vg-attr-{uuid.uuid4().hex[:8]}",
            "utm_source": "vanguard",
            "utm_medium": "website",
            "utm_campaign": "career-q3",
        },
    )
    assert res.status == 201
    item = (await res.json())["item"]
    assert item["external_id"].startswith("vg-attr-")
    assert item["vacancy_id"] == "vac-frontend"
    assert item["utm_source"] == "vanguard"
    assert item["utm_campaign"] == "career-q3"
    listed = await client.get(f"{OPS}/leads", headers={"X-Organization-Id": org, "X-Role": "platform_owner"})
    names = [x["name"] for x in (await listed.json())["items"]]
    assert "E2E_TEST" in names
    activity = await (await client.get(f"{OPS}/activity", headers={"X-Organization-Id": org, "X-Role": "platform_owner"})).json()
    actions = {a["action"] for a in activity["items"]}
    assert "lead_created" in actions
    assert "vanguard_lead_ingested" in actions


async def test_duplicate_submit_handled(client: TestClient):
    body = {
        "first_name": "Дубль",
        "email": f"dup.{uuid.uuid4().hex[:8]}@example.com",
        "source": "vanguard",
        "vacancy_id": "vac-same",
        "external_id": f"vg-dup-{uuid.uuid4().hex[:8]}",
    }
    first = await _post_signed(client, body)
    assert first.status == 201
    lead_id = (await first.json())["item"]["id"]
    second = await _post_signed(client, body)
    assert second.status == 200
    payload = await second.json()
    assert payload["duplicate"] is True
    assert payload["item"]["id"] == lead_id


async def test_different_vacancy_allowed(client: TestClient):
    base = {
        "first_name": "Мульти",
        "email": f"multi.{uuid.uuid4().hex[:8]}@example.com",
        "source": "vanguard",
        "external_id": f"vg-multi-{uuid.uuid4().hex[:8]}",
    }
    a = await _post_signed(client, {**base, "vacancy_id": "vac-a"})
    b = await _post_signed(client, {**base, "vacancy_id": "vac-b"})
    assert a.status == 201
    assert b.status == 201
    id_a = (await a.json())["item"]["id"]
    id_b = (await b.json())["item"]["id"]
    assert id_a != id_b


async def test_production_ingest_fails_closed_when_storage_unavailable(client: TestClient, monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("VANGUARD_INGEST_SECRET", "prod-secret-value")
    reset_recruiting_ops_for_tests()
    set_store_for_tests(SharedStore(backend="memory_shared", shared=True, mapping={}))
    raw, headers = _signed(
        {
            "first_name": "ProdFail",
            "email": "prod@example.com",
            "source": "vanguard",
            "external_id": "vg-prod-fail",
        },
        secret="prod-secret-value",
    )
    with patch(
        "services.recruiting_ops.service.RecruitingOpsService._persist",
        new_callable=AsyncMock,
        side_effect=PersistUnavailable("postgres down"),
    ):
        res = await client.post(INGEST, data=raw, headers=headers)
    assert res.status == 503
    payload = await res.json()
    assert payload["ok"] is False
    assert payload["error"] == "storage_unavailable"
    listed = await client.get(
        f"{OPS}/leads",
        headers={"X-Organization-Id": "ados", "X-Role": "platform_owner"},
    )
    names = [x["name"] for x in (await listed.json())["items"]]
    assert "ProdFail" not in names


async def test_production_without_secret_rejects_ingest(client: TestClient, monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.delenv("VANGUARD_INGEST_SECRET", raising=False)
    reset_recruiting_ops_for_tests()
    raw, headers = _signed({"first_name": "X", "email": "x@example.com"})
    res = await client.post(INGEST, data=raw, headers=headers)
    assert res.status == 503
    assert (await res.json())["error"] == "ingest_not_configured"


async def test_contract_does_not_expose_secret(client: TestClient):
    contract = await (await client.get(f"{OPS}/vanguard/contract")).json()
    blob = json.dumps(contract)
    assert DEV_FALLBACK_SECRET not in blob
    assert "VANGUARD_INGEST_SECRET" in blob
    assert contract["inbound"]["secret_frontend_exposure"] is False
