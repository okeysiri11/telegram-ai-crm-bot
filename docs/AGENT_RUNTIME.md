# Agent Runtime

**Sprint:** 32.1 · Package: `src/web/src/enterprise-runtime/aiAgentRuntime.ts`

## Lifecycle phases

Idle → Planning → Waiting → Running → Paused → Review → Completed / Failed / Cancelled → Retry

Coarse `status` maps from `phase` (`phaseToStatus`).

## API

- `list` / `get` / `subscribe`  
- `launch` · `pause` · `resume` · `complete` · `fail` · `cancel` · `retry` · `setPhase`  
- `healthSummary` · `tick` · `reset`  

Tasks remain owned by **Job Manager** / `taskExecution` — agents project work; they do not replace the queue.
