# Typed immutable platform settings — frozen configuration models.

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class DatabaseSettings(BaseModel):
    model_config = ConfigDict(frozen=True)

    url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/ai_ecosystem"
    )
    postgres_only: bool = True


class RedisSettings(BaseModel):
    model_config = ConfigDict(frozen=True)

    url: str = ""
    required: bool = False


class JWTSettings(BaseModel):
    model_config = ConfigDict(frozen=True)

    secret: str = "change-me-in-production"
    algorithm: str = "HS256"
    expire_minutes: int = 1440
    iam_secret: str = ""
    iam_algorithm: str = "HS256"
    access_token_minutes: int = 15
    refresh_token_days: int = 7
    api_jwt_secret: str = "change-me-in-production-api-jwt-secret"
    api_jwt_ttl_hours: int = 24
    session_ttl_seconds: int = 7 * 24 * 3600
    login_secret: str = ""


class TelegramSettings(BaseModel):
    model_config = ConfigDict(frozen=True)

    bot_token: str = ""
    bot_username: str = ""
    owner_id: int | None = None
    platform_owner_telegram_id: int | None = None
    platform_owner_name: str = "Platform Owner"
    default_auto_manager_id: int | None = None
    default_dealer_manager_id: int | None = None
    default_agro_manager_id: int | None = None
    default_realty_manager_id: int | None = None
    marketing_channel_id: str | None = None
    bidex_channel_username: str = "bidex_Odesa"
    bidex_channel_id: str | None = None
    dealer_rates_channel_id: str | None = None
    foma_rates_channel_id: str | None = None


class AISettings(BaseModel):
    model_config = ConfigDict(frozen=True)

    openrouter_api_key: str = ""
    providers_enabled: bool = False


class PluginSettings(BaseModel):
    model_config = ConfigDict(frozen=True)

    enabled: bool = True
    directory: str = "plugins"
    hot_reload: bool = False


class WorkflowSettings(BaseModel):
    model_config = ConfigDict(frozen=True)

    definitions_directory: str = "workflows"
    auto_reload: bool = False
    v2_enabled: bool = False


class RealtimeSettings(BaseModel):
    model_config = ConfigDict(frozen=True)

    websocket_enabled: bool = True


class ManagementSettings(BaseModel):
    model_config = ConfigDict(frozen=True)

    api_host: str = "0.0.0.0"
    api_port: int = 8080
    build_version: str = "1.0.0"
    platform_version: str = "2.0.0"
    git_revision: str = "unknown"


class SecuritySettings(BaseModel):
    model_config = ConfigDict(frozen=True)

    environment: str = "development"
    log_level: str = "INFO"
    sentry_dsn: str = ""
    prometheus_enabled: bool = True


class StorageSettings(BaseModel):
    model_config = ConfigDict(frozen=True)

    media_provider: str = "telegram"
    media_local_cache: bool = True
    local_storage_dir: str = "data/media_cache"
    media_cdn_base_url: str = ""
    s3_bucket: str = ""
    s3_region: str = "eu-central-1"
    s3_endpoint_url: str = ""
    s3_access_key: str = ""
    s3_secret_key: str = ""


class EventBusSettings(BaseModel):
    model_config = ConfigDict(frozen=True)

    max_retries: int = 5
    retry_delay_seconds: float = 2.0
    handler_timeout_seconds: float = 30.0
    worker_count: int = 2
    poll_interval_seconds: float = 1.0


class FeatureFlags(BaseModel):
    model_config = ConfigDict(frozen=True)

    workflow_v2: bool = False
    plugin_hot_reload: bool = False
    memory_cache: bool = True
    experimental_ai: bool = False
    multi_provider: bool = False
    plugins_enabled: bool = True
    ai_providers: bool = False
    notifications_enabled: bool = True


class NotificationSettings(BaseModel):
    model_config = ConfigDict(frozen=True)

    smtp_host: str = ""
    sms_provider_url: str = ""


class OperationsSettings(BaseModel):
    model_config = ConfigDict(frozen=True)

    dashboard_ttl_seconds: int = 15


class AssignmentSettings(BaseModel):
    model_config = ConfigDict(frozen=True)

    extra_segments: str = ""


class PricingSettings(BaseModel):
    model_config = ConfigDict(frozen=True)

    company_margin: str = "0.005"
    liquidity_low_threshold: str = "1000"
    pool_limit_ratio: str = "0.9"


class LegacyMigrationFlags(BaseModel):
    model_config = ConfigDict(frozen=True)

    legacy_users: bool = False
    legacy_requests: bool = False
    legacy_notifications: bool = False
    legacy_ai: bool = False
    legacy_handlers: bool = False
    legacy_scheduler: bool = False
    legacy_database: bool = False
    legacy_managers: bool = False
    legacy_workflow: bool = False
    legacy_configuration: bool = False


class PlatformSettings(BaseModel):
    model_config = ConfigDict(frozen=True)

    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    jwt: JWTSettings = Field(default_factory=JWTSettings)
    telegram: TelegramSettings = Field(default_factory=TelegramSettings)
    ai: AISettings = Field(default_factory=AISettings)
    plugins: PluginSettings = Field(default_factory=PluginSettings)
    workflow: WorkflowSettings = Field(default_factory=WorkflowSettings)
    realtime: RealtimeSettings = Field(default_factory=RealtimeSettings)
    management: ManagementSettings = Field(default_factory=ManagementSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    storage: StorageSettings = Field(default_factory=StorageSettings)
    event_bus: EventBusSettings = Field(default_factory=EventBusSettings)
    feature_flags: FeatureFlags = Field(default_factory=FeatureFlags)
    notifications: NotificationSettings = Field(default_factory=NotificationSettings)
    operations: OperationsSettings = Field(default_factory=OperationsSettings)
    assignment: AssignmentSettings = Field(default_factory=AssignmentSettings)
    pricing: PricingSettings = Field(default_factory=PricingSettings)
    legacy_migration: LegacyMigrationFlags = Field(default_factory=LegacyMigrationFlags)

    @property
    def is_production(self) -> bool:
        return self.security.environment in {"production", "prod"}
