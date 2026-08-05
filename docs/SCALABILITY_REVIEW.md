# Enterprise Overnight Audit — Scalability Review

**Scope:** architecture-level bottleneck estimation only — no load testing was performed
(`docs/TECH_DEBT.md` §2.5 already states this explicitly for its own TD-32 and this review inherits
that same honesty: structural read, not a runtime measurement). Documentation only, `src` not
modified.

## 1. Database — single Postgres instance, no read replicas, real query risk unverified

`POSTGRES_ONLY=true` is enforced (`scripts/check_no_sqlite.py`). `docker-compose.prod.yml` defines no
read replicas and no connection-pooler (e.g. PgBouncer) was found. `TD-32` (`TECH_DEBT.md`) already
flags `platform_management.management_router`'s 9-package fan-out and
`platform_operations.dashboard_service`'s 7-service synchronous aggregation as un-load-tested fan-out
risk — restated, not re-derived. This audit adds one new observation: `deal_pipeline_engine.py`'s real
`DealStage`/`DealStageHistory` design (the most mature real pipeline engine, per `TD-47`) is exactly
the kind of write-heavy, audit-trail-per-transition table that benefits from partitioning at scale —
worth a specific index/partition review once real transaction volume exists, not before.

## 2. Runtime — eleven real frontend runtimes, entirely in-process JS state

`src/web/src/runtime/` has eleven real packages (`spatialRuntime`, `lifeEngine`, `businessNetwork`,
`digitalCitizen`, `assetRuntime`, `workflowRuntime`, `automation`, `cityVisualization`,
`intelligenceRuntime`, `interactionRuntime`, `commandRuntime`) — every one holds its state in plain
JS `Map`/array structures inside a single browser tab's memory, with no persistence layer and no
cross-tab/cross-window sync (confirmed earlier in this engagement: a City window opened via
`WindowFrame.tsx`'s iframe does not share this JS-realm state with its parent, `docs/CITY_DESKTOP.md`
§2, CG-6). This is fine for a single-user demo session; it does not scale to multiple concurrent
browser sessions seeing the same "live" state without a real backend sync layer, which does not exist
today for most of these eleven runtimes. `lifeEventEngine`'s event list is explicitly capped at 400
entries (`lifeEventEngine.ts:62`); other runtimes' registries (`spatialRegistry`'s `entities`/
`relationships` Maps, `businessInteractions`' 200-item cap) were only spot-checked, not all eleven
exhaustively confirmed to have a cap — worth a follow-up pass before assuming none will grow unbounded
in a long-running session.

## 3. Search — no real search/vector engine exists anywhere

Confirmed repeatedly across this engagement (CG-8, CQ-14, CQ-20): `platform_ai/memory/
memory_embeddings.py`'s `OpenAIEmbeddingProvider`/`LocalEmbeddingProvider` both call the same
deterministic SHA-256 `_hash_embed()` — there is no real vector database anywhere (pgvector/Qdrant/
Milvus/Weaviate are referenced only in aspirational comments). Any "semantic search" feature today is
not doing real similarity search. This is a real, load-bearing gap for the Knowledge Graph systems
(`TD-49`) specifically, since "semantic search" is one of their headline claimed capabilities.

## 4. Knowledge Graph — four real systems, unclear which one owns query load at scale

`TD-49` (`TECH_DEBT.md`) already documents the four-way knowledge-graph collision. From a scalability
angle specifically: none of the four systems' real storage backend was confirmed in this pass (in-memory
dict-store per `EnterpriseHubStore`-style patterns seen elsewhere in `applications/enterprise_hub/`, or
real Postgres tables — not verified for all four). If any of them is in-memory-only today, it inherits
the same single-process-state limitation as the frontend runtimes in §2.

## 5. Automation / Workflow — seven real engines, no shared queue

Per `TD-48`, seven real workflow-shaped systems exist, none sharing infrastructure. No real distributed
task queue exists anywhere (`platform_jobs/` is a generic cron scheduler disconnected from all seven;
the only "Kafka" in the repo is a mock `KafkaConnector` in `applications/enterprise_hub/integrations/
connectors/kafka.py`). At current scale this is not urgent — it becomes a real bottleneck the moment
any one of the seven engines needs to run work across more than one process/machine, which none of the
current deployment configs (`docker-compose.yml`: 2 services; `docker-compose.prod.yml`: 6 services, no
replicas) are set up to support.

## 6. AI Runtime — one real provider, rate-limit/backpressure not evaluated

Only `openrouter.py` is a real, wired AI provider (`aiohttp` POST to OpenRouter, model
`openai/gpt-5-mini`). Every other registered provider (`platform_ai/provider_manager.py`'s openai/
anthropic/google/local_llama/deepseek) is a `MockAIProvider`. This means the platform's entire real AI
surface currently funnels through one external HTTP dependency with no visible circuit-breaker/
rate-limit handling confirmed in this pass — a real single-point-of-failure/backpressure risk once AI
usage volume grows, not evaluated further here (would need reading `openrouter.py`'s error-handling
path in depth, out of scope for this pass).

## 7. Memory / CPU — City rendering has a real LOD concept, other runtimes don't

Enterprise City's real Graphics Engine (CG-2/CG-3) has a real performance-budget/LOD system
(`performanceMonitor.ts`, `layerSystem.ts`'s 8 layers, `CITY_SIMULATION.md` §3's fixed-ceiling
discipline) — this is a genuine scalability positive, deliberately designed to cap rendering cost
regardless of entity count. The eleven backend-adjacent runtimes (§2) have no equivalent budget
concept — nothing was found capping computation cost as entity count grows (e.g. `routingEngine`'s
real Dijkstra implementation recomputes per-call with a cache, but the cache itself has no eviction
policy confirmed in this pass).

## 8. Network — Socket.IO real-time sync confirmed dormant, not evaluated at scale

`Socket.IO` is a real dependency in `src/web`'s package list but was confirmed in earlier research
(CG-5/CG-6) to be dormant by default for City collaboration — not actively used for real-time
multi-user sync today. This audit did not re-verify that status or evaluate whether, if activated, the
current setup would need a pub/sub backplane (Redis adapter) to scale past a single process — flagged
as a "when this feature is turned on" concern, not a current bottleneck.

## Priority summary

| Finding | Bottleneck class | Urgency |
|---|---|---|
| No real vector/search engine (§3) | Feature-blocking, not scale-blocking yet | Medium — blocks a claimed capability, not current load |
| Seven disconnected workflow engines, no shared queue (§5) | Scale-blocking once multi-process execution is needed | Medium |
| Eleven frontend runtimes, no cross-session sync (§2) | Scale-blocking for real multi-user features | Medium-High, since multiple sprints (CQ-15 War Room, CQ-17 cross-org cooperation) already assume multi-user sync exists |
| Single AI provider, backpressure unverified (§6) | Availability risk | Low today (single provider is a deliberate choice per `AI_PROVIDER_LAYER.md`), worth revisiting at higher volume |
| DB fan-out load-testing (§1, `TD-32`) | Unmeasured | Medium — should precede any claim of production readiness |

## 9. Sprint CQ-30.6 addition — organization-count scaling estimate

Per-tenant scaling was not load-tested (consistent with this document's own stated methodology) — this
is an architectural estimate based on what's real vs. what's confirmed missing, not a benchmark.

| Org count | Verdict | Reasoning |
|---|---|---|
| 10 orgs | **Fine** | Single Postgres instance, no pooler, in-process queues — all comfortably sufficient; this is roughly today's real, exercised scale |
| 100 orgs | **Fine, watch DB fan-out** | `TD-32`'s un-load-tested `management_router`/`dashboard_service` fan-out becomes worth actually measuring around this scale, not before |
| 1,000 orgs | **Real risk** | No connection pooler confirmed (§1); real tenant-isolation gaps not yet triaged (`docs/SECURITY_REVIEW.md` §8's 79 findings) become a real cross-tenant risk surface at this scale, not just a theoretical one; three independent in-process task queues (`docs/ARCHITECTURE_REVIEW_V2.md` §1.1) would need consolidation or at least confirmed independent capacity |
| 10,000 orgs | **Not ready** | No read replicas, no distributed queue, no confirmed horizontal scaling path for any of the eleven-plus frontend runtimes (all single-process JS state per §2) — this scale requires real infrastructure work, not configuration changes |
| 100,000 orgs | **Not ready, and not the platform's current design target** | Would require re-architecting the frontend runtimes' single-process-state model entirely — a legitimate future direction, not a near-term Beta concern |

**Recommendation**: Beta should explicitly target the 10–100 org range and say so — this is not a
weakness to hide, it's an honest, defensible scope for a first Beta, consistent with `docs/ENTERPRISE_
V1_READINESS.md`'s (CQ-30) own "small/medium companies: ready" verdict.

## 10. AI Runtime / Task Queue triplication (new finding this review)

Three independent, real, in-process priority task queues exist: `platform_jobs/job_queue.py`,
`platform_workflow/task_queue.py`, `applications/enterprise_hub/ai_os/task_queue.py` — each a genuine,
non-trivial implementation (priority FIFO, dead-letter/retry/delay). None is distributed (no Redis/
Celery-backed broker confirmed for any of the three). This adds concrete detail to §5's "seven
disconnected workflow engines, no shared queue" finding: the queue layer itself is *also* triplicated,
one level below the workflow-engine layer.

## 11. Sprint CQ-32.2 addition — 100,000-org bottleneck detail

Re-asked against the brief's specific ladder (100/1,000/10,000/100,000 orgs): §9's verdicts stand
unchanged (100: fine; 1,000: real risk without a pooler + tenant-isolation triage; 10,000/100,000: not
ready). At 100,000 specifically, the concrete bottlenecks, ranked by which would fail first: (1) the
three in-process, non-distributed task queues (§10) — a single-process queue cannot serve 100,000
tenants' async work regardless of DB scaling; (2) the eleven-plus frontend runtimes' single-process JS
state (§2) — irrelevant at this scale since frontend state is per-browser-session, not a real
bottleneck at any org count, correcting this document's own framing: frontend runtime state scales
with concurrent *users*, not organizations, and was miscategorized as an org-count risk in §9's
original table; (3) absent read replicas/pooling (§1). **Correction**: item 2 should not be read as a
100,000-org blocker — it's a concurrent-session concern, orthogonal to org count.

## Related documents

`docs/TECH_DEBT.md` (TD-32, TD-48, TD-49), `docs/AI_PROVIDER_LAYER.md` (CG-8), `docs/CITY_SIMULATION.md`
(CG-4/CG-9, the real LOD/performance-budget precedent), `docs/CITY_DESKTOP.md` §2 (CG-6, the
cross-window state finding), `docs/DIGITAL_TWIN_STANDARDS.md` §4 (CQ-16, per-runtime EventBus
synchronization gap already flagged for multi-city), `docs/SECURITY_REVIEW.md` §8 (CQ-30.6, the
79-item tenant isolation scan relevant to §9's 1,000-org risk), `docs/ARCHITECTURE_REVIEW_V2.md`
(CQ-30.6 sibling), `docs/PERFORMANCE_REVIEW.md` §6 (CQ-32.2 sibling).
