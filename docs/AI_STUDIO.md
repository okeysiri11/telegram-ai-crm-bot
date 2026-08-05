# Enterprise AI Studio

**Sprint:** 28.3 · Route `/ai-studio`  
**Package:** `src/web/src/ai-studio/` (thin shell) + `src/web/src/ai-production-studio/` (capability owner)

## Purpose

Production-ready visual AI Studio for creating and managing AI-generated content — composed on Enterprise Runtime and Production Center.

## Rule

No second store, job engine, or design system. `/ai-studio` composes Production + Runtime modules.

## Surfaces

| Area | Implementation |
|------|----------------|
| Image / Video / Audio / Voice / Avatar / Prompt | `StudioWorkbench` over existing studio IDs |
| Template / Asset / Media | `LibraryBrowser` |
| Project Explorer / Dashboard | `ProjectExplorer` + `ProjectDashboard` |
| Generation History / Favorites | `GenerationHistoryPanel` |
| Prompts | Collections · categories · variables · versioning · search · favorites |
| Runtime | Existing `ProductionRuntimePanel` / Job Manager |

## Deep links

- `/ai-studio?studio=image`  
- `/ai-studio?tab=projects|prompts|templates|assets|media|history|favorites|runtime`  

## City / Desktop

Existing Production district buildings + AI Studio building (`/ai-studio`). Assets / Templates / Media buildings open AI Studio library tabs.

## Related

- [`PRODUCTION_CENTER.md`](./PRODUCTION_CENTER.md)  
- [`RUNTIME_ENGINE.md`](./RUNTIME_ENGINE.md)  
- [`SPRINT_28_3_RESULT.md`](./SPRINT_28_3_RESULT.md)  

## Sprint 30.8 hub

`src/web/src/enterprise-business/AiStudioModulePage.tsx` — Russian hub linking Agent Center, Prompt Library, Workflow Builder, AI tasks (`jobManager`), pipeline history, Command/AI Runtime logs. No mock agent catalog — uses `DEFAULT_AGENTS` + production store.
