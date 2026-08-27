# Sprint Recruiting 1.2 — Projects + Vanguard Control Center

**Date:** 2026-08-27

## What shipped

- Recruiting remains the business vertical. Vanguard is a **project** (`project_key=vanguard`) inside Recruiting.
- Navigation: **Проекты** → `/workspace/recruiting/projects`
- Vanguard Control Center: `/workspace/recruiting/projects/vanguard`
- Same Recruiting data, filtered by `project_key` / `source=vanguard`
- Dashboard section **ПРОЕКТЫ РЕКРУТИНГА** with 1-click **Открыть Vanguard**
- Honest empty copy: **Нет данных**. No fabricated visits/metrics.
- Local Recruiting Ops API was down (`ECONNREFUSED :8080`). Backend started via `scripts/run_api_local.py`.

## Architectural decisions

- No new vertical, no second CRM, no new `platform_recruiting`.
- Projects are a catalog in `services/recruiting_ops/projects.py` plus filters on existing `recruiting_ops_records`.
- Website URL comes from `VANGUARD_WEBSITE_URL` (never localhost in production).
- Marketing/ads sending is not started.

## Next sprint

VANGUARD LIVE INGESTION + RECRUITING MARKETING FUNNEL
