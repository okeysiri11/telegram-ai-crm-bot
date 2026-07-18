"""Tests — ConfigurationCenter typed settings, validation, reload, feature flags."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from platform_configuration.configuration_center import ConfigurationCenter, configuration_center
from platform_configuration.config_provider import config_provider


@pytest.fixture(autouse=True)
def _reset_center():
    from platform_configuration.env_source import load_environment

    load_environment.cache_clear()
    configuration_center._settings = None  # noqa: SLF001
    configuration_center._runtime_overrides.clear()  # noqa: SLF001
    configuration_center._providers_loaded.clear()  # noqa: SLF001
    config_provider.reset_snapshot()
    yield
    load_environment.cache_clear()
    configuration_center._settings = None  # noqa: SLF001
    configuration_center._runtime_overrides.clear()  # noqa: SLF001
    configuration_center._providers_loaded.clear()  # noqa: SLF001
    config_provider.reset_snapshot()


def test_loads_typed_settings():
    center = ConfigurationCenter()
    settings = center.load()
    assert settings.database.url
    assert "postgresql" in settings.database.url
    assert settings.feature_flags.memory_cache is True
    assert settings.jwt.session_ttl_seconds > 0


def test_validation_passes_in_development():
    center = ConfigurationCenter()
    center.load(overrides={"environment": "development"})
    report = center.validate()
    assert report.ok is True
    assert not report.errors


def test_validation_fail_fast_on_insecure_production_jwt(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("IAM_JWT_SECRET", "change-me-in-production")
    center = ConfigurationCenter()
    center.load()
    with pytest.raises(RuntimeError, match="IAM_JWT_SECRET"):
        center.validate(fail_fast=True)


def test_override_priority_env_wins(monkeypatch):
    monkeypatch.setenv("OPS_DASHBOARD_TTL_SECONDS", "99")
    center = ConfigurationCenter()
    settings = center.load()
    assert settings.operations.dashboard_ttl_seconds == 99


def test_feature_flags_sync_to_config_provider(monkeypatch):
    monkeypatch.setenv("FEATURE_WORKFLOW_V2", "true")
    monkeypatch.setenv("PLUGIN_HOT_RELOAD", "1")
    center = ConfigurationCenter()
    center.load()
    assert config_provider.get("feature_flags.experimental.workflow_v2") is True
    assert config_provider.get("feature_flags.plugins.hot_reload") is True


def test_runtime_reload_notifies_observers(monkeypatch):
    monkeypatch.setenv("FEATURE_EXPERIMENTAL_AI", "false")
    center = ConfigurationCenter()
    center.load()
    seen: list[bool] = []

    def observer(c: ConfigurationCenter) -> None:
        seen.append(c.settings.feature_flags.experimental_ai)

    center.subscribe(observer)
    monkeypatch.setenv("FEATURE_EXPERIMENTAL_AI", "true")
    center.reload()
    assert seen == [True]
    assert center.settings.feature_flags.experimental_ai is True


def test_diagnostics_redacts_secrets():
    center = ConfigurationCenter()
    center.load()
    export = center.redacted_export()
    assert export["redis"]["url"] == "***" or export["redis"]["url"] == ""
    assert "secret" not in export["jwt"] or export["jwt"].get("secret") is None
    assert export["feature_flags"]["workflow_v2"] is False


def test_missing_redis_required_in_production(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("POSTGRES_ONLY", "true")
    monkeypatch.setenv("REDIS_URL", "")
    center = ConfigurationCenter()
    center.load()
    report = center.validate()
    assert any("REDIS_URL" in err for err in report.errors)


def test_config_changed_event_on_reload(monkeypatch):
    from events.configuration_events import ConfigurationChangedEvent
    from events.event_bus import reset_subscribers, subscribe

    reset_subscribers()
    captured: list[str] = []

    async def handler(event: ConfigurationChangedEvent) -> None:
        captured.append(event.config_key)

    subscribe(ConfigurationChangedEvent, handler)
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    configuration_center.reload()
    assert captured == ["platform.settings"]


def test_singleton_settings_property_loads_lazily():
    s = configuration_center.settings
    assert s.security.environment
