"""Integration tests — FSM recovery from persisted pending state."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from services.auto_client_flow_engine import REQUEST_BUY, REQUEST_SELL, pending_key
from states.entry_flow_states import AUTO_CLIENT_PENDING_RESTORE, AutoClientFlow


@pytest.mark.asyncio
async def test_restore_buy_car_photos_step(mock_message, mock_fsm_context):
    from routers.auto_client_router import _restore_auto_client_fsm

    pending = pending_key(REQUEST_BUY, "photos")
    with patch(
        "routers.auto_client_router.VerticalOnboardingEngineV1.get_auto_client_pending",
        new=AsyncMock(return_value=pending),
    ):
        await _restore_auto_client_fsm(mock_message, mock_fsm_context)

    state = await mock_fsm_context.get_state()
    assert state == AutoClientFlow.awaiting_photos.state
    data = await mock_fsm_context.get_data()
    assert data.get("flow_type") == REQUEST_BUY
    assert data.get("flow_step") == "photos"


@pytest.mark.asyncio
async def test_restore_sell_car_vin_optional(mock_message, mock_fsm_context):
    from routers.auto_client_router import _restore_auto_client_fsm

    pending = pending_key(REQUEST_SELL, "vin_optional")
    with patch(
        "routers.auto_client_router.VerticalOnboardingEngineV1.get_auto_client_pending",
        new=AsyncMock(return_value=pending),
    ):
        await _restore_auto_client_fsm(mock_message, mock_fsm_context)

    state = await mock_fsm_context.get_state()
    assert state == AutoClientFlow.awaiting_vin_choice.state


def test_all_flow_steps_have_pending_mapping():
    from services.auto_client_flow_engine import FLOW_STEPS

    for flow_type, steps in FLOW_STEPS.items():
        for step in steps:
            key = pending_key(flow_type, step)
            assert key in AUTO_CLIENT_PENDING_RESTORE, f"missing {key}"


@pytest.mark.asyncio
async def test_redis_not_forced_by_postgres_only_in_development(monkeypatch):
    """Sprint 32.6B — POSTGRES_ONLY no longer forces Redis in development."""
    from platform_configuration.configuration_center import ConfigurationCenter
    from platform_configuration.env_source import load_environment

    monkeypatch.setenv("POSTGRES_ONLY", "true")
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("REDIS_REQUIRED", "false")
    load_environment.cache_clear()
    center = ConfigurationCenter()
    settings = center.load()
    assert settings.database.postgres_only is True
    assert settings.redis.required is False


@pytest.mark.asyncio
async def test_explicit_redis_required_true_in_development(monkeypatch):
    from platform_configuration.configuration_center import ConfigurationCenter
    from platform_configuration.env_source import load_environment

    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("REDIS_REQUIRED", "true")
    load_environment.cache_clear()
    center = ConfigurationCenter()
    settings = center.load()
    assert settings.redis.required is True


@pytest.mark.asyncio
async def test_production_always_requires_redis(monkeypatch):
    from platform_configuration.configuration_center import ConfigurationCenter
    from platform_configuration.env_source import load_environment

    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("REDIS_REQUIRED", "false")
    load_environment.cache_clear()
    center = ConfigurationCenter()
    settings = center.load()
    assert settings.redis.required is True

@pytest.mark.asyncio
async def test_fsm_storage_exits_without_redis_when_required(monkeypatch):
    import fsm_storage

    monkeypatch.setattr(fsm_storage, "REDIS_URL", "")
    monkeypatch.setattr(fsm_storage, "REDIS_REQUIRED", True)

    with pytest.raises(SystemExit):
        await fsm_storage.create_fsm_storage()
