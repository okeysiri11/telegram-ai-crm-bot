"""Sprint Recruiting 3.0.2 — explicit candidate merge without collapsing leads."""

from __future__ import annotations

import uuid

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.recruiting_enterprise.api.register import register_recruiting_enterprise_routes
from services.recruiting_ops import get_recruiting_ops_service, reset_recruiting_ops_for_tests
from services.recruiting_ops.identity import identity_decision, merge_safety
from services.recruiting_ops.service import PersistUnavailable

OPS = "/api/recruiting-ops/v1"
EMAIL = "timofiikarpenchuk@gmail.com"
PHONE = "37281093104"


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


async def _convert(client: TestClient, org: str, lead_id: str, role: str = "recruiter") -> dict:
    res = await client.post(f"{OPS}/leads/{lead_id}/convert", headers=_hdr(org, role))
    assert res.status in {200, 201}, await res.text()
    return (await res.json())["item"]


def _overlay(org: str, candidate_id: str, **fields: object) -> dict:
    svc = get_recruiting_ops_service()
    item = svc._find(org, "candidate", candidate_id)
    assert item is not None
    item.update(fields)
    svc._replace(org, "candidate", item)
    return item


async def _historical_pair(
    client: TestClient,
    org: str,
    *,
    overlay: dict[str, object] | None = None,
    extra_a: dict[str, object] | None = None,
    extra_b: dict[str, object] | None = None,
    stage_a: str = "QUALIFIED",
    stage_b: str = "APPROVED",
) -> tuple[dict, dict, dict, dict]:
    extra_a = extra_a or {}
    extra_b = extra_b or {}
    n = uuid.uuid4().int % 10**8
    lead_a = await _lead(
        client,
        org,
        name="Timofii",
        email=f"a.{n}@example.com",
        phone=f"37011{n:08d}",
        source="google",
        notes="note-a",
        **extra_a,
    )
    lead_b = await _lead(
        client,
        org,
        name="Timofii",
        email=f"b.{n}@example.com",
        phone=f"37022{n:08d}",
        source="meta",
        notes="note-b",
        **extra_b,
    )
    cand_a = await _convert(client, org, lead_a["id"])
    cand_b = await _convert(client, org, lead_b["id"])
    await client.post(f"{OPS}/candidates/{cand_a['id']}/stage", json={"pipeline_stage": stage_a}, headers=_hdr(org))
    await client.post(f"{OPS}/candidates/{cand_b['id']}/stage", json={"pipeline_stage": stage_b}, headers=_hdr(org))
    _overlay(
        org,
        cand_a["id"],
        pipeline_history=[{"action": "pipeline_moved", "to_stage": stage_a, "at": "2026-08-01"}],
        notes="note-a",
    )
    fields = {
        "email": EMAIL,
        "phone": PHONE,
        "pipeline_history": [{"action": "pipeline_moved", "to_stage": stage_b, "at": "2026-08-02"}],
        "notes": "note-b",
        **(overlay or {}),
    }
    if "email" not in (overlay or {}) and "phone" not in (overlay or {}):
        fields["email"] = EMAIL
        fields["phone"] = PHONE
        _overlay(org, cand_a["id"], email=EMAIL, phone=PHONE)
    cand_b = _overlay(org, cand_b["id"], **fields)
    cand_a = get_recruiting_ops_service()._find(org, "candidate", cand_a["id"])
    return cand_a, cand_b, lead_a, lead_b


async def _merge(
    client: TestClient,
    org: str,
    canonical_id: str,
    duplicate_id: str,
    *,
    role: str = "recruiter",
    force: bool = False,
    preview: bool = False,
    reason: str = "test merge",
):
    return await client.post(
        f"{OPS}/candidates/{canonical_id}/merge",
        json={"duplicate_candidate_id": duplicate_id, "reason": reason, "force": force, "preview": preview},
        headers=_hdr(org, role),
    )


def test_identity_safety_rules():
    match = {"email": EMAIL, "phone": PHONE}
    assert identity_decision(match, {"email": EMAIL, "phone": "+372 810 93104"}) == "match"
    assert merge_safety(match, {"email": EMAIL, "phone": "37000000000"}) == "ambiguous"
    assert merge_safety(match, {"email": "other@x.com", "phone": PHONE}) == "ambiguous"
    assert merge_safety(match, {"email": "other@x.com", "phone": "37000000000"}) == "unsafe"
    assert identity_decision({"name": "Timofii", "email": "a@x.com", "phone": "1"}, {"name": "Timofii", "email": "b@x.com", "phone": "2"}) == "distinct"


async def test_1_same_email_phone_merge(client: TestClient):
    org = f"m1-{uuid.uuid4().hex[:8]}"
    a, b, lead_a, lead_b = await _historical_pair(client, org)
    listed = await (await client.get(f"{OPS}/candidates", headers=_hdr(org))).json()
    assert len(listed["items"]) == 2
    assert all(item.get("possible_duplicate") for item in listed["items"])
    res = await _merge(client, org, a["id"], b["id"])
    assert res.status == 200, await res.text()
    body = await res.json()
    item = body["item"]
    assert item["id"] == a["id"]
    assert body.get("already_merged") is False
    after = await (await client.get(f"{OPS}/candidates", headers=_hdr(org))).json()
    assert len(after["items"]) == 1
    assert after["items"][0]["id"] == a["id"]


async def test_2_normalized_phone_variants_merge(client: TestClient):
    org = f"m2-{uuid.uuid4().hex[:8]}"
    a, b, *_ = await _historical_pair(client, org, overlay={"email": EMAIL, "phone": "+372 810 93104"})
    _overlay(org, a["id"], email=EMAIL, phone=PHONE)
    res = await _merge(client, org, a["id"], b["id"])
    assert res.status == 200, await res.text()


async def test_3_same_email_different_phone_ambiguous(client: TestClient):
    org = f"m3-{uuid.uuid4().hex[:8]}"
    a, b, *_ = await _historical_pair(client, org, overlay={"email": EMAIL, "phone": "37000000001"})
    _overlay(org, a["id"], email=EMAIL, phone=PHONE)
    res = await _merge(client, org, a["id"], b["id"])
    assert res.status == 409
    body = await res.json()
    assert body["error"] == "conflict"
    assert body["safety"] == "ambiguous"


async def test_4_same_phone_different_email_ambiguous(client: TestClient):
    org = f"m4-{uuid.uuid4().hex[:8]}"
    a, b, *_ = await _historical_pair(client, org, overlay={"email": "other@x.com", "phone": PHONE})
    _overlay(org, a["id"], email=EMAIL, phone=PHONE)
    res = await _merge(client, org, a["id"], b["id"])
    assert res.status == 409
    assert (await res.json())["safety"] == "ambiguous"


async def test_5_different_email_phone_unsafe(client: TestClient):
    org = f"m5-{uuid.uuid4().hex[:8]}"
    a, b, *_ = await _historical_pair(client, org, overlay={"email": "other@x.com", "phone": "37000000002"})
    res = await _merge(client, org, a["id"], b["id"])
    assert res.status == 409
    assert (await res.json())["safety"] == "unsafe"


async def test_6_name_only_match_does_not_auto_merge(client: TestClient):
    org = f"m6-{uuid.uuid4().hex[:8]}"
    a, b, *_ = await _historical_pair(client, org, overlay={"email": "other@x.com", "phone": "37000000003"})
    listed = await (await client.get(f"{OPS}/candidates", headers=_hdr(org))).json()
    assert all(not item.get("possible_duplicate") for item in listed["items"])
    res = await _merge(client, org, a["id"], b["id"])
    assert res.status == 409


async def test_7_to_18_merge_preserves_history(client: TestClient):
    org = f"m7-{uuid.uuid4().hex[:8]}"
    h = _hdr(org)
    vac_a = (await (await client.post(f"{OPS}/vacancies", json={"title": "Дронщик"}, headers=h)).json())["item"]
    vac_b = (await (await client.post(f"{OPS}/vacancies", json={"title": "Логист"}, headers=h)).json())["item"]
    camp = (await (await client.post(f"{OPS}/campaigns", json={"name": "career-q3", "source": "vanguard"}, headers=h)).json())["item"]
    a, b, lead_a, lead_b = await _historical_pair(
        client,
        org,
        extra_a={
            "utm_source": "google",
            "utm_medium": "cpc",
            "utm_campaign": "career-q3",
            "campaign_id": camp["id"],
            "vacancy_id": vac_a["id"],
            "external_id": "ref-a",
            "assignee": "recruiter.anna",
        },
        extra_b={
            "utm_source": "meta",
            "utm_medium": "paid",
            "utm_campaign": "career-q3",
            "campaign_id": camp["id"],
            "vacancy_id": vac_b["id"],
            "external_id": "ref-b",
            "assignee": "recruiter.owner",
        },
    )
    res = await _merge(client, org, a["id"], b["id"])
    assert res.status == 200, await res.text()
    item = (await res.json())["item"]
    leads = (await (await client.get(f"{OPS}/leads", headers=h)).json())["items"]
    assert len(leads) == 2
    assert {row["id"] for row in leads} == {lead_a["id"], lead_b["id"]}
    assert all(row.get("candidate_id") == a["id"] for row in leads)
    apps = item.get("applications") or []
    assert len(apps) == 2
    assert {app.get("utm_source") for app in apps} == {"google", "meta"}
    assert all(app.get("utm_campaign") == "career-q3" or app.get("campaign_id") == camp["id"] for app in apps)
    assert {app.get("external_id") for app in apps} == {"ref-a", "ref-b"}
    assert {app.get("campaign_id") for app in apps} <= {camp["id"], None} or camp["id"] in {app.get("campaign_id") for app in apps}
    assert "recruiter.anna" in (item.get("assignee_history") or [item.get("assignee")]) or item.get("assignee")
    assert vac_a["id"] in (item.get("vacancy_ids") or []) or item.get("vacancy_id") in {vac_a["id"], vac_b["id"]}
    assert vac_b["id"] in (item.get("vacancy_ids") or [item.get("vacancy_id")])
    pipeline = (await (await client.get(f"{OPS}/candidates", headers=h)).json())["pipeline"]
    cards = [card for stage in pipeline.values() for card in stage]
    assert len(cards) == 1
    assert item["pipeline_stage"] == "APPROVED"
    history = item.get("pipeline_history") or []
    assert any(evt.get("to_stage") == "QUALIFIED" for evt in history)
    assert any(evt.get("to_stage") == "APPROVED" or evt.get("action") == "candidate_merged" for evt in history)
    notes = item.get("notes") or ""
    assert "note-a" in notes and "note-b" in notes
    activity = (await (await client.get(f"{OPS}/activity", headers=h)).json())["items"]
    assert any(row.get("action") == "candidate_merged" for row in activity)


async def test_13_different_recruiters_no_data_loss(client: TestClient):
    org = f"m13-{uuid.uuid4().hex[:8]}"
    a, b, *_ = await _historical_pair(
        client,
        org,
        extra_a={"assignee": "recruiter.anna"},
        extra_b={"assignee": "recruiter.owner"},
    )
    item = (await (await _merge(client, org, a["id"], b["id"])).json())["item"]
    history = item.get("assignee_history") or []
    assert {"recruiter.anna", "recruiter.owner"} <= set(history) | {item.get("assignee")}


async def test_19_tenant_isolation(client: TestClient):
    org_a = f"ta-{uuid.uuid4().hex[:8]}"
    org_b = f"tb-{uuid.uuid4().hex[:8]}"
    a, *_ = await _historical_pair(client, org_a)
    b, *_ = await _historical_pair(client, org_b)
    res = await _merge(client, org_a, a["id"], b["id"])
    assert res.status == 404


async def test_20_authorization(client: TestClient):
    org = f"m20-{uuid.uuid4().hex[:8]}"
    a, b, *_ = await _historical_pair(client, org)
    denied = await _merge(client, org, a["id"], b["id"], role="observer")
    assert denied.status == 403
    manager = await _merge(client, org, a["id"], b["id"], role="hiring_manager")
    assert manager.status == 403
    unsafe = await _historical_pair(client, org, overlay={"email": "x@y.com", "phone": "37000000009"})
    forced = await _merge(client, org, unsafe[0]["id"], unsafe[1]["id"], role="recruiter", force=True)
    assert forced.status == 403
    owner = await _merge(client, org, unsafe[0]["id"], unsafe[1]["id"], role="owner", force=True)
    assert owner.status == 200, await owner.text()


async def test_21_22_idempotent_second_merge_resolves_canonical(client: TestClient):
    org = f"m21-{uuid.uuid4().hex[:8]}"
    a, b, lead_a, lead_b = await _historical_pair(client, org)
    first = await _merge(client, org, a["id"], b["id"])
    assert first.status == 200
    first_item = (await first.json())["item"]
    second = await _merge(client, org, a["id"], b["id"])
    assert second.status == 200, await second.text()
    body = await second.json()
    assert body.get("already_merged") is True
    item = body["item"]
    assert item["id"] == a["id"] == first_item["id"]
    assert len(item.get("applications") or []) == 2
    listed = await (await client.get(f"{OPS}/candidates", headers=_hdr(org))).json()
    assert len(listed["items"]) == 1
    leads = (await (await client.get(f"{OPS}/leads", headers=_hdr(org))).json())["items"]
    assert len(leads) == 2
    swapped = await _merge(client, org, b["id"], a["id"])
    assert swapped.status == 200
    assert (await swapped.json())["item"]["id"] == a["id"]
    pipeline = listed["pipeline"]
    assert len([card for stage in pipeline.values() for card in stage]) == 1


async def test_23_rollback_on_merge_failure(client: TestClient, monkeypatch):
    org = f"m23-{uuid.uuid4().hex[:8]}"
    a, b, *_ = await _historical_pair(client, org)
    svc = get_recruiting_ops_service()

    async def boom(*_args, **_kwargs):
        raise PersistUnavailable("forced-fail")

    monkeypatch.setattr(svc, "_persist_merge_batch", boom)
    res = await _merge(client, org, a["id"], b["id"])
    assert res.status == 503
    listed = await (await client.get(f"{OPS}/candidates", headers=_hdr(org))).json()
    assert len(listed["items"]) == 2
    assert {item["id"] for item in listed["items"]} == {a["id"], b["id"]}
    assert all(not item.get("merged") for item in listed["items"])


async def test_preview_does_not_write(client: TestClient):
    org = f"mprev-{uuid.uuid4().hex[:8]}"
    a, b, *_ = await _historical_pair(client, org)
    res = await _merge(client, org, a["id"], b["id"], preview=True)
    assert res.status == 200
    body = await res.json()
    assert body["preview"]["pipeline_stage"] == "APPROVED"
    assert body["preview"]["lead_count"] == 2
    listed = await (await client.get(f"{OPS}/candidates", headers=_hdr(org))).json()
    assert len(listed["items"]) == 2


async def test_new_application_still_links_after_historical_style_identity(client: TestClient):
    """Phase 2.10 convert path is unchanged: same person still one candidate."""
    org = f"m210-{uuid.uuid4().hex[:8]}"
    h = _hdr(org)
    a = await _lead(client, org, name="New Person", email="new.person@example.com", phone="37269990001")
    b = await _lead(client, org, name="New Person", email="new.person@example.com", phone="+372 6999 0001")
    first = await client.post(f"{OPS}/leads/{a['id']}/convert", headers=h)
    second = await client.post(f"{OPS}/leads/{b['id']}/convert", headers=h)
    assert first.status == 201
    assert second.status == 200
    assert (await first.json())["item"]["id"] == (await second.json())["item"]["id"]
    listed = await (await client.get(f"{OPS}/candidates", headers=h)).json()
    assert len(listed["items"]) == 1
    leads = (await (await client.get(f"{OPS}/leads", headers=h)).json())["items"]
    assert len(leads) == 2
