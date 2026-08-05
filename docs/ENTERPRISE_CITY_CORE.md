# Enterprise City Core — Architecture

**Sprint:** 27.8  
**Package:** `src/web/src/enterprise-city/`  
**Foundation:** Enterprise Desktop (`/desktop`) as OS · City as primary navigation space

## Principle

City is a **visual navigation layer**, not a separate application.

```
Enterprise Desktop (OS)
        ↓ openApp("city") / nav
Enterprise City (map)
        ↓ building click
Existing routes / Workspace (embed)
```

No duplicated pages. Buildings only deep-link into shell / workspace / platform-builder routes.

## Layers

| Layer | Module | Role |
|-------|--------|------|
| Engine | `cityEngine.ts` | Camera · zoom · pan · viewport memory |
| Districts | `cityDistricts.ts` | 12 districts · plaza · street graph |
| Buildings | `cityCatalog.ts` | Catalog · routes · AI assistant labels |
| Navigation | `cityNavigation.ts` | History · recent · favorites · breadcrumbs |
| Live | `useCityLiveStatus.ts` | Notifications + live-ops enrichment |
| Visual | `cityVisualLanguage.ts` | States · silhouettes · advisor hints |
| UI | `EnterpriseCityPage.tsx` | Map stage · minimap · chrome |

## Routes

| Path | Behavior |
|------|----------|
| `/enterprise-city` | Canonical City Core |
| `/city` | Same map (unified) |
| `/city-hub` | Legacy module hub (optional) |
| `?embed=1` | Desktop window (no FullLayout) |

## APIs (client)

No new backend APIs. City consumes:

- Notification store  
- Live Enterprise snapshot  
- Search index / provider  
- Favorites manager  
- Desktop session (windows)  
- Concierge / smart suggestions  

## Performance

- Route-level `React.lazy`  
- Memoized search / street / glance  
- Session viewport (no poll storms beyond existing live-ops)  
- Buildings open existing code-split routes  

See also: [CITY_ENGINE.md](./CITY_ENGINE.md) · [CITY_DISTRICTS.md](./CITY_DISTRICTS.md) · [DESKTOP.md](./DESKTOP.md) · [AI_PRODUCTION_CENTER_ARCHITECTURE.md](./AI_PRODUCTION_CENTER_ARCHITECTURE.md)
