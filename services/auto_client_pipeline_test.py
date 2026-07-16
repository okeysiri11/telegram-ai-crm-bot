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

    assert AutoClientFlow.collecting
    assert AutoClientFlow.awaiting_photos
    assert AutoClientFlow.awaiting_vin
    assert AutoClientFlow.awaiting_phone


def test_flow_steps_defined() -> None:
    from services.auto_client_flow_engine import (
        FLOW_STEPS,
        REQUEST_BUY,
        REQUEST_LISTING,
        REQUEST_MANAGER,
        REQUEST_SELL,
        REQUEST_SERVICES,
        first_step,
        next_step,
    )

    assert first_step(REQUEST_BUY) == "brand"
    assert "vin_optional" in FLOW_STEPS[REQUEST_BUY]
    assert "photos" in FLOW_STEPS[REQUEST_BUY]
    assert FLOW_STEPS[REQUEST_BUY].index("photos") < FLOW_STEPS[REQUEST_BUY].index("phone")
    assert FLOW_STEPS[REQUEST_BUY].index("phone") < FLOW_STEPS[REQUEST_BUY].index("vin_optional")
    assert FLOW_STEPS[REQUEST_BUY][-1] == "vin_optional"
    assert FLOW_STEPS[REQUEST_SELL] == FLOW_STEPS[REQUEST_BUY]
    assert FLOW_STEPS[REQUEST_LISTING] == FLOW_STEPS[REQUEST_BUY]
    assert next_step(REQUEST_MANAGER, "description") == "phone"
    assert REQUEST_SERVICES not in {REQUEST_BUY, REQUEST_SELL}
    assert "vin_optional" not in FLOW_STEPS[REQUEST_SERVICES]
    assert "vin_optional" not in FLOW_STEPS[REQUEST_MANAGER]


def test_vin_validation_only_when_entering() -> None:
    from services.auto_client_flow_engine import validate_text_step

    ok, error, _ = validate_text_step("brand", "BMW", flow_type="buy_car")
    assert ok

    ok, error, _ = validate_text_step("vin", "SHORT", flow_type="buy_car")
    assert not ok
    assert error


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
        "auto_client_collect_photos",
        "auto_client_collecting_text",
        "auto_client_vin_action",
        "auto_client_phone_text",
    }
    assert required.issubset(handler_names)


def test_flow_type_mapping() -> None:
    from database.models.auto_client_request import AutoClientRequestType
    from services.pg_auto_client_request_engine import FLOW_TYPE_TO_DB

    assert FLOW_TYPE_TO_DB["buy_car"] == AutoClientRequestType.AUTO_SEARCH.value
    assert FLOW_TYPE_TO_DB["services"] == AutoClientRequestType.AUTO_SERVICES.value


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
    test_flow_steps_defined()
    test_vin_validation_only_when_entering()
    test_router_handlers_registered()
    test_flow_type_mapping()
    test_lead_snapshot_has_client_fields()
    print("auto_client_pipeline: OK")


if __name__ == "__main__":
    main()
