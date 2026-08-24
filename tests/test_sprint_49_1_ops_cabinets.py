"""Sprint 49.1 — Beauty/Cafe operational persistence (list + create flows)."""

from __future__ import annotations

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.enterprise_hub import enterprise_hub
from applications.enterprise_hub.api.register import register_enterprise_hub_routes

BOS = "/api/enterprise-bos/v1"
COS = "/api/enterprise-cos/v1"


@pytest.fixture
def app() -> web.Application:
    application = web.Application()
    register_enterprise_hub_routes(application)
    return application


@pytest.fixture
async def client(app: web.Application):
    async with TestClient(TestServer(app)) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def reset_store():
    enterprise_hub.reset()
    yield
    enterprise_hub.reset()


async def test_beauty_list_and_appointment_create_cancel(client: TestClient):
    boot = await client.post(f"{BOS}/bootstrap")
    assert boot.status == 201
    customers = await client.get(f"{BOS}/customers")
    services = await client.get(f"{BOS}/services")
    employees = await client.get(f"{BOS}/employees")
    assert customers.status == 200
    assert services.status == 200
    assert employees.status == 200
    cu = (await customers.json())["items"][-1]["customer_id"]
    svc = (await services.json())["items"][-1]["service_id"]
    emp = (await employees.json())["items"][-1]["employee_id"]

    created = await client.post(
        f"{BOS}/appointments",
        json={
            "customer_id": cu,
            "service_id": svc,
            "employee_id": emp,
            "start": "2026-08-11T10:00:00",
            "end": "2026-08-11T11:00:00",
        },
    )
    assert created.status == 201
    body = await created.json()
    aid = body["appointment_id"]

    listed = await client.get(f"{BOS}/appointments")
    assert listed.status == 200
    ids = [x["appointment_id"] for x in (await listed.json())["items"]]
    assert aid in ids

    cancelled = await client.post(
        f"{BOS}/appointments",
        json={"appointment_id": aid, "status": "cancelled"},
    )
    assert cancelled.status == 200
    assert (await cancelled.json())["status"] == "cancelled"

    again = await client.get(f"{BOS}/appointments")
    hit = next(x for x in (await again.json())["items"] if x["appointment_id"] == aid)
    assert hit["status"] == "cancelled"


async def test_beauty_isolated_store_instances():
    from applications.enterprise_hub.shared.store import EnterpriseHubStore
    from applications.enterprise_hub.beauty_os.facade import BeautyOSSuite

    a = BeautyOSSuite(store=EnterpriseHubStore())
    b = BeautyOSSuite(store=EnterpriseHubStore())
    a.create_customer(name="OnlyA")
    assert len(a.list_customers()["items"]) == 1
    assert len(b.list_customers()["items"]) == 0


async def test_cafe_order_event_type_and_shift(client: TestClient):
    boot = await client.post(f"{COS}/bootstrap")
    assert boot.status == 201
    customers = await client.get(f"{COS}/customers")
    tables = await client.get(f"{COS}/tables")
    menu = await client.get(f"{COS}/menu")
    staff = await client.get(f"{COS}/staff")
    assert customers.status == 200
    cu = (await customers.json())["items"][-1]["customer_id"]
    tbl = (await tables.json())["items"][-1]["table_id"]
    item = (await menu.json())["items"][-1]
    stf = (await staff.json())["items"][-1]["staff_id"]

    order = await client.post(
        f"{COS}/orders",
        json={
            "customer_id": cu,
            "table_id": tbl,
            "items": [{"name": item.get("name", "dish"), "price": item.get("price", 10), "qty": 1}],
            "order_type": "Банкет",
            "guests": 12,
            "responsible": "Админ",
            "comment": "Sprint 49.1",
        },
    )
    assert order.status == 201
    ob = await order.json()
    assert ob["order_type"] == "Банкет"
    assert ob["guests"] == 12

    listed = await client.get(f"{COS}/orders")
    assert listed.status == 200
    assert any(x["order_id"] == ob["order_id"] for x in (await listed.json())["items"])

    opened = await client.post(f"{COS}/shifts", json={"staff_id": stf, "role": "waiter"})
    assert opened.status == 201
    sid = (await opened.json())["shift_id"]
    shifts = await client.get(f"{COS}/shifts")
    assert shifts.status == 200
    assert any(x["shift_id"] == sid for x in (await shifts.json())["items"])

    closed = await client.post(f"{COS}/shifts", json={"shift_id": sid, "action": "close"})
    assert closed.status == 200
    assert (await closed.json())["status"] == "Закрыта"
