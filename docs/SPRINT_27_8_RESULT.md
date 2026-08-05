# Sprint 27.8 — Enterprise City Core

**Phase:** Enterprise Platform v9  
**App:** `src/web` · sprint `27.8`  
**Priority:** CRITICAL  
**Constraint:** Extend Enterprise Desktop + existing City — no rewrite, no duplicated pages.

## Goal

Ship the first full **Enterprise City Core** as the primary visual navigation layer. Desktop remains the OS foundation; City is the map into existing workspaces.

## Implemented

1. **City Engine (presentation)** — camera, zoom, pan, viewport memory (`cityEngine.ts`)  
2. **District System** — 12 districts: Enterprise · CRM · ERP · AI · Production · Marketplace · Analytics · Knowledge · Finance · Developer · Security · Settings  
3. **Building System** — 22 buildings → existing routes only (+ AI assistant per building)  
4. **Street Navigation** — plaza-centered street graph + district links  
5. **Plaza** — Central Plaza hub with focus ring  
6. **Camera / Zoom / Pan** — drag pan, wheel zoom, buttons, session restore  
7. **Minimap** — status dots + live viewport rectangle  
8. **Navigation** — breadcrumbs, search, quick jump, history, recent, favorites  
9. **AI** — existing Concierge / smart suggestions + per-building assistant labels  
10. **Desktop foundation** — City pinned in dock, menubar link, `/city` → real map, catalog path `/enterprise-city`

## Existing services reused

| Service | Use |
|---------|-----|
| `WorkspaceLayout` + `?embed=1` | Desktop window embed |
| `useCityLiveStatus` / `useLiveEnterprise` / notifications | Live building status |
| `searchIndex` / `searchProvider` | Search + quick jump |
| `favoritesManager` | Sync city favorites |
| `suggestionsForPath` / Concierge routes | AI assistants |
| `desktopStore` / dock catalog | OS foundation |
| Shell routes (`/crm`, `/erp`, …) | Building destinations |
| EDL glass / motion | Visual language |

## Extended

- `cityCatalog.ts` — districts + buildings (ERP, Marketplace, Developer, Security, Settings, Plaza, AI Studio)  
- `cityVisualLanguage.ts` — identities / advisor `assistant` field  
- `EnterpriseCityPage.tsx` — camera, streets, nav chrome, plaza  
- `deriveTwin.ts` — districts from `CITY_DISTRICTS`  
- Desktop / shell nav / module catalog / `/city` route  
- CSS — district labels, plaza, minimap viewport, breadcrumbs

## Optimized

- Lazy route already via `React.lazy(EnterpriseCityPage)`  
- Minimized re-renders via memoized filters / viewport rect  
- Session viewport persistence (no new server state)  
- Single catalog source for Twin + City + Desktop

## Docs

- `docs/ENTERPRISE_CITY_CORE.md` — architecture  
- `docs/CITY_ENGINE.md` — camera/nav engine  
- `docs/CITY_DISTRICTS.md` — districts & buildings  
- `docs/SPRINT_27_8_RESULT.md` — this report  
- Updated `docs/ENTERPRISE_CITY.md` / `docs/DESKTOP.md` pointers

## Tests

| Check | Result |
|-------|--------|
| lint (`tsc -b`) | OK |
| test | **105 passed** |
| build | OK |

## Readiness

**Enterprise City Core readiness: ~78%**

## Remaining to full City

- 3D / WebGL horizon (Bible)  
- Nested keep-alive building interiors (non-iframe)  
- Occupancy / presence layer  
- Multi-space virtual desktops  
- Guided tours + street path animation  
- Host-level metrics on map  
- Deeper AI agent binding (runtime agents per building, not labels only)

## Verify

```bash
cd src/web && npm run lint && npm test && npm run build && npm run dev
```

Open `/enterprise-city` or Desktop → City · pan/zoom · jump CRM · Enter building.
