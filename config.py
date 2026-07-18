import logging
import os

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


def _optional_telegram_id(env_name: str) -> int | None:
    raw = os.getenv(env_name, "").strip()
    if not raw:
        logger.warning(
            "%s is not set in .env — related routing and access checks may be limited",
            env_name,
        )
        return None
    try:
        return int(raw)
    except ValueError:
        logger.warning(
            "%s=%r is not a valid Telegram user id — expected integer",
            env_name,
            raw,
        )
        return None


BOT_TOKEN = os.getenv("BOT_TOKEN")
BOT_USERNAME = os.getenv("BOT_USERNAME", "")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# PostgreSQL (SQLAlchemy 2 async + asyncpg)
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/ai_ecosystem",
)

# When true (default), SQLite memory.db is not bootstrapped — PostgreSQL only.
POSTGRES_ONLY = os.getenv("POSTGRES_ONLY", "true").lower() in {"1", "true", "yes"}

# Environment: production enables stricter defaults (Redis required, no SQLite).
ENVIRONMENT = os.getenv("ENVIRONMENT", "development").strip().lower()
IS_PRODUCTION = ENVIRONMENT in {"production", "prod"}

# Redis — FSM storage (required in production / when POSTGRES_ONLY).
REDIS_URL = os.getenv("REDIS_URL", "")
_redis_required_env = os.getenv("REDIS_REQUIRED", "").lower() in {"1", "true", "yes"}
REDIS_REQUIRED = _redis_required_env or IS_PRODUCTION or POSTGRES_ONLY

# HTTP API (health checks)
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8080"))

# Platform Telegram user ids (optional — warn if missing, do not abort startup)
OWNER_ID = _optional_telegram_id("OWNER_ID")
PLATFORM_OWNER_TELEGRAM_ID = _optional_telegram_id("PLATFORM_OWNER_TELEGRAM_ID") or OWNER_ID
PLATFORM_OWNER_NAME = os.getenv("PLATFORM_OWNER_NAME", "Platform Owner")
OWNER_ESCALATION_ENABLED = os.getenv("OWNER_ESCALATION_ENABLED", "true").lower() in {
    "1",
    "true",
    "yes",
}
OWNER_ESCALATION_DELAY_MINUTES = int(os.getenv("OWNER_ESCALATION_DELAY_MINUTES", "240"))
DEFAULT_AUTO_MANAGER_ID = _optional_telegram_id("DEFAULT_AUTO_MANAGER_ID")
DEFAULT_DEALER_MANAGER_ID = _optional_telegram_id("DEFAULT_DEALER_MANAGER_ID")
DEFAULT_AGRO_MANAGER_ID = _optional_telegram_id("DEFAULT_AGRO_MANAGER_ID")
DEFAULT_REALTY_MANAGER_ID = _optional_telegram_id("DEFAULT_REALTY_MANAGER_ID")

# Legacy alias used across CRM engines
MANAGER_ID = DEFAULT_DEALER_MANAGER_ID

MANAGERS: dict[int, str] = {}
if DEFAULT_DEALER_MANAGER_ID is not None:
    MANAGERS[DEFAULT_DEALER_MANAGER_ID] = os.getenv(
        "DEFAULT_DEALER_MANAGER_NAME",
        "Dealer Manager",
    )
if DEFAULT_AUTO_MANAGER_ID is not None and DEFAULT_AUTO_MANAGER_ID not in MANAGERS:
    MANAGERS[DEFAULT_AUTO_MANAGER_ID] = os.getenv(
        "DEFAULT_AUTO_MANAGER_NAME",
        "Борода",
    )
if DEFAULT_AGRO_MANAGER_ID is not None and DEFAULT_AGRO_MANAGER_ID not in MANAGERS:
    MANAGERS[DEFAULT_AGRO_MANAGER_ID] = os.getenv(
        "DEFAULT_AGRO_MANAGER_NAME",
        "Christopher Moltisanti",
    )
if DEFAULT_REALTY_MANAGER_ID is not None and DEFAULT_REALTY_MANAGER_ID not in MANAGERS:
    MANAGERS[DEFAULT_REALTY_MANAGER_ID] = os.getenv(
        "DEFAULT_REALTY_MANAGER_NAME",
        "Luc",
    )

MARKETING_TELEGRAM_CHANNEL_ID = os.getenv("MARKETING_TELEGRAM_CHANNEL_ID")

# BidEx @bidex_Odesa — authoritative dealer FX rates channel
BIDEX_TELEGRAM_CHANNEL_USERNAME = os.getenv("BIDEX_TELEGRAM_CHANNEL_USERNAME", "bidex_Odesa")
BIDEX_TELEGRAM_CHANNEL_ID = os.getenv("BIDEX_TELEGRAM_CHANNEL_ID")

# Automotive Treasury — dealer FX rates channel (legacy / fallback)
DEALER_RATES_TELEGRAM_CHANNEL_ID = os.getenv("DEALER_RATES_TELEGRAM_CHANNEL_ID")
FOMA_RATES_TELEGRAM_CHANNEL_ID = os.getenv(
    "FOMA_RATES_TELEGRAM_CHANNEL_ID",
    DEALER_RATES_TELEGRAM_CHANNEL_ID,
)

# Media storage (telegram | local | s3)
MEDIA_STORAGE_PROVIDER = os.getenv("MEDIA_STORAGE_PROVIDER", "telegram")
MEDIA_LOCAL_CACHE = os.getenv("MEDIA_LOCAL_CACHE", "true").lower() in {"1", "true", "yes"}
LOCAL_STORAGE_DIR = os.getenv("LOCAL_STORAGE_DIR", "data/media_cache")
MEDIA_CDN_BASE_URL = os.getenv("MEDIA_CDN_BASE_URL", "")
S3_BUCKET = os.getenv("S3_BUCKET", "")
S3_REGION = os.getenv("S3_REGION", "eu-central-1")
S3_ENDPOINT_URL = os.getenv("S3_ENDPOINT_URL", "")
S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY", "")
S3_SECRET_KEY = os.getenv("S3_SECRET_KEY", "")

# JWT / REST API
JWT_SECRET = os.getenv("JWT_SECRET", "change-me-in-production")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "1440"))

# Observability
SENTRY_DSN = os.getenv("SENTRY_DSN", "")
PROMETHEUS_ENABLED = os.getenv("PROMETHEUS_ENABLED", "true").lower() in {"1", "true", "yes"}
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# SLA / Escalation (seconds)
SLA_ASSIGNMENT_SEC = int(os.getenv("SLA_ASSIGNMENT_SEC", str(15 * 60)))
SLA_FIRST_RESPONSE_SEC = int(os.getenv("SLA_FIRST_RESPONSE_SEC", str(30 * 60)))
SLA_CLOSE_SEC = int(os.getenv("SLA_CLOSE_SEC", str(72 * 3600)))

# Dynamic manager pool assignment strategy
MANAGER_ASSIGNMENT_MODE = os.getenv("MANAGER_ASSIGNMENT_MODE", "ROUND_ROBIN").upper()

# Smart assignment engine (primary)
ASSIGNMENT_MODE = os.getenv("ASSIGNMENT_MODE", "SMART").upper()
SMART_ASSIGNMENT_LOAD_WEIGHT = float(os.getenv("SMART_ASSIGNMENT_LOAD_WEIGHT", "0.40"))
SMART_ASSIGNMENT_RESPONSE_WEIGHT = float(os.getenv("SMART_ASSIGNMENT_RESPONSE_WEIGHT", "0.25"))
SMART_ASSIGNMENT_COMPLETED_WEIGHT = float(os.getenv("SMART_ASSIGNMENT_COMPLETED_WEIGHT", "0.15"))
SMART_ASSIGNMENT_PRIORITY_WEIGHT = float(os.getenv("SMART_ASSIGNMENT_PRIORITY_WEIGHT", "0.10"))
SMART_ASSIGNMENT_SPECIALIZATION_WEIGHT = float(
    os.getenv("SMART_ASSIGNMENT_SPECIALIZATION_WEIGHT", "0.10")
)
