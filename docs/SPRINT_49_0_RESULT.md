# SPRINT 49.0 RESULT

Beauty / Cafe / Crypto OTC — business cabinets (RU ops UI), not engineering reuse matrices.

## Goal

Turn three vertical workspaces into understandable **business software**: salon ops, venue ops, OTC trader desk. Architecture stays underneath; workflows and menus lead.

## Architectural decisions

1. **Replace LiveWorkflow as the primary `/workspace/{beauty|cafe|crypto}` surface** with dedicated `*BusinessPage` cabinets. LiveWorkflow pages remain in the repo for certification/pilot reuse audits, but are no longer the default trader/salon/venue entry.
2. **Shared shell** `workspace/business-ops/BusinessCabinetShell.tsx` + `opsApi.ts` — one table/nav UX for all three verticals (search placeholder, empty/loading/error, RU labels).
3. **No fake payment gateways / live markets** — empty or «требуется настройка» when APIs/providers are absent; BOS/COS/crypto-enterprise remain sources of truth.
4. **Preserve Sprint 48.x payout antifraud** — OTC desk links to existing confirm panel; no bypass of `CryptoPayoutOrchestrator` / `CryptoTxAntifraudEngine`.
5. **Catalog** — expand Beauty/Crypto nav; **add Cafe** to `VERTICAL_WORKSPACES` with deep links into `/workspace/*?view=…`.

Rejected: rewriting LiveWorkflow in place (still engineering-first); inventing new RBAC; fabricating chart/market live feeds.

---

## 1. BEAUTY

**Implemented:**
- RU cabinet: Главная, Клиенты, Услуги, Товары, Записи, Календарь, Мастера, Смены, Продажи, Аналитика, Маркетинг, Склад, Финансы, Настройки
- Loads `/api/enterprise-bos/v1` (customers, services, appointments, employees, dashboard) + bootstrap
- Quick actions to bookings/clients/calendar; Beauty AI kept as separate link
- No platform reuse matrix on open

**Remaining:**
- Rich calendar UI (list/week views beyond table)
- Full product catalog CRUD when warehouse API is populated
- Marketing send only after channel config (status shown, no fake send)

## 2. CAFE

**Implemented:**
- RU venue cabinet with full nav (Главная … Настройки)
- Order types: Обычный / Банкет / ДР / Кейтеринг / Караоке / Закрытие / Beauty-мероприятие / Корпоратив / Другое
- COS API wiring (orders, menu, tables, reservations, staff, customers, dashboard)
- Halls/tables list management (no floorplan engine this sprint)

**Remaining:**
- Full order create form persistence beyond API shape
- Graphical floorplan (deferred by design)
- Cashier refunds when COS exposes them

## 3. CRYPTO OTC

**Implemented:**
- Trader desk nav (no Automotive/Beauty/Cafe/Agro/Legal/Enterprise Reuse tables)
- Watchlist in localStorage; pair table with source/freshness notes
- Charts / analysis / scheduled analysis UI with «не подключено» when provider missing
- Deals / wallets / transfers operational views; antifraud link retained

**Remaining:**
- Real chart provider adapter when TradingView/market feed is configured
- Cross-rate calculator backend wiring beyond UI shell
- Signal engine when product provides one

## 4. LOCALIZATION

**Russian coverage:** Business cabinets and vertical catalog nav/labels for Beauty, Cafe, Crypto OTC are RU-first.

**Remaining English strings:** Vertical switcher titles (`Beauty`, `Cafe`, `Crypto OTC`) kept as product names; some shared chrome/EDS components outside this sprint.

## 5. BACKEND

**New/changed APIs:** none required for cabinet shell (consumes existing BOS/COS/crypto-enterprise).

**New/changed models / migrations:** none.

## 6. TESTS

| Suite | Result |
|-------|--------|
| Frontend Sprint 49 cabinets | 3 passed |
| Frontend vertical catalog 42.8/49.0 | 11 passed |
| Backend API freeze + management security | 22 passed |
| Backend crypto antifraud 48.0 + payout 48.1 | 33 passed |
| Failures | none in targeted runs |

## 7. LOCALHOST

| Item | Value |
|------|--------|
| Frontend URL | http://localhost:5180 |
| Backend URL | http://127.0.0.1:8080 |
| Health | `GET /health` → ready/ok (status may be `degraded`) |
| Login | http://localhost:5180/login → 200 |
| Beauty | http://localhost:5180/workspace/beauty → 200 |
| Cafe | http://localhost:5180/workspace/cafe → 200 |
| Crypto OTC | http://localhost:5180/workspace/crypto → 200 |
| BOS/COS/Crypto health | 200 |

Demo auth: `owner@demo.corp` / `demo` when `VITE_DEMO_AUTH` (default in DEV).

## 8. TECHNICAL DEBT

- LiveWorkflow pages still exist for other verticals / audits — keep out of trader/salon primary paths
- Table UX: search is local placeholder; full filter/sort/pagination/column visibility not fully wired to shared DataTable yet
- OTC watchlist is client-local until a user-pref API exists
- Cafe/Beauty empty modules show honest empty/config states rather than synthetic datasets

## 9. FILES CHANGED

**shared**
- `src/web/workspace/business-ops/BusinessCabinetShell.tsx`
- `src/web/workspace/business-ops/opsApi.ts`
- `src/web/src/App.tsx` (route wiring)
- `src/web/src/vertical-workspace/catalog.ts`

**beauty**
- `src/web/workspace/beauty/BeautyBusinessPage.tsx`

**cafe**
- `src/web/workspace/cafe/CafeBusinessPage.tsx`

**crypto**
- `src/web/workspace/crypto/CryptoOtcDeskPage.tsx`

**backend**
- (none this sprint)

**tests**
- `src/web/workspace/business-ops/sprint_49_0_business_cabinets.test.tsx`
- `src/web/src/vertical-workspace/sprint_42_8_vertical_workspaces.test.ts`

**docs**
- `docs/SPRINT_49_0_RESULT.md` (this file)

## 10. NEXT RECOMMENDED SPRINT

**Sprint 49.1 — Operational depth:** Beauty calendar week grid + create appointment flow; Cafe order create/edit with event types persisted; OTC chart provider abstraction + watchlist API; shared DataTable filters/pagination for all three cabinets.

Do **not** start automatically.
