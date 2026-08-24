"""AGRO 2.1 — Counterparty 360 / CRM / deals / settlements. Extends agro-ops."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.agro_enterprise.api.register import register_agro_enterprise_routes
from services.agro_ops import reset_agro_ops_for_tests

OPS = "/api/agro-ops/v1"


@pytest.fixture
def app() -> web.Application:
    application = web.Application()
    register_agro_enterprise_routes(application)
    return application


@pytest.fixture
async def client(app: web.Application):
    async with TestClient(TestServer(app)) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def reset_ops():
    reset_agro_ops_for_tests()
    yield
    reset_agro_ops_for_tests()


def _hdr(org: str, role: str = "agro_director") -> dict[str, str]:
    return {"X-Organization-Id": org, "X-Role": role}


async def test_health_keeps_2_0_and_adds_crm_version(client: TestClient):
    body = await (await client.get(f"{OPS}/health")).json()
    assert body["sprint"] == "agro-2.0"
    assert body["ux_version"] == "AGRO_2_0"
    assert body["command_center"] == "AGRO_2_0"
    assert body["crm_version"] == "AGRO_2_1"
    cats = body["catalogs"]
    assert any(t["id"] == "producer" for t in cats["counterparty_types"])
    assert any(t["id"] == "awaiting_contract" for t in cats["deal_statuses"])


async def test_counterparty_360_roles_contacts_settlement(client: TestClient):
    org = f"org-a21-{uuid.uuid4().hex[:8]}"
    h = _hdr(org)
    created = await client.post(
        f"{OPS}/entities/counterparty",
        json={"name": "ООО Агро Юг", "types": ["supplier", "buyer", "elevator"], "city": "Одесса", "phone": "+380501111111", "edrpou": "12345678"},
        headers=h,
    )
    assert created.status == 201
    cp = (await created.json())["item"]
    assert set(cp["types"]) == {"supplier", "buyer", "elevator"}
    c1 = await client.post(f"{OPS}/entities/contact", json={"full_name": "Иван Директор", "position": "Директор", "phone": "+380501111112", "counterparty_id": cp["id"]}, headers=h)
    c2 = await client.post(f"{OPS}/entities/contact", json={"full_name": "Мария Бухгалтер", "position": "Бухгалтер", "email": "acc@agroyug.test", "counterparty_id": cp["id"]}, headers=h)
    assert c1.status == 201 and c2.status == 201
    deal = await (
        await client.post(
            f"{OPS}/entities/deal",
            json={"title": "Пшеница", "counterparty_id": cp["id"], "crop": "Пшеница", "side": "sell", "quantity": 100, "price": 10000, "currency": "UAH"},
            headers=h,
        )
    ).json()
    did = deal["item"]["id"]
    assert deal["item"]["amount"] == 1000000
    pay = await client.post(
        f"{OPS}/entities/payment",
        json={"title": "Часть 1", "amount": 300000, "currency": "UAH", "deal_id": did, "counterparty_id": cp["id"], "status": "paid", "direction": "in"},
        headers=h,
    )
    assert pay.status == 201
    card = await (await client.get(f"{OPS}/crm/counterparty/{cp['id']}", headers=h)).json()
    assert card["ok"] is True
    assert card["item"]["name"] == "ООО Агро Юг"
    assert "supplier" in card["item"]["types"]
    crops = {c["crop"]: c for c in card["crops"]}
    assert crops["Пшеница"]["sells"] is True
    settle = card["settlement"]["receivable"]
    assert settle.get("UAH") == 700000
    assert "EUR" not in settle or settle.get("EUR") is None
    d360 = await (await client.get(f"{OPS}/crm/deal/{did}", headers=h)).json()
    assert d360["item"]["paid"] == 300000
    assert d360["item"]["remaining"] == 700000
    assert d360["calculation"]["cost_missing"] is True


async def test_duplicate_warning_no_automerge(client: TestClient):
    org = f"org-a21-dup-{uuid.uuid4().hex[:8]}"
    h = _hdr(org)
    first = await client.post(f"{OPS}/entities/counterparty", json={"name": "Агро Юг", "edrpou": "87654321"}, headers=h)
    assert first.status == 201
    second = await client.post(f"{OPS}/entities/counterparty", json={"name": "Агро Юг", "edrpou": "87654321"}, headers=h)
    assert second.status == 409
    body = await second.json()
    assert "существует" in (body.get("message_ru") or "")
    assert body["matches"]
    forced = await client.post(
        f"{OPS}/entities/counterparty",
        json={"name": "Агро Юг", "edrpou": "87654321", "force": True},
        headers=h,
    )
    assert forced.status == 201
    assert (await forced.json())["item"]["id"] != (await first.json())["item"]["id"]


async def test_deal_workflow_rejects_impossible_jump(client: TestClient):
    org = f"org-a21-wf-{uuid.uuid4().hex[:8]}"
    h = _hdr(org)
    deal = (await (await client.post(f"{OPS}/entities/deal", json={"title": "Ячмень"}, headers=h)).json())["item"]
    bad = await client.post(f"{OPS}/crm/deal/{deal['id']}/status", json={"status": "closed"}, headers=h)
    assert bad.status == 400
    ok = await client.post(f"{OPS}/crm/deal/{deal['id']}/status", json={"status": "negotiation", "comment": "звонок"}, headers=h)
    assert ok.status == 200
    act = await (await client.get(f"{OPS}/entities/activity?entity_id={deal['id']}", headers=h)).json()
    summaries = [a.get("summary") for a in act.get("items") or []]
    assert any(a.get("action") == "status_changed" or "Статус" in str(s) for a, s in zip(act.get("items") or [], summaries))


async def test_crm_list_search_filter_and_rbac(client: TestClient):
    org = f"org-a21-list-{uuid.uuid4().hex[:8]}"
    h = _hdr(org)
    await client.post(f"{OPS}/entities/counterparty", json={"name": "Ферма Степь", "types": ["farmer"], "region": "Одесская", "tags": ["VIP", "Пшеница"], "phone": "0991112233"}, headers=h)
    listed = await (await client.get(f"{OPS}/crm/list?q=степь", headers=h)).json()
    assert listed["items"] and listed["items"][0]["name"] == "Ферма Степь"
    tagged = await (await client.get(f"{OPS}/crm/list?tag=VIP", headers=h)).json()
    assert tagged["items"]
    viewer = await client.get(f"{OPS}/crm/list", headers=_hdr(org, "agro_viewer"))
    assert viewer.status == 200
    mgr = await (await client.get(f"{OPS}/crm/list", headers=_hdr(org, "agro_manager"))).json()
    assert mgr["can_finance"] is False
    assert mgr["items"][0]["receivable"] is None
    acc_export = await client.get(f"{OPS}/crm/export", headers=_hdr(org, "agro_accountant"))
    assert acc_export.status == 200
    viewer_export = await client.get(f"{OPS}/crm/export", headers=_hdr(org, "agro_viewer"))
    assert viewer_export.status == 403
    viewer_create = await client.post(f"{OPS}/entities/counterparty", json={"name": "X"}, headers=_hdr(org, "agro_viewer"))
    assert viewer_create.status == 403


async def test_bank_hidden_without_finance(client: TestClient):
    org = f"org-a21-bank-{uuid.uuid4().hex[:8]}"
    h = _hdr(org)
    cp = (await (await client.post(f"{OPS}/entities/counterparty", json={"name": "БанкТест", "iban": "UA123", "bank": "Приват"}, headers=h)).json())["item"]
    mgr = await (await client.get(f"{OPS}/crm/counterparty/{cp['id']}", headers=_hdr(org, "agro_manager"))).json()
    assert mgr["item"].get("iban") in (None, "")
    acc = await (await client.get(f"{OPS}/crm/counterparty/{cp['id']}", headers=_hdr(org, "agro_accountant"))).json()
    assert acc["item"].get("iban") == "UA123"


async def test_communication_manual_and_follow_up(client: TestClient):
    org = f"org-a21-comm-{uuid.uuid4().hex[:8]}"
    h = _hdr(org)
    cp = (await (await client.post(f"{OPS}/entities/counterparty", json={"name": "Связь"}, headers=h)).json())["item"]
    fake = await client.post(f"{OPS}/crm/communication", json={"comm_type": "telegram", "counterparty_id": cp["id"], "source": "USER"}, headers=h)
    assert fake.status == 400
    call = await client.post(f"{OPS}/crm/communication", json={"comm_type": "call", "title": "Звонок", "text": "Договорились", "counterparty_id": cp["id"]}, headers=h)
    assert call.status == 201
    fu = await client.post(f"{OPS}/crm/follow-up", json={"title": "Позвонить завтра", "counterparty_id": cp["id"]}, headers=h)
    assert fu.status == 201
    assert (await fu.json())["item"]["kind"] == "follow_up"


async def test_import_preview_skips_duplicates(client: TestClient):
    org = f"org-a21-imp-{uuid.uuid4().hex[:8]}"
    h = _hdr(org)
    await client.post(f"{OPS}/entities/counterparty", json={"name": "Существующий", "edrpou": "11111111"}, headers=h)
    csv_text = "name,edrpou\nСуществующий,11111111\nНовый Партнёр,22222222\n"
    preview = await (await client.post(f"{OPS}/crm/import", json={"csv": csv_text, "preview": True}, headers=h)).json()
    assert preview["preview"] is True
    assert preview["created"] == 0
    commit = await (await client.post(f"{OPS}/crm/import", json={"csv": csv_text, "commit": True}, headers=h)).json()
    assert commit["created"] == 1
    assert commit["skipped"] >= 1


async def test_credit_warning_does_not_block(client: TestClient):
    org = f"org-a21-lim-{uuid.uuid4().hex[:8]}"
    h = _hdr(org)
    cp = (await (await client.post(f"{OPS}/entities/counterparty", json={"name": "Лимит", "credit_limit": 100}, headers=h)).json())["item"]
    await client.post(
        f"{OPS}/entities/deal",
        json={"title": "Долг", "counterparty_id": cp["id"], "side": "sell", "quantity": 10, "price": 50, "currency": "UAH"},
        headers=h,
    )
    nxt = await client.post(
        f"{OPS}/entities/deal",
        json={"title": "Ещё продажа", "counterparty_id": cp["id"], "side": "sell", "quantity": 1, "price": 10},
        headers=h,
    )
    body = await nxt.json()
    assert nxt.status == 201
    assert body.get("warning", {}).get("code") == "LIMIT_EXCEEDED"


async def test_contract_expiry_buckets(client: TestClient):
    org = f"org-a21-exp-{uuid.uuid4().hex[:8]}"
    h = _hdr(org)
    end = (datetime.now(timezone.utc).date() + timedelta(days=7)).isoformat()
    await client.post(f"{OPS}/entities/contract", json={"title": "Рамка", "ends_at": end, "status": "active"}, headers=h)
    dash = await (await client.get(f"{OPS}/dashboard", headers=h)).json()
    titles = [e.get("title") for e in dash["command_center"]["today"]]
    assert any("Истекает договор" in str(t) for t in titles)


async def test_manager_no_company_margin(client: TestClient):
    org = f"org-a21-m-{uuid.uuid4().hex[:8]}"
    analytics = await (await client.get(f"{OPS}/crm/analytics", headers=_hdr(org, "agro_manager"))).json()
    assert analytics["ok"] is True
    assert analytics.get("sales") is None
    director = await (await client.get(f"{OPS}/crm/analytics", headers=_hdr(org))).json()
    assert director["sales"] == {} or director["sales"] is not None
    assert "кто больше продал" not in str(director).lower()
