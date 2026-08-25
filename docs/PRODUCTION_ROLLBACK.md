# Production rollback

Durable rollback uses existing Postgres backup/restore. It does **not** auto-run `alembic downgrade`.

## Backup

```bash
./scripts/backup_postgres.sh
```

Writes `backups/ados_pg_<db>_<stamp>.dump` plus a sha256 sidecar.

## Restore (destructive)

```bash
./scripts/rollback_production.sh --restore-backup backups/ados_pg_<db>_<stamp>.dump
```

This wraps `scripts/restore_postgres.sh <dump> --yes`. Confirm the dump hash before running. This overwrites the live database.

## Integrity check without overwrite

```bash
./scripts/restore_postgres.sh backups/ados_pg_<db>_<stamp>.dump --verify-only
```

## Image rollback

```bash
./scripts/rollback_production.sh --image <previous-image-id>
```

Alembic schema is left as-is so a newer head is not silently destroyed. If a schema downgrade is required, it must be an explicit operator decision after backup.
