"""Tests — Farmer Portal, Mobile API & Partner Integrations (Sprint 8.7)."""

from __future__ import annotations

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.agro_marketplace import agro_marketplace
from applications.agro_marketplace.api.register import register_agro_marketplace_routes
from applications.agro_marketplace.portal.models import (
    MessageThread,
    PartnerConnection,
    PartnerType,
    PortalKind,
    PortalUser,
    SharedDocument,
    WebhookSubscription,
)


@pytest.fixture
def app() -> web.Application:
    application = web.Application()
    register_agro_marketplace_routes(application)
    return application


@pytest.fixture
async def client(app: web.Application):
    async with TestClient(TestServer(app)) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def reset_store():
    agro_marketplace.reset()
    yield
    agro_marketplace.reset()


def test_version_portal_engine():
    health = agro_marketplace.health()
    assert health["application_version"] == "2.0.0"
    assert health["portal_engine"] == "1.0"


@pytest.mark.asyncio
async def test_farmer_portal_and_notifications():
    user = await agro_marketplace.portal_engine.register_user(
        PortalUser(email="farmer@test.com", display_name="Farmer A", role="farmer")
    )
    view = await agro_marketplace.portal_engine.build_portal(PortalKind.FARMER, user_id=user.user_id)
    assert view.kind == PortalKind.FARMER
    assert view.widgets
    inbox = agro_marketplace.notification_center.inbox(user.user_id)
    assert inbox
    alert = await agro_marketplace.notification_center.ai_alert(user.user_id, "low_moisture")
    assert alert.channel == "ai_alert"


@pytest.mark.asyncio
async def test_all_portals_and_mobile_auth():
    for kind in PortalKind:
        view = await agro_marketplace.portal_engine.build_portal(kind, user_id="u1")
        assert view.kind == kind

    session = await agro_marketplace.mobile_engine.authenticate(
        email="buyer@test.com",
        role="buyer",
        platform="android",
    )
    assert session["session"]["is_active"] is True
    assert session["user"]["email"] == "buyer@test.com"
    home = agro_marketplace.mobile_engine.home(session["user"]["user_id"])
    assert home["user"]["role"] == "buyer"


@pytest.mark.asyncio
async def test_partners_webhooks_messaging_docs():
    bank = await agro_marketplace.partner_api.connect(
        PartnerConnection(partner_type=PartnerType.BANK, partner_name="AgriBank")
    )
    assert bank.status == "connected"
    quote = agro_marketplace.partner_api.invoke(
        PartnerType.INSURANCE, "quote", coverage=50000, crop="maize"
    )
    assert quote["premium"] > 0

    sub = agro_marketplace.webhooks_registry.subscribe(
        WebhookSubscription(
            target_url="https://partner.example/hooks",
            event_types=["order", "*"],
            partner_id=bank.connection_id,
        )
    )
    deliveries = await agro_marketplace.webhooks_registry.trigger("order", {"id": "1"})
    assert deliveries
    assert deliveries[0]["subscription_id"] == sub.subscription_id

    u1 = await agro_marketplace.users.register(PortalUser(email="a@t.com", role="farmer"))
    u2 = await agro_marketplace.users.register(PortalUser(email="b@t.com", role="buyer"))
    thread = agro_marketplace.portal_engine.messaging.create_thread(
        MessageThread(participants=[u1.user_id, u2.user_id], subject="Deal")
    )
    assert thread.thread_id
    share = await agro_marketplace.portal_engine.documents.share(
        SharedDocument(
            document_id="doc-1",
            owner_id=u1.user_id,
            recipient_id=u2.user_id,
            title="Invoice",
        )
    )
    assert share.share_id


@pytest.mark.asyncio
async def test_api_portal_mobile_partner(client: TestClient):
    health = await client.get("/api/agro/v1/portal/health")
    assert health.status == 200
    body = await health.json()
    assert body["portal_engine"] == "1.0"
    assert body["application_version"] == "2.0.0"

    reg = await client.post(
        "/api/agro/v1/portal/users",
        json={"email": "api@agro.test", "role": "farmer", "display_name": "API Farmer"},
    )
    assert reg.status == 201
    user = await reg.json()

    portal = await client.get(f"/api/agro/v1/portal/farmer?user_id={user['user_id']}")
    assert portal.status == 200

    auth = await client.post(
        "/api/agro/mobile/v1/auth",
        json={"email": "mobile@agro.test", "role": "buyer", "platform": "ios"},
    )
    assert auth.status == 201

    partner = await client.post(
        "/api/agro/partner/v1/connections",
        json={"partner_type": "logistics", "partner_name": "FastHaul"},
    )
    assert partner.status == 201

    note = await client.post(
        "/api/agro/v1/notifications",
        json={"recipient_id": user["user_id"], "title": "Hi", "body": "Welcome", "channel": "push"},
    )
    assert note.status == 201
