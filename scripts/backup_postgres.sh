#!/usr/bin/env bash
# PostgreSQL backup for ADOS compose stack — Sprint 39.1
# Usage: ./scripts/backup_postgres.sh [output_dir]
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

OUT_DIR="${1:-$ROOT/backups}"
mkdir -p "$OUT_DIR"

if [[ -f "$ROOT/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "$ROOT/.env"
  set +a
fi

POSTGRES_USER="${POSTGRES_USER:-postgres}"
POSTGRES_DB="${POSTGRES_DB:-ai_ecosystem}"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
FILE="$OUT_DIR/ados_pg_${POSTGRES_DB}_${STAMP}.dump"
META="$FILE.sha256"

echo "Backing up ${POSTGRES_DB} as ${POSTGRES_USER} → ${FILE}"

docker compose exec -T postgres \
  pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc --no-owner --no-acl \
  > "$FILE"

BYTES="$(wc -c < "$FILE" | tr -d ' ')"
if [[ "$BYTES" -lt 1024 ]]; then
  echo "ERROR: backup too small (${BYTES} bytes)" >&2
  exit 1
fi

if command -v shasum >/dev/null 2>&1; then
  HASH="$(shasum -a 256 "$FILE" | awk '{print $1}')"
else
  HASH="$(sha256sum "$FILE" | awk '{print $1}')"
fi
printf '%s  %s\n' "$HASH" "$(basename "$FILE")" > "$META"

# Integrity: custom-format archive must list a TOC
docker compose exec -T -i postgres pg_restore -l < "$FILE" >/dev/null
echo "TOC list OK"
echo "BACKUP_OK file=$FILE bytes=$BYTES sha256=$HASH"
echo "$FILE"
