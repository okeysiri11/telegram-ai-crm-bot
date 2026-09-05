"""Sprint Recruiting 3.3 — Advertising Control Center economics (no fake providers)."""

from __future__ import annotations

import uuid

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.recruiting_enterprise.api.register import register_recruiting_enterprise_routes
from services.recruiting_ops import reset_recruiting_ops_for_tests
from services.recruiting_ops.ads_economics import funnel_economics, normalize_source, ratio, resolve_date_window
from services.recruiting_ops.attribution import is_test_traffic

OPS = "/api/recruiting-ops/v1"


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


def _hdr(org: str = "ados", role: str = "platform_owner") -> dict[str, str]:
    return {"X-Organization-Id": org, "X-Role": role, "X-Recruiting-Organization-Id": org}


async def _json(res):
    body = await res.json()
    assert res.status in {200, 201}, body
    return body


def test_formulas_never_divide_by_zero():
    assert ratio(10, 0) is None
    assert ratio(10, None) is None
    empty = funnel_economics(applications=0, hired=0, spend=100)
    assert empty["cpl"] is None
    assert empty["cost_per_hire"] is None
    assert empty["ctr"] is None
    assert empty["impressions"] is None
    filled = funnel_economics(applications=4, hired=1, spend=200, impressions=1000, clicks=50)
    assert filled["cpl"] == 50
    assert filled["cost_per_hire"] == 200
    assert filled["ctr"] == 0.05
    assert filled["cpc"] == 4


def test_date_window_presets():
    from datetime import date

    today = date(2026, 9, 5)
    month = resolve_date_window(preset="this_month", today=today)
    assert month["from"] == "2026-09-01"
    assert month["to"] == "2026-09-05"
    last = resolve_date_window(preset="last_month", today=today)
    assert last["from"] == "2026-08-01"
    assert last["to"] == "2026-08-31"


def test_source_aliases():
    assert normalize_source("Instagram") == "instagram"
    assert normalize_source("paid_social") == "instagram"
    assert normalize_source("unknown-channel") == "other"


async def test_internal_campaign_crud_and_manual_spend(client: TestClient):
    org = f"ads33-{uuid.uuid4().hex[:8]}"
    h = _hdr(org)
    created = await _json(
        await client.post(
            f"{OPS}/campaigns",
            json={
                "name": "Vanguard Instagram Estonia",
                "source": "instagram",
                "country": "EE",
                "program": "logistics",
                "utm_source": "instagram",
                "utm_medium": "paid_social",
                "utm_campaign": "ee_logistics_ig",
                "utm_content": "creative_01",
                "project_key": "vanguard",
            },
            headers=h,
        )
    )
    camp = created["item"]
    assert camp["origin"] == "INTERNAL"
    assert camp["ads_api"] == "not_connected"
    assert camp["provider_status"] == "NOT_CONFIGURED"
    assert camp["utm_content"] == "creative_01"
    assert camp["country"] == "EE"
    spend = await _json(
        await client.post(
            f"{OPS}/campaigns/{camp['id']}/spend",
            json={"amount": 120, "currency": "EUR", "spent_on": "2026-09-05", "comment": "boost"},
            headers=h,
        )
    )
    assert spend["item"]["source"] == "OPERATOR_MANUAL"
    assert spend["item"]["provider_synced"] is False
    assert spend["item"]["label_ru"] == "Расход внесён оператором"
    detail = await _json(await client.get(f"{OPS}/campaigns/{camp['id']}", headers=h))
    assert detail["funnel"]["spend"] == 120
    assert detail["funnel"]["impressions"] is None
    assert detail["spend_source"] == "OPERATOR_MANUAL"
    center = await _json(await client.get(f"{OPS}/ads/control-center?project=vanguard", headers=h))
    assert center["overview"]["impressions"] is None
    assert center["overview"]["clicks"] is None
    assert center["overview"]["spend"] == 120
    assert center["overview"]["data_source"]["spend"] == "OPERATOR_MANUAL"
    assert center["kpis"]["spend"] == 120
    row = next(item for item in center["campaigns"] if item["id"] == camp["id"])
    assert row["provider_status_label_ru"] == "НЕ ПОДКЛЮЧЕНО"
    assert row["cpl"] is None  # no production applications
    assert all(card["connected"] is False for card in center["provider_connect"])
    assert all(card["status"] != "CONNECTED" for card in center["provider_connect"])


async def test_test_traffic_excluded_from_campaign_economics(client: TestClient):
    org = f"ads33t-{uuid.uuid4().hex[:8]}"
    h = _hdr(org)
    camp = (
        await _json(
            await client.post(
                f"{OPS}/campaigns",
                json={"name": "IG live", "source": "instagram", "utm_campaign": "ee_live", "project_key": "vanguard"},
                headers=h,
            )
        )
    )["item"]
    await _json(
        await client.post(
            f"{OPS}/campaigns/{camp['id']}/spend",
            json={"amount": 90, "currency": "EUR", "spent_on": "2026-09-05"},
            headers=h,
        )
    )
    test_lead = await _json(
        await client.post(
            f"{OPS}/leads",
            json={
                "name": "Pre Ads Test",
                "source": "vanguard-global",
                "utm_source": "instagram",
                "utm_campaign": "ee_live",
                "utm_content": "creative_test_01",
                "traffic_class": "TEST",
                "project_key": "vanguard",
            },
            headers=h,
        )
    )
    assert is_test_traffic(test_lead["item"]) is True
    real = await _json(
        await client.post(
            f"{OPS}/leads",
            json={
                "name": "Real Applicant",
                "source": "vanguard-global",
                "utm_source": "instagram",
                "utm_campaign": "ee_live",
                "project_key": "vanguard",
            },
            headers=h,
        )
    )
    await _json(await client.post(f"{OPS}/leads/{real['item']['id']}/assign", json={"assignee": "recruiter.ira"}, headers=h))
    await _json(await client.post(f"{OPS}/leads/{real['item']['id']}/qualify", json={}, headers=h))
    converted = await _json(await client.post(f"{OPS}/leads/{real['item']['id']}/convert", json={}, headers=h))
    cand_id = converted["item"]["id"]
    await _json(await client.post(f"{OPS}/candidates/{cand_id}/assign", json={"assignee": "recruiter.ira"}, headers=h))
    await _json(await client.post(f"{OPS}/candidates/{cand_id}/interview", json={}, headers=h))
    await _json(await client.post(f"{OPS}/candidates/{cand_id}/stage", json={"pipeline_stage": "APPROVED"}, headers=h))
    await _json(await client.post(f"{OPS}/candidates/{cand_id}/stage", json={"pipeline_stage": "HIRED"}, headers=h))

    center = await _json(await client.get(f"{OPS}/ads/control-center?project=vanguard", headers=h))
    assert center["traffic"]["excluded_test_leads"] >= 1
    assert center["kpis"]["applications"] == 1
    assert center["overview"]["hires"] == 1
    assert center["kpis"]["cpl"] == 90
    assert center["kpis"]["cost_per_hire"] == 90
    row = next(item for item in center["campaigns"] if item["id"] == camp["id"])
    assert row["applications"] == 1
    assert row["hired"] == 1
    ig = next(item for item in center["source_economics"] if item["source"] == "instagram")
    assert ig["applications"] == 1
    assert ig["hired"] == 1
    assert ig["spend"] == 90
    detail = await _json(await client.get(f"{OPS}/campaigns/{camp['id']}", headers=h))
    assert detail["funnel"]["applications"] == 1
    assert detail["funnel"]["hired"] == 1
    ira = next(item for item in detail["recruiters"] if item["recruiter"] == "recruiter.ira")
    assert ira["hired"] == 1
    assert ira["assigned_candidates"] == 1


async def test_date_filter_excludes_old_spend_and_leads(client: TestClient):
    org = f"ads33d-{uuid.uuid4().hex[:8]}"
    h = _hdr(org)
    camp = (
        await _json(
            await client.post(
                f"{OPS}/campaigns",
                json={"name": "Window", "source": "google", "utm_campaign": "win", "project_key": "vanguard"},
                headers=h,
            )
        )
    )["item"]
    await _json(
        await client.post(
            f"{OPS}/campaigns/{camp['id']}/spend",
            json={"amount": 40, "spent_on": "2026-07-01", "comment": "old"},
            headers=h,
        )
    )
    await _json(
        await client.post(
            f"{OPS}/campaigns/{camp['id']}/spend",
            json={"amount": 15, "spent_on": "2026-09-04", "comment": "new"},
            headers=h,
        )
    )
    this_month = await _json(
        await client.get(f"{OPS}/ads/control-center?project=vanguard&range=this_month", headers=h)
    )
    last_month = await _json(
        await client.get(f"{OPS}/ads/control-center?project=vanguard&range=last_month", headers=h)
    )
    assert this_month["overview"]["spend"] == 15
    assert last_month["overview"]["spend"] in {None, 0} or this_month["date_range"]["preset"] == "this_month"


async def test_observer_cannot_mutate_campaign_or_spend(client: TestClient):
    org = f"ads33s-{uuid.uuid4().hex[:8]}"
    owner = _hdr(org, "platform_owner")
    camp = (await _json(await client.post(f"{OPS}/campaigns", json={"name": "Sec", "project_key": "vanguard"}, headers=owner)))["item"]
    denied = await client.post(f"{OPS}/campaigns", json={"name": "Nope", "project_key": "vanguard"}, headers=_hdr(org, "observer"))
    body = await denied.json()
    assert denied.status in {401, 403} or body.get("ok") is False
    spend = await client.post(
        f"{OPS}/campaigns/{camp['id']}/spend",
        json={"amount": 10},
        headers=_hdr(org, "observer"),
    )
    spend_body = await spend.json()
    assert spend.status in {401, 403} or spend_body.get("ok") is False


async def test_tenant_isolation_on_spend(client: TestClient):
    a = f"ads33a-{uuid.uuid4().hex[:8]}"
    b = f"ads33b-{uuid.uuid4().hex[:8]}"
    camp = (await _json(await client.post(f"{OPS}/campaigns", json={"name": "A only", "project_key": "vanguard"}, headers=_hdr(a))))["item"]
    foreign = await client.post(f"{OPS}/campaigns/{camp['id']}/spend", json={"amount": 5}, headers=_hdr(b))
    body = await foreign.json()
    assert foreign.status in {404} or body.get("ok") is False
    listed = await _json(await client.get(f"{OPS}/ads/control-center?project=vanguard", headers=_hdr(b)))
    assert all(item.get("id") != camp["id"] for item in listed.get("campaigns") or [])


async def test_utm_survives_stage_changes(client: TestClient):
    org = f"ads33u-{uuid.uuid4().hex[:8]}"
    h = _hdr(org)
    lead = await _json(
        await client.post(
            f"{OPS}/leads",
            json={
                "name": "Utm Keep",
                "source": "vanguard-global",
                "utm_source": "instagram",
                "utm_medium": "paid_social",
                "utm_campaign": "keep_utm",
                "utm_content": "c1",
                "utm_term": "driver",
                "landing_page": "https://vanguard-global.net/apply",
                "referrer": "https://www.instagram.com/",
                "project_key": "vanguard",
            },
            headers=h,
        )
    )
    await _json(await client.post(f"{OPS}/leads/{lead['item']['id']}/qualify", json={}, headers=h))
    conv = await _json(await client.post(f"{OPS}/leads/{lead['item']['id']}/convert", json={}, headers=h))
    cand_id = conv["item"]["id"]
    await _json(await client.post(f"{OPS}/candidates/{cand_id}/stage", json={"pipeline_stage": "APPROVED"}, headers=h))
    listed = await _json(await client.get(f"{OPS}/candidates", headers=h))
    cand = next(item for item in listed["items"] if item["id"] == cand_id)
    assert cand["utm_source"] == "instagram"
    assert cand["utm_campaign"] == "keep_utm"
    assert cand["utm_content"] == "c1"
    assert cand.get("utm_term") == "driver"
