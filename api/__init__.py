# REST/GraphQL API layer + system HTTP endpoints.
#
# Routes:
#   GET /system/db-health  — PostgreSQL async health check
#
# Run via bot.py (alongside Telegram polling) or standalone:
#   python -c "import asyncio; from api.server import start_api_server; asyncio.run(start_api_server())"

API_VERSION = "v1"
