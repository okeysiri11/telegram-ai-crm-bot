"""Sprint Recruiting 2.10 — candidate identity links without collapsing leads."""

from __future__ import annotations

import asyncio
import uuid

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.recruiting_enterprise.api.register import register_recruiting_enterprise_routes
from services.recruiting_ops import reset_recruiting_ops_for_tests
from services.recruiting_ops.identity import identity_decision

OPS = "/api/recruiting-ops/v1"
PHONE = "37281093104"
EMAIL = "timofiikarpenchuk@gmail.com"


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
def reset_ops():
    reset_recruiting_ops_for_tests()
    yield
    reset_recruiting_ops_for_tests()


def _hdr(org: str, role: str = "recruiter") -> dict[str, str]:
    return {"X-Organization-Id": org, "X-Role": role, "X-Recruiting-Organization-Id": org}


async def _lead(client: TestClient, org: str, **payload: object) -> dict:
    res = await client.post(f"{OPS}/leads", json=payload, headers=_hdr(org))
    assert res.status == 201, await res.text()
    return (await res.json())["item"]


def test_identity_rules_do_not_merge_ambiguous_people():
    assert identity_decision({"email": EMAIL, "phone": PHONE}, {"email": EMAIL, "phone": "+372 810 93104"}) == "match"
    assert identity_decision({"email": EMAIL, "phone": "111"}, {"email": "other@x.com", "phone": "222"}) == "distinct"
    assert identity_decision({"email": EMAIL, "phone": "111"}, {"email": EMAIL, "phone": "222"}) == "ambiguous"
    assert identity_decision({"email": EMAIL, "phone": PHONE}, {"email": "other@x.com", "phone": PHONE}) == "ambiguous"


async def test_a_convert_creates_candidate(client: TestClient):
    org = f"id-a-{uuid.uuid4().hex[:8]}"
    lead = await _lead(client, org, name="Timofii", email=EMAIL, phone=PHONE)
    converted = await client.post(f"{OPS}/leads/{lead['id']}/convert", headers=_hdr(org))
    assert converted.status == 201
    item = (await converted.json())["item"]
    assert item["email"] == EMAIL
    assert lead["id"] in (item.get("lead_ids") or [item.get("lead_id")])


async def test_b_second_lead_same_contact_links_one_candidate(client: TestClient):
    org = f"id-b-{uuid.uuid4().hex[:8]}"
    h = _hdr(org)
    a = await _lead(client, org, name="Timofii A", email=EMAIL, phone=PHONE, utm_source="google", external_id="ref-a")
    b = await _lead(client, org, name="Timofii B", email=EMAIL, phone=PHONE, utm_source="meta", external_id="ref-b")
    first = await client.post(f"{OPS}/leads/{a['id']}/convert", headers=h)
    second = await client.post(f"{OPS}/leads/{b['id']}/convert", headers=h)
    assert first.status == 201
    assert second.status == 200
    cand_a = (await first.json())["item"]
    cand_b = (await second.json())["item"]
    assert cand_a["id"] == cand_b["id"]
    assert len(cand_b.get("applications") or []) == 2
    assert {a["id"], b["id"]} <= set(cand_b.get("lead_ids") or [])
    listed = await (await client.get(f"{OPS}/candidates", headers=h)).json()
    assert len(listed["items"]) == 1
    leads = (await (await client.get(f"{OPS}/leads", headers=h)).json())["items"]
    assert len(leads) == 2
    assert {row["id"] for row in leads} == {a["id"], b["id"]}


async def test_c_same_name_different_contact_is_different_candidate(client: TestClient):
    org = f"id-c-{uuid.uuid4().hex[:8]}"
    h = _hdr(org)
    a = await _lead(client, org, name="Alex", email="a@example.com", phone="37211111111")
    b = await _lead(client, org, name="Alex", email="b@example.com", phone="37222222222")
    ca = await client.post(f"{OPS}/leads/{a['id']}/convert", headers=h)
    cb = await client.post(f"{OPS}/leads/{b['id']}/convert", headers=h)
    assert ca.status == 201
    assert cb.status == 201
    assert (await ca.json())["item"]["id"] != (await cb.json())["item"]["id"]


async def test_d_normalized_phone_formats_match(client: TestClient):
    org = f"id-d-{uuid.uuid4().hex[:8]}"
    h = _hdr(org)
    a = await _lead(client, org, name="Timofii", email=EMAIL, phone="+372 810 93104")
    b = await _lead(client, org, name="Timofii", email=EMAIL, phone="37281093104")
    first = await client.post(f"{OPS}/leads/{a['id']}/convert", headers=h)
    second = await client.post(f"{OPS}/leads/{b['id']}/convert", headers=h)
    assert first.status == 201
    assert second.status == 200
    assert (await first.json())["item"]["id"] == (await second.json())["item"]["id"]


async def test_e_concurrent_conversion_one_candidate(client: TestClient):
    org = f"id-e-{uuid.uuid4().hex[:8]}"
    h = _hdr(org)
    a = await _lead(client, org, name="Timofii", email=EMAIL, phone=PHONE)
    b = await _lead(client, org, name="Timofii", email=EMAIL, phone=PHONE)
    first, second = await asyncio.gather(
        client.post(f"{OPS}/leads/{a['id']}/convert", headers=h),
        client.post(f"{OPS}/leads/{b['id']}/convert", headers=h),
    )
    assert first.status in {200, 201}
    assert second.status in {200, 201}
    ids = {(await first.json())["item"]["id"], (await second.json())["item"]["id"]}
    assert len(ids) == 1
    listed = await (await client.get(f"{OPS}/candidates", headers=h)).json()
    assert len(listed["items"]) == 1
    assert len(listed["items"][0].get("applications") or []) == 2


async def test_f_merge_preserves_application_history(client: TestClient):
    org = f"id-f-{uuid.uuid4().hex[:8]}"
    h = _hdr(org)
    a = await _lead(
        client,
        org,
        name="Timofii",
        email=EMAIL,
        phone=PHONE,
        utm_source="google",
        utm_campaign="brand",
        external_id="app-1",
        campaign_id="camp-1",
    )
    b = await _lead(
        client,
        org,
        name="Timofii",
        email=EMAIL,
        phone=PHONE,
        utm_source="meta",
        utm_campaign="retarget",
        external_id="app-2",
        campaign_id="camp-2",
    )
    await client.post(f"{OPS}/leads/{a['id']}/convert", headers=h)
    linked = await client.post(f"{OPS}/leads/{b['id']}/convert", headers=h)
    cand = (await linked.json())["item"]
    apps = cand.get("applications") or []
    assert len(apps) == 2
    ext = {app.get("external_id") for app in apps}
    utm = {app.get("utm_source") for app in apps}
    assert ext == {"app-1", "app-2"}
    assert utm == {"google", "meta"}
    leads = (await (await client.get(f"{OPS}/leads", headers=h)).json())["items"]
    by_id = {row["id"]: row for row in leads}
    assert by_id[a["id"]]["utm_source"] == "google"
    assert by_id[b["id"]]["utm_source"] == "meta"
    assert by_id[a["id"]]["external_id"] == "app-1"
    assert by_id[b["id"]]["external_id"] == "app-2"
    assert by_id[a["id"]]["id"] != by_id[b["id"]]["id"]
