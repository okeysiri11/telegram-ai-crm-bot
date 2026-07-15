# CRM platform regression tests (no Telegram required).

from __future__ import annotations


def test_status_pipeline_defined() -> None:
    from database.models.client_request import ClientRequestStatus
    from services.pg_client_request_crm_engine import STATUS_TRANSITIONS

    required = {
        "NEW",
        "ASSIGNED",
        "IN_PROGRESS",
        "WAITING_CLIENT",
        "COMPLETED",
        "CANCELLED",
    }
    assert required == {s.value for s in ClientRequestStatus}
    assert ClientRequestStatus.NEW.value in STATUS_TRANSITIONS


def test_funnel_stages_defined() -> None:
    from database.models.client_request import CrmFunnelStage
    from services.pg_client_request_crm_engine import FUNNEL_TRANSITIONS

    stages = {s.value for s in CrmFunnelStage}
    assert "NEW_LEAD" in stages
    assert "CLOSED" in stages
    assert CrmFunnelStage.NEW_LEAD.value in FUNNEL_TRANSITIONS


def test_ai_manager_intents() -> None:
    import asyncio

    from services.pg_ai_manager_engine import AI_MANAGER_INTENTS, AiManagerEngineV1

    result = asyncio.run(AiManagerEngineV1.qualify_message("Хочу купить BMW X5 в Одессе"))
    assert result["intent"] in AI_MANAGER_INTENTS
    assert 0 <= result["lead_score"] <= 100


def test_marketplace_listing_payload() -> None:
    from services.pg_marketplace_listing_engine import MarketplaceListingEngineV1

    payload = MarketplaceListingEngineV1.build_listing_payload(
        {
            "brand": "BMW",
            "model": "X5",
            "year": 2021,
            "price": 42000,
            "user_description": "Diesel Odessa",
        }
    )
    assert payload["brand"] == "BMW"
    assert payload["year"] == 2021


def test_manager_notification_format() -> None:
    from services.auto_client_flow_engine import build_manager_notification_lines

    lines = build_manager_notification_lines(
        flow_type="sell_car",
        request_number="AUTO-0001",
        data={
            "brand": "BMW",
            "model": "X5",
            "year": 2021,
            "price": 42000,
            "user_description": "Official vehicle.",
            "photo_file_ids": ["a", "b", "c"],
        },
        client_username="testuser",
        client_full_name=None,
        client_phone="+380501234567",
    )
    text = "\n".join(lines)
    assert "🚗 Новый лид" in text
    assert "6 attached" not in text
    assert "3 attached" in text
    assert "+380501234567" in text


def test_photo_album_collector_single() -> None:
    import asyncio
    from types import SimpleNamespace

    from services.photo_album_collector import PhotoAlbumCollector

    collector = PhotoAlbumCollector(delay=0.01)
    msg = SimpleNamespace(
        photo=[SimpleNamespace(file_id="photo1")],
        media_group_id=None,
        chat=SimpleNamespace(id=1),
    )

    result = asyncio.run(collector.add_photo(msg))
    assert result == ["photo1"]


def test_fsm_interrupt_helper() -> None:
    from services.entry_point_routing import is_auto_client_interrupt_text

    assert is_auto_client_interrupt_text("🚗 Поиск автомобиля")
    assert is_auto_client_interrupt_text("📂 Мои заявки")


def test_routers_registered() -> None:
    from routers.manager_crm_router import router as mgr
    from routers.client_history_router import router as hist

    assert mgr.message.handlers
    assert hist.message.handlers


def test_owner_analytics_format() -> None:
    from services.pg_owner_analytics_engine import OwnerAnalyticsEngineV1

    text = OwnerAnalyticsEngineV1.format_dashboard(
        {"new_leads_today": 5, "active_leads": 10, "closed_leads": 2, "conversion_rate_pct": 20.0, "total_leads": 10}
    )
    assert "5" in text
    assert "Конверсия" in text


def main() -> None:
    test_status_pipeline_defined()
    test_funnel_stages_defined()
    test_ai_manager_intents()
    test_marketplace_listing_payload()
    test_manager_notification_format()
    test_photo_album_collector_single()
    test_fsm_interrupt_helper()
    test_routers_registered()
    test_owner_analytics_format()
    print("crm_platform_regression: OK")


if __name__ == "__main__":
    main()
