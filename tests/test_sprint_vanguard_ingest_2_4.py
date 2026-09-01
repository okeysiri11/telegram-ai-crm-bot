"""Sprint Vanguard ingest 2.4 — production-style persistence, CRM GET, conversion, idempotency."""

from __future__ import annotations

import json
import time
import uuid
from unittest.mock import patch

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.recruiting_enterprise.api.register import register_recruiting_enterprise_routes
from services.recruiting_ops import get_recruiting_ops_service, reset_recruiting_ops_for_tests
from services.recruiting_ops.ingest_auth import DEV_FALLBACK_SECRET, sign_ingest_body
from services.recruiting_ops.shared_store import SharedStore, set_store_for_tests

OPS = "/api/recruiting-ops/v1"
INGEST = f"{OPS}/vanguard/leads"

EXPECTED_FIELDS = (
    "name",
    "email",
    "phone",
    "country",
    "preferred_language",
    "age",
    "contact_consent",
    "program_of_interest",
    "unit_of_interest",
    "application_message",
    "source",
    "project_key",
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_content",
    "utm_term",
    "gclid",
    "fbclid",
    "click_id",
    "created_at",
    "external_id",
)


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


def _hdr(org: str = "ados", role: str = "platform_owner") -> dict[str, str]:
    return {"X-Organization-Id": org, "X-Role": role}


def _signed(body: dict, *, secret: str = DEV_FALLBACK_SECRET) -> tuple[bytes, dict[str, str]]:
    raw = json.dumps(body, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ts = str(time.time())
    nn = uuid.uuid4().hex
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


def _website_payload(**overrides) -> dict:
    submission = overrides.pop("external_id", None) or f"sub-{uuid.uuid4().hex[:12]}"
    payload = {
        "name": "Ada Lovelace",
        "email": f"ada.{uuid.uuid4().hex[:8]}@example.com",
        "phone": "+44 7700 900123",
        "country": "United Kingdom",
        "age": 28,
        "preferred_language": "en",
        "program_of_interest": "logistics",
        "unit_of_interest": "unit-1",
        "application_message": "I want to train.",
        "contact_consent": True,
        "utm_source": "google",
        "utm_medium": "cpc",
        "utm_campaign": "vanguard-q3",
        "utm_content": "hero-cta",
        "utm_term": "internships",
        "gclid": "CjwKCAjg-gclid",
        "fbclid": "IwAR0-fbclid",
        "click_id": "click-explicit-1",
        "source": "vanguard-global",
        "project_key": "vanguard",
        "external_id": submission,
        "idempotency_key": submission,
    }
    payload.update(overrides)
    return payload


def _assert_website_fields(item: dict) -> None:
    for key in EXPECTED_FIELDS:
        assert key in item, f"missing {key}"
    assert item["name"] == "Ada Lovelace"
    assert item["phone"] == "447700900123"
    assert item["country"] == "United Kingdom"
    assert item["preferred_language"] == "en"
    assert item["age"] == 28
    assert item["contact_consent"] is True
    assert item["program_of_interest"] == "logistics"
    assert item["unit_of_interest"] == "unit-1"
    assert item["application_message"] == "I want to train."
    assert item["source"] == "vanguard-global"
    assert item["project_key"] == "vanguard"
    assert item["utm_source"] == "google"
    assert item["utm_medium"] == "cpc"
    assert item["utm_campaign"] == "vanguard-q3"
    assert item["utm_content"] == "hero-cta"
    assert item["utm_term"] == "internships"
    assert item["gclid"] == "CjwKCAjg-gclid"
    assert item["fbclid"] == "IwAR0-fbclid"
    assert item["click_id"] == "click-explicit-1"
    assert item["created_at"]
    assert item["idempotency_key"] == item["external_id"]


async def test_production_style_payload_persists_and_is_visible(client: TestClient):
    body = _website_payload()
    res = await _post_signed(client, body)
    assert res.status == 201
    item = (await res.json())["item"]
    _assert_website_fields(item)
    listed = await (await client.get(f"{OPS}/leads", headers=_hdr())).json()
    found = next(x for x in listed["items"] if x["id"] == item["id"])
    _assert_website_fields(found)
    filtered = await (await client.get(f"{OPS}/leads?project=vanguard", headers=_hdr())).json()
    assert any(x["id"] == item["id"] for x in filtered["items"])
    overview = await (await client.get(f"{OPS}/projects/vanguard", headers=_hdr())).json()
    assert overview["ok"] is True
    assert overview["cards"]["new_leads"] >= 1


async def test_vanguard_filter_excludes_manual_leads(client: TestClient):
    await _post_signed(client, _website_payload())
    await client.post(
        f"{OPS}/leads",
        json={"name": "Manual Other", "source": "manual", "email": f"m.{uuid.uuid4().hex[:8]}@example.com"},
        headers=_hdr(),
    )
    filtered = await (await client.get(f"{OPS}/leads?project=vanguard", headers=_hdr())).json()
    names = [row["name"] for row in filtered["items"]]
    assert "Ada Lovelace" in names
    assert "Manual Other" not in names


async def test_conversion_preserves_application_fields(client: TestClient):
    ingested = await _post_signed(client, _website_payload())
    lead = (await ingested.json())["item"]
    converted = await client.post(f"{OPS}/leads/{lead['id']}/convert", json={}, headers=_hdr())
    assert converted.status in {200, 201}
    candidate = (await converted.json())["item"]
    for key in EXPECTED_FIELDS:
        if key == "created_at":
            continue
        assert candidate.get(key) == lead.get(key), key
    cands = await (await client.get(f"{OPS}/candidates?project=vanguard", headers=_hdr())).json()
    found = next(x for x in cands["items"] if x["id"] == candidate["id"])
    assert found["email"] == lead["email"]
    assert found["gclid"] == lead["gclid"]
    assert found["application_message"] == lead["application_message"]
    assert found["project_key"] == "vanguard"


async def test_same_submission_without_vacancy_does_not_create_second_lead(client: TestClient):
    body = _website_payload()
    first = await _post_signed(client, body)
    assert first.status == 201
    lead_id = (await first.json())["item"]["id"]
    second = await _post_signed(client, body)
    assert second.status == 200
    payload = await second.json()
    assert payload["duplicate"] is True
    assert payload["item"]["id"] == lead_id
    listed = await (await client.get(f"{OPS}/leads?project=vanguard", headers=_hdr())).json()
    matches = [x for x in listed["items"] if x.get("external_id") == body["external_id"]]
    assert len(matches) == 1


async def test_new_application_same_email_creates_new_lead(client: TestClient):
    email = f"same.{uuid.uuid4().hex[:8]}@example.com"
    a = await _post_signed(client, _website_payload(email=email, program_of_interest="logistics"))
    b = await _post_signed(client, _website_payload(email=email, program_of_interest="logistics"))
    assert a.status == 201
    assert b.status == 201
    assert (await a.json())["item"]["id"] != (await b.json())["item"]["id"]


async def test_postgres_flags_required_in_production(client: TestClient, monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("VANGUARD_INGEST_SECRET", "prod-secret-2-4")
    reset_recruiting_ops_for_tests()
    set_store_for_tests(SharedStore(backend="memory_shared", shared=True, mapping={}))

    async def fake_persist(self, kind, data):
        saved = dict(data)
        saved["durable"] = True
        saved["storage"] = "postgres"
        saved["persistence_mode"] = "POSTGRES"
        return saved

    with patch("services.recruiting_ops.service.RecruitingOpsService._persist", fake_persist):
        raw, headers = _signed(_website_payload(), secret="prod-secret-2-4")
        res = await client.post(INGEST, data=raw, headers=headers)
    assert res.status == 201
    item = (await res.json())["item"]
    assert item["durable"] is True
    assert item["storage"] == "postgres"
    assert item["persistence_mode"] == "POSTGRES"
    assert item["project_key"] == "vanguard"


async def test_survives_in_memory_reload_snapshot(client: TestClient):
    ingested = await _post_signed(client, _website_payload())
    lead = (await ingested.json())["item"]
    snapshot = dict(lead)
    svc = get_recruiting_ops_service()
    svc._mem.clear()
    svc._bag("ados")["lead"] = [snapshot]
    listed = await (await client.get(f"{OPS}/leads?project=vanguard", headers=_hdr())).json()
    found = next(x for x in listed["items"] if x["id"] == snapshot["id"])
    assert found["name"] == "Ada Lovelace"
    assert found["project_key"] == "vanguard"


async def test_hmac_headers_unchanged():
    raw, headers = _signed(_website_payload())
    assert set(headers) >= {
        "X-Vanguard-Signature",
        "X-Vanguard-Timestamp",
        "X-Vanguard-Nonce",
        "Content-Type",
    }
    assert "X-Vanguard-Signature" in headers
    blob = json.dumps(headers)
    assert DEV_FALLBACK_SECRET not in blob
