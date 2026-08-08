# ADOS PostgreSQL backups (Sprint 39.1)

Dump files are **not** committed (see `.gitignore`).

```bash
# Create backup
./scripts/backup_postgres.sh

# Safe integrity check (temp DB; does not touch live data)
./scripts/restore_postgres.sh backups/ados_pg_<timestamp>.dump --verify-only

# Destructive restore into live DB (explicit)
./scripts/restore_postgres.sh backups/ados_pg_<timestamp>.dump --yes
```

Format: PostgreSQL custom (`pg_dump -Fc`) + sibling `.sha256` checksum.
