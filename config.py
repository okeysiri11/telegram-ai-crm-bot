# Legacy config facade — all values sourced from ConfigurationCenter (no direct getenv).

from __future__ import annotations

import logging
from typing import Any

from platform_configuration.configuration_center import configuration_center

logger = logging.getLogger(__name__)

_settings = configuration_center.settings


def _refresh() -> None:
    global _settings
    _settings = configuration_center.settings


def reload_config() -> None:
    configuration_center.reload()
    _refresh()


# ---- Database / Redis / API ----
DATABASE_URL = _settings.database.url
POSTGRES_ONLY = _settings.database.postgres_only
ENVIRONMENT = _settings.security.environment
IS_PRODUCTION = _settings.is_production
REDIS_URL = _settings.redis.url
REDIS_REQUIRED = _settings.redis.required
API_HOST = _settings.management.api_host
API_PORT = _settings.management.api_port

# ---- Telegram ----
BOT_TOKEN = _settings.telegram.bot_token or None
BOT_USERNAME = _settings.telegram.bot_username
OPENROUTER_API_KEY = _settings.ai.openrouter_api_key or None
OWNER_ID = _settings.telegram.owner_id
PLATFORM_OWNER_TELEGRAM_ID = _settings.telegram.platform_owner_telegram_id
PLATFORM_OWNER_NAME = _settings.telegram.platform_owner_name
DEFAULT_AUTO_MANAGER_ID = _settings.telegram.default_auto_manager_id
DEFAULT_DEALER_MANAGER_ID = _settings.telegram.default_dealer_manager_id
DEFAULT_AGRO_MANAGER_ID = _settings.telegram.default_agro_manager_id
DEFAULT_REALTY_MANAGER_ID = _settings.telegram.default_realty_manager_id
MANAGER_ID = DEFAULT_DEALER_MANAGER_ID

MANAGERS: dict[int, str] = {}
if DEFAULT_DEALER_MANAGER_ID is not None:
    MANAGERS[DEFAULT_DEALER_MANAGER_ID] = "Dealer Manager"
if DEFAULT_AUTO_MANAGER_ID is not None and DEFAULT_AUTO_MANAGER_ID not in MANAGERS:
    MANAGERS[DEFAULT_AUTO_MANAGER_ID] = "Борода"
if DEFAULT_AGRO_MANAGER_ID is not None and DEFAULT_AGRO_MANAGER_ID not in MANAGERS:
    MANAGERS[DEFAULT_AGRO_MANAGER_ID] = "Christopher Moltisanti"
if DEFAULT_REALTY_MANAGER_ID is not None and DEFAULT_REALTY_MANAGER_ID not in MANAGERS:
    MANAGERS[DEFAULT_REALTY_MANAGER_ID] = "Luc"

MARKETING_TELEGRAM_CHANNEL_ID = _settings.telegram.marketing_channel_id
BIDEX_TELEGRAM_CHANNEL_USERNAME = _settings.telegram.bidex_channel_username
BIDEX_TELEGRAM_CHANNEL_ID = _settings.telegram.bidex_channel_id
DEALER_RATES_TELEGRAM_CHANNEL_ID = _settings.telegram.dealer_rates_channel_id
FOMA_RATES_TELEGRAM_CHANNEL_ID = _settings.telegram.foma_rates_channel_id

# ---- Storage ----
MEDIA_STORAGE_PROVIDER = _settings.storage.media_provider
MEDIA_LOCAL_CACHE = _settings.storage.media_local_cache
LOCAL_STORAGE_DIR = _settings.storage.local_storage_dir
MEDIA_CDN_BASE_URL = _settings.storage.media_cdn_base_url
S3_BUCKET = _settings.storage.s3_bucket
S3_REGION = _settings.storage.s3_region
S3_ENDPOINT_URL = _settings.storage.s3_endpoint_url
S3_ACCESS_KEY = _settings.storage.s3_access_key
S3_SECRET_KEY = _settings.storage.s3_secret_key

# ---- JWT / IAM ----
JWT_SECRET = _settings.jwt.secret
JWT_ALGORITHM = _settings.jwt.algorithm
JWT_EXPIRE_MINUTES = _settings.jwt.expire_minutes
IAM_SESSION_TTL_SECONDS = _settings.jwt.session_ttl_seconds
IAM_LOGIN_SECRET = _settings.jwt.login_secret

# ---- Notifications ----
SMTP_HOST = _settings.notifications.smtp_host or None
SMS_PROVIDER_URL = _settings.notifications.sms_provider_url or None

# ---- Operations ----
OPS_DASHBOARD_TTL_SECONDS = _settings.operations.dashboard_ttl_seconds

# ---- Assignment / Pricing ----
SMART_ASSIGNMENT_EXTRA_SEGMENTS = _settings.assignment.extra_segments
PRICING_COMPANY_MARGIN = _settings.pricing.company_margin
LIQUIDITY_LOW_THRESHOLD = _settings.pricing.liquidity_low_threshold
LIQUIDITY_POOL_LIMIT_RATIO = _settings.pricing.pool_limit_ratio

# ---- Observability ----
SENTRY_DSN = _settings.security.sentry_dsn
PROMETHEUS_ENABLED = _settings.security.prometheus_enabled
LOG_LEVEL = _settings.security.log_level


def _platform_config(key: str, default: Any) -> Any:
    try:
        from platform_configuration.config_provider import config_provider

        return config_provider.get(key, default)
    except Exception:
        return default


def _platform_int(key: str, default: int) -> int:
    try:
        return int(_platform_config(key, default))
    except (TypeError, ValueError):
        return default


def _platform_float(key: str, default: float) -> float:
    try:
        return float(_platform_config(key, default))
    except (TypeError, ValueError):
        return default


def _platform_str(key: str, default: str) -> str:
    return str(_platform_config(key, default))


def _platform_bool(key: str, default: bool) -> bool:
    value = _platform_config(key, default)
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in {"1", "true", "yes", "on"}
    return bool(value)


SLA_ASSIGNMENT_SEC = _platform_int("sla.assignment_sec", 15 * 60)
SLA_FIRST_RESPONSE_SEC = _platform_int("sla.first_response_sec", 30 * 60)
SLA_CLOSE_SEC = _platform_int("sla.close_sec", 72 * 3600)
MANAGER_ASSIGNMENT_MODE = _platform_str("managers.assignment_mode", "ROUND_ROBIN").upper()
ASSIGNMENT_MODE = _platform_str("smart_assignment.mode", "SMART").upper()
SMART_ASSIGNMENT_LOAD_WEIGHT = _platform_float("smart_assignment.load_weight", 0.40)
SMART_ASSIGNMENT_RESPONSE_WEIGHT = _platform_float("smart_assignment.response_weight", 0.25)
SMART_ASSIGNMENT_COMPLETED_WEIGHT = _platform_float("smart_assignment.completed_weight", 0.15)
SMART_ASSIGNMENT_PRIORITY_WEIGHT = _platform_float("smart_assignment.priority_weight", 0.10)
SMART_ASSIGNMENT_SPECIALIZATION_WEIGHT = _platform_float(
    "smart_assignment.specialization_weight",
    0.10,
)
OWNER_ESCALATION_ENABLED = _platform_bool("escalation.owner_enabled", True)
OWNER_ESCALATION_DELAY_MINUTES = _platform_int("escalation.owner_delay_minutes", 240)

# Warn for missing optional telegram ids (preserves legacy behavior)
for _env_name, _value in (
    ("PLATFORM_OWNER_TELEGRAM_ID", PLATFORM_OWNER_TELEGRAM_ID),
    ("DEFAULT_AGRO_MANAGER_ID", DEFAULT_AGRO_MANAGER_ID),
    ("DEFAULT_REALTY_MANAGER_ID", DEFAULT_REALTY_MANAGER_ID),
):
    if _value is None:
        logger.warning(
            "%s is not set in .env — related routing and access checks may be limited",
            _env_name,
        )
