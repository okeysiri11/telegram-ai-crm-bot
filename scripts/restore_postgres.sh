#!/usr/bin/env bash
# PostgreSQL restore for ADOS compose stack — Sprint 39.1
#
# Usage:
#   ./scripts/restore_postgres.sh <backup.dump> --verify-only
#       Restore into a temporary DB, then drop it (safe integrity check).
#   ./scripts/restore_postgres.sh <backup.dump> --yes
#       Destructive restore into the live POSTGRES_DB (requires --yes).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

BACKUP="${1:-}"
MODE="${2:-}"

if [[ -z "$BACKUP" || ! -f "$BACKUP" ]]; then
  echo "Usage: $0 <path-to-ados_pg_*.dump> (--verify-only|--yes)" >&2
  exit 2
fi

if [[ "$MODE" != "--yes" && "$MODE" != "--verify-only" ]]; then
  echo "Refusing without --verify-only or --yes." >&2
  exit 2
fi

if [[ -f "$ROOT/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "$ROOT/.env"
  set +a
fi

POSTGRES_USER="${POSTGRES_USER:-postgres}"
POSTGRES_DB="${POSTGRES_DB:-ai_ecosystem}"
SUM_FILE="${BACKUP}.sha256"

echo "Verifying backup integrity…"
BYTES="$(wc -c < "$BACKUP" | tr -d ' ')"
if [[ "$BYTES" -lt 1024 ]]; then
  echo "ERROR: backup too small (${BYTES} bytes)" >&2
  exit 1
fi

if [[ -f "$SUM_FILE" ]]; then
  if command -v shasum >/dev/null 2>&1; then
    ACTUAL="$(shasum -a 256 "$BACKUP" | awk '{print $1}')"
  else
    ACTUAL="$(sha256sum "$BACKUP" | awk '{print $1}')"
  fi
  WANT="$(awk '{print $1}' "$SUM_FILE")"
  if [[ "$ACTUAL" != "$WANT" ]]; then
    echo "ERROR: checksum mismatch actual=$ACTUAL want=$WANT" >&2
    exit 1
  fi
  echo "Checksum OK ($ACTUAL)"
else
  echo "WARN: no ${SUM_FILE}; skipping checksum compare"
fi

docker compose exec -T -i postgres pg_restore -l < "$BACKUP" >/dev/null
echo "pg_restore -l OK"

if [[ "$MODE" == "--verify-only" ]]; then
  TMP_DB="ados_restore_check"
  echo "Restoring into temporary database ${TMP_DB}…"
  docker compose exec -T postgres \
    psql -U "$POSTGRES_USER" -d postgres -v ON_ERROR_STOP=1 \
    -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='${TMP_DB}' AND pid <> pg_backend_pid();" \
    >/dev/null || true
  docker compose exec -T postgres \
    psql -U "$POSTGRES_USER" -d postgres -v ON_ERROR_STOP=1 \
    -c "DROP DATABASE IF EXISTS ${TMP_DB};" >/dev/null
  docker compose exec -T postgres \
    psql -U "$POSTGRES_USER" -d postgres -v ON_ERROR_STOP=1 \
    -c "CREATE DATABASE ${TMP_DB};" >/dev/null
  docker compose exec -T -i postgres \
    pg_restore -U "$POSTGRES_USER" -d "$TMP_DB" --no-owner --no-acl \
    < "$BACKUP"
  TABLES="$(docker compose exec -T postgres \
    psql -U "$POSTGRES_USER" -d "$TMP_DB" -Atc \
    "SELECT count(*) FROM information_schema.tables WHERE table_schema='public';")"
  docker compose exec -T postgres \
    psql -U "$POSTGRES_USER" -d postgres -v ON_ERROR_STOP=1 \
    -c "DROP DATABASE ${TMP_DB};" >/dev/null
  echo "VERIFY_OK tables_restored=${TABLES} (temp DB dropped)"
  exit 0
fi

echo "Restoring into LIVE database ${POSTGRES_DB} (clean)…"
docker compose exec -T -i postgres \
  pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --clean --if-exists --no-owner --no-acl \
  < "$BACKUP"
echo "RESTORE_OK database=${POSTGRES_DB} from=${BACKUP}"
