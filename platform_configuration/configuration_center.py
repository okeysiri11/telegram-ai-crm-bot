# ConfigurationCenter — single configuration provider for the entire platform.

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from platform_configuration.env_source import (
    env_snapshot_redacted,
    getenv,
    getenv_bool,
    getenv_float,
    getenv_int,
    load_environment,
    optional_telegram_id,
)
from platform_configuration.settings import (
    AISettings,
    AssignmentSettings,
    DatabaseSettings,
    EventBusSettings,
    FeatureFlags,
    JWTSettings,
    ManagementSettings,
    NotificationSettings,
    OperationsSettings,
    PlatformSettings,
    PluginSettings,
    PricingSettings,
    RealtimeSettings,
    RedisSettings,
    SecuritySettings,
    StorageSettings,
    TelegramSettings,
    WorkflowSettings,
)

logger = logging.getLogger(__name__)

Observer = Callable[["ConfigurationCenter"], None]

_INSECURE_JWT_SECRETS = frozenset(
    {"", "change-me-in-production", "change-me-in-production-api-jwt-secret"}
)


@dataclass
class ConfigurationValidationReport:
    ok: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    providers: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "errors": self.errors,
            "warnings": self.warnings,
            "providers": self.providers,
        }


class ConfigurationCenter:
    """Loads, validates, and serves typed platform configuration."""

    def __init__(self) -> None:
        self._settings: PlatformSettings | None = None
        self._runtime_overrides: dict[str, Any] = {}
        self._observers: list[Observer] = []
        self._providers_loaded: list[str] = []

    @property
    def settings(self) -> PlatformSettings:
        if self._settings is None:
            self.load()
        assert self._settings is not None
        return self._settings

    def load(self, *, overrides: dict[str, Any] | None = None) -> PlatformSettings:
        load_environment()
        self._providers_loaded = ["environment", ".env"]
        if overrides:
            self._runtime_overrides.update(overrides)
            self._providers_loaded.append("runtime_overrides")

        env = self._runtime_overrides.get("environment") or getenv("ENVIRONMENT", "development")
        is_production = str(env).lower() in {"production", "prod"}
        postgres_only = getenv_bool("POSTGRES_ONLY", True)
        redis_url = getenv("REDIS_URL", "")
        redis_required = getenv_bool("REDIS_REQUIRED", False) or is_production or postgres_only

        owner_id = optional_telegram_id("OWNER_ID")
        platform_owner = optional_telegram_id("PLATFORM_OWNER_TELEGRAM_ID") or owner_id

        jwt_secret = getenv("JWT_SECRET", "change-me-in-production")
        iam_secret = getenv("IAM_JWT_SECRET", jwt_secret)
        openrouter_key = getenv("OPENROUTER_API_KEY", "")

        self._settings = PlatformSettings(
            database=DatabaseSettings(
                url=getenv(
                    "DATABASE_URL",
                    "postgresql+asyncpg://postgres:postgres@localhost:5432/ai_ecosystem",
                ),
                postgres_only=postgres_only,
            ),
            redis=RedisSettings(url=redis_url, required=redis_required),
            jwt=JWTSettings(
                secret=jwt_secret,
                algorithm=getenv("JWT_ALGORITHM", "HS256"),
                expire_minutes=getenv_int("JWT_EXPIRE_MINUTES", 1440),
                iam_secret=iam_secret,
                iam_algorithm=getenv("IAM_JWT_ALGORITHM", "HS256"),
                access_token_minutes=getenv_int("IAM_ACCESS_TOKEN_MINUTES", 15),
                refresh_token_days=getenv_int("IAM_REFRESH_TOKEN_DAYS", 7),
                api_jwt_secret=getenv("API_JWT_SECRET", "change-me-in-production-api-jwt-secret"),
                api_jwt_ttl_hours=getenv_int("API_JWT_TTL_HOURS", 24),
                session_ttl_seconds=getenv_int("IAM_SESSION_TTL_SECONDS", 7 * 24 * 3600),
                login_secret=getenv("IAM_LOGIN_SECRET", ""),
            ),
            telegram=TelegramSettings(
                bot_token=getenv("BOT_TOKEN", ""),
                bot_username=getenv("BOT_USERNAME", ""),
                owner_id=owner_id,
                platform_owner_telegram_id=platform_owner,
                platform_owner_name=getenv("PLATFORM_OWNER_NAME", "Platform Owner"),
                default_auto_manager_id=optional_telegram_id("DEFAULT_AUTO_MANAGER_ID"),
                default_dealer_manager_id=optional_telegram_id("DEFAULT_DEALER_MANAGER_ID"),
                default_agro_manager_id=optional_telegram_id("DEFAULT_AGRO_MANAGER_ID"),
                default_realty_manager_id=optional_telegram_id("DEFAULT_REALTY_MANAGER_ID"),
                marketing_channel_id=getenv("MARKETING_TELEGRAM_CHANNEL_ID", "") or None,
                bidex_channel_username=getenv("BIDEX_TELEGRAM_CHANNEL_USERNAME", "bidex_Odesa"),
                bidex_channel_id=getenv("BIDEX_TELEGRAM_CHANNEL_ID", "") or None,
                dealer_rates_channel_id=getenv("DEALER_RATES_TELEGRAM_CHANNEL_ID", "") or None,
                foma_rates_channel_id=getenv(
                    "FOMA_RATES_TELEGRAM_CHANNEL_ID",
                    getenv("DEALER_RATES_TELEGRAM_CHANNEL_ID", ""),
                )
                or None,
            ),
            ai=AISettings(
                openrouter_api_key=openrouter_key,
                providers_enabled=bool(openrouter_key),
            ),
            plugins=PluginSettings(
                enabled=True,
                directory=getenv("PLUGINS_DIRECTORY", "plugins"),
                hot_reload=getenv_bool("PLUGIN_HOT_RELOAD", False),
            ),
            workflow=WorkflowSettings(
                definitions_directory=getenv("WORKFLOW_DEFINITIONS_DIR", "workflows"),
                auto_reload=getenv_bool("WORKFLOW_AUTO_RELOAD", False),
                v2_enabled=getenv_bool("FEATURE_WORKFLOW_V2", False),
            ),
            realtime=RealtimeSettings(websocket_enabled=getenv_bool("REALTIME_ENABLED", True)),
            management=ManagementSettings(
                api_host=getenv("API_HOST", "0.0.0.0"),
                api_port=getenv_int("API_PORT", 8080),
                build_version=getenv("PLATFORM_BUILD_VERSION", "1.0.0"),
                platform_version=getenv("PLATFORM_VERSION", "2.0.0"),
                git_revision=getenv("GIT_REVISION", getenv("GIT_COMMIT", "unknown")),
            ),
            security=SecuritySettings(
                environment=str(env).lower(),
                log_level=getenv("LOG_LEVEL", "INFO"),
                sentry_dsn=getenv("SENTRY_DSN", ""),
                prometheus_enabled=getenv_bool("PROMETHEUS_ENABLED", True),
            ),
            storage=StorageSettings(
                media_provider=getenv("MEDIA_STORAGE_PROVIDER", "telegram"),
                media_local_cache=getenv_bool("MEDIA_LOCAL_CACHE", True),
                local_storage_dir=getenv("LOCAL_STORAGE_DIR", "data/media_cache"),
                media_cdn_base_url=getenv("MEDIA_CDN_BASE_URL", ""),
                s3_bucket=getenv("S3_BUCKET", ""),
                s3_region=getenv("S3_REGION", "eu-central-1"),
                s3_endpoint_url=getenv("S3_ENDPOINT_URL", ""),
                s3_access_key=getenv("S3_ACCESS_KEY", ""),
                s3_secret_key=getenv("S3_SECRET_KEY", ""),
            ),
            event_bus=EventBusSettings(
                max_retries=getenv_int("EVENT_BUS_MAX_RETRIES", 5),
                retry_delay_seconds=getenv_float("EVENT_BUS_RETRY_DELAY_SECONDS", 2.0),
                handler_timeout_seconds=getenv_float("EVENT_BUS_HANDLER_TIMEOUT_SECONDS", 30.0),
                worker_count=getenv_int("EVENT_BUS_WORKER_COUNT", 2),
                poll_interval_seconds=getenv_float("EVENT_BUS_POLL_INTERVAL_SECONDS", 1.0),
            ),
            feature_flags=FeatureFlags(
                workflow_v2=getenv_bool("FEATURE_WORKFLOW_V2", False),
                plugin_hot_reload=getenv_bool("PLUGIN_HOT_RELOAD", False),
                memory_cache=getenv_bool("FEATURE_MEMORY_CACHE", True),
                experimental_ai=getenv_bool("FEATURE_EXPERIMENTAL_AI", False),
                multi_provider=getenv_bool("FEATURE_MULTI_PROVIDER", False),
                plugins_enabled=getenv_bool("FEATURE_PLUGINS_ENABLED", True),
                ai_providers=getenv_bool("FEATURE_AI_PROVIDERS", False),
                notifications_enabled=getenv_bool("FEATURE_NOTIFICATIONS_ENABLED", True),
            ),
            notifications=NotificationSettings(
                smtp_host=getenv("SMTP_HOST", ""),
                sms_provider_url=getenv("SMS_PROVIDER_URL", ""),
            ),
            operations=OperationsSettings(
                dashboard_ttl_seconds=getenv_int("OPS_DASHBOARD_TTL_SECONDS", 15),
            ),
            assignment=AssignmentSettings(
                extra_segments=getenv("SMART_ASSIGNMENT_EXTRA_SEGMENTS", ""),
            ),
            pricing=PricingSettings(
                company_margin=getenv("PRICING_COMPANY_MARGIN", "0.005"),
                liquidity_low_threshold=getenv("LIQUIDITY_LOW_THRESHOLD", "1000"),
                pool_limit_ratio=getenv("LIQUIDITY_POOL_LIMIT_RATIO", "0.9"),
            ),
        )
        self._sync_runtime_provider()
        return self._settings

    def _sync_runtime_provider(self) -> None:
        try:
            from platform_configuration.config_provider import config_provider

            flags = self.settings.feature_flags
            snapshot = {
                "feature_flags.experimental.workflow_v2": flags.workflow_v2,
                "feature_flags.plugins.hot_reload": flags.plugin_hot_reload,
                "feature_flags.ai.memory_cache": flags.memory_cache,
                "feature_flags.experimental.ai": flags.experimental_ai,
                "feature_flags.ai.multi_provider": flags.multi_provider,
                "feature_flags.plugins.enabled": flags.plugins_enabled,
                "feature_flags.ai.providers": flags.ai_providers,
                "feature_flags.notifications.enabled": flags.notifications_enabled,
                "workflow.definitions_auto_reload": self.settings.workflow.auto_reload,
                "general.environment": self.settings.security.environment,
                "general.log_level": self.settings.security.log_level,
            }
            config_provider.apply_snapshot({**config_provider.snapshot(), **snapshot})
            self._providers_loaded.append("config_provider")
        except Exception:
            logger.debug("config_provider_sync_skipped", exc_info=True)

    def validate(self, *, fail_fast: bool = False) -> ConfigurationValidationReport:
        s = self.settings
        report = ConfigurationValidationReport(ok=True, providers=list(self._providers_loaded))

        if not s.database.url or "postgresql" not in s.database.url:
            report.errors.append("DATABASE_URL must be a PostgreSQL URL")
        if s.redis.required and not s.redis.url:
            report.errors.append("REDIS_URL is required in production / POSTGRES_ONLY mode")
        if not s.telegram.bot_token:
            report.warnings.append("BOT_TOKEN is not set — Telegram bot will not start")
        if s.jwt.iam_secret in _INSECURE_JWT_SECRETS and s.is_production:
            report.errors.append("IAM_JWT_SECRET must be set to a secure value in production")
        if s.jwt.secret in _INSECURE_JWT_SECRETS and s.is_production:
            report.errors.append("JWT_SECRET must be set to a secure value in production")

        if s.plugins.directory and not Path(s.plugins.directory).exists():
            report.warnings.append(f"Plugin directory not found: {s.plugins.directory}")
        if s.workflow.definitions_directory and not Path(s.workflow.definitions_directory).exists():
            report.warnings.append(
                f"Workflow directory not found: {s.workflow.definitions_directory}"
            )
        if s.storage.local_storage_dir and not Path(s.storage.local_storage_dir).exists():
            report.warnings.append(
                f"Storage path not found (will be created): {s.storage.local_storage_dir}"
            )
        if s.ai.providers_enabled and not s.ai.openrouter_api_key:
            report.warnings.append("AI providers enabled but OPENROUTER_API_KEY is missing")

        report.ok = not report.errors
        if fail_fast and report.errors:
            raise RuntimeError("Configuration validation failed: " + "; ".join(report.errors))
        return report

    def reload(self, *, overrides: dict[str, Any] | None = None) -> PlatformSettings:
        logger.info("configuration_center_reload")
        if overrides:
            self._runtime_overrides.update(overrides)
        load_environment.cache_clear()
        settings = self.load()
        report = self.validate()
        self._notify_observers()
        self._publish_config_changed(report)
        return settings

    def subscribe(self, observer: Observer) -> None:
        self._observers.append(observer)

    def _notify_observers(self) -> None:
        for observer in list(self._observers):
            try:
                observer(self)
            except Exception:
                logger.exception("configuration_observer_failed")

    def _publish_config_changed(self, report: ConfigurationValidationReport) -> None:
        try:
            from events.configuration_events import ConfigurationChangedEvent
            from events.event_bus import publish

            event = ConfigurationChangedEvent(
                config_key="platform.settings",
                old_value=None,
                new_value={"validation": report.to_dict()},
                changed_by="configuration_center",
                reason="reload",
            )
            coro = publish(event, wait=False)
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(coro)
            except RuntimeError:
                asyncio.run(coro)
        except Exception:
            logger.debug("config_changed_event_skipped", exc_info=True)

    def diagnostics(self) -> dict[str, Any]:
        s = self.settings
        report = self.validate()
        return {
            "validation": report.to_dict(),
            "providers_loaded": self._providers_loaded,
            "environment_redacted": env_snapshot_redacted(),
            "feature_flags": s.feature_flags.model_dump(),
            "database": {"url": "***", "postgres_only": s.database.postgres_only},
            "redis": {"configured": bool(s.redis.url), "required": s.redis.required},
            "telegram": {
                "bot_configured": bool(s.telegram.bot_token),
                "owner_configured": s.telegram.platform_owner_telegram_id is not None,
            },
            "plugins": s.plugins.model_dump(),
            "workflow": s.workflow.model_dump(),
            "management": s.management.model_dump(),
        }

    def redacted_export(self) -> dict[str, Any]:
        s = self.settings
        return {
            "database": s.database.model_dump(),
            "redis": {"url": "***" if s.redis.url else "", "required": s.redis.required},
            "jwt": {
                "algorithm": s.jwt.algorithm,
                "expire_minutes": s.jwt.expire_minutes,
                "iam_algorithm": s.jwt.iam_algorithm,
                "access_token_minutes": s.jwt.access_token_minutes,
                "refresh_token_days": s.jwt.refresh_token_days,
                "secret_configured": s.jwt.secret not in _INSECURE_JWT_SECRETS,
                "iam_secret_configured": s.jwt.iam_secret not in _INSECURE_JWT_SECRETS,
            },
            "telegram": {
                **s.telegram.model_dump(exclude={"bot_token"}),
                "bot_token_configured": bool(s.telegram.bot_token),
            },
            "ai": {
                "providers_enabled": s.ai.providers_enabled,
                "openrouter_configured": bool(s.ai.openrouter_api_key),
            },
            "plugins": s.plugins.model_dump(),
            "workflow": s.workflow.model_dump(),
            "realtime": s.realtime.model_dump(),
            "management": s.management.model_dump(),
            "security": {
                "environment": s.security.environment,
                "log_level": s.security.log_level,
                "prometheus_enabled": s.security.prometheus_enabled,
                "sentry_configured": bool(s.security.sentry_dsn),
            },
            "storage": {
                **s.storage.model_dump(exclude={"s3_access_key", "s3_secret_key"}),
                "s3_configured": bool(s.storage.s3_bucket),
            },
            "event_bus": s.event_bus.model_dump(),
            "feature_flags": s.feature_flags.model_dump(),
            "notifications": {
                "smtp_configured": bool(s.notifications.smtp_host),
                "sms_configured": bool(s.notifications.sms_provider_url),
            },
            "operations": s.operations.model_dump(),
            "assignment": s.assignment.model_dump(),
            "pricing": s.pricing.model_dump(),
        }


configuration_center = ConfigurationCenter()
