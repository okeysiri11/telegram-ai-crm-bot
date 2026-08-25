#!/bin/sh
set -eu
# Durable production entrypoint: apply Alembic then exec the API/bot.
# Does not start Cloudflare tunnels. Does not fabricate credentials.
echo "ados-entrypoint revision=${GIT_SHA:-unknown}"
python /app/scripts/ensure_local_schema.py
exec "$@"
