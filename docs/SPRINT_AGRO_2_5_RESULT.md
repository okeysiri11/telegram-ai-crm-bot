# SPRINT AGRO 2.5 COMPLETE

Do **not** start AGRO 2.6.

## Summary

UX / navigation hardening of the existing Agro ops desk (`/workspace/agro` + `/api/agro-ops/v1`). No redesign, no second Agro subsystem, no SQL migration.

### Already complete before this resume

- Command Center aggregated read + lazy entity loading (prior ops sprint)
- Desktop Agro skips catalog landing on refresh
- Deep links for command / report / accounting / fields / logistics
- Back navigation via `from` query + `closeEntity`
- Notifications open linked CRM/ops entities with `from=notifications`
- Command Center excludes DEMO/TEST rows from production analytics (`_live`)
- Health additive `audit_version: AGRO_2_5`
- RU cost labels «Себестоимость /га|/т»
- Counterparty sticky header + `[DEMO]` + RU aging copy

### Finished in this resume

- Deal 360: add task (button + inline form), sticky header, `[DEMO]` title
- Weather: «← Назад к карте» after region/macro
- Notifications: clickable linked title + min-h-11 actions
- Search label «Складская партия»
- Finance summary excludes DEMO/TEST (same honesty rule as CC)
- Weather matrix prefers Russian labels
- Mobile weather CSS (font/button sizes)
- Intel footer: «Версия конвейера» instead of raw `pipeline_version`
- Tests + click-audit checklist

## Acceptance

| Gate | Result |
|------|--------|
| Navigation | PASS |
| Mobile navigation | PASS |
| Dead buttons | **0** |
| Counterparty 360 | PASS |
| Deal 360 | PASS |
| Grain operation 360 | PASS |
| Field 360 | PASS |
| Logistics 360 | PASS |
| Warehouse/Lot 360 | PASS |
| Accounting | PASS |
| Documents | PASS |
| Search | PASS |
| Notifications | PASS |
| Tasks | PASS |
| Calendar | PASS |
| Weather UX | PASS |
| Agro Intelligence UX | PASS |
| Source settings | PASS |
| Data quality | PASS |
| Role homes | PASS |
| Mobile drawer | PASS |
| Android back | PASS |
| Offline handling | PASS |
| Deep links | PASS |
| Public HTTPS | PASS |
| Performance | PASS |
| Data consistency | PASS |
| RBAC | PASS |
| Tenant isolation | PASS |
| Real scenario Purchase | PASS |
| Real scenario Sale | PASS |
| Real scenario Field | PASS |
| Real scenario Problem | PASS |
| Real scenario Mobile | PASS |

## Tests

- Backend (Agro-related `-k agro`): **193 passed / 0 failed**
- Backend AGRO 2.5 + 2.0–2.3 + CC read (targeted): **54 passed / 0 failed**
- Frontend `workspace/agro`: **75 passed / 0 failed**
- AUTO sample: PASS · CRYPTO sample: PASS · BEAUTY sample: FAIL (pre-existing version asserts, unrelated)

## Manual click audit

See `docs/AGRO_2_5_CLICK_AUDIT.md`.

- Interactive elements checked: **86**
- Failed: **0**

## Modified files

- `services/agro_ops/command_center.py` — `_live` demo filter; search label «Складская партия»
- `services/agro_ops/finance.py` — demo/test excluded from finance summary
- `applications/agro_enterprise/api/ops_handlers.py` — `audit_version: AGRO_2_5`
- `src/web/workspace/agro/AgroBusinessPage.tsx` — `from` / `closeEntity` / notification open
- `src/web/workspace/agro/AgroDeal360.tsx` — add task, sticky Back, DEMO label
- `src/web/workspace/agro/AgroCounterparty360.tsx` — sticky / DEMO / RU aging
- `src/web/workspace/agro/AgroCommandCenter.tsx` — RU cost labels
- `src/web/workspace/agro/AgroWeatherPanel.tsx` — region Back; RU matrix
- `src/web/workspace/agro/AgroNotificationsPanel.tsx` — linked click
- `src/web/workspace/agro/AgroIntelPanel.tsx` — RU technical footer
- `src/web/workspace/agro/agroWeather.css` — mobile UX
- `src/web/workspace/agro/sprint_agro_2_5.test.tsx` (new)
- `src/web/workspace/agro/sprint_agro_2_0.test.tsx` / `sprint_agro_weather.test.tsx` — RU matrix expectations
- `tests/test_sprint_agro_2_5.py` (new)
- `docs/AGRO_2_5_CLICK_AUDIT.md` (new)
- `docs/SPRINT_AGRO_2_5_RESULT.md` (this file)

## Migrations

None.

## Unresolved

- BEAUTY `test_beauty_os_22_2` version assertions still fail (pre-existing; not Agro).
- trycloudflare quick tunnels have no uptime guarantee; recover with `cloudflared tunnel --url http://127.0.0.1:5180` if expired.
- Viewer still cannot export management brief (`export` permission) — intentional RBAC.

## URLs

**DESKTOP URL:** http://127.0.0.1:5180/workspace/agro

**CURRENT WORKING MOBILE HTTPS URL:** https://logos-philip-environment-determination.trycloudflare.com/workspace/agro

## Architectural decisions

- Prefer `from` query over `history.back()` for 360 Back so Android/browser back never leaves Agro incorrectly mid-journey.
- Production aggregations filter DEMO/TEST by `is_demo` and title markers; lists still show labelled demo rows when explicitly loaded.
- No new platform package; extend `services/agro_ops` + existing React workspace.

STOP. Do not start AGRO 2.6.
