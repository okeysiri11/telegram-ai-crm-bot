"""Unit tests — ErrorTrackingService."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.error_tracking_service import ErrorTrackingService, SOURCE_TELEGRAM


@pytest.mark.asyncio
async def test_extract_context_from_message():
    event = MagicMock()
    event.text = "hello"
    event.caption = None
    event.from_user = MagicMock(id=12345)

    state = AsyncMock()
    state.get_state.return_value = "AutoClientFlow:menu"
    state.get_data.return_value = {"request_number": "AUTO-1", "vertical": "auto"}

    handler = MagicMock()
    handler.callback.__name__ = "on_menu"

    data = {
        "event_from_user": event.from_user,
        "state": state,
        "handler": handler,
    }

    ctx = await ErrorTrackingService.extract_context(event, data)

    assert ctx["telegram_id"] == 12345
    assert ctx["payload"] == "hello"
    assert ctx["fsm_state"] == "AutoClientFlow:menu"
    assert ctx["request_id"] == "AUTO-1"
    assert ctx["vertical"] == "auto"
    assert ctx["handler_name"] == "on_menu"


@pytest.mark.asyncio
async def test_extract_context_from_callback():
    event = MagicMock()
    event.data = "auto:buy"
    event.from_user = MagicMock(id=99)

    ctx = await ErrorTrackingService.extract_context(event, {"event_from_user": event.from_user})

    assert ctx["telegram_id"] == 99
    assert ctx["payload"] == "auto:buy"


@pytest.mark.asyncio
async def test_capture_exception_is_non_blocking():
    exc = RuntimeError("boom")

    with patch.object(ErrorTrackingService, "_capture", new=AsyncMock()) as capture_mock, patch(
        "services.error_tracking_service.asyncio.get_running_loop",
    ) as get_loop:
        loop = MagicMock()
        get_loop.return_value = loop

        await ErrorTrackingService.capture_exception(
            exc,
            context={"telegram_id": 1, "handler_name": "test_handler"},
        )

        loop.create_task.assert_called_once()


@pytest.mark.asyncio
async def test_capture_persists_to_postgresql():
    exc = ValueError("bad input")
    context = {
        "telegram_id": 42,
        "vertical": "auto",
        "fsm_state": "AutoClientFlow:vin",
        "request_id": "AUTO-99",
        "handler_name": "handle_vin",
        "payload": "ABC",
    }

    mock_repo = AsyncMock()
    mock_cm = AsyncMock()
    mock_cm.__aenter__.return_value = AsyncMock()
    mock_cm.__aexit__.return_value = None

    with patch("services.error_tracking_service.get_session", return_value=mock_cm), patch(
        "services.error_tracking_service.ErrorEventRepository",
        return_value=mock_repo,
    ), patch.object(ErrorTrackingService, "_report_sentry") as sentry_mock:
        await ErrorTrackingService._capture(exc, context=context)

    mock_repo.record.assert_called_once()
    call_kwargs = mock_repo.record.call_args.kwargs
    assert call_kwargs["source"] == SOURCE_TELEGRAM
    assert call_kwargs["error_type"] == "ValueError"
    assert call_kwargs["context"] == context
    assert call_kwargs["stack_trace"]
    sentry_mock.assert_called_once()


@pytest.mark.asyncio
async def test_capture_persist_failure_does_not_raise():
    exc = RuntimeError("fail")

    mock_cm = AsyncMock()
    mock_cm.__aenter__.side_effect = RuntimeError("db down")

    with patch("services.error_tracking_service.get_session", return_value=mock_cm), patch.object(
        ErrorTrackingService,
        "_report_sentry",
    ):
        await ErrorTrackingService._capture(exc, context={"telegram_id": 1})


@pytest.mark.asyncio
async def test_middleware_swallows_handler_exception():
    from middleware.error_tracking_middleware import ErrorTrackingMiddleware

    middleware = ErrorTrackingMiddleware()
    event = MagicMock()
    data = {}

    async def bad_handler(_event, _data):
        raise RuntimeError("handler failed")

    with patch(
        "middleware.error_tracking_middleware.error_tracking_service.track_from_handler",
        new=AsyncMock(),
    ), patch(
        "middleware.error_tracking_middleware._notify_user",
        new=AsyncMock(),
    ):
        result = await middleware(bad_handler, event, data)

    assert result is None
