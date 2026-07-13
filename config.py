import os

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# PostgreSQL (SQLAlchemy 2 async + asyncpg)
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/ai_ecosystem",
)

# HTTP API (health checks)
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8080"))

# Optional Redis (cache / queue)
REDIS_URL = os.getenv("REDIS_URL", "")
REDIS_REQUIRED = os.getenv("REDIS_REQUIRED", "").lower() in {"1", "true", "yes"}

OWNER_ID = 1208044579
MANAGER_ID = 8312013093

MARKETING_TELEGRAM_CHANNEL_ID = os.getenv("MARKETING_TELEGRAM_CHANNEL_ID")

# Automotive Treasury — dealer FX rates channel (primary rate source)
DEALER_RATES_TELEGRAM_CHANNEL_ID = os.getenv("DEALER_RATES_TELEGRAM_CHANNEL_ID")

MANAGERS = {
    8312013093: "Tony"
}