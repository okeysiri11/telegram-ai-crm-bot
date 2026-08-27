# Sprint — Recruiting real provider connections foundation

**Date:** 2026-08-27  
**Branch:** `origin/develop`  
**Backend:** `recruiting_1.8`

Move Recruiting from infrastructure-ready to **real-provider-ready**. The 1.7 Green Gate is not reopened. No production credentials were invented or requested.

## What shipped

### Provider Connection Center

Recruiting → Интеграции (`/workspace/recruiting/integrations`).

Cards: Meta Ads, Google Ads, TikTok Ads, Telegram, WhatsApp, Email.

Each card shows status (`NOT_CONFIGURED` / `CONFIGURING` / `CONNECTED` / `DEGRADED` / `ERROR`), connection type, account id, last successful health check, last error, credential presence, expiry, scopes, tracking status.

Actions: Настроить, Проверить соединение, Переподключить, Отключить, Диагностика.

Secrets are never rendered. LIVE / MOCK / Не настроено are explicit badges.

### SecretStore

`services/recruiting_ops/secret_store.py`

- No secrets in frontend, git, or normal API responses
- `SecretStore` protocol + `EnvSecretStore` (env + encrypted-at-rest envelope)
- Rotation metadata, expiry, scopes
- Audit via `_activity` using `public_secret_audit` (field names only)

### Provider adapter contract

`services/recruiting_ops/provider_contract.py`

Capabilities: connect, disconnect, health_check, refresh_credentials, list_accounts, list_campaigns, create_campaign, update_campaign, pause_campaign, resume_campaign, fetch_metrics, fetch_leads, send_message.

Unsupported capability returns typed `UNSUPPORTED`, never a silent success.

LIVE adapters without a successful live health check stay `NOT_CONFIGURED` (credentials present → `CONFIGURING`, never fake `CONNECTED`). MOCK adapters are `mode=MOCK` and forbidden in production.

### WAITING_PROVIDER reactivation

When a provider becomes `CONNECTED` (mock connect in tests), eligible `WAITING_PROVIDER` events for that destination move to `RETRYING` in a bounded batch, with audit and failure isolation. Events are not deleted. Runtime connected state (not env-secret presence) drives `provider_is_configured`.

### Advertising Control Center

Recruiting → Реклама (`/workspace/recruiting/ads`).

Sections: Обзор, Провайдеры, Кампании, Лиды, Воронка, Атрибуция, Источники, Автоматизация, AI-оптимизация, Диагностика.

Provider spend / impressions / clicks stay `null` + «Нет живых данных». Funnel counts from Recruiting records may be real. Provider outage does not mark core infra DOWN (`provider_health.infra_independent=true`).

### Campaign / lead / attribution

Canonical campaign statuses: `DRAFT` `READY` `ACTIVE` `PAUSED` `COMPLETED` `FAILED` in `lifecycle_status`. Legacy `status` (`active`/`paused`) is preserved for 1.5.

Lead ingest normalizes provider payload, dedupes by provider+external_id then email/phone, updates last-touch only.

Attribution chain: Provider → Campaign → Click/Lead → Candidate → Qualified → Interview → Hire. First-touch and last-touch; `multi_touch_ready=true` for a later sprint.

### Automation and AI

New automation rules default to `approval_required=true`. Spend-changing evaluations return `APPROVAL_REQUIRED` and do not auto-apply.

AI recommendations are advisory only (`AI_LIVE_WRITE_ACCESS=false`). Approve/Reject never writes live campaigns.

## Architectural decisions

- Extend `services/recruiting_ops/` and existing `recruiting_ops_records` JSONB kinds. No new table, Alembic head unchanged (`v2r345678901`).
- New kinds: `provider_connection`, `automation_rule`, `automation_run`, `ai_recommendation`.
- Additive `/api/recruiting-ops/v1` routes. Existing `/ads/control-center` `providers.*.status == not_connected` contract kept for 1.5.
- Env-only CONFIGURED is not live CONNECTED. Green Gate tracking health stays independent of ads providers.

Rejected: calling Meta/Google/TikTok/WhatsApp/SMTP with invented credentials; reporting CONNECTED from secret presence; letting AI pause spend.

## Intentionally deferred

Real OAuth/HTTP to Meta, Google, TikTok. Real Telegram/WhatsApp/SMTP send. Production KMS/Secret Manager. Multi-touch attribution execution. Autonomous campaign writes after approval.

## Verification

| Check | Result |
|---|---|
| pytest Recruiting/Vanguard + 1.8 | 90 passed |
| vitest recruiting 1.0/1.5/1.6/tracking/1.8 | 9 passed |
| `npx vite build` (`src/web`) | PASS |
| Green Gate tests | preserved |

## UI language

User-facing Recruiting copy is Russian. Enums and API names stay English.
