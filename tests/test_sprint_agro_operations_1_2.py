"""AGRO Operations 1.2 — alerts, calendar, crops, deliveries, notifications."""

from __future__ import annotations

import base64
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.agro_enterprise.api.register import register_agro_enterprise_routes
from services.agro_ops import reset_agro_ops_for_tests

OPS = "/api/agro-ops/v1"
TINY_PDF = b"%PDF-1.1\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF"


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


async def test_health_sprint_1_2(client: TestClient):
    body = await (await client.get(f"{OPS}/health")).json()
    assert body["sprint"] == "agro-2.0"
    assert any(r["id"] == "agro_viewer" for r in body["roles"])


async def test_acceptance_crop_delivery_alert_calendar(client: TestClient):
    org = f"org-a12-{uuid.uuid4().hex[:8]}"
    h = _hdr(org)
    crop = (await (await client.post(f"{OPS}/entities/crop", json={"name": "Пшеница"}, headers=h)).json())["item"]
    supplier = (await (await client.post(f"{OPS}/entities/counterparty", json={"name": "ООО Поставщик", "types": ["supplier"]}, headers=h)).json())["item"]
    buyer = (await (await client.post(f"{OPS}/entities/counterparty", json={"name": "ООО Покупатель", "types": ["buyer"]}, headers=h)).json())["item"]
    await client.post(
        f"{OPS}/entities/availability",
        json={"commodity": "Пшеница", "crop_id": crop["id"], "quantity": 1000, "counterparty_id": supplier["id"], "region": "Одесская обл."},
        headers=h,
    )
    await client.post(
        f"{OPS}/entities/demand",
        json={"commodity": "Пшеница", "crop_id": crop["id"], "quantity": 600, "counterparty_id": buyer["id"]},
        headers=h,
    )
    bal = await (await client.get(f"{OPS}/crops/{crop['id']}/balance", headers=h)).json()
    assert bal["item"]["available"] == 1000
    assert bal["item"]["demand"] == 600
    assert bal["item"]["gap"] == 400

    deadline = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
    ship = (await (await client.post(
        f"{OPS}/entities/shipment",
        json={"title": "Поставка пшеницы 600", "quantity": 600, "crop": "Пшеница", "counterparty_id": buyer["id"], "deadline_at": deadline},
        headers=h,
    )).json())["item"]
    assert ship["quantity_planned"] == 600
    assert ship["progress_pct"] == 0

    uploaded = await client.post(
        f"{OPS}/files",
        json={"filename": "spec.pdf", "content_base64": base64.b64encode(TINY_PDF).decode(), "entity_type": "shipment", "entity_id": ship["id"], "doc_type": "specification"},
        headers=h,
    )
    assert uploaded.status in {200, 201}

    cal = await (await client.get(f"{OPS}/entities/calendar", headers=h)).json()
    assert any("поставки" in str(i.get("title") or "").lower() for i in cal["items"])
    event = next(i for i in cal["items"] if i.get("shipment_id") == ship["id"])
    remind = await (await client.post(f"{OPS}/calendar/{event['id']}/remind", json={"days_before": 1}, headers=h)).json()
    assert remind["ok"]
    reminded = await (await client.post(f"{OPS}/reminders/evaluate", json={}, headers=h)).json()
    assert reminded["sent"] >= 1

    market = (await (await client.post(f"{OPS}/entities/market", json={"name": "Одесса"}, headers=h)).json())["item"]
    await client.post(f"{OPS}/entities/alert_rule", json={"commodity": "Пшеница", "operator": "lt", "target_price": 8500}, headers=h)
    price = (await (await client.post(
        f"{OPS}/entities/market_price",
        json={"market_id": market["id"], "commodity": "Пшеница", "price": 8200, "currency": "UAH"},
        headers=h,
    )).json())["item"]
    ev = await (await client.post(f"{OPS}/alerts/evaluate", json={}, headers=h)).json()
    assert ev["created"] == 1
    notes = await (await client.get(f"{OPS}/entities/notification", headers=h)).json()
    alert_note = next(n for n in notes["items"] if n.get("kind") == "price_alert")
    opened = await (await client.post(f"{OPS}/notifications/{alert_note['id']}/actions", json={"action": "open"}, headers=h)).json()
    assert opened["ok"]
    assert opened["linked"]["id"] == price["id"]
    task = await (await client.post(
        f"{OPS}/notifications/{alert_note['id']}/actions",
        json={"action": "create_task", "title": "Проверить поставку №15", "owner": "agro_manager", "priority": "high"},
        headers=h,
    )).json()
    assert task["item"]["title"] == "Проверить поставку №15"
    assert task["item"]["owner"] == "agro_manager"
    assert task["item"]["priority"] == "high"
    assert task["item"]["entity_id"] == price["id"]

    prog = await (await client.post(f"{OPS}/deliveries/{ship['id']}/progress", json={"quantity": 200}, headers=h)).json()
    assert prog["item"]["quantity_delivered"] == 200
    assert prog["item"]["progress_pct"] == 33.33

    trip = await client.post(
        f"{OPS}/entities/trip",
        json={"title": "Рейс-2", "shipment_id": ship["id"], "weight_planned": 100, "crop": "Пшеница"},
        headers=h,
    )
    assert trip.status == 201
    ship2 = await (await client.get(f"{OPS}/entities/shipment/{ship['id']}", headers=h)).json()
    assert ship2["item"]["quantity_delivered"] == 300
    assert ship2["item"]["progress_pct"] == 50.0

    other = await (await client.get(f"{OPS}/entities/availability", headers=_hdr(f"org-x-{uuid.uuid4().hex[:6]}"))).json()
    assert other["items"] == []


async def test_alert_cooldown_and_rbac(client: TestClient):
    org = f"org-a12c-{uuid.uuid4().hex[:8]}"
    h = _hdr(org)
    await client.post(f"{OPS}/entities/market", json={"name": "M"}, headers=h)
    await client.post(f"{OPS}/entities/alert_rule", json={"commodity": "Пшеница", "operator": "lt", "target_price": 9000, "cooldown_hours": 24}, headers=h)
    await client.post(f"{OPS}/entities/market_price", json={"commodity": "Пшеница", "price": 8000}, headers=h)
    first = await (await client.post(f"{OPS}/alerts/evaluate", json={}, headers=h)).json()
    second = await (await client.post(f"{OPS}/alerts/evaluate", json={}, headers=h)).json()
    assert first["created"] == 1
    assert second["created"] == 0
    assert second["skipped_cooldown"] >= 1
    viewer = await client.post(f"{OPS}/entities/availability", json={"commodity": "Пшеница", "quantity": 10}, headers=_hdr(org, "agro_viewer"))
    assert (await viewer.json()).get("error") == "forbidden"
    acc = await client.post(f"{OPS}/entities/availability", json={"commodity": "Пшеница", "quantity": 10}, headers=_hdr(org, "agro_accountant"))
    assert (await acc.json()).get("error") == "forbidden"


async def test_notification_actions_and_demo(client: TestClient):
    org = f"org-a12n-{uuid.uuid4().hex[:8]}"
    h = _hdr(org)
    boot = await (await client.post(f"{OPS}/bootstrap", json={}, headers=h)).json()
    assert boot["ok"]
    assert boot["item"]["availability"]["quantity"] == 500
    assert boot["item"]["demand"]["quantity"] == 800
    notes = await (await client.get(f"{OPS}/entities/notification", headers=h)).json()
    demo = next(n for n in notes["items"] if n.get("is_demo"))
    assert "DEMO" in str(demo.get("title"))
    read = await (await client.post(f"{OPS}/notifications/{demo['id']}/actions", json={"action": "mark_read"}, headers=h)).json()
    assert read["item"]["status"] == "read"
    snooze = await (await client.post(f"{OPS}/notifications/{demo['id']}/actions", json={"action": "snooze", "hours": 2}, headers=h)).json()
    assert snooze["item"]["status"] == "snoozed"
    cal = await (await client.post(f"{OPS}/notifications/{demo['id']}/actions", json={"action": "add_calendar"}, headers=h)).json()
    assert cal["ok"]
    again = await (await client.post(f"{OPS}/bootstrap", json={}, headers=h)).json()
    assert again["already"] is True
    viewer_boot = await client.post(f"{OPS}/bootstrap", json={}, headers=_hdr(org, "agro_viewer"))
    assert (await viewer_boot.json()).get("error") == "forbidden"


async def test_crop_directory_zero_balances(client: TestClient):
    org = f"org-a12d-{uuid.uuid4().hex[:8]}"
    items = (await (await client.get(f"{OPS}/crops/directory", headers=_hdr(org))).json())["items"]
    wheat = next(i for i in items if i["name"] == "Пшеница")
    assert wheat["available"] == 0
    assert wheat["demand"] == 0
    assert wheat["in_catalog"] is True
