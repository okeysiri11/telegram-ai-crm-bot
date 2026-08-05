# Sprint CQ-32.2 — AI Runtime & AI Production Studio Review

**Scope:** agent lifecycle, prompt execution, memory, knowledge access, RAG boundaries, provider
abstraction, queue isolation, retry logic, human approval (§6) + Production Studio's workflow engine,
generation queues, media pipeline, prompt/template libraries, brand kit, provider abstraction, cost
tracking, approval workflow (§12). Documentation only, `src` not modified.

## Part A — AI Runtime

### 1. Agent lifecycle — real, but split across three registries

Restated from CG-8: `platform_agents.registry`, `platform_orchestrator.agent_registry`, and
`platform_ai_os`'s "Agent Registry 2.0" are three disconnected registries. **New this review**: the
frontend adds a fourth layer, the real `orchestrator`/`kernel` runtime pair (`TD-59`/`TD-60`), which
tracks frontend-visible agent-adjacent runtime health but is not confirmed to share identity with any
of the three backend registries.

- **Priority:** High. **Effort:** L (requires picking one canonical registry and migrating consumers).

### 2. Prompt execution — real, now security-hardened (Sprint 30.9)

Real `openrouter.py` is the one wired provider; real Prompt Firewall (`docs/AI_SECURITY.md`, corrected
this sprint per `docs/SECURITY_ARCHITECTURE_REVIEW.md` §1) sits on the invoke path. This is a genuine
positive — prompt execution is real, and now real-and-guarded, not just real.

### 3. Memory — four fragmented surfaces, fake embeddings, unchanged

Restated from CG-8/CQ-14, not re-derived: `platform_memory/` vs. `platform_ai/memory/` vs.
`ecosystem/assistant/global_memory/` vs. `platform_enterprise_knowledge_graph/memory/`. The real
`OpenAIEmbeddingProvider`/`LocalEmbeddingProvider` both call the same deterministic SHA-256
`_hash_embed()` — there is no real vector similarity search anywhere, confirmed still true.

### 4. Knowledge access / RAG boundaries — the review's most important open question

No real vector database exists (§3), which means any "RAG" (retrieval-augmented generation) claim
anywhere in the platform's documentation is not backed by real semantic retrieval today — retrieval, if
it happens at all, is keyword/structured-query-based, not embedding-similarity-based. **Combined with
`docs/SECURITY_ARCHITECTURE_REVIEW.md` §4's flagged Knowledge Base tenant-isolation question**, this is
the review's highest-priority AI Runtime item: until real RAG exists, the tenant-isolation question is
somewhat moot (there's no real cross-tenant *semantic* retrieval to leak through), but the moment real
embeddings are built, tenant-scoping the vector index must be designed in from the start, not retrofitted.

- **Recommendation:** when real vector search is eventually built (already flagged as a future item
  across multiple prior reviews), tenant-scoping must be part of the initial design, not a follow-up —
  called out explicitly here so it isn't forgotten by the time that work starts.
- **Priority:** Medium now (nothing to leak yet), Critical at the moment real RAG work begins.

### 5. Provider abstraction — real interface, entirely mock-backed except one

`platform_ai/provider_manager.py`'s `ProviderManager` real class registers openai/anthropic/google/
local_llama/deepseek — all `MockAIProvider` except the separate, real `openrouter.py` path. No
`abstractmethod`/ABC pattern was found enforcing a consistent provider interface — the abstraction
exists as a registry pattern, not a strictly-typed contract.

- **Priority:** Low for Beta (one real provider is a legitimate, deliberate choice per prior reviews);
  Medium for future multi-provider work — an explicit ABC/Protocol would make adding a second real
  provider safer.

### 6. Queue isolation, retry logic — real, per-queue, not per-tenant

Three real in-process priority queues exist (`TD` context from CQ-30.6/30.8): `platform_jobs/job_
queue.py` (DLQ), `platform_workflow/task_queue.py` (real `requeue_for_retry()`, real `retry_count`
tracking). **New this review**: no evidence of per-tenant queue isolation was found in either — a
noisy or abusive tenant's AI/workflow tasks would share the same priority queue as every other
tenant's, with only task-level `priority` as a fairness mechanism, not tenant-level quotas.

- **Priority:** Medium — not urgent at Beta's recommended 10–100 org scale (`docs/SCALABILITY_
  REVIEW.md` §9), becomes real at 1,000+ orgs.

### 7. Timeout handling — not confirmed by name

Neither `job_queue.py` nor `task_queue.py` was confirmed this pass to have an explicit per-task
timeout mechanism (distinct from retry/delay, which are confirmed real). Flagged as unverified, not
asserted absent — a direct code read of both files' full content (not just the header/grep hits sampled
across this engagement) would resolve this.

- **Priority:** Medium (verify). **Effort:** S.

### 8. Human approval — real, and reused consistently

The real Approval Center (three gates: `platform_learning.accept/reject`, `platform_workflow` human-
task pause, `EBN_PARTNERSHIP_SYSTEM.md` dual sign-off — `docs/EXECUTIVE_DECISION_CENTER.md`, CQ-15) is
consistently cited as the reuse target across this engagement's AI-adjacent designs. This is a genuine
architecture strength: the platform has one real human-approval composition, not several competing
ones — the opposite pattern from Workflow/Marketplace/Knowledge Base.

## Part B — AI Production Studio

| Item | Real status | Evidence |
|---|---|---|
| Workflow engine | Real 7-stage pipeline (`draft→review→approval→generation→render→publish→archive`), no real execution behind `generation` | `productionCatalog.ts`, `TD-45` |
| Generation queues | **Not confirmed to exist** — no real generation backend means no real generation queue was found either; the three real task queues (Part A §6) are generic, not Production-Studio-specific | Not found |
| Media pipeline | Real storage layer (`services/storage`) could back this once generation is real; no confirmed pipeline connecting generation output to storage today | Inferred, not directly confirmed |
| Prompt Library | Real `prompt` studio, correctly scoped separately from AI Builder Studio's library | `docs/AI_PRODUCTION_CENTER_BIBLE.md` |
| Template Library | Real `templates` studio (Template Center) | `productionCatalog.ts` |
| Brand Kit | Real `brand` studio (Brand Studio) + `assets` (Asset Library) | `productionCatalog.ts` |
| Provider abstraction | Same as Part A §5 — no Production-Studio-specific provider abstraction found; would inherit the general one once built | Inferred |
| **Cost tracking** | **Real** — `platform_ai/cost_tracker.py`'s `cost_tracker`, real `response.cost_usd`, real `cost_tracker.summary()`, confirmed by direct test read (`tests/test_ai_platform.py`) | New finding this review, corrects any assumption of absence |
| Approval workflow | Real — the `approval` pipeline stage composes the same real Approval Center as Part A §8 | `productionCatalog.ts`'s `PIPELINE_STAGES` |

**Correction to the record**: cost tracking is real, not absent — this review found it directly where
prior reviews hadn't looked (`platform_ai/cost_tracker.py`). This meaningfully changes the Production
Studio readiness picture: once real generation providers are wired, cost accounting is *already*
there waiting for them, not a gap that would block launch of real generation.

## Non-goals

- No agent-registry consolidation implemented.
- No real vector/RAG implementation designed in depth — flagged as future work with an explicit
  tenant-isolation-by-design requirement (§4).
- No generation backend implemented.

## Related documents

`docs/TECH_DEBT.md` (TD-45, TD-46, TD-59, TD-60), `docs/SECURITY_ARCHITECTURE_REVIEW.md` (CQ-32.2
sibling, §1/§4), `docs/AI_SECURITY.md` (real, Sprint 30.9), `docs/PRODUCTION_STUDIO_UX.md` (CQ-30.1),
`docs/EXECUTIVE_DECISION_CENTER.md` (CQ-15, real Approval Center), `docs/PLATFORM_CORE_REVIEW.md`
(CQ-32.2 sibling, AI Runtime's Core-placement verdict).
