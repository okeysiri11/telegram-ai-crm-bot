"""Sprint Vanguard ingest 2.2 — persist candidate + marketing attribution on HMAC ingest."""

from __future__ import annotations

import json
import time
import uuid

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.recruiting_enterprise.api.register import register_recruiting_enterprise_routes
from services.recruiting_ops import get_recruiting_ops_service, reset_recruiting_ops_for_tests
from services.recruiting_ops.ingest_auth import DEV_FALLBACK_SECRET, sign_ingest_body
from services.recruiting_ops.ingest_fields import parse_application_fields, parse_age, parse_contact_consent
from services.recruiting_ops.whatsapp_ops import phones_match

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


def _hdr(org: str = "ados", role: str = "platform_owner") -> dict[str, str]:
    return {"X-Organization-Id": org, "X-Role": role}


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


def _vanguard_application(**overrides) -> dict:
    payload = {
        "name": "Мария Вангард",
        "email": f"maria.{uuid.uuid4().hex[:8]}@example.com",
        "phone": "+380 50 111 22 33",
        "country": "UA",
        "age": 24,
        "preferred_language": "uk",
        "program_of_interest": "deck",
        "unit_of_interest": "fleet-a",
        "application_message": "Ready to join",
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
        "external_id": f"vg-app-{uuid.uuid4().hex[:10]}",
        "vacancy_id": "vac-deck",
    }
    payload.update(overrides)
    return payload


def test_parse_age_bounds():
    assert parse_age(None, present=False) is None
    assert parse_age(18, present=True) == 18
    assert parse_age(99, present=True) == 99
    with pytest.raises(Exception):
        parse_age(17, present=True)
    with pytest.raises(Exception):
        parse_age(100, present=True)


def test_parse_contact_consent_never_defaults_true():
    assert parse_contact_consent({}) is None
    assert parse_contact_consent({"contact_consent": False}) is False
    assert parse_contact_consent({"contact_consent": True}) is True
    fields, err = parse_application_fields({"phone": "+380501112233"})
    assert err is None
    assert fields["contact_consent"] is None
    assert fields["contact_consent"] is not True


async def test_age_contact_consent_phone_and_attribution_persist(client: TestClient):
    body = _vanguard_application()
    res = await _post_signed(client, body)
    assert res.status == 201
    item = (await res.json())["item"]
    assert item["age"] == 24
    assert item["contact_consent"] is True
    assert item["phone"] == "380501112233"
    assert item["utm_source"] == "google"
    assert item["utm_medium"] == "cpc"
    assert item["utm_campaign"] == "vanguard-q3"
    assert item["utm_content"] == "hero-cta"
    assert item["utm_term"] == "internships"
    assert item["gclid"] == "CjwKCAjg-gclid"
    assert item["fbclid"] == "IwAR0-fbclid"
    assert item["click_id"] == "click-explicit-1"
    assert item["source"] == "vanguard-global"
    assert item["project_key"] == "vanguard"
    assert phones_match(item["phone"], "+380501112233")


async def test_contact_consent_false_is_preserved(client: TestClient):
    res = await _post_signed(client, _vanguard_application(contact_consent=False, age=22))
    assert res.status == 201
    item = (await res.json())["item"]
    assert item["contact_consent"] is False
    assert item["contact_consent"] is not True


async def test_omitted_age_and_consent_are_optional(client: TestClient):
    body = _vanguard_application()
    body.pop("age")
    body.pop("contact_consent")
    res = await _post_signed(client, body)
    assert res.status == 201
    item = (await res.json())["item"]
    assert item.get("age") is None
    assert item.get("contact_consent") is None
    assert item.get("contact_consent") is not True


async def test_underage_rejected(client: TestClient):
    res = await _post_signed(client, _vanguard_application(age=17))
    assert res.status == 400
    payload = await res.json()
    assert payload["ok"] is False
    assert payload["error"] == "validation"


async def test_gclid_fbclid_and_click_id_stored_separately(client: TestClient):
    res = await _post_signed(
        client,
        _vanguard_application(gclid="G-ONLY", fbclid="F-ONLY", click_id="C-ONLY"),
    )
    item = (await res.json())["item"]
    assert item["gclid"] == "G-ONLY"
    assert item["fbclid"] == "F-ONLY"
    assert item["click_id"] == "C-ONLY"
    assert item["gclid"] != item["click_id"]
    assert item["fbclid"] != item["click_id"]


async def test_hmac_valid_and_invalid_signature(client: TestClient):
    body = _vanguard_application()
    ok = await _post_signed(client, body)
    assert ok.status == 201
    raw, headers = _signed(_vanguard_application())
    headers["X-Vanguard-Signature"] = "deadbeef" * 4
    bad = await client.post(INGEST, data=raw, headers=headers)
    assert bad.status == 401
    assert (await bad.json())["error"] == "bad_signature"


async def test_duplicate_does_not_create_second_lead(client: TestClient):
    body = _vanguard_application()
    first = await _post_signed(client, body)
    assert first.status == 201
    lead_id = (await first.json())["item"]["id"]
    second = await _post_signed(client, body)
    assert second.status == 200
    payload = await second.json()
    assert payload["duplicate"] is True
    assert payload["item"]["id"] == lead_id
    listed = await (await client.get(f"{OPS}/leads", headers=_hdr())).json()
    matches = [x for x in listed["items"] if x.get("external_id") == body["external_id"]]
    assert len(matches) == 1


async def test_new_application_still_creates_lead(client: TestClient):
    a = await _post_signed(client, _vanguard_application())
    b = await _post_signed(client, _vanguard_application())
    assert a.status == 201
    assert b.status == 201
    assert (await a.json())["item"]["id"] != (await b.json())["item"]["id"]


async def test_old_records_without_new_fields_still_load(client: TestClient):
    svc = get_recruiting_ops_service()
    org = "ados"
    await svc.ensure_hydrated(org)
    legacy_id = str(uuid.uuid4())
    svc._bag(org)["lead"].insert(
        0,
        {
            "id": legacy_id,
            "organization_id": org,
            "name": "Исторический лид",
            "status": "new",
            "source": "vanguard",
            "email": "old@example.com",
        },
    )
    listed = await client.get(f"{OPS}/leads", headers=_hdr())
    assert listed.status == 200
    found = next(x for x in (await listed.json())["items"] if x["id"] == legacy_id)
    assert found["name"] == "Исторический лид"
    assert "age" not in found
    assert "contact_consent" not in found
    assert "gclid" not in found
    assert "fbclid" not in found


async def test_recruiting_api_returns_persisted_metadata(client: TestClient):
    body = _vanguard_application(contact_consent=False, age=31)
    ingested = await _post_signed(client, body)
    assert ingested.status == 201
    lead_id = (await ingested.json())["item"]["id"]
    listed = await (await client.get(f"{OPS}/leads", headers=_hdr())).json()
    lead = next(x for x in listed["items"] if x["id"] == lead_id)
    assert lead["phone"] == "380501112233"
    assert lead["age"] == 31
    assert lead["contact_consent"] is False
    assert lead["source"] == "vanguard-global"
    assert lead["project_key"] == "vanguard"
    assert lead["utm_source"] == "google"
    assert lead["utm_medium"] == "cpc"
    assert lead["utm_campaign"] == "vanguard-q3"
    assert lead["utm_content"] == "hero-cta"
    assert lead["utm_term"] == "internships"
    assert lead["gclid"] == "CjwKCAjg-gclid"
    assert lead["fbclid"] == "IwAR0-fbclid"
    converted = await client.post(f"{OPS}/leads/{lead_id}/convert", json={}, headers=_hdr())
    assert converted.status in {200, 201}
    candidate = (await converted.json())["item"]
    assert candidate["phone"] == "380501112233"
    assert candidate["age"] == 31
    assert candidate["contact_consent"] is False
    assert candidate["gclid"] == "CjwKCAjg-gclid"
    assert candidate["fbclid"] == "IwAR0-fbclid"
    assert candidate["utm_content"] == "hero-cta"
    cands = await (await client.get(f"{OPS}/candidates", headers=_hdr())).json()
    found = next(x for x in cands["items"] if x["id"] == candidate["id"])
    assert found["age"] == 31
    assert found["contact_consent"] is False


async def test_contract_lists_new_optional_fields_without_secret(client: TestClient):
    contract = await (await client.get(f"{OPS}/vanguard/contract")).json()
    optional = contract["inbound"]["optional"]
    for field in ("age", "contact_consent", "gclid", "fbclid", "click_id", "utm_content", "utm_term"):
        assert field in optional
    blob = json.dumps(contract)
    assert DEV_FALLBACK_SECRET not in blob
    assert contract["inbound"]["headers"] == [
        "X-Vanguard-Signature",
        "X-Vanguard-Timestamp",
        "X-Vanguard-Nonce",
    ]
    assert contract["inbound"]["signature_message"] == "{timestamp}.{nonce}.{raw_body}"
