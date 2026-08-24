"""Sprint Lawyer 3.6 — detail drawers (related bundles), cross-linking, AI handoff."""

from __future__ import annotations

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


async def _seed_graph(client: TestClient, h: dict[str, str]) -> dict[str, str]:
    """client → case → contract/document/task/hearing + watch item on the case."""
    cl = (await (await client.post(f"{OPS}/clients", json={"name": "Клиент 3.6"}, headers=h)).json())["item"]
    cs = (
        await (
            await client.post(f"{OPS}/cases", json={"title": "Дело 3.6", "client_id": cl["id"]}, headers=h)
        ).json()
    )["item"]
    ct = (
        await (
            await client.post(
                f"{OPS}/contracts",
                json={"title": "Договор 3.6", "client_id": cl["id"], "case_id": cs["id"]},
                headers=h,
            )
        ).json()
    )["item"]
    doc = (
        await (
            await client.post(
                f"{OPS}/documents",
                json={"title": "Документ 3.6", "case_id": cs["id"], "client_id": cl["id"]},
                headers=h,
            )
        ).json()
    )["item"]
    task = (
        await (
            await client.post(
                f"{OPS}/tasks",
                json={"title": "Задача 3.6", "case_id": cs["id"], "client_id": cl["id"], "kind": "deadline"},
                headers=h,
            )
        ).json()
    )["item"]
    hearing = (
        await (
            await client.post(
                f"{OPS}/hearings",
                json={"title": "Заседание 3.6", "case_id": cs["id"], "scheduled_at": "2026-09-01T10:00:00+00:00"},
                headers=h,
            )
        ).json()
    )["item"]
    watch = (
        await (
            await client.post(
                f"{OPS}/monitoring/watchlist",
                json={"identifier": "W-36", "provider": "manual_import", "case_id": cs["id"], "client_id": cl["id"]},
                headers=h,
            )
        ).json()
    )["item"]
    return {
        "client": cl["id"],
        "case": cs["id"],
        "contract": ct["id"],
        "document": doc["id"],
        "task": task["id"],
        "hearing": hearing["id"],
        "watch": watch["id"],
    }


async def test_health_sprint_3_6(client: TestClient):
    body = await (await client.get(f"{OPS}/health")).json()
    assert body["sprint"] == "3.6"


async def test_related_bundle_all_kinds(client: TestClient):
    org = f"org-36-r-{uuid.uuid4().hex[:8]}"
    h = _hdr(org)
    ids = await _seed_graph(client, h)
    for kind in ("client", "case", "contract", "document", "task", "hearing"):
        res = await client.get(f"{OPS}/entities/{kind}/{ids[kind]}/related", headers=h)
        assert res.status == 200, kind
        rel = (await res.json())["related"]
        # every kind must resolve its cross-links through the case/client anchors
        if kind != "case":
            assert any(c["id"] == ids["case"] for c in rel["cases"]), kind
        if kind != "client":
            assert any(c["id"] == ids["client"] for c in rel["clients"]), kind
        if kind != "document":
            assert any(d["id"] == ids["document"] for d in rel["documents"]), kind
        if kind != "hearing":
            assert any(x["id"] == ids["hearing"] for x in rel["hearings"]), kind
        # monitoring items are linked for all kinds
        assert any(w["id"] == ids["watch"] for w in rel["monitoring"]), kind


async def test_related_bundle_case_shows_monitoring_and_changes(client: TestClient):
    org = f"org-36-m-{uuid.uuid4().hex[:8]}"
    h = _hdr(org)
    ids = await _seed_graph(client, h)
    await client.post(
        f"{OPS}/monitoring/watchlist/{ids['watch']}/check",
        json={"imported_state": {"status": "open", "events": [], "documents": []}},
        headers=h,
    )
    await client.post(
        f"{OPS}/monitoring/watchlist/{ids['watch']}/check",
        json={
            "imported_state": {
                "status": "open",
                "events": [{"title": "Новое заседание", "starts_at": "2026-09-02T11:00:00+00:00"}],
                "documents": [],
            }
        },
        headers=h,
    )
    rel = (await (await client.get(f"{OPS}/entities/case/{ids['case']}/related", headers=h)).json())["related"]
    assert rel["monitoring"], "watch item must be linked to the case"
    assert rel["changes"], "detected change must be linked to the case"


async def test_related_bundle_rejects_unknown_kind(client: TestClient):
    org = f"org-36-x-{uuid.uuid4().hex[:8]}"
    res = await client.get(f"{OPS}/entities/calendar/whatever/related", headers=_hdr(org))
    body = await res.json()
    assert body.get("ok") is False
    assert body.get("error") == "validation"


async def test_ai_handoff_with_change_context_and_classification(client: TestClient):
    org = f"org-36-ai-{uuid.uuid4().hex[:8]}"
    h = _hdr(org)
    ids = await _seed_graph(client, h)
    await client.post(
        f"{OPS}/monitoring/watchlist/{ids['watch']}/check",
        json={"imported_state": {"status": "open", "events": [], "documents": []}},
        headers=h,
    )
    await client.post(
        f"{OPS}/monitoring/watchlist/{ids['watch']}/check",
        json={
            "imported_state": {
                "status": "open",
                "events": [{"title": "Заседание", "starts_at": "2026-09-03T09:00:00+00:00"}],
                "documents": [],
            }
        },
        headers=h,
    )
    change_id = (await (await client.get(f"{OPS}/monitoring/changes", headers=h)).json())["items"][0]["id"]

    run = await client.post(
        f"{OPS}/ai/lawyer/run",
        json={"mode": "consult", "prompt": "Оцени риски по изменению", "change_id": change_id},
        headers=h,
    )
    assert run.status == 200
    body = await run.json()
    assert body["ok"] is True
    sources = body["context"]["sources"]
    kinds = {s["kind"] for s in sources}
    assert "monitor_change" in kinds
    assert "case" in kinds  # anchored through the change's case_id

    sc = body["reply"]["source_classification"]
    assert sc["ados_facts"], "ADOS facts must be listed explicitly"
    assert sc["user_provided"], "user prompt must be classified as user-provided"
    assert sc["external_verified"] == [], "no external verified sources may be fabricated"
    assert "DATA GAP" in sc["data_gaps_label_ru"]
    assert any("не подключены" in g or "не проверялись" in g for g in sc["data_gaps"])


async def test_ai_handoff_contract_and_hearing_anchors(client: TestClient):
    org = f"org-36-ch-{uuid.uuid4().hex[:8]}"
    h = _hdr(org)
    ids = await _seed_graph(client, h)
    for key, field in (("contract", "contract_id"), ("hearing", "hearing_id")):
        run = await client.post(
            f"{OPS}/ai/lawyer/run",
            json={"mode": "consult", "prompt": "Анализ", field: ids[key]},
            headers=h,
        )
        body = await run.json()
        assert body["ok"] is True, key
        kinds = {s["kind"] for s in body["context"]["sources"]}
        assert key in kinds, key
        assert "case" in kinds, key


async def test_ai_handoff_data_gap_without_case(client: TestClient):
    org = f"org-36-gap-{uuid.uuid4().hex[:8]}"
    h = _hdr(org)
    run = await client.post(
        f"{OPS}/ai/lawyer/run",
        json={"mode": "consult", "prompt": "Общий вопрос без контекста"},
        headers=h,
    )
    body = await run.json()
    assert body["ok"] is True
    gaps = body["reply"]["source_classification"]["data_gaps"]
    assert any("Дело не привязано" in g for g in gaps)
    assert any("Документы не приложены" in g for g in gaps)


async def test_related_bundle_tenant_isolation(client: TestClient):
    a, b = f"org-36-a-{uuid.uuid4().hex[:6]}", f"org-36-b-{uuid.uuid4().hex[:6]}"
    ids = await _seed_graph(client, _hdr(a))
    res = await client.get(f"{OPS}/entities/case/{ids['case']}/related", headers=_hdr(b))
    body = await res.json()
    assert body.get("ok") is False
    assert body.get("error") == "not_found"


async def test_observer_cannot_run_ai_handoff(client: TestClient):
    org = f"org-36-role-{uuid.uuid4().hex[:6]}"
    res = await client.post(
        f"{OPS}/ai/lawyer/run",
        json={"mode": "consult", "prompt": "Вопрос"},
        headers=_hdr(org, role="observer"),
    )
    body = await res.json()
    assert body.get("ok") is False
    assert body.get("error") == "forbidden"
