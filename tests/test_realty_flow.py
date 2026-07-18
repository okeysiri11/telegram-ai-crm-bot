"""Integration tests — REALTY vertical flows."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from config import DEFAULT_REALTY_MANAGER_ID
from services.manager_service import manager_service
from services.realty_flow_engine import (
    SCENARIO_BUY,
    SCENARIO_RENT,
    SCENARIO_SELL,
    build_description,
    first_step,
    next_step,
    pending_key,
    submit_realty_request,
    validate_text_step,
)
from services.system_roles import Vertical
from states.realty_flow_states import REALTY_PENDING_RESTORE, RealtyFlow


@pytest.mark.asyncio
async def test_rent_flow_step_sequence():
    assert first_step(SCENARIO_RENT) == "city"
    steps = []
    current = first_step(SCENARIO_RENT)
    while current:
        steps.append(current)
        current = next_step(SCENARIO_RENT, current)
    assert steps == list(("city", "district", "budget", "rooms", "notes", "photos", "contact"))


@pytest.mark.asyncio
async def test_buy_flow_step_sequence():
    assert first_step(SCENARIO_BUY) == "city"
    assert next_step(SCENARIO_BUY, "requirements") == "contact"


@pytest.mark.asyncio
async def test_sell_flow_step_sequence():
    assert first_step(SCENARIO_SELL) == "address"
    assert "photos" in (next_step(SCENARIO_SELL, "description"),)


@pytest.mark.asyncio
async def test_rent_validate_steps():
    ok, err, val = validate_text_step("city", "Kyiv")
    assert ok and val == "Kyiv"

    ok, err, val = validate_text_step("rooms", "3")
    assert ok and val == 3

    ok, err, val = validate_text_step("notes", "-")
    assert ok and val == ""


@pytest.mark.asyncio
async def test_rent_request_submit(client_user_id):
    data = {
        "object_type": "apartment",
        "city": "Kyiv",
        "district": "Pechersk",
        "budget": "1500 USD",
        "rooms": 2,
        "notes": "Near metro",
        "contact": "+380501234567",
        "photo_file_ids": ["p1", "p2"],
    }

    with patch(
        "services.request_service.request_service.create_request",
        new=AsyncMock(
            return_value={
                "request_number": "REALTY-00001",
                "request_type": "REALTY_RENT_APARTMENT",
            }
        ),
    ) as create:
        result = await submit_realty_request(
            scenario=SCENARIO_RENT,
            data=data,
            client_telegram_id=client_user_id,
            client_name="Test Client",
        )

    assert result["request_number"] == "REALTY-00001"
    create.assert_awaited_once()
    kwargs = create.call_args.kwargs
    assert kwargs["vertical"] == "realty"
    assert kwargs["request_type"] == "REALTY_RENT_APARTMENT"
    assert kwargs["city"] == "Kyiv"
    assert kwargs["photo_file_ids"] == ["p1", "p2"]
    assert kwargs["ai_qualification"]["scenario"] == SCENARIO_RENT


@pytest.mark.asyncio
async def test_buy_request_submit(client_user_id):
    with patch(
        "services.request_service.request_service.create_request",
        new=AsyncMock(return_value={"request_number": "REALTY-00002"}),
    ) as create:
        await submit_realty_request(
            scenario=SCENARIO_BUY,
            data={
                "object_type": "house",
                "city": "Odesa",
                "budget": "200000",
                "area": 120.5,
                "requirements": "Garage",
                "contact": "+380509999999",
            },
            client_telegram_id=client_user_id,
        )

    kwargs = create.call_args.kwargs
    assert kwargs["request_type"] == "REALTY_BUY_HOUSE"
    assert kwargs["budget"] == 200000.0


@pytest.mark.asyncio
async def test_sell_request_submit(client_user_id):
    with patch(
        "services.request_service.request_service.create_request",
        new=AsyncMock(return_value={"request_number": "REALTY-00003"}),
    ) as create:
        await submit_realty_request(
            scenario=SCENARIO_SELL,
            data={
                "object_type": "land",
                "address": "Village X",
                "area": 800,
                "price": "50000",
                "description": "Flat plot",
                "contact": "+380501111111",
                "photo_file_ids": ["land1"],
            },
            client_telegram_id=client_user_id,
        )

    kwargs = create.call_args.kwargs
    assert kwargs["request_type"] == "REALTY_SELL_LAND"
    assert kwargs["price"] == 50000.0
    assert kwargs["photo_file_ids"] == ["land1"]


@pytest.mark.asyncio
async def test_realty_photos_collection(mock_message, mock_fsm_context):
    from routers.realty_router import realty_collect_photo

    mock_message.photo = [MagicMock(file_id="photo_realty_1")]
    mock_fsm_context._store.update(
        {
            "scenario": SCENARIO_RENT,
            "flow_step": "photos",
            "photo_file_ids": [],
        }
    )
    await mock_fsm_context.set_state(RealtyFlow.awaiting_photos.state)

    with patch(
        "routers.realty_router.media_service.store_telegram_file",
        new=AsyncMock(return_value={"stored": True}),
    ):
        await realty_collect_photo(mock_message, mock_fsm_context)

    data = await mock_fsm_context.get_data()
    assert data["photo_file_ids"] == ["photo_realty_1"]


@pytest.mark.asyncio
async def test_realty_manager_from_pool():
    from services.manager_pool_service import manager_pool_service

    pool_mgr = {
        "user_id": str(uuid.uuid4()),
        "telegram_id": DEFAULT_REALTY_MANAGER_ID or 777777,
        "display_name": "Luc",
        "pool_id": str(uuid.uuid4()),
        "vertical": Vertical.REALTY.value,
    }
    with patch.object(
        manager_pool_service,
        "assign_manager",
        new=AsyncMock(return_value=pool_mgr),
    ):
        mgr = await manager_service.resolve_manager_for_vertical(Vertical.REALTY.value)
        assert mgr is not None
        assert mgr["telegram_id"] == pool_mgr["telegram_id"]


@pytest.mark.asyncio
async def test_request_service_uses_manager_for_realty(client_user_id):
    from services.request_service import request_service

    with patch(
        "services.manager_service.manager_service.resolve_manager_for_vertical",
        new=AsyncMock(
            return_value={
                "user_id": "00000000-0000-0000-0000-000000000001",
                "telegram_id": DEFAULT_REALTY_MANAGER_ID or 1,
                "display_name": "Luc",
            }
        ),
    ), patch(
        "repositories.request_repository.RequestRepository.next_crm_number",
        new=AsyncMock(return_value="REALTY-00099"),
    ), patch(
        "repositories.request_repository.RequestRepository.create_crm",
        new=AsyncMock(),
    ) as create, patch(
        "services.request_service.RequestService._publish_request_created",
        new=AsyncMock(),
    ) as publish_mock, patch(
        "services.notification_service.notification_service.notify_managers_new_request",
        new=AsyncMock(),
    ) as notify_mock:
        row = AsyncMock()
        row.id = "00000000-0000-0000-0000-000000000099"
        row.request_number = "REALTY-00099"
        row.request_type = "REALTY_RENT_APARTMENT"
        row.status = "NEW"
        row.client_telegram_id = client_user_id
        row.client_first_name = "Test"
        row.client_username = None
        row.description = "rent"
        row.manager_id = None
        row.created_at = None
        create.return_value = row

        result = await request_service.create_request(
            vertical="realty",
            client_telegram_id=client_user_id,
            product="rent",
            description="Kyiv apartment",
            request_type="REALTY_RENT_APARTMENT",
        )
        assert result["request_number"] == "REALTY-00099"
        create.assert_awaited_once()
        publish_mock.assert_awaited_once()
        notify_mock.assert_not_called()


@pytest.mark.asyncio
async def test_realty_role_service_client_access():
    from services.system_roles import SystemRole, role_has_access

    assert role_has_access(SystemRole.CLIENT, "create_request") is True


@pytest.mark.asyncio
async def test_restore_rent_photos_step(mock_message, mock_fsm_context):
    from routers.realty_router import restore_realty_fsm_from_pending

    pending = pending_key(SCENARIO_RENT, "photos")
    restored = await restore_realty_fsm_from_pending(mock_message, mock_fsm_context, pending)

    assert restored is True
    state = await mock_fsm_context.get_state()
    assert state == RealtyFlow.awaiting_photos.state
    data = await mock_fsm_context.get_data()
    assert data.get("scenario") == SCENARIO_RENT
    assert data.get("flow_step") == "photos"


@pytest.mark.asyncio
async def test_restore_sell_contact_step(mock_message, mock_fsm_context):
    from routers.realty_router import restore_realty_fsm_from_pending

    pending = pending_key(SCENARIO_SELL, "contact")
    restored = await restore_realty_fsm_from_pending(mock_message, mock_fsm_context, pending)

    assert restored is True
    state = await mock_fsm_context.get_state()
    assert state == RealtyFlow.awaiting_contact.state


def test_all_realty_flow_steps_have_pending_mapping():
    from services.realty_flow_engine import FLOW_STEPS

    for scenario, steps in FLOW_STEPS.items():
        for step in steps:
            key = pending_key(scenario, step)
            assert key in REALTY_PENDING_RESTORE, f"missing {key}"


def test_build_description_includes_rent_fields():
    text = build_description(
        SCENARIO_RENT,
        {
            "object_type": "apartment",
            "city": "Kyiv",
            "district": "Center",
            "budget": "1000",
            "rooms": 2,
            "photo_file_ids": ["x"],
        },
    )
    assert "Аренда" in text
    assert "Kyiv" in text
    assert "Фото: 1" in text
