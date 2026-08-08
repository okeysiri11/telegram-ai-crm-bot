# Infrastructure Validation — Sprint 39.1

**MODE:** INFRASTRUCTURE  
**BASELINE:** v0.9.4-rc1  
**Date:** 2026-08-05  
**Verdict:** INFRASTRUCTURE READY (after end-of-sprint gates)

Commercial-first-client infrastructure checklist. Functional product code was not modified.

---

## Checklist

| Area | Status | Evidence |
|------|--------|----------|
| Backup | ✔ | `scripts/backup_postgres.sh` → `backups/ados_pg_*.dump` + `.sha256` |
| Restore | ✔ | `scripts/restore_postgres.sh --verify-only` restored 393 tables into temp DB |
| Docker | ✔ | `down` / `build` / `up` / `restart` / `ps` / healthy |
| Health | ✔ | `GET /health` → 200 healthy |
| Ready | ✔ | `GET /ready` → 200 ready |
| Telegram | ✔ | `getMe` @UnoCachio_bot; polling mode (empty webhook); OWNER getChat OK |
| PostgreSQL | ✔ | Healthy; Alembic head `u4o567890123`; downgrade -1 + upgrade + re-upgrade OK |
| Redis | ✔ | Healthy; PONG |
| Secrets | ✔ | `.env.example` documents keys; `.env.production` untracked; `validate_secrets_env.py` PASS |
| HTTPS readiness | ✔ | Forward headers on `/api` + `/management` + `/swagger`; ACME path; TLS block + `deploy/certs/` stub (disabled until domain) |

---

## Backup / restore

```bash
./scripts/backup_postgres.sh
./scripts/restore_postgres.sh backups/ados_pg_<stamp>.dump --verify-only
# live restore (destructive):
./scripts/restore_postgres.sh backups/ados_pg_<stamp>.dump --yes
```

Docs: `backups/README.md`

---

## Secrets

- Required keys documented in `.env.example` (JWT, Telegram, DB, Grafana, OpenRouter, optional OpenAI/Anthropic/Google/Meta).
- Runtime secrets via ENV / compose `env_file` only.
- `.env` / `.env.production` must not be tracked (gate enforced by `scripts/validate_secrets_env.py`).
- GitHub Actions uses repository Secrets / job env placeholders — never commit live tokens.

---

## HTTPS

- nginx proxies `X-Forwarded-For` / `X-Forwarded-Proto` / `Host` / `X-Real-IP`.
- `/.well-known/acme-challenge/` ready for certbot.
- TLS server block remains **commented** until certs exist under `deploy/certs/`.
- HSTS header noted for post-TLS enablement.

---

## Telegram

```bash
python scripts/validate_telegram_bot.py
```

Validates token, `getMe`, webhook vs polling, optional OWNER chat, recent reconnect-class errors in logs.

---

## Database migrations

```text
alembic current          → u4o567890123 (head)
alembic downgrade -1     → t3n456789012
alembic upgrade head     → u4o567890123
alembic upgrade head     → no-op (idempotent)
```

No migration conflicts observed at head.

---

## Freeze note (post 39.1)

Until new requirements appear, **do not** change Docker, Compose, CI, Backup, Security, or Healthcheck outside an **INFRASTRUCTURE** sprint.  
Further sprints should be **FEATURE** or **BUGFIX** only.
