#!/usr/bin/env bash
# Durable production rollback. Does not auto-downgrade Alembic (data safety).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

MODE="${1:-}"
if [[ "$MODE" != "--image" && "$MODE" != "--restore-backup" ]]; then
  echo "Usage:" >&2
  echo "  $0 --image <previous-image-id>   # recreate bot from a known image" >&2
  echo "  $0 --restore-backup <dump>       # wrapper around scripts/restore_postgres.sh --yes" >&2
  echo "Alembic downgrade is NOT run automatically." >&2
  exit 2
fi

if ! command -v docker >/dev/null 2>&1; then
  echo "ERROR: docker is required for rollback." >&2
  exit 1
fi

if [[ "$MODE" == "--image" ]]; then
  IMAGE="${2:-}"
  if [[ -z "$IMAGE" ]]; then
    echo "ERROR: previous image id required." >&2
    exit 2
  fi
  docker compose --env-file .env.production -f docker-compose.prod.yml stop bot
  docker compose --env-file .env.production -f docker-compose.prod.yml run -d --no-deps --name ados-bot-rollback "$IMAGE"
  echo "ROLLBACK_IMAGE=$IMAGE"
  exit 0
fi

BACKUP="${2:-}"
exec "$ROOT/scripts/restore_postgres.sh" "$BACKUP" --yes
