#!/bin/sh
set -eu
# Apply schema then start the bot/API process.
python /app/scripts/ensure_local_schema.py
exec "$@"
