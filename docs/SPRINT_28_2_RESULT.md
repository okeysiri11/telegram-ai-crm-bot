# Sprint 28.2 — AI Production Center Runtime

**Phase:** Enterprise Platform v9  
**Priority:** CRITICAL  
**App:** `src/web` · sprint `28.2`  
**Constraint:** Extend Enterprise Runtime only — no second job engine / no UI framework.

## Goal

Production Center is a first-class part of the Enterprise Runtime. All creative operations enqueue through Job Manager + Production Runtime facade.

## Implemented

1. **Production Runtime** (`productionRuntime.ts`) — queues, workers, retry, analytics over existing Job Manager  
2. **Queues** — Production · Task · Render · Generation · Publishing  
3. **Job / Progress Monitor** — `ProductionRuntimePanel` (lazy) in Production Center → Runtime tab  
4. **Background Workers** — 6 typed workers scheduled on Runtime Engine tick  
5. **Retry Manager** — `productionRuntime.retryFailed()` → `jobManager.retry`  
6. **Queue Analytics** — depth, running, failed, ETA, throughput, clear estimate  
7. **Universal Pipelines** (8) — Image, Video, Audio, Voice, Avatar, Reels, Campaign, Publishing  
8. **AI** — agent assignment / collaboration / multi-agent via existing `aiAgentRuntime`  
9. **City** — Audio, Voice, Avatar, Creative, Render, Analytics buildings + live queue occupancy  
10. **Desktop** — studio apps + Production Runtime launcher entry  
11. **Monitoring** — Runtime metrics include queue depths; EventBus `production` / `queue` streams  

## Existing services used

- Enterprise Runtime Engine · Job Manager · Health Service · AI Agent Runtime  
- `enterpriseEventBus` · `notificationStore` · `productionStore`  
- Desktop Window Manager · City catalog · Design System · WorkspaceLayout  

## Runtime services extended

| Service | Extension |
|---------|-----------|
| `RuntimeJobRecord` | `queueKind`, `studioId`, `pipelineId`, `universalPipelineId`, `agentIds`, `workerId` |
| `jobManager` | queue annotation on automation sync · `listByQueue` |
| `runtimeEngine` | calls `productionRuntime.tick()` · queue metrics on snapshot |
| `useRuntimeHealth` | unchanged singleton |
| Production Center | Runtime tab · `runUniversalPipeline` · enqueue mirrors to Job Manager |

## New pipelines

| ID | Studio | Primary queue |
|----|--------|---------------|
| `image_generation` | image | generation |
| `video_generation` | video | generation |
| `audio_generation` | audio | generation |
| `voice_generation` | voice | generation |
| `avatar_generation` | avatar | render |
| `reels_generation` | reels | generation |
| `campaign_generation` | ads | production |
| `publishing` | publishing | publishing |

## Architecture

```
Production UI / City / Desktop
        ↓
productionStore.runUniversalPipeline / enqueueJob
        ↓
productionRuntime (facade)
        ↓
jobManager + aiAgentRuntime + healthService
        ↓
runtimeEngine tick → EventBus
```

## Tests

| Check | Result |
|-------|--------|
| lint (`tsc -b`) | OK |
| test | **133 passed** (includes `productionRuntime.test.ts`) |
| build | OK |

## Remaining work

- Wire frontend adapter to backend `platform_jobs` `/management/v1/jobs`  
- True render-farm resource classes / cost  
- Enforce approval gate before Publishing queue execute  
- City camera URL sync + richer district heatmaps  
- Multi-window Desktop coexistence for studio deep links  

## Readiness

| Area | Estimate |
|------|----------|
| Enterprise Runtime | **88%** |
| Production Center | **82%** |
| Enterprise Platform | **78%** |
