# Sprint Recruiting 1.0 — RESULT

**Vertical:** Recruiting / Vanguard lead acquisition  
**App:** `src/web` + `/api/recruiting-ops/v1`  
**Date:** 2026-08-27

## What shipped

Operational recruiting desk at `/workspace/recruiting` (not an admin table viewer).

- Dashboard: overdue + next tasks, attention indicators, honest visit copy
- Leads → assign recruiter → note → qualify → convert to candidate
- Candidates + pipeline stages: NEW / QUALIFIED / INTERVIEW / APPROVED / HIRED / REJECTED
- Vacancies, campaigns, recruiting tasks, manual communication log
- Attribution analytics by source / campaign / vacancy
- Funnel: visits (if available) → leads → qualified → interviews → approved → hired
- Visits are **not fabricated**. Copy: «Нет данных о посещениях»
- `platform_owner` full access from normal platform navigation
- Vanguard **API contract only** (`GET /api/recruiting-ops/v1/vanguard/contract`). Website is not connected.

## Architectural decisions

- **Extend Legal/Agro ops pattern**, do not reuse frozen `/api/v1/leads` (vehicle CRM) or `ecosystem/workforce`.
- New vertical application `applications/recruiting_enterprise` + `services/recruiting_ops`.
- Durable store: `recruiting_ops_records` (kind + JSONB), memory fallback when Postgres is unreachable.
- Data mode is always `REAL` for API-created records. No silent demo seed mixed into production metrics.
- Communication channels TELEGRAM / WHATSAPP / EMAIL / PHONE / MANUAL are an abstraction. Manual log only; no send.

## Intentionally deferred

- Vanguard website live integration
- Meta / Google / TikTok Ads APIs
- Real Telegram / WhatsApp / email send
- Autonomous ad spend and advertising credentials
- Casino / Crypto / Odessa3D changes

## Verify

| Check | Result |
| --- | --- |
| pytest `tests/test_sprint_recruiting_1_0.py` | targeted |
| vitest recruiting + owner access + vertical catalog | targeted |
| `src/web` production build | targeted |

## Next sprint

**VANGUARD WEBSITE → RECRUITING LIVE INTEGRATION**

Do not start automatically.
