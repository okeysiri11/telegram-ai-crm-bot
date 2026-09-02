"""Sprint Recruiting 2.8 — durable CRM mutations and convert idempotency."""

from __future__ import annotations

import asyncio
import uuid

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.recruiting_enterprise.api.register import register_recruiting_enterprise_routes
from applications.recruiting_enterprise.config import DEFAULT_CONFIG
from services.recruiting_ops import reset_recruiting_ops_for_tests

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


def _hdr(org: str, role: str = "recruiter") -> dict[str, str]:
    return {
        "X-Organization-Id": org,
        "X-Tenant-Id": org,
        "X-Recruiting-Organization-Id": org,
        "X-Role": role,
    }


async def _create_lead(client: TestClient, org: str, *, name: str, email: str, phone: str, role: str = "recruiter") -> dict:
    res = await client.post(
        f"{OPS}/leads",
        json={"name": name, "email": email, "phone": phone, "source": "manual"},
        headers=_hdr(org, role),
    )
    assert res.status == 201, await res.text()
    return (await res.json())["item"]


async def _lead(client: TestClient, org: str, lead_id: str) -> dict:
    listed = await client.get(f"{OPS}/leads", headers=_hdr(org, "platform_owner"))
    assert listed.status == 200
    items = (await listed.json())["items"]
    return next(item for item in items if item["id"] == lead_id)


async def test_lead_status_persists_and_blocks_direct_convert(client: TestClient):
    org = f"crm-status-{uuid.uuid4().hex[:8]}"
    h = _hdr(org)
    lead = await _create_lead(client, org, name="Статус", email="status@example.com", phone="+380501000001")
    lead_id = lead["id"]
    assert lead["status"] == "new"

    qualified = await client.post(f"{OPS}/leads/{lead_id}/status", json={"status": "qualified"}, headers=h)
    assert qualified.status == 200
    assert (await qualified.json())["item"]["status"] == "qualified"
    assert (await _lead(client, org, lead_id))["status"] == "qualified"

    lost = await client.post(f"{OPS}/leads/{lead_id}/status", json={"status": "lost"}, headers=h)
    assert lost.status == 200
    assert (await lost.json())["item"]["status"] == "lost"
    assert (await _lead(client, org, lead_id))["status"] == "lost"

    reopened = await client.post(f"{OPS}/leads/{lead_id}/status", json={"status": "new"}, headers=h)
    assert reopened.status == 200
    assert (await _lead(client, org, lead_id))["status"] == "new"

    blocked = await client.post(f"{OPS}/leads/{lead_id}/status", json={"status": "converted"}, headers=h)
    assert blocked.status == 400
    body = await blocked.json()
    assert body["error"] == "validation"
    assert (await _lead(client, org, lead_id))["status"] == "new"


async def test_recruiter_assignment_persists(client: TestClient):
    org = f"crm-assign-{uuid.uuid4().hex[:8]}"
    h = _hdr(org)
    lead = await _create_lead(client, org, name="Назначение", email="assign@example.com", phone="+380501000002")
    res = await client.post(f"{OPS}/leads/{lead['id']}/assign", json={"assignee": "recruiter.ira"}, headers=h)
    assert res.status == 200
    assert (await res.json())["item"]["assignee"] == "recruiter.ira"
    assert (await _lead(client, org, lead["id"]))["assignee"] == "recruiter.ira"


async def test_note_persists_and_appends(client: TestClient):
    org = f"crm-note-{uuid.uuid4().hex[:8]}"
    h = _hdr(org)
    lead = await _create_lead(client, org, name="Заметка", email="note@example.com", phone="+380501000003")
    first = await client.post(f"{OPS}/leads/{lead['id']}/notes", json={"notes": "Первый контакт"}, headers=h)
    assert first.status == 200
    assert "Первый контакт" in ((await first.json())["item"].get("notes") or "")
    second = await client.post(f"{OPS}/leads/{lead['id']}/notes", json={"notes": "Договорились созвониться"}, headers=h)
    assert second.status == 200
    notes = (await _lead(client, org, lead["id"])).get("notes") or ""
    assert "Первый контакт" in notes
    assert "Договорились созвониться" in notes


async def test_vacancy_crud_and_assignment(client: TestClient):
    org = f"crm-vac-{uuid.uuid4().hex[:8]}"
    h = _hdr(org)
    created = await client.post(
        f"{OPS}/vacancies",
        json={"title": "Логист Vanguard", "department": "Ops", "location": "Remote"},
        headers=h,
    )
    assert created.status == 201
    vacancy = (await created.json())["item"]
    vacancy_id = vacancy["id"]
    assert vacancy["title"] == "Логист Vanguard"
    assert vacancy["status"] == "open"

    listed = await client.get(f"{OPS}/vacancies", headers=h)
    assert listed.status == 200
    assert any(item["id"] == vacancy_id for item in (await listed.json())["items"])

    updated = await client.post(
        f"{OPS}/vacancies/{vacancy_id}",
        json={"title": "Старший логист", "status": "closed", "location": "Kyiv"},
        headers=h,
    )
    assert updated.status == 200
    item = (await updated.json())["item"]
    assert item["title"] == "Старший логист"
    assert item["status"] == "closed"
    assert item["location"] == "Kyiv"

    again = await client.get(f"{OPS}/vacancies", headers=h)
    stored = next(v for v in (await again.json())["items"] if v["id"] == vacancy_id)
    assert stored["title"] == "Старший логист"
    assert stored["status"] == "closed"

    lead = await _create_lead(client, org, name="Вакансия", email="vac@example.com", phone="+380501000004")
    assigned = await client.post(
        f"{OPS}/leads/{lead['id']}/vacancy",
        json={"vacancy_id": vacancy_id},
        headers=h,
    )
    assert assigned.status == 200
    payload = (await assigned.json())["item"]
    assert payload["vacancy_id"] == vacancy_id
    persisted = await _lead(client, org, lead["id"])
    assert persisted["vacancy_id"] == vacancy_id
    assert "логист" in (persisted.get("vacancy") or "").lower()

    missing = await client.post(
        f"{OPS}/leads/{lead['id']}/vacancy",
        json={"vacancy_id": "vac-missing"},
        headers=h,
    )
    assert missing.status == 404


async def test_lead_to_candidate_conversion_and_idempotency(client: TestClient):
    org = f"crm-conv-{uuid.uuid4().hex[:8]}"
    h = _hdr(org)
    lead = await _create_lead(client, org, name="Конверсия", email="conv@example.com", phone="+380501000005")
    lead_id = lead["id"]

    first = await client.post(f"{OPS}/leads/{lead_id}/convert", headers=h)
    assert first.status == 201
    first_body = await first.json()
    candidate = first_body["item"]
    candidate_id = candidate["id"]
    assert candidate["lead_id"] == lead_id
    assert first_body.get("already_converted") is not True

    stored_lead = await _lead(client, org, lead_id)
    assert stored_lead["status"] == "converted"
    assert stored_lead["candidate_id"] == candidate_id

    second = await client.post(f"{OPS}/leads/{lead_id}/convert", headers=h)
    assert second.status == 200
    second_body = await second.json()
    assert second_body["item"]["id"] == candidate_id
    assert second_body.get("already_converted") or second_body.get("duplicate")

    listed = await client.get(f"{OPS}/candidates", headers=h)
    assert listed.status == 200
    same_lead = [c for c in (await listed.json())["items"] if c.get("lead_id") == lead_id]
    assert len(same_lead) == 1
    assert same_lead[0]["id"] == candidate_id

    blocked = await client.post(f"{OPS}/leads/{lead_id}/status", json={"status": "lost"}, headers=h)
    assert blocked.status == 400
    assert (await _lead(client, org, lead_id))["status"] == "converted"


async def test_concurrent_convert_does_not_create_second_candidate(client: TestClient):
    org = f"crm-race-{uuid.uuid4().hex[:8]}"
    h = _hdr(org)
    lead = await _create_lead(client, org, name="Гонка", email="race@example.com", phone="+380501000006")
    lead_id = lead["id"]

    first, second = await asyncio.gather(
        client.post(f"{OPS}/leads/{lead_id}/convert", headers=h),
        client.post(f"{OPS}/leads/{lead_id}/convert", headers=h),
    )
    assert first.status in {200, 201}
    assert second.status in {200, 201}
    ids = {(await first.json())["item"]["id"], (await second.json())["item"]["id"]}
    assert len(ids) == 1

    listed = await client.get(f"{OPS}/candidates", headers=h)
    same_lead = [c for c in (await listed.json())["items"] if c.get("lead_id") == lead_id]
    assert len(same_lead) == 1


async def test_independent_leads_same_email_phone_convert_separately(client: TestClient):
    org = f"crm-twin-{uuid.uuid4().hex[:8]}"
    h = _hdr(org)
    email = "twins@example.com"
    phone = "+380501000007"
    first = await _create_lead(client, org, name="Первый близнец", email=email, phone=phone)
    second = await _create_lead(client, org, name="Второй близнец", email=email, phone=phone)
    assert first["id"] != second["id"]

    conv1 = await client.post(f"{OPS}/leads/{first['id']}/convert", headers=h)
    conv2 = await client.post(f"{OPS}/leads/{second['id']}/convert", headers=h)
    assert conv1.status == 201
    assert conv2.status == 201
    cand1 = (await conv1.json())["item"]
    cand2 = (await conv2.json())["item"]
    assert cand1["id"] != cand2["id"]
    assert cand1["lead_id"] == first["id"]
    assert cand2["lead_id"] == second["id"]

    listed = await client.get(f"{OPS}/candidates", headers=h)
    items = (await listed.json())["items"]
    assert {c["id"] for c in items if c.get("email") == email} == {cand1["id"], cand2["id"]}
    assert (await _lead(client, org, first["id"]))["candidate_id"] == cand1["id"]
    assert (await _lead(client, org, second["id"]))["candidate_id"] == cand2["id"]


async def test_candidate_pipeline_transitions_persist(client: TestClient):
    org = f"crm-pipe-{uuid.uuid4().hex[:8]}"
    h = _hdr(org)
    lead = await _create_lead(client, org, name="Воронка", email="pipe@example.com", phone="+380501000008")
    converted = await client.post(f"{OPS}/leads/{lead['id']}/convert", headers=h)
    candidate_id = (await converted.json())["item"]["id"]

    moved = await client.post(
        f"{OPS}/candidates/{candidate_id}/stage",
        json={"pipeline_stage": "INTERVIEW"},
        headers=h,
    )
    assert moved.status == 200
    assert (await moved.json())["item"]["pipeline_stage"] == "INTERVIEW"

    listed = await client.get(f"{OPS}/candidates", headers=h)
    body = await listed.json()
    stored = next(c for c in body["items"] if c["id"] == candidate_id)
    assert stored["pipeline_stage"] == "INTERVIEW"
    assert any(c["id"] == candidate_id for c in body["pipeline"]["INTERVIEW"])

    again = await client.post(
        f"{OPS}/candidates/{candidate_id}/stage",
        json={"pipeline_stage": "APPROVED"},
        headers=h,
    )
    assert again.status == 200
    refreshed = await client.get(f"{OPS}/candidates", headers=h)
    refreshed_body = await refreshed.json()
    stored = next(c for c in refreshed_body["items"] if c["id"] == candidate_id)
    assert stored["pipeline_stage"] == "APPROVED"
    assert any(c["id"] == candidate_id for c in refreshed_body["pipeline"]["APPROVED"])


async def test_authorization_observer_and_hiring_manager(client: TestClient):
    org = f"crm-rbac-{uuid.uuid4().hex[:8]}"
    owner = _hdr(org, "platform_owner")
    observer = _hdr(org, "observer")
    manager = _hdr(org, "hiring_manager")

    denied_create = await client.post(
        f"{OPS}/leads",
        json={"name": "Наблюдатель", "email": "obs@example.com", "phone": "+380501000009"},
        headers=observer,
    )
    assert denied_create.status == 403

    lead = await _create_lead(client, org, name="RBAC", email="rbac@example.com", phone="+380501000010", role="recruiter")
    lead_id = lead["id"]

    assert (await client.post(f"{OPS}/leads/{lead_id}/notes", json={"notes": "нет"}, headers=observer)).status == 403
    assert (await client.post(f"{OPS}/leads/{lead_id}/status", json={"status": "lost"}, headers=observer)).status == 403
    assert (await client.post(f"{OPS}/leads/{lead_id}/convert", headers=observer)).status == 403
    assert (await client.post(f"{OPS}/vacancies", json={"title": "Нет"}, headers=observer)).status == 403

    vac = await client.post(f"{OPS}/vacancies", json={"title": "Менеджер может"}, headers=manager)
    assert vac.status == 201
    qualified = await client.post(f"{OPS}/leads/{lead_id}/qualify", headers=manager)
    assert qualified.status == 200
    denied_convert = await client.post(f"{OPS}/leads/{lead_id}/convert", headers=manager)
    assert denied_convert.status == 403
    body = await denied_convert.json()
    assert body["error"] == "forbidden"

    converted = await client.post(f"{OPS}/leads/{lead_id}/convert", headers=_hdr(org, "recruiter"))
    assert converted.status == 201
    listed = await client.get(f"{OPS}/leads", headers=owner)
    assert listed.status == 200


async def test_production_relative_api_routing_contract():
    assert DEFAULT_CONFIG.api_prefix == "/api/recruiting-ops/v1"
    assert not DEFAULT_CONFIG.api_prefix.startswith("http")
    assert "localhost" not in DEFAULT_CONFIG.api_prefix
    assert ":8080" not in DEFAULT_CONFIG.api_prefix
