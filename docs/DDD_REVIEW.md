# Sprint CQ-32.2 — Domain-Driven Design Review

**Scope:** Entities, Aggregates, Repositories, Services, Application Layer, Infrastructure Layer,
Bounded Contexts, Domain Events. Documentation only, `src` not modified.

## Headline finding: the platform's one clean DDD pattern lives in its most orphaned tree

`src/events/__init__.py` contains a genuinely well-formed DDD `DomainEvent` base class with real,
specific domain events: `LeadCreated`, `LeadAssigned`, `LeadClosed`, `ClientCreated`,
`ManagerAssigned`, `PhotoUploaded` — each a real dataclass subclassing `DomainEvent`, dispatched
through a real `EventHandler`/`dispatch()` mechanism. This is textbook DDD: named, past-tense,
business-meaningful events, not generic CRUD notifications.

**The irony**: `src/events` is part of the `src/domains`/`src/platform`/`src/verticals`/`src/events`
Python tree this engagement's CQ-30.6 review found is largely orphaned (`TD-55` measured `src/
domains` specifically at 141 files with near-zero external usage; `src/events` was not individually
re-measured this pass, but sits in the same tree). **The platform's cleanest domain-modeling code may
be its least-used code.** This is worth a direct product decision, not just a debt entry: either this
DDD pattern should be the template for future domain-event work platform-wide (in which case it should
be pulled out of the orphaned tree and given real consumers), or it's a legitimately abandoned earlier
direction (in which case it's fine as historical reference, not a pattern to propagate).

- **Priority:** High (decision), Medium (execution once decided).
- **Effort:** S (decide) / L (if the decision is "adopt platform-wide").

## Per-concept mapping (brief's eight)

| DDD concept | Real platform equivalent | Assessment |
|---|---|---|
| Entities | Real SQLAlchemy models (`database/models/*.py`) — `Deal`, `Task`, `Company`, etc. | Real, but ORM-model-as-entity, not a distinct domain-model layer — standard for this style of Python backend, not a smell in itself |
| Aggregates | **No real aggregate-root pattern found** — no code found grouping related entities under one consistency boundary with a single real write path | Genuine gap — e.g., `Deal`+`DealStage`+`DealTask`+`DealStageHistory` are four related tables (`TD-47`) with no enforced aggregate boundary; any of the six real deal systems could write to any of them independently |
| Repositories | Real, extensive — `repositories/` (~100+ modules, per `CLAUDE.md`) | Real and genuinely repository-shaped (one file per entity, query methods) — the strongest real DDD-adjacent layer in the codebase |
| Services | Real, extensive — `services/` (~380+ modules) | Real, though per `CLAUDE.md`'s own description this is "business logic, no direct HTTP exposure" — functionally an application-service layer even without DDD terminology |
| Application Layer | De facto real — `services/` + route handlers | Not named as such, but the separation exists functionally |
| Infrastructure Layer | De facto real — `repositories/`, `database/`, `platform_configuration/` | Same — functional separation without DDD naming |
| Bounded Contexts | **Not formally defined anywhere** — the ~76 `platform_*` + 17 `applications/*` packages are the closest real proxy, but none is explicitly documented as a bounded context with its own ubiquitous language | The six-way deal collision (`TD-47`) and seven-way workflow collision (`TD-48`) are arguably evidence of **missing** bounded-context discipline — each duplicate implementation may reflect a different team's context without a shared model |
| Domain Events | Real in one place (`src/events`, above), not used platform-wide | The real `enterpriseEventBus`/`PlatformEventBus` publish generic event payloads, not the named, business-meaningful event classes DDD calls for |

## The real gap this review considers most consequential: no aggregate boundary on the Deal cluster

`Deal`/`DealStage`/`DealTask`/`DealStageHistory` (the recommended-canonical system per `TD-47`) has no
enforced single write path — any of the six real deal systems, or any future one, could write to these
tables directly. A real aggregate root would centralize writes through one object that enforces
invariants (e.g., "a stage transition must produce a history row"). Whether `DealStageHistory` rows are
*always* created alongside every real stage transition, or only when the code path remembers to, was
not verified this pass — this is exactly the kind of correctness question an aggregate boundary exists
to make structurally impossible to get wrong, rather than relying on every caller remembering.

- **Priority:** High. **Effort:** M (introduce a real `DealAggregate` facade over the existing tables
  — additive, not a rewrite of the tables themselves).

## Recommendation: adopt DDD vocabulary incrementally, starting with Bounded Contexts

Given the platform's real, demonstrated pattern of independently-built duplicate systems (deal
pipelines, workflow engines, knowledge graphs — `TD-47`/`TD-48`/`TD-49`), the single highest-leverage
DDD practice to adopt is **explicit bounded-context documentation** — a short doc per major domain
(Sales, Operations, AI, Territory) naming its own ubiquitous language and its one canonical
implementation, extending `docs/CANONICAL_PROCESS_MODEL.md`'s (CQ-19) already-established
vocabulary-reconciliation work with an explicit context boundary, not just a term dictionary.

## Non-goals

- No aggregate-root code implemented — the `DealAggregate` recommendation above is a proposal, not a
  build in this documentation-only pass.
- No repository/service layer restructuring recommended — both are already real and functionally
  sound, just not DDD-labeled.

## Related documents

`src/events/__init__.py` (real, the one clean DDD pattern found), `docs/TECH_DEBT.md` (TD-47, TD-48,
TD-55), `docs/CANONICAL_PROCESS_MODEL.md`/`docs/ENTITY_RECONCILIATION.md` (CQ-19, the vocabulary
reconciliation this review's bounded-context recommendation extends), `docs/PLATFORM_CORE_REVIEW.md`
(CQ-32.2 sibling).
