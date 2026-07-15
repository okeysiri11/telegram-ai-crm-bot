# Production hardening regression tests.

from __future__ import annotations

import asyncio
from pathlib import Path


def test_storage_providers() -> None:
    from services.storage import TelegramStorage, LocalStorage, get_storage_provider

    async def run() -> None:
        tg = TelegramStorage()
        media = await tg.store(file_id="AgACAgIAAx...")
        assert media.file_id == "AgACAgIAAx..."

        local = LocalStorage(base_dir="data/test_media_cache")
        cached = await local.store(data=b"hello", file_id="f1", filename="t.bin")
        assert cached.local_path
        assert Path(cached.local_path).exists()

        provider = get_storage_provider()
        assert provider is not None

    asyncio.run(run())


def test_inventory_search_filters() -> None:
    from database.models.marketplace_inventory import InventoryStatus
    from services.pg_marketplace_inventory_engine import InventoryEngineV1

    assert InventoryStatus.ACTIVE.value == "ACTIVE"
    assert callable(InventoryEngineV1.search)
    assert callable(InventoryEngineV1.recommend)


def test_notification_providers() -> None:
    from services.notification_center import (
        EmailProvider,
        NotificationCenterV1,
        SMSProvider,
        TelegramProvider,
    )

    providers = NotificationCenterV1.providers()
    assert "telegram" in providers
    assert isinstance(providers["telegram"], TelegramProvider)
    assert isinstance(providers["email"], EmailProvider)
    assert isinstance(providers["sms"], SMSProvider)

    async def run() -> None:
        ok = await EmailProvider().send(to="a@b.c", subject="t", body="hello")
        assert ok is True

    asyncio.run(run())


def test_escalation_thresholds() -> None:
    from services.pg_escalation_engine import ESCALATION_STEPS

    assert len(ESCALATION_STEPS) == 4
    assert ESCALATION_STEPS[0][0] == 300
    assert ESCALATION_STEPS[-1][1] == 4


def test_permissions_seed_map() -> None:
    from services.pg_platform_permissions_engine import (
        PLATFORM_PERMISSIONS,
        PLATFORM_ROLES,
        ROLE_PERMISSION_MAP,
    )

    for role in (
        "OWNER",
        "ADMIN",
        "MANAGER",
        "AUTO_MANAGER",
        "DEALER_MANAGER",
        "CLIENT",
        "AI_AGENT",
    ):
        assert role in PLATFORM_ROLES
        assert role in ROLE_PERMISSION_MAP
    assert "leads.view" in PLATFORM_PERMISSIONS


def test_audit_event_types() -> None:
    from database.models.platform_audit_log import PlatformAuditEvent

    assert PlatformAuditEvent.LEAD_CREATED.value == "LEAD_CREATED"
    assert PlatformAuditEvent.AI_ACTION.value == "AI_ACTION"


def test_jwt_roundtrip() -> None:
    from api.crm_api import _decode_jwt, _encode_jwt

    token = _encode_jwt({"sub": "1", "role": "ADMIN"})
    claims = _decode_jwt(token)
    assert claims is not None
    assert claims["sub"] == "1"


def test_openapi_paths() -> None:
    import asyncio

    from api.crm_api import openapi_spec_handler

    async def run() -> None:
        resp = await openapi_spec_handler(None)  # type: ignore[arg-type]
        assert resp.status == 200

    asyncio.run(run())


def test_observability_metrics() -> None:
    from services.observability import inc_metric, observability_snapshot, prometheus_text

    inc_metric("leads_created_total")
    text = prometheus_text()
    assert "leads_created_total" in text
    assert "leads_created_total" in observability_snapshot()


def test_ai_engine_fallback() -> None:
    from services.pg_ai_manager_engine import AiManagerEngineV1

    result = asyncio.run(AiManagerEngineV1.qualify_message("Нужна страховка авто"))
    assert result["intent"] in {
        "BUY_CAR",
        "SELL_CAR",
        "LEASING",
        "INSURANCE",
        "CREDIT",
        "LOGISTICS",
        "LEGAL",
        "SERVICE",
        "OTHER",
    }


def test_crm_api_routes_registered() -> None:
    from aiohttp import web
    from api.crm_api import register_crm_api_routes

    app = web.Application()
    register_crm_api_routes(app)
    paths = {r.resource.canonical for r in app.router.routes() if hasattr(r, "resource")}
    assert "/api/leads" in paths
    assert "/api/inventory" in paths
    assert "/api/analytics" in paths


def main() -> None:
    test_storage_providers()
    test_inventory_search_filters()
    test_notification_providers()
    test_escalation_thresholds()
    test_permissions_seed_map()
    test_audit_event_types()
    test_jwt_roundtrip()
    test_openapi_paths()
    test_observability_metrics()
    test_ai_engine_fallback()
    test_crm_api_routes_registered()
    print("production_hardening_regression: OK")


if __name__ == "__main__":
    main()
