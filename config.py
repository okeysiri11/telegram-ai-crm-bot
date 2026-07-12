import os

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# PostgreSQL (SQLAlchemy async + asyncpg)
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
POSTGRES_DB = os.getenv("POSTGRES_DB", "bidex")
POSTGRES_USER = os.getenv("POSTGRES_USER", "bidex")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "")

# HTTP API (health checks)
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8080"))

OWNER_ID = 1208044579
MANAGER_ID = 8312013093

MANAGERS = {
    8312013093: "Tony"
}