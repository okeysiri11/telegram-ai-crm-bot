# Optional VIN flow tests — client scenarios without Telegram/DB.

from __future__ import annotations

VALID_VIN = "1HGCM82633A004352"


def test_no_flow_starts_with_vin() -> None:
    from services.auto_client_flow_engine import FLOW_STEPS, first_step

    for flow_type, steps in FLOW_STEPS.items():
        assert first_step(flow_type) != "vin"
        assert first_step(flow_type) != "vin_optional"
        assert steps[0] != "vin"
        assert steps[0] != "vin_optional"


def test_unified_car_flow_order() -> None:
    from services.auto_client_flow_engine import (
        FLOW_STEPS,
        REQUEST_BUY,
        REQUEST_LISTING,
        REQUEST_SELL,
    )

    expected = (
        "brand",
        "model",
        "year",
        "engine",
        "color",
        "description",
        "photos",
        "phone",
        "vin_optional",
    )
    for flow_type in (REQUEST_BUY, REQUEST_SELL, REQUEST_LISTING):
        assert FLOW_STEPS[flow_type] == expected
        assert FLOW_STEPS[flow_type].index("phone") < FLOW_STEPS[flow_type].index(
            "vin_optional"
        )
        assert FLOW_STEPS[flow_type].index("photos") < FLOW_STEPS[flow_type].index(
            "phone"
        )


def test_request_without_vin() -> None:
    from services.auto_client_flow_engine import (
        build_description,
        build_manager_notification_lines,
        vin_present,
    )

    data = {
        "brand": "BMW",
        "model": "X5",
        "year": 2021,
        "engine": "3.0",
        "color": "чёрный",
        "user_description": "Нужен автоподбор",
        "photo_file_ids": [],
        "vin": None,
    }
    assert vin_present(data) is False
    description = build_description("buy_car", data)
    assert "VIN" not in description
    assert "BMW" in description

    lines = build_manager_notification_lines(
        flow_type="buy_car",
        request_number="AUTO-0001",
        data=data,
        client_username="client",
        client_full_name="Test Client",
        client_phone="+380501112233",
    )
    text = "\n".join(lines)
    assert "VIN_PRESENT=False" in text
    assert "Поиск автомобиля" in text


def test_request_with_vin() -> None:
    from services.auto_client_flow_engine import (
        build_description,
        build_manager_notification_lines,
        validate_text_step,
        vin_present,
    )

    ok, error, value = validate_text_step("vin", VALID_VIN, flow_type="sell_car")
    assert ok, error
    assert value == VALID_VIN

    data = {
        "brand": "Toyota",
        "model": "Camry",
        "year": 2020,
        "engine": "2.5",
        "color": "белый",
        "user_description": "Продаю авто",
        "vin": value,
        "photo_file_ids": [],
    }
    assert vin_present(data) is True
    description = build_description("sell_car", data)
    assert VALID_VIN in description

    lines = build_manager_notification_lines(
        flow_type="sell_car",
        request_number="AUTO-0002",
        data=data,
        client_username=None,
        client_full_name="Seller",
        client_phone="+380671112233",
    )
    text = "\n".join(lines)
    assert "VIN_PRESENT=True" in text
    assert VALID_VIN in text


def test_request_with_photos_without_vin() -> None:
    from services.auto_client_flow_engine import (
        build_manager_notification_lines,
        vin_present,
    )

    data = {
        "brand": "Audi",
        "model": "A6",
        "year": 2019,
        "user_description": "Размещение объявления",
        "photo_file_ids": ["photo_a", "photo_b"],
        "vin": None,
    }
    assert vin_present(data) is False
    lines = build_manager_notification_lines(
        flow_type="listing",
        request_number="AUTO-0003",
        data=data,
        client_username="seller",
        client_full_name=None,
        client_phone="+380931112233",
    )
    text = "\n".join(lines)
    assert "Photos:" in text
    assert "2 attached" in text
    assert "VIN_PRESENT=False" in text


def test_request_with_photos_and_vin() -> None:
    from services.auto_client_flow_engine import (
        build_manager_notification_lines,
        vin_present,
    )

    data = {
        "brand": "Mercedes",
        "model": "E200",
        "year": 2022,
        "user_description": "С фото и VIN",
        "photo_file_ids": ["p1"],
        "vin": VALID_VIN,
    }
    assert vin_present(data) is True
    lines = build_manager_notification_lines(
        flow_type="listing",
        request_number="AUTO-0004",
        data=data,
        client_username="seller",
        client_full_name="Seller Name",
        client_phone="+380441112233",
    )
    text = "\n".join(lines)
    assert "1 attached" in text
    assert "VIN_PRESENT=True" in text
    assert VALID_VIN in text


def test_manager_delivery_payload_without_vin() -> None:
    """Manager notification must be buildable and deliverable without VIN."""
    from services.auto_client_flow_engine import build_manager_notification_lines

    lines = build_manager_notification_lines(
        flow_type="buy_car",
        request_number="AUTO-0099",
        data={
            "brand": "Kia",
            "model": "Sportage",
            "year": 2018,
            "user_description": "автоподбор без VIN",
            "photo_file_ids": [],
            "vin": None,
        },
        client_username="buyer",
        client_full_name="Buyer",
        client_phone="+380991112233",
    )
    text = "\n".join(lines)
    assert "AUTO-0099" in text
    assert "VIN_PRESENT=False" in text
    assert "+380991112233" in text
    # Delivery path uses the same lines; empty VIN must not block message body.
    assert "Новый лид" in text


def test_vin_buttons_are_yes_no() -> None:
    from keyboards import auto_client_vin_inline

    markup = auto_client_vin_inline()
    texts = [btn.text for row in markup.inline_keyboard for btn in row]
    callbacks = [btn.callback_data for row in markup.inline_keyboard for btn in row]
    assert "Да" in texts
    assert "Нет" in texts
    assert "ac:vin:add" in callbacks
    assert "ac:vin:skip" in callbacks


def test_dealer_add_car_starts_with_make() -> None:
    from pathlib import Path

    src = Path("auto_vertical_handlers.py").read_text(encoding="utf-8")
    assert '"step": "make"' in src or "'step': 'make'" in src
    assert "Введите VIN автомобиля (17 символов)" not in src
    assert "Хотите добавить VIN автомобиля?" in src
    assert "VIN_PRESENT" in src


def test_submit_accepts_null_vin_signature() -> None:
    import inspect

    from services.pg_auto_client_request_engine import AutoClientRequestEngineV1

    sig = inspect.signature(AutoClientRequestEngineV1.submit)
    assert "vin" in sig.parameters
    assert sig.parameters["vin"].default is None


def main() -> None:
    test_no_flow_starts_with_vin()
    test_unified_car_flow_order()
    test_request_without_vin()
    test_request_with_vin()
    test_request_with_photos_without_vin()
    test_request_with_photos_and_vin()
    test_manager_delivery_payload_without_vin()
    test_vin_buttons_are_yes_no()
    test_dealer_add_car_starts_with_make()
    test_submit_accepts_null_vin_signature()
    print("optional_vin_flow: OK")


if __name__ == "__main__":
    main()
