# Sprint 42.1 — Multi-Role Experience & Parallel Workspaces

**Status:** COMPLETE · READY FOR REAL CLIENT DEMO (multi-window)  
**Scope:** Multi-tenant UX · role simulation · session isolation  
**Baseline:** Sprint 42.0 Workspace Revolution

---

## Goal

Open the platform **simultaneously** under different roles/companies without sessions colliding.

---

## Feature map

| # | Feature | Delivery |
|---|---------|----------|
| 1 | Parallel workspaces | Ports `3000–3004+` + `VITE_WORKSPACE_SLOT` · scoped `localStorage` via `wsKey()` |
| 2 | Demo users | 10 seeded accounts (`*@ados.demo` / `travel@globefly.demo`), password `demo` |
| 3 | Client onboarding | 6-step wizard `/onboarding/client` |
| 4 | Role-based home | Owner → `/owner`, Admin → `/admin`, Manager → daily tasks, Sales → pipeline, Client → workspace |
| 5 | Client workspace | Allowlist: CRM, Documents, Analytics, Tasks, Knowledge, Support, Settings |
| 6 | Role switcher | `DevRoleSwitcher` — developer mode (or `VITE_DEV_ROLE_SWITCHER=true`) |
| 7 | Session isolation | Per-slot keys + per-role vault (`roleSessionVault`) |
| 8 | Client demo mode | **Open Demo Workspace** one-click seed |
| 9 | Acceptance | Tests + this doc |

---

## Parallel windows (how to run)

```bash
cd src/web
npm run dev:owner    # :3000  Owner
npm run dev:travel   # :3001  Travel Agency
npm run dev:crypto   # :3002  Crypto OTC Manager
npm run dev:build    # :3003  Construction
npm run dev:drone    # :3004  Drone (optional)
```

Default `npm run dev` stays on **:5180** (slot `default`, backward-compatible keys).

Each port = separate browser origin → independent login, prefs, docks, notifications.

---

## Demo users (password: `demo`)

| Email | Company | Suggested port | View mode |
|-------|---------|----------------|-----------|
| `owner@ados.demo` | ADOS Platform | 3000 | platform_owner |
| `admin@ados.demo` | ADOS Platform | 3000 | company_admin |
| `travel@globefly.demo` | GlobeFly Travel | 3001 | client |
| `crypto@ados.demo` | Crypto Desk | 3002 | manager |
| `build@ados.demo` | BuildCorp | 3003 | client |
| `drone@ados.demo` | SkyFleet | 3004 | manager |
| `auto@ados.demo` | Prime Auto | 3005 | manager |
| `legal@ados.demo` | Lex & Partners | 3006 | client |
| `agro@ados.demo` | GreenField | 3007 | manager |
| `seller@ados.demo` | Seller Co | 3008 | client |

Login page includes a **demo account picker** + **Open Demo Workspace**.

---

## Client onboarding (6 steps)

1. Welcome  
2. Company profile  
3. Business type  
4. Choose modules  
5. Import data (demo / skip / file later)  
6. Finish → `/dashboard`

---

## Session isolation

- `wsKey(base)` prefixes keys when slot ≠ `default` (`ews_ws_{slot}__…`)
- Scoped: session, view mode, role, docks, toolbar, preferences, theme, first-entry, client onboarding, demo seed
- `roleSessionVault` snapshots toolbar/dock/tabs/prefs when Dev Role Switcher changes role **without logout**

---

## Acceptance checklist

| Check | Expected |
|-------|----------|
| Window Owner `:3000` + `owner@ados.demo` | Executive `/owner`, full chrome |
| Window Travel `:3001` + `travel@globefly.demo` | Client modules only, onboarding once |
| Window Crypto `:3002` + `crypto@ados.demo` | Manager home, crypto modules |
| Window Build `:3003` + `build@ados.demo` | Independent client session |
| Logout on one port | Others stay signed in |
| Notifications / docks | Independent per port |

---

## Tests

| Suite | Result |
|-------|--------|
| Vitest `multi_role_42_1.test.ts` | **PASS** (8) |
| TypeScript (`npm run lint`) | **PASS** |

---

## Architectural decisions

- Prefer **port isolation** (browser origin) for parallel demos — no shared cookie jar.  
- Slot prefix adds isolation when env is set even before navigation.  
- Extended `demoAuthProvider` for `@ados.demo` without new IAM backend.  
- Client onboarding is separate from platform First Entry (owners/admins keep 34.x wizard).

---

## Recommendations

1. Start four terminals with `dev:owner|travel|crypto|build` for stakeholder demos.  
2. Use Chrome profiles or separate windows per port.  
3. Add Playwright multi-origin smoke next sprint.  
4. Watch port **3000** collision with Grafana/kernel if those are running.

**READY FOR REAL CLIENT DEMO**
