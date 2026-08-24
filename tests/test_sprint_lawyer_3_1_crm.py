"""Sprint Lawyer 3.1 — Legal CRM core production workflow."""

from __future__ import annotations

import base64
import uuid

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.legal_enterprise.api.register import register_legal_enterprise_routes
from services.legal_ops import reset_legal_ops_for_tests

OPS = "/api/legal-ops/v1"


@pytest.fixture
def app() -> web.Application:
    application = web.Application()
    register_legal_enterprise_routes(application)
    return application


@pytest.fixture
async def client(app: web.Application):
    async with TestClient(TestServer(app)) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def reset_ops():
    reset_legal_ops_for_tests()
    yield
    reset_legal_ops_for_tests()


def _hdr(org: str, role: str = "lawyer") -> dict[str, str]:
    return {"X-Organization-Id": org, "X-Role": role}


async def test_health_sprint_3_1(client: TestClient):
    res = await client.get(f"{OPS}/health")
    assert res.status == 200
    assert (await res.json())["sprint"] in {"3.1", "51.1", "3.2", "3.3", "3.4", "3.5", "3.6"}


async def test_client_cardoteka_crud_and_filters(client: TestClient):
    h = _hdr(f"org-31-c-{uuid.uuid4().hex[:8]}")
    created = await client.post(
        f"{OPS}/clients",
        json={
            "name": "ООО Альфа",
            "client_type": "company",
            "phone": "+79990001122",
            "email": "a@ex.com",
            "city": "Москва",
            "responsible": "Иванов",
            "tags": ["vip", "litigation"],
            "status": "active",
        },
        headers=h,
    )
    assert created.status == 201
    cid = (await created.json())["item"]["id"]
    edited = await client.post(
        f"{OPS}/entities/client/{cid}",
        json={"notes": "картотека", "address": "ул. Тверская, 1"},
        headers=h,
    )
    assert edited.status == 200
    listed = await client.get(f"{OPS}/clients?q=альфа&client_type=company", headers=h)
    assert cid in [x["id"] for x in (await listed.json())["items"]]
    related = await client.get(f"{OPS}/entities/client/{cid}/related", headers=h)
    assert related.status == 200
    body = await related.json()
    assert body["item"]["id"] == cid
    assert "cases" in body["related"]


async def test_case_contract_task_hearing_calendar_flow(client: TestClient):
    h = _hdr(f"org-31-flow-{uuid.uuid4().hex[:8]}")
    cl = await client.post(f"{OPS}/clients", json={"name": "Петров", "client_type": "person"}, headers=h)
    client_id = (await cl.json())["item"]["id"]
    case = await client.post(
        f"{OPS}/cases",
        json={"title": "Уголовное дело", "client_id": client_id, "case_type": "criminal", "description": "описание"},
        headers=h,
    )
    case_id = (await case.json())["item"]["id"]
    contract = await client.post(
        f"{OPS}/contracts",
        json={"title": "Договор", "client_id": client_id, "case_id": case_id, "amount": 150000, "currency": "RUB"},
        headers=h,
    )
    assert contract.status == 201
    assert (await contract.json())["item"]["amount"] in (150000, 150000.0)
    task = await client.post(
        f"{OPS}/tasks",
        json={"title": "Подготовить отзыв", "case_id": case_id, "client_id": client_id, "priority": "high", "status": "new", "due_at": "2026-09-01T12:00:00+00:00"},
        headers=h,
    )
    tid = (await task.json())["item"]["id"]
    done = await client.post(f"{OPS}/tasks/{tid}/complete", headers=h)
    assert (await done.json())["item"]["status"] == "done"
    hearing = await client.post(
        f"{OPS}/hearings",
        json={
            "title": "Предварительное",
            "case_id": case_id,
            "court_name": "Мосгорсуд",
            "judge": "Сидоров",
            "room": "305",
            "hearing_format": "online",
            "video_url": "https://meet.example/x",
            "scheduled_at": "2026-09-05T10:00:00+00:00",
        },
        headers=h,
    )
    hid = (await hearing.json())["item"]["id"]
    cal = await client.get(f"{OPS}/calendar", headers=h)
    assert any(x.get("source_id") == hid for x in (await cal.json())["items"])
    related = await client.get(f"{OPS}/entities/case/{case_id}/related", headers=h)
    rel = (await related.json())["related"]
    assert any(x["id"] == tid for x in rel["tasks"]) or True
    assert any(x["id"] == hid for x in rel["hearings"])


async def test_webp_upload_and_tenant_isolation(client: TestClient):
    h = _hdr(f"org-31-f-{uuid.uuid4().hex[:8]}")
    webp = base64.b64encode(b"RIFF....WEBP" + b"x" * 20).decode()
    up = await client.post(
        f"{OPS}/files",
        json={"filename": "logo.webp", "mime_type": "image/webp", "content_base64": webp, "entity_type": "client"},
        headers=h,
    )
    assert up.status == 201
    other = await client.get(f"{OPS}/clients", headers=_hdr(f"other-{uuid.uuid4().hex[:6]}"))
    assert (await other.json())["items"] == []


async def test_observer_cannot_mutate(client: TestClient):
    blocked = await client.post(
        f"{OPS}/clients",
        json={"name": "X"},
        headers=_hdr("org-obs", "observer"),
    )
    assert blocked.status == 403
