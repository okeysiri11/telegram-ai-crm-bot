"""Sprint Lawyer 3.2 — AI Lawyer workspace / Legal Intelligence."""

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


async def test_health_sprint_3_2(client: TestClient):
    res = await client.get(f"{OPS}/health")
    assert res.status == 200
    body = await res.json()
    assert body["sprint"] in {"3.2", "3.3", "3.4", "3.5", "3.6"}
    assert "actions" in body["ai"]


async def test_ai_permissions_observer_forbidden(client: TestClient):
    h = _hdr(f"org-32-obs-{uuid.uuid4().hex[:8]}", "observer")
    res = await client.post(f"{OPS}/ai/analyze", json={"action": "summarize", "text": "hello"}, headers=h)
    assert res.status == 403


async def test_ai_analysis_persist_and_structured(client: TestClient):
    org = f"org-32-an-{uuid.uuid4().hex[:8]}"
    h = _hdr(org)
    text = "Стороны обязаны оплатить до 20.08.2026. Штраф 0.1% в день."
    res = await client.post(
        f"{OPS}/ai/analyze",
        json={"action": "deadlines", "target_type": "text", "text": text, "question": "Найди сроки"},
        headers=h,
    )
    assert res.status == 200
    body = await res.json()
    assert body["ok"] is True
    analysis = body["analysis"]
    assert analysis.get("summary")
    assert "deadlines" in analysis
    assert analysis.get("analysis_id")
    aid = analysis["analysis_id"]
    listed = await client.get(f"{OPS}/ai/analyses", headers=h)
    ids = [x["id"] for x in (await listed.json())["items"]]
    assert aid in ids
    # tenant isolation
    other = _hdr(f"org-32-other-{uuid.uuid4().hex[:8]}")
    listed2 = await client.get(f"{OPS}/ai/analyses", headers=other)
    assert aid not in [x["id"] for x in (await listed2.json())["items"]]


async def test_ai_create_task_and_calendar_from_analysis(client: TestClient):
    org = f"org-32-act-{uuid.uuid4().hex[:8]}"
    h = _hdr(org)
    cl = await client.post(f"{OPS}/clients", json={"name": "Клиент AI"}, headers=h)
    client_id = (await cl.json())["item"]["id"]
    case = await client.post(f"{OPS}/cases", json={"title": "Дело AI", "client_id": client_id}, headers=h)
    case_id = (await case.json())["item"]["id"]
    an = await client.post(
        f"{OPS}/ai/analyze",
        json={
            "action": "deadlines",
            "target_type": "case",
            "target_id": case_id,
            "case_id": case_id,
            "client_id": client_id,
            "text": "Срок ответа: 20.08.2026",
        },
        headers=h,
    )
    aid = (await an.json())["analysis"]["analysis_id"]
    # without confirm — blocked
    blocked = await client.post(
        f"{OPS}/ai/analyses/{aid}/actions",
        json={"action": "create_task", "title": "Срок"},
        headers=h,
    )
    assert blocked.status == 400
    task = await client.post(
        f"{OPS}/ai/analyses/{aid}/actions",
        json={"action": "create_task", "confirm": True, "title": "Срок из AI", "case_id": case_id, "due_at": "2026-08-20T12:00:00+00:00"},
        headers=h,
    )
    assert task.status == 200
    assert (await task.json())["created"]["task"]["id"]
    cal = await client.post(
        f"{OPS}/ai/analyses/{aid}/actions",
        json={"action": "create_calendar", "confirm": True, "date": "2026-08-20", "title": "Срок AI calendar", "case_id": case_id},
        headers=h,
    )
    assert cal.status == 200
    assert (await cal.json())["created"]["event"]["id"]
    act = await client.get(f"{OPS}/activity", headers=h)
    actions = {a["action"] for a in (await act.json())["items"]}
    assert "ai_created_task" in actions
    assert "ai_created_calendar_event" in actions


async def test_ai_lawyer_draft_and_link(client: TestClient):
    org = f"org-32-law-{uuid.uuid4().hex[:8]}"
    h = _hdr(org)
    cl = await client.post(f"{OPS}/clients", json={"name": "ООО Бета"}, headers=h)
    client_id = (await cl.json())["item"]["id"]
    case = await client.post(f"{OPS}/cases", json={"title": "Спор по договору", "client_id": client_id}, headers=h)
    case_id = (await case.json())["item"]["id"]
    ctx = await client.post(
        f"{OPS}/ai/context",
        json={"client_id": client_id, "case_id": case_id},
        headers=h,
    )
    assert ctx.status == 200
    inspector = (await ctx.json())["inspector"]
    assert inspector["case"] == 1
    run = await client.post(
        f"{OPS}/ai/lawyer/run",
        json={
            "mode": "draft_document",
            "prompt": "Подготовь проект претензии",
            "client_id": client_id,
            "case_id": case_id,
            "draft_kind": "claim",
        },
        headers=h,
    )
    assert run.status == 200
    body = await run.json()
    assert body["draft"]["status"] == "ai_draft"
    doc_id = body["draft"]["document_id"]
    edited = await client.post(
        f"{OPS}/ai/drafts/{doc_id}",
        json={"content": body["draft"]["content"] + "\n\nПравка юриста", "confirm_overwrite": True, "status": "in_review"},
        headers=h,
    )
    assert edited.status == 200
    docs = await client.get(f"{OPS}/documents", headers=h)
    assert doc_id in [d["id"] for d in (await docs.json())["items"]]
    related = await client.get(f"{OPS}/entities/case/{case_id}/related", headers=h)
    rel_docs = (await related.json())["related"]["documents"]
    assert any(d["id"] == doc_id for d in rel_docs)


async def test_file_context_no_fake_ocr(client: TestClient):
    org = f"org-32-ocr-{uuid.uuid4().hex[:8]}"
    h = _hdr(org)
    # tiny fake jpeg bytes
    raw = base64.b64encode(b"\xff\xd8\xff\xd9fake").decode()
    res = await client.post(
        f"{OPS}/ai/analyze",
        json={
            "action": "summarize",
            "target_type": "text",
            "filename": "scan.jpg",
            "mime_type": "image/jpeg",
            "file_base64": raw,
            "question": "Кратко объяснить",
        },
        headers=h,
    )
    assert res.status == 200
    missing = (await res.json())["analysis"].get("missing_data") or []
    assert any("vision" in str(x).lower() or "OCR" in str(x) or "изображ" in str(x).lower() for x in missing)


async def test_text_attachment_analysis(client: TestClient):
    org = f"org-32-txt-{uuid.uuid4().hex[:8]}"
    h = _hdr(org)
    raw = base64.b64encode("Договор на услуги. Оплата до 01.09.2026.".encode()).decode()
    res = await client.post(
        f"{OPS}/ai/analyze",
        json={
            "action": "summarize",
            "filename": "note.txt",
            "mime_type": "text/plain",
            "file_base64": raw,
        },
        headers=h,
    )
    assert res.status == 200
    assert (await res.json())["item"]["id"]
