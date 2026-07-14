# Auto client pipeline verification (no Telegram/DB required).

from __future__ import annotations


def test_is_auto_dealer_lead_includes_auto_client() -> None:
    from services.pg_auto_dealer_manager_engine import AutoDealerManagerEngineV1

    assert AutoDealerManagerEngineV1.is_auto_dealer_lead(
        source_link="auto_client",
        vertical="auto",
    )
    assert AutoDealerManagerEngineV1.is_auto_dealer_lead(
        source_link="auto_dealer",
        vertical="auto",
    )


def test_request_type_labels() -> None:
    from services.pg_auto_dealer_manager_engine import AutoDealerManagerEngineV1

    assert "Поиск" in AutoDealerManagerEngineV1.request_type_label("buy_car")
    assert "Продажа" in AutoDealerManagerEngineV1.request_type_label("sell_car")
    assert "объявления" in AutoDealerManagerEngineV1.request_type_label("listing")


def test_fsm_states_exist() -> None:
    from states.entry_flow_states import AutoClientFlow

    assert AutoClientFlow.awaiting_description
    assert AutoClientFlow.awaiting_photo
    assert AutoClientFlow.awaiting_listing_description


def test_router_handlers_registered() -> None:
    from routers.auto_client_router import router

    handler_names = {
        getattr(h.callback, "__name__", str(h.callback))
        for h in router.message.handlers + router.callback_query.handlers
    }
    required = {
        "cmd_start_auto_client",
        "auto_client_language_selected",
        "auto_client_menu_action",
        "auto_client_listing_photo",
        "auto_client_listing_photo_required",
        "auto_client_description",
        "auto_client_listing_description",
    }
    assert required.issubset(handler_names)


def test_lead_snapshot_has_client_fields() -> None:
    from services.pg_lead_engine import LeadEngineV1
    from types import SimpleNamespace

    row = SimpleNamespace(
        id="test-id",
        vertical="auto",
        role="buyer",
        language="ru",
        source_link="auto_client",
        utm_source=None,
        utm_campaign=None,
        utm_medium=None,
        referral_code=None,
        referrer=None,
        marketing_source=None,
        telegram_user_id=1,
        telegram_username="test",
        full_name="Test",
        phone=None,
        assigned_manager_id=None,
        status="CONTACTED",
        phone_normalized=None,
        vin=None,
        vehicle_registration=None,
        agro_product=None,
        agro_volume=None,
        agro_location=None,
        client_request_type="buy_car",
        client_description="Test",
        client_photo_file_id="photo123",
        is_duplicate=False,
        duplicate_of_id=None,
        merged_into_id=None,
        created_at=None,
        updated_at=None,
    )
    snap = LeadEngineV1._snapshot(row)  # type: ignore[arg-type]
    assert snap["client_request_type"] == "buy_car"
    assert snap["client_description"] == "Test"
    assert snap["client_photo_file_id"] == "photo123"


def main() -> None:
    test_is_auto_dealer_lead_includes_auto_client()
    test_request_type_labels()
    test_fsm_states_exist()
    test_router_handlers_registered()
    test_lead_snapshot_has_client_fields()
    print("auto_client_pipeline: OK")


if __name__ == "__main__":
    main()
