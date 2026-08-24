# Sprint AGRO Command Center ops (52–62)

## Result

Hardening of the existing Agro Command Center on `/workspace/agro` + `/api/agro-ops/v1`. No second Agro subsystem. No SQL migration. Health remains `sprint: agro-2.0` / `command_center: AGRO_2_0`.

## Working URLs

**Public HTTPS (current trycloudflare):** https://logos-philip-environment-determination.trycloudflare.com/workspace/agro

Desktop: http://127.0.0.1:5180/workspace/agro

Deep routes (HTTP 200, SPA, Command Center — not catalog landing):

- https://logos-philip-environment-determination.trycloudflare.com/workspace/agro
- https://logos-philip-environment-determination.trycloudflare.com/workspace/agro?view=accounting
- https://logos-philip-environment-determination.trycloudflare.com/workspace/agro?view=fields
- https://logos-philip-environment-determination.trycloudflare.com/workspace/agro?view=logistics
- https://logos-philip-environment-determination.trycloudflare.com/workspace/agro?view=command
- https://logos-philip-environment-determination.trycloudflare.com/workspace/agro?view=report

## Architectural decisions

- **Aggregated read is agro-ops, not a new `/api/agro/v1` package.** `GET /api/agro-ops/v1/command-center` wraps the existing dashboard bag. Sections (`kpis`, `decisions`, `today`, `cash`, `inventory`, `logistics`, `fields`, `harvest`, `risks`, `data_quality`) are projections. Source tables are unchanged.
- **Desktop `/workspace/agro` is the ops cabinet.** `WorkspaceLandingGate` no longer shows the catalog landing for Agro, so refresh cannot bounce to «Открыть ферму».
- **Home load is one aggregated request.** Entity lists load lazily per `?view=` and are cached in-session. Settings/intel still fetch `/providers`.
- **Currencies are not summed.** Mixed-currency AR/AP totals are `null` with per-currency buckets. FX is reported only when a real rate exists (`Курс не подключён` otherwise). Timezone is the desk timezone, default `Europe/Kyiv`.
- **Exports reuse `GET /api/agro-ops/v1/export/{section}`.** Added `pnl`, `receivables`, `payables`, `inventory`, `crop-economics`, `field-economics`, `management-report`. No second export framework.
- **Management brief** is `GET /api/agro-ops/v1/command-center/report` (JSON or `?format=html`) titled **АГРО — УПРАВЛЕНЧЕСКАЯ СВОДКА**. Audited with `source=command_center`.
- **Drill-down** uses existing `?view=` + `filter` / `status=IN_TRANSIT` / `overdue=true`. KPI «в пути» opens logistics; overdue opens accounting.
- **RBAC** on aggregated sections: director/owner company-wide; accountant finance; logistics logistics; warehouse inventory; agronomist production; viewer read-only. Enforced in `command_center_read`.
- **Tenant:** `organization_id` + `workspace_id` (header `X-Workspace-Id`, default `agro`) on the aggregated read. Cross-org isolation tested.

## Tests

- Backend: `tests/test_sprint_agro_command_center_read.py` — 7 passed. Prior 2.0–2.3 command-center tests still green.
- Frontend: `src/web` `workspace/agro` — 70 passed / 0 failed.

## Migrations

None.

## Unresolved

- trycloudflare remains a quick tunnel (no uptime guarantee). If it expires, recover with `cloudflared tunnel --url http://127.0.0.1:5180`.
- XLSX export is Excel-compatible CSV served with an `.xlsx` filename when requested; there is no second binary XLSX engine.
- Viewer cannot download the management brief (`export` permission required).
