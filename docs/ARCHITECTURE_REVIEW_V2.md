# Sprint CQ-30.6 — Independent Architecture Review

**Mode:** independent CTO/Principal Architect review, performed *while* Cursor implements Sprint 30.6
in parallel — not a review of Sprint 30.6's output (not yet finished), a fresh, evidence-based read of
the platform as it stands now. Documentation only, `src` not modified, no implementation.

## 1. Overall architecture

### 1.1 Architectural smells (new evidence this review)

- **Three independent, real, in-process priority task queues**, none sharing infrastructure:
  `platform_jobs/job_queue.py` ("priority FIFO with dead letter queue"), `platform_workflow/
  task_queue.py` ("priority FIFO with retry, delay, and scheduling"), and `applications/enterprise_hub/
  ai_os/task_queue.py`. Both sampled implementations are genuinely sophisticated (`asyncio`+`heapq`,
  DLQ, retry/delay) — this is not thin duplication, it's three real engineering investments in the same
  problem. New finding this review; not previously catalogued.
- **Enterprise Knowledge Graph's `ENTITY_TYPES`/`RELATION_TYPES` are Python tuples** (`platform_
  enterprise_knowledge_graph/models.py:5`) — compile-time constants, not a runtime-registrable
  taxonomy. Directly relevant to this review's §6 extensibility question: adding a new entity/relation
  kind today requires a code change and redeploy, not a config change or admin action.

### 1.2 Hidden coupling

The real `orchestrator` (`EnterpriseOrchestrator.ts`, Sprint 29.8) registers ten of the eleven base
frontend runtimes in its `RuntimeId` union and tracks their health via a real dependency graph
(`RuntimeDependencyGraph.ts`, "Read-only topology"). `cityVisualization` (Sprint 29.5) independently
derives its own view of the same eleven runtimes' state with no confirmed relationship to `orchestrator`.
This is coupling that isn't visible from either file in isolation — only visible by reading both and
noticing they silently cover the same ground. Restated with precision from `docs/TECH_DEBT.md` TD-59,
not re-derived, but worth stating plainly here as this review's own top hidden-coupling finding.

### 1.3 Wrong dependencies / layer violations

`docs/TECH_DEBT.md` TD-19 (`database/__init__.py` importing `database_legacy`) remains the clearest
confirmed layer violation — the modern package depends on the legacy layer it's meant to be isolated
from. Not re-verified this pass (no new evidence gathered); carried forward as still-open per the last
confirmed check (Sprint CQ-30).

### 1.4 Circular references

No new circular-reference evidence was gathered this review beyond what `TD-36` already documents
(47 legacy `pg_*` engine cycles, contained within the compatibility layer) and the real, reassuring
counter-finding already on record: `docs/architecture_baseline/DEPENDENCY_GRAPH.md` reports **0 strict
cycles in governed layers** — i.e., the cycles that exist are confined to code the platform has already
fenced off as legacy, not the actively-developed core. This distinction matters for an investor-facing
read: the platform does not have an active circular-dependency problem in its governed layers.

### 1.5 Over-engineering

The three-queue situation (§1.1) and the three-layer runtime-integration stack (§1.2) are this
platform's clearest over-engineering instances — not because any single piece is poorly built, but
because effort was spent solving the same problem three times independently rather than once. `TD-18`
(`container.py`'s unused DI scaffold) is a smaller instance of the same shape: real, competent
engineering that never got adopted.

### 1.6 Under-engineering

Three real, concrete gaps: no generic `Project` entity (`TD-51`) despite the ontology already naming
it; no generic history/versioning pattern (`TD-54`); Client and Dealer roles have no real platform-wide
UX or data model (`docs/ROLE_NAVIGATION.md` §3, CQ-30.1). Each is a case of the platform's real
capability lagging behind what its own documentation/ontology already assumes exists.

## 5. Enterprise City — is it becoming a God Object?

**Direct answer: not the City module itself, but its dependency graph is the actual risk.**
`src/web/src/enterprise-city/` is 34 real `.ts`/`.tsx` files — a modest size, not evidence of bloat on
its own. The real risk is architectural, not volumetric: `cityVisualizationRuntime.ts` (Sprint 29.5)
composes all eight other real runtimes, and the newer `orchestrator` (Sprint 29.8) independently
composes ten. Neither the City module's file count nor its own internal complexity is the concern —
it's that **two different real systems have each taken on the responsibility of being "the thing that
knows about every runtime,"** and City-adjacent code (`cityVisualization`) is one of the two.

- **Could City become a bottleneck?** Only via `cityVisualization`'s fan-in role, not via City's own
  rendering code (which has real, deliberate LOD/performance-budget discipline, a genuine strength —
  see `docs/SCALABILITY_REVIEW.md` §7).
- **Could City become a God Object?** `cityVisualization` is already halfway there by design intent
  ("single source of truth for future 2D/3D City clients") — the real risk is it and `orchestrator`
  both claiming that role simultaneously, not City accreting unrelated responsibilities itself.
- **Duplicated navigation layer?** No — confirmed this engagement's CQ-30.1 review that `src/web/src/
  navigation/`'s shell components correctly consume `src/web/navigation/`'s real managers; City's own
  navigation (`cityNavigation.ts`, now real per Sprint 30.4 per this platform's own concurrent
  implementation) is a distinct, legitimately separate concern (spatial pan/zoom/focus, not app
  routing).
- **Should districts become plugins?** Not recommended at this stage — `docs/CROSS_VERTICAL_
  EXTENSIONS.md` (CQ-19) already designed a real, lower-risk extension mechanism (the `module`
  discriminator pattern already proven on `Deal`/`CalendarEvent`) that achieves the same
  per-vertical-extension goal without a plugin runtime's added complexity.
- **Should rendering be isolated?** It effectively already is — the real Graphics Engine (CG-2/CG-3) is
  a distinct layer from the data/coordination runtimes, which is the correct separation. No change
  recommended.

## 6. Knowledge Graph — future extensibility

The recommended-canonical Sprint 24.2 system (`platform_enterprise_knowledge_graph`,
`docs/ENTERPRISE_ONTOLOGY.md`) has real, well-designed `ENTITY_TYPES`/`RELATION_TYPES` — but as
confirmed this review (§1.1), both are Python tuples, not a database-backed or config-driven registry.
**This is the one concrete extensibility gap this review found**: adding a new entity kind for a new
vertical (e.g., a future "Healthcare" or "Manufacturing" vertical needing its own entity types, per
`docs/ENTERPRISE_SCENARIO_LIBRARY.md`'s already-identified thin verticals, CQ-17) requires editing this
file and redeploying, not a runtime action. For a platform explicitly designed for many verticals, this
is worth a deliberate decision: keep it code-defined (simpler, safer, requires a release per new
vertical) or make it a real registry (more flexible, more surface area to secure/validate). This review
recommends **keeping it code-defined for Beta** — the real risk of a dynamically-registrable ontology
(data-quality/governance risk) outweighs the convenience for a Beta-stage platform with a small number
of verticals.

## Non-goals

- No implementation of any recommendation in this document — evidence and analysis only.
- No re-litigation of the six-way deal or seven-way workflow collisions — unchanged since `docs/TECH_
  DEBT.md` TD-47/TD-48, not re-derived this pass.

## Related documents

`docs/TECH_DEBT.md` (TD-18, TD-19, TD-36, TD-59), `docs/RUNTIME_CONSISTENCY.md`/`docs/DOMAIN_
BOUNDARIES.md` (CQ-30), `docs/CROSS_VERTICAL_EXTENSIONS.md` (CQ-19), `docs/ENTERPRISE_ONTOLOGY.md`
(CQ-20), `docs/API_REVIEW.md`/`docs/SCALABILITY_REVIEW.md`/`docs/SECURITY_REVIEW.md` (CQ-30.6
siblings).
