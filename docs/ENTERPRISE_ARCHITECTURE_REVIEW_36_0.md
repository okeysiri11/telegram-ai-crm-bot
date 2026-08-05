# Enterprise Architecture Review Board — Post-Sprint 36.0 Review

**Role:** Enterprise Architecture Review Board (Lead Enterprise Software Architect). Documentation
only — `src` not modified, no existing module rewritten. This review evaluates the platform as it
stands after Sprint 36.0 (Enterprise Service Builder), and verifies the real work shipped in Sprints
34.2C–35.0 that this Board's own prior review (`docs/ARCHITECTURE_REVIEW_34_2C.md`) had flagged as
open or missing.

**Note on the record, stated plainly**: this Board's own prior review's Sync Engine finding
(§7.1, flagged Critical) has since been marked superseded by a real supersession banner added to that
document — Sprint 35.0's Foundation Audit confirmed `platform_state.sync_engine.SyncEngine`,
`VersionEngine`, `PlatformEventStore`, and `ConflictResolutionEngine` are real, built on the canonical
`PlatformEventBus`, exactly per this Board's own prior recommendation to sequence Sync Engine against
a shared versioning primitive rather than a bespoke one. This is the review process functioning as
intended, and this document verifies the result rather than re-deriving the original problem.

---

## 1. Missing enterprise components

| Component | Status | Priority | Why it matters |
|---|---|---|---|
| Voice Runtime | **Confirmed absent from the real Service Builder registry** — no `display_name: "Voice Runtime"` entry exists anywhere in `platform_service_builder/service.py`'s real seeded runtimes (`AI Runtime`, `Multi-Agent Runtime`, `Creative Factory`, `Enterprise City Runtime` are seeded; Voice is not) | High | The brief explicitly asks for Voice Runtime compatibility; today there is nothing to be compatible *with* — this needs a foundation-registration decision before any voice feature work proceeds, or it will be built ad hoc outside the canonical registry the platform has worked hard to establish |
| Project Memory | **Confirmed absent as a named concept** — real memory surfaces exist (`platform_memory/context_assembler.py`, `docs/architecture/PLATFORM_MEMORY.md`, `knowledge/memory/ENTERPRISE_MEMORY.md`) but none is scoped specifically to *per-project* memory (distinct from per-citizen, per-org, or platform-wide memory) | High | Without a real `Project` entity (`TD-51`, still open per the canonical registry) there is no real anchor for "memory about this specific project" to attach to — this is a compounding gap, not an isolated one |
| Postgres-backed Event Store (at scale) | Real today via JSONL (Sprint 35.0's own deliberate stabilization choice) | Medium | `FOUNDATION_AUDIT_35_0.md` §"Remaining technical debt" already lists this as its own item 6 — restated, not re-derived, because it directly affects item 2 below (scalability) |
| Multi-instance durable VersionEngine heads (HA) | Confirmed open (`FOUNDATION_AUDIT_35_0.md` item 5) | Medium | Required before any real horizontal scaling of the state layer — HA claims are not credible until this exists |
| Real third-party marketplace publish path | Confirmed foundation-only (`TD-63`, restated from `ARCHITECTURE_REVIEW_34_2C.md`) | Medium | Unchanged since the prior review — the Service Builder (Sprint 36.0) is the right foundation for this to eventually build on, but hasn't yet |

## 2. Hidden scalability bottlenecks

| Bottleneck | Priority | Why it matters |
|---|---|---|
| Event Store on JSONL, not Postgres | Medium | A deliberate, correct short-term choice (Sprint 35.0 removed an actual `sqlite3` policy violation and replaced it with JSONL, not a database) — but JSONL has a real ceiling for write-heavy event volume at the brief's stated scale (thousands of AI agents, hundreds of simultaneous conversations from the prior City review). Not urgent today; will become the binding constraint before Postgres-backed storage is built. |
| VersionEngine single-instance heads | High | Confirmed no HA path yet (§1) — this is a hidden bottleneck specifically because it doesn't show up under normal load, only under the multi-instance scaling this platform will eventually need |
| `platform_state` package's prior eager-import graph | **Resolved, Sprint 35.0** — now lazy `__getattr__` exports | N/A | Cited as a positive finding: this was a real, hidden startup-cost and circular-import risk, found and fixed before it became a production incident |
| Web menu catalog / `shellModuleRegistry` still hand-mirrored in TS, not bridged to the real Registry API | Medium | Every hand-mirrored copy is a place client and server can silently drift — restated from `FOUNDATION_AUDIT_35_0.md`'s own remaining-debt item 2 |

## 3. Potential circular dependencies

The real Foundation Audit (Sprint 35.0) already found and fixed the one concrete circular-import risk
this Board would otherwise have flagged (`platform_state`'s eager `__init__` graph → lazy exports).
This Board's own independent check this pass did not find a new circular-dependency candidate beyond
what `docs/TECH_DEBT.md` `TD-24`'s 29 `reverse_layer_dependency` warnings already track — restated, not
re-derived.

- **Priority:** Low (no new finding); Medium for `TD-24`'s existing warnings, unchanged.

## 4. Event-driven architecture improvements

The canonical `PlatformEventBus` is now explicitly the **only** sanctioned cross-module communication
path (`platform_architecture/canonical_services.py`'s real `policy: "All cross-module communication
MUST publish/subscribe via PlatformEventBus"`) — this is a strong, explicit, machine-readable policy
statement, a genuine governance improvement over a merely-documented convention.

- **Remaining risk:** `TD-20`'s six-plus allowlisted legacy `EventBus` classes still exist as
  explicitly-allowlisted adapters, not deleted — correct per Sprint 35.0's own "explicitly not done
  (risky)" list, but each allowlisted bus is a real exception to the new policy that should shrink over
  time, not persist indefinitely.
- **Priority:** Medium. **Why it matters:** a strict policy with permanent, growing exceptions is
  weaker than the policy text implies — worth a scheduled (not urgent) cutover cadence, same
  recommendation as the deal/workflow adapter cutover.

## 5. DDD boundary recommendations

Restated from `docs/DDD_REVIEW.md` (this Board's own prior finding): no real Aggregate-root pattern
exists for the Deal cluster. **New this pass**: the real Service Builder's own registry entry shape
(lifecycle/registry/versions/dependencies/loader/sandbox/health/permissions/audit, per
`docs/SPRINT_36_0_RESULT.md`) is itself a genuinely well-formed aggregate-adjacent pattern — every
registered service has one lifecycle owner. This is worth generalizing: the Service Builder's own
internal shape is a better real DDD template than anything found in the Deal cluster, and could be the
pattern a future `TD-14` (aggregate-root retrofit) work item follows.

- **Priority:** Medium. **Why it matters:** the platform now has a real, proven-good internal example
  of the pattern this Board has recommended since CQ-32.2 — using it as the template lowers the risk of
  inventing a new, untested pattern for the Deal cluster specifically.

## 6. Microservice decomposition opportunities

This Board's position, restated and reaffirmed after seeing Sprint 36.0's work: **do not decompose into
microservices yet.** The real canonical-services consolidation (Sprints 32.2–36.0) has just achieved
clean, declared, single-owner boundaries within a monolith — that is the correct prerequisite for a
future microservices decomposition, not a reason to skip straight there. The Service Builder's own
registry (lifecycle, health, permissions, audit per service) is, notably, exactly the shape of metadata
a future service-per-process deployment would need — meaning **if** microservices are pursued later,
this Board recommends the Service Builder's registry become the source of truth for that decomposition,
not a separate exercise.

- **Priority:** Low (not recommended now). **Why it matters:** premature decomposition before boundaries
  are proven stable in production is a well-documented failure mode this Board has warned against since
  the CQ-32.2/34.2C reviews — nothing in Sprint 36.0 changes that judgment, though it does improve the
  quality of the eventual decomposition's starting material.

## 7. Security review

Real, substantial, and improving: Security Center (Sprint 32.4) progressively wiring in (`TD-66`),
real Prompt Firewall (Sprint 30.9), real secret-policy hardening (`TD-65`, Sprint 32.3). **New this
pass**: no security-relevant regression was found in Sprint 36.0's Service Builder — real permissions
and audit are first-class fields on every registered service (`docs/SPRINT_36_0_RESULT.md`'s own
delivered list: "...health, permissions, audit").

- **Priority:** Low (no new critical finding); Medium for `TD-66`'s continuing progressive rollout,
  unchanged from the prior review.

## 8. Zero Trust improvements

**No dedicated Zero Trust architecture exists yet** — confirmed by direct search; the real security
posture (Identity Core, RBAC, Security Center, tenant isolation) is a strong, real *perimeter-and-role*
model, which is necessary but not sufficient for a formal Zero Trust posture (which additionally
requires continuous verification per-request, not just per-session, and explicit least-privilege
service-to-service authentication rather than implicit in-process trust).

- **Recommendation:** do not build a full Zero Trust architecture now — the real, current model is
  appropriate for the platform's current single-process-per-tenant deployment shape. Revisit
  specifically **if and when** microservice decomposition (§6) is pursued, since that is the point at
  which service-to-service trust actually becomes a distinct, real concern distinct from user-to-service
  trust.
- **Priority:** Low now, High if/when §6 is ever pursued — explicitly sequenced, not simultaneous.

## 9. Database optimization

Restated from `docs/ARCHITECTURE_REVIEW_34_2C.md` §6/§10: no confirmed table partitioning/archiving
strategy for canonical Deal tables ahead of "millions of records." **Updated this pass**: the real
Service Builder adds new ORM tables (`i2c345678901` migration) — worth confirming these follow the
same indexing discipline as the canonical Deal tables from the start, since a new subsystem is a
cheaper place to get this right than a retrofit.

- **Priority:** High (Deal table partitioning, carried forward), Medium (Service Builder table review,
  new and cheap to check now while the table is young).

## 10. API consistency review

Real dual-prefix pattern confirmed for Service Builder (`REST /api/service-builder` + management
dual-prefix, per `SPRINT_36_0_RESULT.md`) — consistent with the platform's established (if imperfect)
convention of a public `/api/*` and an authenticated `/management/*` surface. No new inconsistency
found this pass beyond `docs/API_REVIEW.md`'s (CQ-32.2) already-tracked findings (uneven `limit`
defaults, missing Knowledge Graph prefixes in `API_MAP.md`).

- **Priority:** Medium, unchanged.

## 11. Naming consistency

**Positive finding, explicit governance improvement**: `docs/SPRINT_36_0_RESULT.md` states the Service
Builder was deliberately built as `platform_service_builder/`, **not** `platform_core/` — "forbidden by
platform standards." This is a real, enforced naming discipline this Board has recommended since
CQ-32.2 (`TD-62`'s "no `platform_core` package, Core is intentionally composed" finding) — confirmation
that the platform's own standards now actively prevent the exact naming mistake this Board warned
about, not just document it after the fact.

- **Priority:** N/A (positive finding, no action needed).

## 12. Versioning strategy

Real `VersionEngine` + `VersionMixin` (Sprint 34.2D) is the canonical versioning primitive — directly
resolving `TD-54`'s "no generic history/versioning mixin" finding this Board has tracked since CQ-19.
**Remaining gap, explicitly acknowledged by the platform's own audit**: `VersionMixin` retrofit onto
existing SQLAlchemy models remains open (`FOUNDATION_AUDIT_35_0.md`'s remaining-debt item 1) — the
primitive exists, adoption is partial.

- **Priority:** Medium. **Why it matters:** every model not yet retrofitted continues to reinvent its
  own ad hoc history tracking (e.g., `DealStageHistory`) — the fix is available and proven, just not
  yet applied everywhere.

## 13. Plugin architecture improvements

The real Platform Registry (`modules/`/`features/`/`visibility/`, Sprint 34.2B) plus the new Service
Builder (Sprint 36.0, real lifecycle/loader/sandbox/health/permissions) together are a genuinely strong
plugin-architecture foundation — the `sandbox` field specifically is notable, since it implies real
isolation-boundary thinking for third-party-loaded code, not just a registry entry.

- **Priority:** Medium — the foundation is real and good; the gap (§1) is that no real third-party
  plugin has exercised this path yet, so its actual isolation guarantees remain unproven under real
  adversarial conditions.

## 14–19. Future runtime compatibility — per system

| Runtime | Status | Priority | Why it matters |
|---|---|---|---|
| **14. AI Runtime** | **Seeded** in the real Service Builder registry (`display_name: "AI Runtime"`) | Medium | A real foundation entry exists; whether it's wired to the actual canonical `platform_jobs` lane=`ai` execution path (per `canonical_services.py`) or is a registry-only placeholder was not confirmed this pass — worth a direct trace before assuming full compatibility |
| **15. Multi-Agent Runtime** | **Seeded** (`display_name: "Multi-Agent Runtime"`) | Medium | Same caveat as above — real registration confirmed, real execution wiring not independently verified this pass |
| **16. Enterprise City Runtime** | **Seeded** (`display_name: "Enterprise City Runtime"`) | Medium | Same caveat; also worth cross-checking against this Board's own separate Enterprise City redesign work (`docs/ENTERPRISE_CITY_2D_VISION.md` and companions) to ensure the Service Builder's registration and the City's own real runtime consolidation (`cityVisualization`/`orchestrator`/`kernel`) are describing the same thing, not two independent claims to the same name |
| **17. Project Memory** | **Not found anywhere** — genuinely absent | High | No real anchor exists for this specific memory scope; flagged in §1 as a missing component, restated here for the brief's specific compatibility framing |
| **18. Voice Runtime** | **Not found anywhere** — genuinely absent | High | Same as above; flagged in §1 |
| **19. Workflow Runtime** | **Real and canonical** — `platform_workflow/` per both `canonical_services.py` and `FOUNDATION_AUDIT_35_0.md`'s canonical map | Low | Already the platform's most mature canonical decision (this Board's own CQ-18/19 recommendation, followed exactly); legacy adapters remain per policy, not a gap |

## Non-goals

- No implementation of any recommendation — evidence, analysis, and priority only.
- No re-litigation of findings this pass independently confirmed are already resolved (Sync Engine,
  `sqlite3` violation, eager-import cycle) — cited as resolved, not re-argued.

## Related documents

`docs/ARCHITECTURE_REVIEW_34_2C.md` (this Board's prior review, now partially superseded per its own
banner), `docs/FOUNDATION_AUDIT_35_0.md`/`docs/SPRINT_36_0_RESULT.md` (real, the primary evidence this
review verifies), `docs/CANONICAL_SERVICES.md`/`platform_architecture/canonical_services.py` (real,
machine-readable canonical registry), `docs/TECH_DEBT.md` (canonical debt registry),
`docs/ARCHITECTURE_BACKLOG_37.md` (this review's companion, the ordered pre-Sprint-37 backlog).
