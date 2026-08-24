"""Sprint AUTO 1.4 — live Telegram staff auth inside the existing ADOS bot."""

from __future__ import annotations

import uuid

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.auto_enterprise.api.register import register_auto_enterprise_routes
from services.auto_ops import reset_auto_ops_for_tests
from services.auto_ops.telegram_auth import command_allowed, looks_like_intercept
from startup import BOT_ROUTER_PATHS

OPS = "/api/auto-ops/v1"
VIN = "1HGCM82633A004352"
PNG_1PX = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="


@pytest.fixture
def app() -> web.Application:
    application = web.Application()
    register_auto_enterprise_routes(application)
    return application


@pytest.fixture
async def client(app: web.Application):
    async with TestClient(TestServer(app)) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def reset_ops():
    reset_auto_ops_for_tests()
    yield
    reset_auto_ops_for_tests()


def _hdr(org: str, role: str = "auto_director") -> dict[str, str]:
    return {"X-Organization-Id": org, "X-Role": role}


async def _vehicle(client: TestClient, org: str, vin: str = VIN, role: str = "auto_manager") -> str:
    res = await client.post(
        f"{OPS}/vehicles",
        json={"vin": vin, "manufacturer": "BMW", "model": "X5", "year": 2013},
        headers=_hdr(org, role),
    )
    assert res.status == 201, await res.text()
    return (await res.json())["item"]["id"]


async def _client_row(client: TestClient, org: str, name: str = "Иванов") -> str:
    res = await client.post(f"{OPS}/clients", json={"name": name, "phone": "+380501112233"}, headers=_hdr(org, "auto_manager"))
    assert res.status == 201, await res.text()
    return (await res.json())["item"]["id"]


async def _bind(client: TestClient, org: str, telegram_id: int, role: str, label: str) -> dict:
    res = await client.post(
        f"{OPS}/telegram/members",
        json={"telegram_id": telegram_id, "role": role, "label": label},
        headers=_hdr(org, "auto_director"),
    )
    assert res.status in {200, 201}, await res.text()
    return await res.json()


async def _in(client: TestClient, telegram_id: int, text: str = "", extra: dict | None = None, callback_data: str | None = None) -> tuple[int, dict]:
    body: dict = {"telegram_id": telegram_id, "text": text}
    if extra:
        body["extra"] = extra
    if callback_data:
        body["callback_data"] = callback_data
    res = await client.post(f"{OPS}/telegram/inbound", json=body, headers=_hdr("default", "auto_director"))
    return res.status, await res.json()


async def test_health_is_auto_1_4_live(client: TestClient):
    res = await client.get(f"{OPS}/health")
    body = await res.json()
    assert body["sprint"] in {"AUTO_1.4", "AUTO_1.5", "AUTO_1.6", "AUTO_1.7", "AUTO_1.8", "AUTO_1.8.5"}
    assert body["telegram"]["implemented"] is True
    assert body["telegram"]["status"] == "live"
    assert "Новый бот не строится" in body["telegram"]["message_ru"]
    intents = {i["command"] for i in body["telegram"]["intents"]}
    assert "/vin <VIN>" in intents
    assert "/pay <VIN> <amount>" in intents
    assert "/report" in intents
    assert "routers.auto_ops_telegram_router" in BOT_ROUTER_PATHS
    assert BOT_ROUTER_PATHS.index("routers.auto_ops_telegram_router") < BOT_ROUTER_PATHS.index("routers.telegram_super_app_router")
    assert looks_like_intercept("/vin ABC") is True
    assert looks_like_intercept("/start") is False
    assert command_allowed("auto_manager", "pay") is False
    assert command_allowed("auto_accountant", "pay") is True


async def test_unauthorized_telegram_denied(client: TestClient):
    status, body = await _in(client, 999001, "/vin 1HGCM82633A004352")
    assert status == 403
    assert body["ok"] is False
    assert "закрытое" in body["message_ru"].lower() or "сотрудник" in body["message_ru"].lower()
    status, start = await _in(client, 999001, "/auto")
    assert status == 403
    assert start.get("intercepted") is True


async def test_director_menu_vin_status_report(client: TestClient):
    org = f"auto-d14-{uuid.uuid4().hex[:8]}"
    await _vehicle(client, org)
    await _bind(client, org, 41001, "auto_director", "Директор")
    st, menu = await _in(client, 41001, "/start")
    assert st == 200
    assert menu["ok"] is True
    assert menu["role"] == "auto_director"
    labels = [b["text"] for row in menu["keyboard"] for b in row]
    assert "VIN" in labels
    assert "Отчёт" in labels
    assert "Статус бота" in labels
    st, vin = await _in(client, 41001, f"/vin {VIN}")
    assert st == 200, vin
    assert vin["item"]["vin"] == VIN
    st, upd = await _in(client, 41001, f"/status {VIN} READY_FOR_SALE")
    assert st == 200, upd
    assert upd["item"]["status"] == "READY_FOR_SALE"
    st, report = await _in(client, 41001, "/report")
    assert st == 200
    assert "Сводка" in report["message_ru"]


async def test_manager_menu_expense_task_photo_doc_no_pay(client: TestClient):
    org = f"auto-m14-{uuid.uuid4().hex[:8]}"
    await _vehicle(client, org)
    await _bind(client, org, 41002, "auto_manager", "Менеджер")
    st, menu = await _in(client, 41002, "/auto")
    assert st == 200
    labels = [b["text"] for row in menu["keyboard"] for b in row]
    assert "VIN" in labels
    assert "Платежи" not in labels
    st, pay = await _in(client, 41002, f"/pay {VIN} 100")
    assert st == 403
    st, exp = await _in(client, 41002, f"/expense {VIN} 80 STORAGE")
    assert st == 200, exp
    assert exp["item"]["category"] == "STORAGE"
    st, task = await _in(client, 41002, f"/task {VIN} Проверить авто", extra={"complete": True})
    assert st == 200, task
    assert task["item"]["status"] == "done"
    st, photo = await _in(
        client,
        41002,
        f"/photo {VIN}",
        extra={"content_base64": PNG_1PX, "filename": "telegram.png", "mime_type": "image/png"},
    )
    assert st == 200, photo
    st, doc = await _in(client, 41002, f"/doc {VIN} invoice")
    assert st == 200, doc
    assert doc["item"]["vehicle_id"]


async def test_accountant_payment_and_forbidden_status(client: TestClient):
    org = f"auto-a14-{uuid.uuid4().hex[:8]}"
    vid = await _vehicle(client, org)
    cid = await _client_row(client, org)
    deal = await client.post(f"{OPS}/crm/deals", json={"client_id": cid, "vehicle_id": vid, "sale_price": 25000}, headers=_hdr(org, "auto_manager"))
    assert deal.status == 201
    await _bind(client, org, 41003, "auto_accountant", "Бухгалтер")
    st, pay = await _in(client, 41003, f"/pay {VIN} 1500")
    assert st == 200, pay
    assert pay["item"]["status"] == "confirmed"
    st, menu = await _in(client, 41003, "/auto")
    assert st == 200
    labels = [b["text"] for row in menu["keyboard"] for b in row]
    assert "Платежи" in labels
    st, bot = await _in(client, 41003, "/botstatus")
    assert st == 403


async def test_logistics_customs_client_deal(client: TestClient):
    org = f"auto-flow14-{uuid.uuid4().hex[:8]}"
    h = _hdr(org, "auto_manager")
    vid = await _vehicle(client, org)
    cid = await _client_row(client, org, "Петров")
    ship = await client.post(
        f"{OPS}/logistics/shipments",
        json={"vehicle_id": vid, "shipment_type": "CONTAINER", "eta": "2026-09-01"},
        headers=h,
    )
    assert ship.status == 201
    customs = await client.post(f"{OPS}/customs/cases", json={"vehicle_id": vid, "status": "DOCUMENTS_PREP"}, headers=h)
    assert customs.status == 201
    deal = await client.post(f"{OPS}/crm/deals", json={"client_id": cid, "vehicle_id": vid, "stage": "CONTACT"}, headers=h)
    assert deal.status == 201
    await _bind(client, org, 41004, "auto_manager", "Менеджер")
    st, logi = await _in(client, 41004, f"/logistics {VIN}")
    assert st == 200, logi
    assert "Логистика" in logi["message_ru"]
    st, cust = await _in(client, 41004, f"/customs {VIN}")
    assert st == 200
    assert "Растаможка" in cust["message_ru"]
    st, client_row = await _in(client, 41004, "/client Петров")
    assert st == 200
    assert "Петров" in client_row["message_ru"]
    st, deal_row = await _in(client, 41004, f"/deal {VIN}")
    assert st == 200
    assert deal_row["item"]["id"] == (await deal.json())["item"]["id"]


async def test_reservation_conflict_and_duplicate_expense(client: TestClient):
    org = f"auto-rsv14-{uuid.uuid4().hex[:8]}"
    await _vehicle(client, org)
    c1 = await _client_row(client, org, "Первый")
    c2 = await _client_row(client, org, "Второй")
    await _bind(client, org, 41005, "auto_manager", "Менеджер")
    st, first = await _in(client, 41005, f"/reserve {VIN} {c1}", extra={"client_id": c1})
    assert st == 200, first
    st, second = await _in(client, 41005, f"/reserve {VIN} {c2}", extra={"client_id": c2})
    assert st == 409
    st, exp1 = await _in(client, 41005, f"/expense {VIN} 40 STORAGE")
    assert st == 200, exp1
    st, exp2 = await _in(client, 41005, f"/expense {VIN} 40 STORAGE")
    assert st == 200
    assert exp2.get("duplicate") is True
    assert exp2["item"]["id"] == exp1["item"]["id"]


async def test_callback_ownership_and_tenant_isolation(client: TestClient):
    org_a = f"auto-ta-{uuid.uuid4().hex[:8]}"
    org_b = f"auto-tb-{uuid.uuid4().hex[:8]}"
    await _vehicle(client, org_a, VIN)
    await _vehicle(client, org_b, VIN, role="auto_manager")
    await _bind(client, org_a, 41100, "auto_director", "A")
    await _bind(client, org_b, 42200, "auto_director", "B")
    stolen = await client.post(
        f"{OPS}/telegram/members",
        json={"telegram_id": 41100, "role": "auto_manager", "label": "steal"},
        headers=_hdr(org_b, "auto_director"),
    )
    assert stolen.status == 409
    st, menu = await _in(client, 41100, "/auto")
    token = menu["keyboard"][0][0]["callback_data"]
    await _bind(client, org_a, 41101, "auto_manager", "Mgr")
    st, cb = await _in(client, 41101, callback_data=token)
    assert st == 403
    assert "другому" in cb["message_ru"]
    st, a_vin = await _in(client, 41100, f"/vin {VIN}")
    st, b_vin = await _in(client, 42200, f"/vin {VIN}")
    assert a_vin["item"]["id"] != b_vin["item"]["id"]
    assert a_vin["organization_id"] == org_a
    assert b_vin["organization_id"] == org_b


async def test_bot_status_summaries_audit_guest_denied(client: TestClient):
    org = f"auto-sum14-{uuid.uuid4().hex[:8]}"
    await _vehicle(client, org)
    await _bind(client, org, 43001, "auto_director", "Директор")
    await _in(client, 43001, f"/vin {VIN}")
    guest = await client.get(f"{OPS}/telegram/status", headers=_hdr(org, "guest"))
    assert guest.status == 403
    mgr = await client.get(f"{OPS}/telegram/status", headers=_hdr(org, "auto_manager"))
    assert mgr.status == 403
    status = await client.get(f"{OPS}/telegram/status", headers=_hdr(org, "auto_director"))
    assert status.status == 200
    body = await status.json()
    assert body["mode"] in {"polling", "webhook"}
    assert body["authorized_count"] >= 1
    assert body["new_bot"] is False
    morning = await client.post(f"{OPS}/telegram/summaries/morning", json={}, headers=_hdr(org, "auto_director"))
    assert morning.status == 200, await morning.text()
    mbody = await morning.json()
    assert mbody["kind"] == "morning"
    assert mbody["sent"] >= 1
    evening = await client.post(f"{OPS}/telegram/summaries/evening", json={}, headers=_hdr(org, "auto_director"))
    assert evening.status == 200
    assert (await evening.json())["kind"] == "evening"
    again = await client.post(f"{OPS}/telegram/summaries/morning", json={}, headers=_hdr(org, "auto_director"))
    assert (await again.json())["sent"] >= 1
    after = await client.get(f"{OPS}/telegram/status", headers=_hdr(org, "auto_director"))
    assert (await after.json())["notifications_sent_today"] >= 1
    audit = await client.get(f"{OPS}/audit", headers=_hdr(org, "auto_director"))
    actions = {a["action"] for a in (await audit.json())["items"]}
    assert "telegram_member_upserted" in actions
    assert "telegram_vin" in actions or "telegram_menu" in actions
    members = await client.get(f"{OPS}/telegram/members", headers=_hdr(org, "auto_director"))
    assert members.status == 200
    assert (await members.json())["total"] >= 1
    members_mgr = await client.get(f"{OPS}/telegram/members", headers=_hdr(org, "auto_manager"))
    assert members_mgr.status == 403
