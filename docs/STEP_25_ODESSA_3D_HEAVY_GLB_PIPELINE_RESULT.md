# STEP 25 — Odessa 3D heavy GLB pipeline + main-thread stall reduction

## Shipped

Dedicated fetch / parse / activation queues, a main-thread parse scheduler with interaction protection, one heavy `GLTFLoader.parse` at a time, Safari-safe yields between parses, fetch backpressure, limited network retry, AbortController cancel for low-priority fetches, pipeline diagnostics, and bounded `performance.mark` history.

STEP 20–24 preserved: water duplicate guard, IDLE / INTERACTING / SETTLING, frame-budgeted activation, environment/sky/fog, virtual LOD priority, sea/coast/look-at protection, hysteresis, bounding cache. Original GLBs were not modified. No generated LOD files, no worker `GLTF.parse`, no weather, traffic, night lighting, or postprocessing.

Not started: STEP 26.

## Before architecture (STEP 24)

```
enqueue → fetch+parse in the same loadOne()
maxConcurrent (1–3) started both I/O and CPU
GLTFLoader.parse ran as soon as the ArrayBuffer arrived
RAF yield only in loadOne.finally — two completed fetches could still parse back-to-back in one turn
activation already budgeted (STEP 22) and paused while INTERACTING
```

Main-thread time was dominated by synchronous `GLTFLoader.parse` (JSON decode + BufferGeometry / Material / Texture construction). Fetch `arrayBuffer()` is async. Scene attach is a later RAF budget (STEP 22). Bounds come from the STEP 24 cache, not per-tick `Box3`.

## After architecture

```
manifest
  → fetch queue          (concurrency = quality maxConcurrentLoads)
  → ArrayBuffer
  → GLB header inspect   (main thread, <1 ms, no copy)
  → parse wait queue     (priority = STEP 24 score + parse band)
  → ParseScheduler       (exactly one GLTF.parse; yield after each)
  → PARSED off-scene
  → ProgressiveSceneActivator (unchanged STEP 22 budgets)
  → ACTIVE
```

```
odessa3d/loading/
  parsePolicy.ts        start rules, backpressure, retry, cancel safety
  parseScheduler.ts     one parse at a time + yield
  parseDiagnostics.ts   timings, long-task buckets, bounded marks
  browserYield.ts       postTask / rAF / setTimeout fallbacks
  glbInspect.ts         header inspect + worker-feasibility constants
  longTaskObserver.ts   optional PerformanceObserver("longtask"), DEV only
```

Lifecycle additive state: `waiting_parse` between `fetching` and `parsing`.

## Queue design

| Queue | Limit | Notes |
|---|---|---|
| FETCH | quality 1 / 2 / 3 | Paused while INTERACTING (STEP 21). Sorted by STEP 24 band + score. |
| PARSE | **1** | Never two HEAVY/EXTREME in the same turn. Mandatory yield after every parse. |
| ACTIVATION | STEP 22 frame budget | Unchanged. |

Backpressure (stop lower-priority fetches):

- waiting-parse count (including in-flight fetches) ≥ 3
- waiting-parse MB ≥ 48
- parsed-waiting-activation count ≥ 8
- parsed-waiting-activation MB ≥ 80

Sea / look-at / visible NEAR–MID may still fetch under backpressure. Prefetch may not.

## Scheduler policy

Parse order (authoritative STEP 24 score, plus hard band):

1. visible NEAR  
2. visible MID  
3. camera-target adjacent (`TARGET`)  
4. visible FAR  
5. EDGE  
6. OUTSIDE  

Starvation: band promotes at most two steps after 8 s / 16 s waiting so a stuck EDGE cannot sit forever behind a stream of slightly nearer files — but a 25 MB OUTSIDE still cannot jump a visible NEAR.

**INTERACTING:** MEDIUM / HEAVY / EXTREME parses **do not start**. LIGHT may start only if the last parse was < 50 ms and FPS ≥ 28. A parse that already entered `GLTFLoader.parse` cannot be preempted.

**SETTLING:** HEAVY / EXTREME wait unless sea / look-at / screen-important.

**EXTREME:** deferred until IDLE + FILLING/READY + no higher-priority waiter, unless the asset is sea-protected or at the camera target (avoids a coastline / look-at hole).

After each HEAVY/EXTREME parse: double `requestAnimationFrame` (one rendered frame). After LIGHT/MEDIUM: `scheduler.postTask` when present, else one rAF / `setTimeout`.

BOOTSTRAP still uses priority tiles for first useful geometry. The city becomes INTERACTIVE at first attach (STEP 22). EXTREME city chunks wait.

Prefetch (streamer extra batch of 2) only while IDLE, not BOOTSTRAP, and only when the parse queue is empty.

## Safari fallback

- No `SharedArrayBuffer` requirement  
- No cross-origin isolation  
- No WebGPU  
- `scheduler.postTask` optional  
- `requestIdleCallback` still optional (STEP 22 idle prep only)  
- `PerformanceObserver({ type: "longtask" })` diagnostics/dev only; not used for scheduling  
- Yield fallback: `requestAnimationFrame` → `setTimeout(0)`  

## Worker feasibility conclusion

**Full `GLTFLoader.parse` is not in a worker.** It builds live Three.js `Object3D` / `BufferGeometry` / `Material` / `Texture` graphs that are not structured-cloneable as GPU objects. Transferring the source `ArrayBuffer` would **detach** it before the required main-thread parse; copying 20–25 MB would cost more memory than the inspect itself.

Worker-safe work that *could* move later (not claimed as implemented parse):

- GLB header / chunk-length inspect (`inspectGlbHeader` already runs on the main thread because it is < 1 ms)
- manifest enrichment
- future meshopt/draco decode *if* a decoder is added and ownership of the buffer is explicit

Buffers are never transferred. The same `ArrayBuffer` is passed into `GLTFLoader.parse`. No duplicate 20–25 MB copies.

## Network / errors

- Fetch failures: up to 2 retries with 400 ms × 3^attempt backoff. Not retried: HTTP 4xx (except 408/429), invalid magic, HTML body, parse errors, priority cancel.  
- Parse failures: `FAILED`, no retry, remainder of the queue continues.  
- In-flight fetches that become EDGE/OUTSIDE, not sea, not look-at, not visible NEAR/MID/FAR, may be aborted. The asset returns to `idle` so the streamer can take it later. Already-parsing GLTF is never aborted.

## Diagnostics

Perf panel section **GLB PIPELINE**: FETCHING, WAITING_PARSE, PARSING, PARSED, WAITING_ACTIVATION, ACTIVE / HIDDEN / FAILED, current parse id/size/elapsed, last/avg/worst parse ms, long tasks 50/100/250/500, queues F/P/A, fetch vs parse concurrency, backpressure, worst offenders.

`performance.mark("odessa25:…")` kept to the last 40 marks.

Normal HUD stays compact (`boot · active/total`).

## Integration with STEP 21 / 22 / 24

- INTERACTING still pauses **new fetches** and **activation** (budget 0) and the LOD visibility pass.  
- Parse of already-downloaded LIGHT files may continue if measured safe.  
- Streamer and activator still use `scoreLodPriority`.  
- City tiles stay retained; sea/coast never hidden; no invented `_lodN` URLs.

## Measured results

Safari / Intel live capture of time-to-first-geometry, INTERACTIVE, READY, parse ms, interaction FPS, and renderer memory: **UNAVAILABLE** in this session. Numbers were not invented.

What is known without a live GPU session:

| | STEP 24 | STEP 25 |
|---|---|---|
| Tests | 139 passed | **162 passed** |
| Vite build | PASS | **PASS** |
| enterprise-city chunk | ~714 kB | **735 kB** |
| GLB files | 45 original | 45 original (unchanged) |
| Worker GLTF parse | none | none (by design) |

Live parse timings appear in Diagnostics after a real load (`GLB PIPELINE` + first-load KPIs). Report those from the overlay; do not copy guessed values into this file.

## Remaining bottlenecks

1. **`GLTFLoader.parse` is still synchronous on the main thread.** STEP 25 makes it *interruptible between files*, not *preemptible inside a 20–25 MB parse*. A single EXTREME file can still hitch for hundreds of milliseconds.  
2. No geometric LOD / meshopt / Draco — one mesh per asset.  
3. First-load hitch remains a function of the first LIGHT/priority GLB size, not of the whole 382 MB package.  
4. A correct worker path needs an authored decode pipeline and explicit buffer ownership — future work, not a fake `postMessage(Object3D)`.

## Tests

`npm test -- src/enterprise-city` — **162 passed** (13 files).

Coverage includes: parse priority vs FIFO, INTERACTING blocking, heavy serialization + yield, starvation, fetch vs parse concurrency, backpressure, AbortController, network retry, parse failure isolation, queue lifecycle, 2D/3D remount cleanup, Safari yield fallback, worker-feasibility flags.

## Build

`npx vite build` — **PASS**.

Follow-up: [STEP 25.2 runtime recovery](./STEP_25_2_ODESSA_3D_RUNTIME_RECOVERY_RESULT.md) (canvas kept on init failure, normalized HUD, local diagnostic panel). STEP 26 not started.
