#!/usr/bin/env bash
# PostgreSQL backup strategy — daily dump with 14-day retention.
set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-./scripts/backup}"
RETENTION_DAYS="${RETENTION_DAYS:-14}"
STAMP="$(date +%Y%m%d_%H%M%S)"
FILE="${BACKUP_DIR}/ai_ecosystem_${STAMP}.sql.gz"

mkdir -p "${BACKUP_DIR}"

if [[ -n "${DATABASE_URL:-}" ]]; then
  # Convert SQLAlchemy async URL to plain postgres URL for pg_dump
  PGURL="${DATABASE_URL/postgresql+asyncpg/postgresql}"
  pg_dump "${PGURL}" | gzip > "${FILE}"
else
  pg_dump -h "${POSTGRES_HOST:-localhost}" -U "${POSTGRES_USER:-postgres}" \
    -d "${POSTGRES_DB:-ai_ecosystem}" | gzip > "${FILE}"
fi

find "${BACKUP_DIR}" -name 'ai_ecosystem_*.sql.gz' -mtime +"${RETENTION_DAYS}" -delete
echo "Backup written: ${FILE}"
