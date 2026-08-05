# Production Studio V1 (Enterprise MVP)

**Sprint:** 32.0 (AI Production Studio MVP track)  
**Package:** `src/web/src/ai-production-studio/`  
**Routes:** `/production-studio`, `/ai-studio` (visual twin)

## Naming collision

Sprint **32.0** is also **Enterprise Web Completion** (`ENTERPRISE_WEB_COMPLETION_32_0.md`).  
This document covers the **Production Studio MVP** track only.

## What ships

| Surface | Implementation |
|---|---|
| Production Home | `ProductionHomeDashboard` |
| Projects / Assets / Templates / Media | Existing explorers + LibraryBrowser |
| Brand Library | `BrandKitPanel` + `brandKit.ts` |
| Prompt Library | `PromptStudioPanel` + store |
| AI / Render queues | `TaskQueuePanel` + `productionRuntime` / `jobManager` |
| Generation History | `GenerationHistoryPanel` + metered records |
| Workflow Builder | `WorkflowBuilderPanel` over pipelines (no second engine) |

## Execution path

```
UI generateInStudio
  → brand variables + prompt resolve
  → optional n8n launch (orchestration only)
  → productionRuntime.runUniversalPipeline → jobManager
  → GenerationRecord (provider · tokens · cost · logs)
  → settleGeneration (done/failed)
```

**System of record:** Enterprise Runtime.  
**AI calls:** via APH / provider registry.  
**n8n:** external automation only.

## Content types

Text · Images · Video · Reels · Stories · Posts · Ads · Presentations · Landing · Email · PDF  
→ mapped to existing studio ids (`contentTypes.ts`).

## Related

`AI_PIPELINES.md`, `BRAND_KIT.md`, `PROMPT_LIBRARY.md`, `WORKFLOW_ENGINE.md`, `SPRINT_32_0_RESULT.md`
