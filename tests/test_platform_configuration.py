"""Tests — Platform Configuration Center."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from events.configuration_events import ConfigurationChangedEvent
from events.event_bus import publish, reset_subscribers, subscribe
from events.handlers import reset_handler_registration
from platform_configuration.config_cache import ConfigCache
from platform_configuration.config_loader import env_overrides_for_seed, schema_defaults
from platform_configuration.config_provider import config_provider
from platform_configuration.config_repository import ConfigRepository
from platform_configuration.config_schema import PLATFORM_CONFIG_SCHEMA
from platform_configuration.config_service import (
    ConfigurationPermissionError,
    configuration_service,
)
from platform_configuration.config_validator import ConfigValidationError, ConfigValidator
from routers.admin.configuration_router import register_configuration_admin_routes


@pytest.fixture(autouse=True)
def _clean_state():
    reset_subscribers()
    reset_handler_registration()
    config_provider.reset_snapshot()
    yield
    reset_subscribers()
    reset_handler_registration()
    config_provider.reset_snapshot()


def _entry(key: str, value, *, version: int = 1):
    row = MagicMock()
    row.key = key
    row.section = key.split(".", 1)[0]
    row.value = value
    row.value_type = "json"
    row.version = version
    row.description = None
    row.updated_by = "tester"
    row.updated_at = datetime.now(timezone.utc)
    return row


def _history(key: str, version: int, old_value, new_value, *, action: str = "set"):
    row = MagicMock()
    row.id = uuid.uuid4()
    row.config_key = key
    row.version = version
    row.old_value = old_value
    row.new_value = new_value
    row.action = action
    row.changed_by = "tester"
    row.reason = "test"
    row.changed_at = datetime.now(timezone.utc)
    return row


@pytest.fixture
def mock_session_cm():
    mock_cm = AsyncMock()
    mock_cm.__aenter__.return_value = AsyncMock()
    mock_cm.__aexit__.return_value = None
    return mock_cm


def test_schema_defaults_cover_hierarchy():
    sections = {spec.section.value for spec in PLATFORM_CONFIG_SCHEMA.values()}
    assert "general" in sections
    assert "feature_flags" in sections
    assert "smart_assignment" in sections
    defaults = schema_defaults()
    assert defaults["sla.assignment_sec"] == 900
    assert defaults["feature_flags.verticals.auto"] is True


def test_config_validator_rejects_invalid_assignment_mode():
    with pytest.raises(ConfigValidationError):
        ConfigValidator.validate_value("smart_assignment.mode", "INVALID")


def test_config_validator_coerces_bool():
    assert ConfigValidator.validate_value("escalation.owner_enabled", "yes") is True


def test_config_provider_reads_schema_defaults():
    assert config_provider.get("sla.first_response_sec") == 1800
    assert config_provider.is_vertical_enabled("auto") is True


def test_config_provider_applies_snapshot():
    config_provider.apply_snapshot({"sla.assignment_sec": 1200})
    assert config_provider.get("sla.assignment_sec") == 1200


@pytest.mark.asyncio
async def test_configuration_cache_memory_ttl():
    cache = ConfigCache(ttl_seconds=60)
    await cache.set("sla.assignment_sec", {"value": 900, "version": 1})
    cached = await cache.get("sla.assignment_sec")
    assert cached["value"] == 900
    await cache.delete("sla.assignment_sec")
    assert await cache.get("sla.assignment_sec") is None


@pytest.mark.asyncio
async def test_configuration_service_set_publishes_event(mock_session_cm):
    key = "sla.assignment_sec"
    entry = _entry(key, 1200, version=2)
    history = _history(key, 2, 900, 1200)

    repo = MagicMock()
    repo.upsert = AsyncMock(return_value=(entry, history))
    repo.get_entry = AsyncMock(return_value=None)

    seen: list[ConfigurationChangedEvent] = []

    async def handler(event: ConfigurationChangedEvent) -> None:
        seen.append(event)

    subscribe(ConfigurationChangedEvent, handler, handler_id="cfg_test")

    async def publish_wait(event, *, wait=False):
        return await publish(event, wait=True)

    with patch("platform_configuration.config_service.get_session", return_value=mock_session_cm), patch(
        "platform_configuration.config_service.ConfigRepository",
        wraps=ConfigRepository,
    ) as repo_cls, patch(
        "platform_configuration.config_service.config_cache.set",
        new_callable=AsyncMock,
    ), patch(
        "platform_configuration.config_service.config_cache.invalidate_section",
        new_callable=AsyncMock,
    ), patch(
        "platform_configuration.config_service.publish",
        side_effect=publish_wait,
    ):
        repo_cls.return_value = repo
        result = await configuration_service.set(
            key,
            1200,
            changed_by="system",
            reason="unit_test",
        )

    assert result["key"] == key
    assert result["value"] == 1200
    assert len(seen) == 1
    assert seen[0].config_key == key
    assert seen[0].old_value == 900
    assert seen[0].new_value == 1200
    assert config_provider.get(key) == 1200


@pytest.mark.asyncio
async def test_configuration_service_rollback(mock_session_cm):
    key = "smart_assignment.mode"
    entry = _entry(key, "ROUND_ROBIN", version=3)
    history = _history(key, 3, "SMART", "ROUND_ROBIN", action="rollback")

    repo = MagicMock()
    repo.rollback_to_version = AsyncMock(return_value=(entry, history))

    with patch("platform_configuration.config_service.get_session", return_value=mock_session_cm), patch(
        "platform_configuration.config_service.ConfigRepository",
        wraps=ConfigRepository,
    ) as repo_cls, patch(
        "platform_configuration.config_service.config_cache.set",
        new_callable=AsyncMock,
    ), patch(
        "platform_configuration.config_service.config_cache.invalidate_section",
        new_callable=AsyncMock,
    ), patch(
        "platform_configuration.config_service.publish",
        new_callable=AsyncMock,
    ):
        repo_cls.return_value = repo
        result = await configuration_service.rollback(
            key,
            2,
            changed_by="system",
            reason="rollback_test",
        )

    assert result is not None
    assert result["value"] == "ROUND_ROBIN"
    assert config_provider.get(key) == "ROUND_ROBIN"


@pytest.mark.asyncio
async def test_configuration_service_delete(mock_session_cm):
    key = "feature_flags.experimental.workflow_v2"
    history = _history(key, 2, False, None, action="delete")

    repo = MagicMock()
    repo.get_entry = AsyncMock(return_value=_entry(key, False))
    repo.delete_key = AsyncMock(return_value=history)

    with patch("platform_configuration.config_service.get_session", return_value=mock_session_cm), patch(
        "platform_configuration.config_service.ConfigRepository",
        wraps=ConfigRepository,
    ) as repo_cls, patch(
        "platform_configuration.config_service.config_cache.delete",
        new_callable=AsyncMock,
    ), patch(
        "platform_configuration.config_service.config_cache.invalidate_section",
        new_callable=AsyncMock,
    ), patch(
        "platform_configuration.config_service.publish",
        new_callable=AsyncMock,
    ):
        repo_cls.return_value = repo
        config_provider.update_key(key, False)
        result = await configuration_service.delete(key, changed_by="system")

    assert result is not None
    assert result["action"] == "delete"
    assert key not in config_provider.snapshot()


@pytest.mark.asyncio
async def test_configuration_service_get_uses_cache(mock_session_cm):
    key = "sla.close_sec"
    cache = ConfigCache(ttl_seconds=60)
    await cache.set(key, {"value": 999, "version": 1})

    with patch("platform_configuration.config_service.config_cache", cache):
        value = await configuration_service.get(key)

    assert value == 999


@pytest.mark.asyncio
async def test_configuration_service_validate_payload():
    result = await configuration_service.validate(
        {"sla.assignment_sec": 600, "escalation.owner_enabled": True}
    )
    assert result["valid"] is True
    assert result["values"]["sla.assignment_sec"] == 600


@pytest.mark.asyncio
async def test_configuration_service_export_import(mock_session_cm):
    export_payload = {
        "version": 1,
        "entries": {
            "notifications.enabled": {"value": False, "section": "notifications"},
        },
    }

    repo = MagicMock()
    repo.export_all = AsyncMock(return_value=export_payload)
    repo.import_entries = AsyncMock(return_value=["notifications.enabled"])
    repo.get_entry = AsyncMock(return_value=_entry("notifications.enabled", False))

    with patch("platform_configuration.config_service.get_session", return_value=mock_session_cm), patch(
        "platform_configuration.config_service.ConfigRepository",
        wraps=ConfigRepository,
    ) as repo_cls, patch(
        "platform_configuration.config_service.config_cache.clear",
        new_callable=AsyncMock,
    ), patch(
        "platform_configuration.config_service.config_cache.delete",
        new_callable=AsyncMock,
    ), patch(
        "platform_configuration.config_service.publish",
        new_callable=AsyncMock,
    ):
        repo_cls.return_value = repo
        exported = await configuration_service.export()
        imported = await configuration_service.import_config(
            export_payload,
            changed_by="import",
        )

    assert exported["entries"]["notifications.enabled"]["value"] is False
    assert imported["imported"] == 1


@pytest.mark.asyncio
async def test_configuration_permission_denied_without_actor():
    with pytest.raises(ConfigurationPermissionError):
        await configuration_service.set("sla.assignment_sec", 500)


@pytest.mark.asyncio
async def test_configuration_permission_allowed_for_owner():
    with patch(
        "services.pg_platform_permissions_engine.PlatformPermissionsEngineV1.user_has_permission",
        new_callable=AsyncMock,
        return_value=True,
    ), patch(
        "platform_configuration.config_service.get_session",
    ) as get_session:
        mock_cm = AsyncMock()
        mock_cm.__aenter__.return_value = AsyncMock()
        mock_cm.__aexit__.return_value = None
        get_session.return_value = mock_cm

        entry = _entry("sla.assignment_sec", 500, version=2)
        history = _history("sla.assignment_sec", 2, 900, 500)
        repo = MagicMock()
        repo.upsert = AsyncMock(return_value=(entry, history))
        with patch(
            "platform_configuration.config_service.ConfigRepository",
            wraps=ConfigRepository,
        ) as repo_cls, patch(
            "platform_configuration.config_service.config_cache.set",
            new_callable=AsyncMock,
        ), patch(
            "platform_configuration.config_service.config_cache.invalidate_section",
            new_callable=AsyncMock,
        ), patch(
            "platform_configuration.config_service.publish",
            new_callable=AsyncMock,
        ):
            repo_cls.return_value = repo
            result = await configuration_service.set(
                "sla.assignment_sec",
                500,
                changed_by="admin",
                actor_telegram_id=42,
            )
    assert result["value"] == 500


@pytest.mark.asyncio
async def test_configuration_changed_event_audit_mapping():
    from audit.audit_event import AuditEventType, audit_record_from_event

    event = ConfigurationChangedEvent(
        config_key="sla.assignment_sec",
        action="set",
        section="sla",
        old_value=900,
        new_value=600,
        version=2,
        changed_by="admin",
        reason="tuning",
    )
    record = audit_record_from_event(event)
    assert record is not None
    assert record.event_type == AuditEventType.CONFIGURATION_CHANGED.value
    assert record.entity_id == "sla.assignment_sec"
    assert record.old_value == {"value": 900}
    assert record.new_value == {"value": 600}


@pytest.mark.asyncio
async def test_configuration_history_endpoint_shape(mock_session_cm):
    repo = MagicMock()
    repo.get_history = AsyncMock(return_value=[_history("sla.assignment_sec", 1, None, 900)])

    with patch("platform_configuration.config_service.get_session", return_value=mock_session_cm), patch(
        "platform_configuration.config_service.ConfigRepository",
        wraps=ConfigRepository,
    ) as repo_cls:
        repo_cls.return_value = repo
        history = await configuration_service.get_history("sla.assignment_sec")

    assert len(history) == 1
    assert history[0]["config_key"] == "sla.assignment_sec"
    assert history[0]["new_value"] == 900


@pytest.mark.asyncio
async def test_configuration_admin_routes():
    config_provider.apply_snapshot({"sla.assignment_sec": 900})

    app = web.Application()
    register_configuration_admin_routes(app)

    with patch(
        "platform_configuration.config_service.configuration_service.get",
        new_callable=AsyncMock,
        return_value=900,
    ):
        async with TestClient(TestServer(app)) as client:
            list_resp = await client.get("/api/v1/configuration")
            assert list_resp.status == 200
            body = await list_resp.json()
            assert "configuration" in body

            get_resp = await client.get("/api/v1/configuration/sla.assignment_sec")
            assert get_resp.status == 200
            assert (await get_resp.json())["value"] == 900


def test_env_overrides_for_seed_mapping(monkeypatch):
    monkeypatch.setenv("SLA_ASSIGNMENT_SEC", "777")
    monkeypatch.setenv("ASSIGNMENT_MODE", "ROUND_ROBIN")
    overrides = env_overrides_for_seed()
    assert overrides["sla.assignment_sec"] == 777
    assert overrides["smart_assignment.mode"] == "ROUND_ROBIN"


@pytest.mark.asyncio
async def test_hot_reload_assignment_mode_without_restart():
    config_provider.apply_snapshot({"smart_assignment.mode": "SMART"})
    from services.smart_assignment_service import SmartAssignmentService

    assert SmartAssignmentService.strategy_name() == "SMART"
    config_provider.update_key("smart_assignment.mode", "ROUND_ROBIN")
    assert SmartAssignmentService.strategy_name() == "ROUND_ROBIN"


def test_feature_flag_helpers():
    config_provider.apply_snapshot(
        {
            "feature_flags.assignment.smart": False,
            "feature_flags.assignment.round_robin": True,
            "smart_assignment.mode": "SMART",
        }
    )
    assert config_provider.resolve_assignment_mode() == "ROUND_ROBIN"
    assert config_provider.is_notification_enabled() is True
    assert config_provider.is_plugin_enabled() is True


@pytest.mark.asyncio
async def test_assignment_strategy_fallback_when_disabled():
    config_provider.apply_snapshot(
        {
            "feature_flags.assignment.smart": False,
            "feature_flags.assignment.round_robin": True,
            "smart_assignment.mode": "SMART",
        }
    )
    from services.smart_assignment_service import SmartAssignmentService

    assert SmartAssignmentService.strategy_name() == "ROUND_ROBIN"


@pytest.mark.asyncio
async def test_configuration_import_alias():
    assert hasattr(configuration_service, "import_")
    assert configuration_service.import_ is configuration_service.import_config


@pytest.mark.asyncio
async def test_read_permission_denied():
    with patch(
        "services.pg_platform_permissions_engine.PlatformPermissionsEngineV1.user_has_permission",
        new_callable=AsyncMock,
        return_value=False,
    ):
        with pytest.raises(ConfigurationPermissionError):
            await configuration_service.get(
                "sla.assignment_sec",
                actor_telegram_id=99,
            )


@pytest.mark.asyncio
async def test_workflow_reload_on_config_change():
    config_provider.apply_snapshot({"workflow.definitions_auto_reload": True})
    reloaded: list[int] = []

    with patch(
        "platform_sdk.workflow_loader.sdk_workflow_loader.reload",
        return_value=3,
    ) as reload_mock:
        from events.handlers.configuration_handler import ConfigurationEventHandler

        await ConfigurationEventHandler.handle(
            ConfigurationChangedEvent(
                config_key="workflow.definitions_auto_reload",
                section="workflow",
                action="set",
                old_value=False,
                new_value=True,
            )
        )
        reload_mock.assert_called_once()


@pytest.mark.asyncio
async def test_configuration_admin_delete_and_history_routes(mock_session_cm):
    key = "notifications.enabled"
    history = _history(key, 2, True, None, action="delete")
    repo = MagicMock()
    repo.get_entry = AsyncMock(return_value=_entry(key, True))
    repo.delete_key = AsyncMock(return_value=history)
    repo.get_history = AsyncMock(return_value=[history])

    app = web.Application()
    register_configuration_admin_routes(app)

    with patch(
        "platform_configuration.config_service.get_session",
        return_value=mock_session_cm,
    ), patch(
        "platform_configuration.config_service.ConfigRepository",
        wraps=ConfigRepository,
    ) as repo_cls, patch(
        "platform_configuration.config_service.config_cache.delete",
        new_callable=AsyncMock,
    ), patch(
        "platform_configuration.config_service.config_cache.invalidate_section",
        new_callable=AsyncMock,
    ), patch(
        "platform_configuration.config_service.publish",
        new_callable=AsyncMock,
    ):
        repo_cls.return_value = repo
        async with TestClient(TestServer(app)) as client:
            delete_resp = await client.request(
                "DELETE",
                f"/api/v1/configuration/{key}",
                json={"changed_by": "system"},
            )
            assert delete_resp.status == 200

            history_resp = await client.get(f"/api/v1/configuration/{key}/history")
            assert history_resp.status == 200
            body = await history_resp.json()
            assert body["key"] == key
            assert len(body["history"]) == 1


@pytest.mark.asyncio
async def test_vertical_registry_enabled_filter():
    from platform_sdk.vertical_registry import VerticalRegistry
    from platform_sdk.verticals.auto_vertical import AutoVertical

    VerticalRegistry.reset_singleton()
    registry = VerticalRegistry()
    registry.clear()
    registry.register(AutoVertical)
    config_provider.apply_snapshot({"feature_flags.verticals.auto": False})
    assert "auto" in registry.list_codes()
    assert "auto" not in registry.list_enabled_codes()
    entry = registry.list()[0]
    assert entry["enabled"] is False

