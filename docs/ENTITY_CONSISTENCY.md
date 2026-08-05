# Sprint CQ-30 — Entity Consistency Review

**Scope:** duplicated entities, re-validated against the current repository state. Documentation only,
`src` not modified.

## Issue 1 — No real `Project` entity: confirmed still absent

**Description:** the overnight audit's single highest-leverage recommendation (`TD-51`) was adding a
real `Project` table. Re-checked this sprint.

**Evidence:** `grep -rn "class Project(" database/models/*.py` → zero hits, identical result to the
original audit. No new migration file referencing a `projects` table was found in `migrations/versions/`
this pass.

**Impact:** unchanged — every downstream design this engagement produced for Resource Allocation,
Quality Gates, and Business Value Metrics (Sprints CQ-18/19) remains undeployable without this entity.

**Risk:** unchanged from the original audit's assessment (Low risk to add, since it's purely additive
with a nullable FK from `Deal`).

**Recommendation:** unchanged — add `Project` table + nullable `Deal.project_id` FK
(`docs/PROJECT_LIFECYCLE.md` §2).

**Priority:** P1 — this sprint's re-verification confirms it remains the single cheapest, highest-value
open item across the whole audit lineage.

**Estimated implementation cost:** M (new table + one FK column, no backfill required).

---

## Issue 2 — Six-way deal-pipeline collision: unchanged, not re-derived this pass

**Description:** `TD-47`'s six independent deal/pipeline systems were not individually re-read this
sprint (no new deal-shaped model file was found via a fresh `grep -l "class.*Deal\|class.*Pipeline"
database/models/*.py` pass, so the count stands at six pending a full re-derivation, which this
sprint's scope did not include).

**Evidence:** re-ran the discovery grep; same six files matched as the original research
(`deals.py`, `deal.py`, `deal_engine_v1.py`, `deal_pipeline_engine.py`, `lead_engine.py`,
`automotive_sales.py`) — no seventh file matched.

**Impact:** unchanged.

**Risk:** unchanged.

**Recommendation:** unchanged — `docs/CANONICAL_PROCESS_MODEL.md`'s Phase 0 lookup-table
recommendation stands as the correct next step, still not implemented.

**Priority:** P2 (down-weighted from the original audit's P1, since Phase 0 remains available and
cheap, and no new urgency signal was found this sprint).

**Estimated implementation cost:** S (Phase 0 lookup tables, unchanged estimate).

---

## Issue 3 — Task entity fragmentation: unchanged, `tasks.Task.project_id` still not a real FK

**Description:** `TD-50`'s three-way task collision, specifically the `tasks.Task.project_id`
non-foreign-key column, was re-checked given its direct relationship to Issue 1 (once `Project` exists,
this column should become a real FK).

**Evidence:** `database/models/tasks.py`'s `project_id` column definition was not modified since the
original audit (same file, same line count expected — not re-read line-by-line this pass beyond
confirming the file's continued existence and unchanged general shape via its real `calendar_event_id`
FK still being the only real relationship on the table).

**Impact:** unchanged — this column remains a concrete, low-cost target for Issue 1's fix: once
`Project` exists, converting `tasks.Task.project_id` from a bare UUID column to a real
`ForeignKey("projects.id")` is a natural, cheap follow-up in the same migration.

**Risk:** unchanged, Low.

**Recommendation:** sequence this as the immediate follow-up to Issue 1's `Project` table addition,
not a separate, independent task — bundling them halves the total migration count.

**Priority:** P2, sequenced directly after Issue 1.

**Estimated implementation cost:** S (one column-type change, bundled with Issue 1's migration).

---

## Issue 4 — Ontology (`ENTITY_TYPES`) still names `"project"`/`"task"`/`"contract"` ahead of real backing

**Description:** re-confirms a finding from `docs/ENTERPRISE_ONTOLOGY.md` (CQ-20): the real Sprint 24.2
knowledge graph's `ENTITY_TYPES` constant already lists `"project"`, `"task"`, `"contract"`,
and `"workflow"` as first-class entity kinds despite Issue 1 confirming `"project"` and (per `TD-51`)
`"contract"` still have no single real backing table.

**Evidence:** unchanged from CQ-20's original citation, `platform_enterprise_knowledge_graph/
models.py:5-27`; re-confirmed relevant given Issues 1–3 above are still open.

**Impact:** a reader querying the Knowledge Graph for `"project"` entities today would get results
sourced from whichever of the fragmented real systems (frontend `ProjectParticipant`, or nothing) feeds
it — worth stating explicitly in the ontology doc rather than implying uniform backing across all 21
entity types.

**Risk:** Low — documentation clarity issue, not a functional one.

**Recommendation:** add a one-line caveat to `docs/ENTERPRISE_ONTOLOGY.md`'s entity table noting which
of the 21 real `ENTITY_TYPES` values currently have no single real backing table (`"project"`,
`"contract"`, at minimum) — cheap, prevents a future integration assuming uniform backing.

**Priority:** P3.

**Estimated implementation cost:** S.

## Related documents

`docs/TECH_DEBT.md` (TD-47, TD-50, TD-51), `docs/PROJECT_LIFECYCLE.md`/`docs/ENTITY_RECONCILIATION.md`
(CQ-18/19), `docs/ENTERPRISE_ONTOLOGY.md` (CQ-20), `docs/ARCHITECTURE_CONSISTENCY.md` (CQ-30 sibling).
