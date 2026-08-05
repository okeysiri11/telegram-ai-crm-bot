# Sprint 28.3 — Enterprise AI Studio

**Phase:** Enterprise Platform v9  
**Priority:** CRITICAL  
**App:** `src/web` · sprint `28.3`  
**Constraint:** Compose on Runtime + Production — no architecture rewrite / no service duplicates.

## Implemented features

- **AI Studio page** `/ai-studio` — visual workspace for Image, Video, Audio, Voice, Avatar, Prompt  
- **StudioWorkbench** — generate via Runtime, variables, multi-agent, recommendations  
- **Prompt Studio** — collections, categories, variables, versioning, search, favorites  
- **Template / Asset / Media libraries** — unified `LibraryBrowser`  
- **Project Explorer** — create, recent, favorites  
- **Project Dashboard** — pipeline status, queue status, progress/ETA, output gallery, history  
- **Generation History** + Favorites  
- **City** — AI Studio + Assets/Templates/Media buildings (existing studio buildings retained)  
- **Desktop** — Avatar Studio launcher; AI Studio path unchanged `/ai-studio`  

## Extended modules

| Module | Extension |
|--------|-----------|
| `productionStore` | v2 snapshot · projects · generations · collections · generateInStudio |
| `productionCatalog` | project/generation/collection types · more prompts · `AI_STUDIO_VERSION` |
| `StudioWorkspace` | workbench + core-only grid for AI Studio |
| `AIProductionCenterPage` | Projects / History tabs · shared panels · link to AI Studio |
| `moduleCatalog` `ai_studio` | deep link → `/ai-studio` |
| City / Desktop catalogs | library buildings · avatar app |

## New reusable components

- `StudioWorkbench`  
- `PromptStudioPanel`  
- `LibraryBrowser`  
- `ProjectExplorer` / `ProjectDashboard`  
- `GenerationHistoryPanel`  
- `AIStudioPage` (composition shell)

## Architecture impact

```
/ai-studio (AIStudioPage)
    └── useProductionStore (shared)
    └── productionRuntime / jobManager / aiAgentRuntime
    └── EnterpriseRuntimeMonitor
/production-studio (unchanged capability owner, extended UI)
```

Full backward compatibility: v1 localStorage migrates to v2; `/production-studio` deep links preserved.

## Remaining work

- Backend generation providers (image/video/voice APIs)  
- Streaming preview thumbnails  
- Cross-window Desktop multi-studio coexistence  
- Stronger approval gate before publish outputs  

## Readiness

| Area | Score |
|------|-------|
| AI Studio | **80%** |
| Production Center | **86%** |
| Enterprise Platform | **80%** |

## Tests

| Check | Result |
|-------|--------|
| lint (`tsc -b`) | OK |
| test | **169 passed** (includes `aiStudio.test.ts`) |
| build | OK |
