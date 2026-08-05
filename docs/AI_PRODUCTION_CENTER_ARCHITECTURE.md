# AI Production Center — Architecture

**Sprint:** 27.9  
**Package:** `src/web/src/ai-production-studio/`  
**Route:** `/production-studio` (alias `/production`)  
**Foundation:** Enterprise Desktop + Enterprise City Production District

## Principle

Production Center is the **creative content OS** of ADOS — not a second platform.

```
Enterprise Desktop / City
        ↓
AI Production Center
        ↓ studios · pipelines · prompts · media · automation
Existing routes (Runtime · Workflow · Themes · Assets · Documents · Analytics)
```

Does **not** replace:

- AI Builder Studio agent prompts  
- Platform Builder visual asset/rendering engines  
- `platform_jobs` / `platform_workflows` backend engines  

## Layers

| Layer | Module |
|-------|--------|
| Catalog | `productionCatalog.ts` — 17 studios, pipeline stages |
| Store | `productionStore.ts` — `ews_ai_production_v1` |
| Shell | `AIProductionCenterPage.tsx` |
| Studios | `StudioWorkspace.tsx` (lazy) |

## Studios (17)

Image · Video · Audio · Voice · Avatar · Reels · Ads · Creative · Prompt · Brand · Asset Library · Template Center · Media Storage · Render · Publishing · Scheduler · Analytics

## Pipeline

`Draft → Review → Approval → Generation → Render → Publish → Archive`

Rule: **AI never publishes alone** (approval stage required before publish).

## Integration

| Surface | Wiring |
|---------|--------|
| City | Production District buildings → `/production-studio?…` |
| Desktop | Production / Reels / Ads / Prompt apps |
| Workflow Center | `creative_campaign` template |
| Notifications / Runtime health | Status chips in center chrome |

See also: [PRODUCTION_CENTER.md](./PRODUCTION_CENTER.md) · [PROMPT_LIBRARY.md](./PROMPT_LIBRARY.md) · [MEDIA_MANAGER.md](./MEDIA_MANAGER.md)
