# AI Pipelines

**Sprint:** 32.0 Production Studio MVP  
**Runtime:** `productionRuntime` · `universalPipelines` · `jobManager`

## Studio pipelines

Each studio maps to a universal pipeline (generation → optional render → publish).  
Stages in the UI builder: Draft → Review → **Approval** → Generation → Render → Publish → Archive.

## Parallelism & retries

- Parallel agents = `agentChain` on pipeline + multi-agent `generateInStudio`  
- Retries = `retryJob` / `productionRuntime.retryFailed`  
- Human approval = stage `approval` gate in Workflow Builder  

## External automation

n8n templates (`n8n_tpl_media_pipeline`) may fan-out HTTP calls; **business logic stays in Runtime**.

## Cost & tokens

`estimateGenerationMeter` + GenerationRecord fields (`providerId`, `tokens`, `costUsd`, `durationMs`, `logs`).
