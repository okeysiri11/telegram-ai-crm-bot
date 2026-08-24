# AUTO 1.0 COMPLETE

Private Auto Import & Dealership Operating System for ADOS Enterprise.

**Workspace:** Рабочее пространство → Авто (`/workspace/auto`)  
**API:** `/api/auto-ops/v1` (private, org-scoped)  
**Not a public marketplace.** Existing `/api/auto/v1` marketplace contracts are unchanged.

---

## Completion checklist

| Gate | Result |
|------|--------|
| Architecture | **PASS** |
| Auto sidebar | **PASS** |
| Dashboard | **PASS** |
| Vehicle database | **PASS** |
| Vehicle profile | **PASS** |
| Lifecycle | **PASS** |
| Expenses foundation | **PASS** |
| Documents foundation | **PASS** |
| Photos | **PASS** |
| Clients foundation | **PASS** |
| RBAC | **PASS** |
| Audit | **PASS** |
| Telegram integration boundary | **PASS** |
| Tests | **14 passed / 0 failed** (backend 9, frontend AUTO 5; Human-First Auto 5 also green) |
| Build | **PASS** for AUTO 1.0 files (repo `tsc -b` still reports pre-existing errors in unrelated agro/crypto/ai-command files) |

---

## Architectural decisions

1. **New private ops desk, not a rewrite of `auto_marketplace`.**  
   Marketplace GA stays at `/api/auto/v1`. AUTO 1.0 adds `services/auto_ops` + `applications/auto_enterprise` at `/api/auto-ops/v1`, following Agro/Legal ops (`BusinessCabinetShell`, org/role headers, memory fallback + Postgres).

2. **Vehicle is a first-class typed entity**, not generic JSONB.  
   Tables: `auto_ops_vehicles`, `auto_ops_expenses`, `auto_ops_documents`, `auto_ops_photos`, `auto_ops_clients`, `auto_ops_tasks`, `auto_ops_audit`, `auto_ops_files`. VIN unique per organization.

3. **Existing CarEngine / marketplace inventory is not destroyed.**  
   New tables are additive. Legacy `car_engine_v1_cars` and marketplace catalog remain. Pilot workflow moved to `/workspace/auto/pilot`.

4. **Clients live in `auto_ops_clients` and link via `vehicle.client_id`.**  
   Enterprise CRM (`/api/auto/v1/crm`) is not duplicated into a second public CRM; the private desk has its own org-scoped contacts for this company OS. A later sprint can optionally link CRM contacts.

5. **Telegram is a prepared boundary only.**  
   Reuses `services/automotive_telegram_access.py` and existing auto routers. No new bot architecture in 1.0.

6. **No fake data.**  
   Dashboard finance and vehicle cost are aggregated only from expense records. Empty park shows zeros / empty states, not demo inventory.

Rejected: turning `AutomotiveLiveWorkflowPage` into the OS; putting ops routes under frozen `/api/auto/v1`; seeding example dollar amounts.

---

## 1. Changed files

### Backend
- `services/auto_ops/` — `catalog.py`, `vin.py`, `rbac.py`, `files.py`, `telegram_boundary.py`, `service.py`, `__init__.py`
- `applications/auto_enterprise/` — config, middleware, `api/ops_handlers.py`, `api/register.py`
- `database/models/auto_ops.py`
- `repositories/auto_ops_repository.py`
- `api/server.py` — registers auto enterprise ops (additive)
- `tests/test_auto_ops_1_0.py`
- `.gitignore` — `data/auto_ops_files/`

### Frontend
- `src/web/workspace/auto/AutoBusinessPage.tsx`
- `src/web/workspace/auto/autoLabels.ts`
- `src/web/workspace/auto/sprint_auto_1_0.test.tsx`
- `src/web/src/App.tsx` — Auto desk + `/workspace/auto/pilot`
- `src/web/src/config/webConfig.ts` — `autoOpsPrefix`
- `src/web/workspace/business-ops/opsApi.ts` — auto ops helpers
- `src/web/workspace/business-ops/cabinetCapabilities.ts` — `"auto"` + accountant finance
- `src/web/src/navigation/enterpriseRuNav.ts` — Бухгалтер role
- `src/web/src/modules/moduleLandingCatalog.ts`
- `src/web/src/human-first/AutoHumanLandingView.tsx`
- `src/web/src/human-first/autoAiIntents.ts`
- `src/web/src/human-first/human_first_auto_42_3.test.ts`
- `src/web/src/ux-revolution/moduleContextNav.ts`
- `src/web/workspace/managers/moduleRegistry.ts`

### Docs / migrations
- `migrations/versions/j9e012345678_auto_ops_1_0.py`
- `docs/SPRINT_AUTO_1_0_RESULT.md` (this file)

**Not modified:** Agro, Crypto, Beauty, Legal, Travel desks; `/api/auto/v1` marketplace contracts.

---

## 2. Migrations created

`migrations/versions/j9e012345678_auto_ops_1_0.py`  
Revises: `i8d901234567`  
Additive tables only. Does not drop or alter existing Auto/CarEngine tables.

Apply with the project Alembic flow when Postgres is available. Local API with `ADOS_SKIP_MIGRATIONS=1` still runs via in-memory fallback.

---

## 3. API endpoints created

Prefix: **`/api/auto-ops/v1`** (private; requires workspace auth + `X-Organization-Id` + `X-Role`)

| Method | Path | Notes |
|--------|------|--------|
| GET | `/health` | sprint, private flag, telegram boundary |
| GET | `/roles` | Director / Accountant / Manager / Admin |
| GET | `/catalogs` | statuses, expenses, documents, photos |
| GET/POST | `/dashboard` | KPI cards + finance from records |
| GET/POST | `/vehicles` | list/search/create |
| GET/POST | `/vehicles/{id}` | profile / update (status, VIN, sale…) |
| GET/POST | `/expenses` | list/create (finance roles) |
| POST/DELETE | `/expenses/{id}` | update/delete |
| GET/POST | `/clients` | clients linked to vehicles |
| GET/POST | `/documents` | metadata + vehicle/client/shipment/customs/sale/payment owner |
| DELETE | `/documents/{id}` | director/admin |
| GET/POST | `/photos` | gallery metadata |
| POST | `/photos/{id}/cover` | set cover |
| DELETE | `/photos/{id}` | |
| GET/POST | `/tasks` | CRM tasks |
| POST | `/tasks/{id}/complete` | |
| GET | `/audit` | business audit log |
| GET | `/reports` | director/accountant |
| GET | `/settings` | catalogs + technical (admin) |
| GET | `/telegram` | reuse plan, `implemented: false` |
| GET/POST | `/files` | blob upload (not public) |
| GET | `/files/{id}/content` | private inline |

No public VIN/client/finance routes.

---

## 4. Routes to inspect manually

With API on `:8080` and Vite on `:5180`, login `owner@demo.corp` / `demo`.

1. `/workspace/auto` — landing, then deep link  
2. `/workspace/auto?view=overview` — KPI dashboard  
3. `/workspace/auto?view=vehicles` — list + **+ Добавить автомобиль**  
4. `/workspace/auto?view=vehicles&action=vehicle` — create form (VIN + make/model or auction URL)  
5. Open a vehicle → tabs Обзор (lifecycle), Покупка, Логистика, Финансы, Документы, Фото, Задачи, История  
6. `/workspace/auto?view=purchases|logistics|customs|sales` — filtered operational lists  
7. `/workspace/auto?view=expenses` — real expenses only  
8. `/workspace/auto?view=telegram` — honest “next sprint” placeholder  
9. `/workspace/auto?view=settings` — roles, statuses, technical block  
10. `/workspace/auto/pilot` — previous live-workflow probe (not the OS)

Switch role to **Бухгалтер** / **Менеджер** and confirm finance vs create permissions.

---

## 5. Remaining issues (deferred to AUTO 1.1+)

- Strict status transition graph (any catalog status is allowed in 1.0).
- Link `auto_ops_clients` to enterprise CRM contacts.
- Shipment/container/customs as full entities (vehicle fields + statuses cover 1.0).
- Notifications via `/api/enterprise-comms/v1`.
- Telegram bot commands (VIN search, expense, photo) — boundary only.
- Auction/broker/tracking live integrations.
- Sale contract wizard.
- Apply Alembic on production Postgres (safe additive).
- Manager visibility of vehicle cost snapshot (currently director/accountant only, per RBAC spec).

---

## 6. Technical debt discovered

- Workspace **Авто** was a Human-First landing + `AutomotiveLiveWorkflowPage` API probe, not an ops desk.
- `applications/auto_marketplace` is a large public marketplace; `/api/auto/v1/ops/*` is DevOps, not business ops.
- Legacy `pg_car_engine.py` / `CarStatus` is a shorter lifecycle (`purchased`…`sold`) and was not migrated in 1.0 to avoid destroying data.
- `BusinessCabinetShell` `Card` does not forward `data-testid` (tests wrap in `div`).
- Role switcher previously had no **Бухгалтер** option; added as shared infra.
- Repo `tsc -b` already fails on unrelated files (`AgroDossierDrawer`, crypto chart, ai-command tests). AUTO 1.0 files typecheck clean in that filter.

---

## Tests run

```
.venv/bin/python -m pytest tests/test_auto_ops_1_0.py -q
# 9 passed

cd src/web && npx vitest run workspace/auto/sprint_auto_1_0.test.tsx src/human-first/human_first_auto_42_3.test.ts
# 10 passed
```

Covered: routes/health, vehicle CRUD, VIN uniqueness/normalize, lifecycle, expenses aggregation (no fake seed), documents/photos/clients/tasks/audit, RBAC (client denied, admin cannot create vehicles, manager cannot write expenses, accountant can view finance), unauthorized org isolation, cabinet IA, dashboard KPIs, Telegram honesty, settings technical block.

---

STOP AFTER AUTO 1.0. Do not start AUTO 1.1.
