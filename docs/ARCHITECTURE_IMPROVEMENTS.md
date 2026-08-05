# Enterprise Overnight Audit — Architecture Improvements

**Scope:** for the highest-value items found across this audit and `docs/TECH_DEBT.md`, the full
structured treatment: current architecture, problem, why it's a problem, recommended solution,
migration difficulty, risk level, expected benefit, priority. Not every TD item gets this treatment
(that would duplicate `TECH_DEBT.md` at length) — this document selects ~18 representative, highest-
leverage items spanning every category; every other tracked item keeps its one-line treatment in
`TECH_DEBT.md`.

---

### 1. Six independent deal/pipeline systems (`TD-47`)

- **Current architecture:** `deals.py`, `deal.py`, `deal_engine_v1.py`, `deal_pipeline_engine.py`,
  `lead_engine.py`, `automotive_sales.py` each define their own deal/lead entity and stage enum.
- **Problem:** no shared vocabulary; a cross-system report or a new integration has to special-case up
  to six different stage taxonomies.
- **Why it's a problem:** every new consumer (a dashboard, an AI agent reasoning about "where is this
  deal") either picks one system arbitrarily or reimplements the reconciliation logic itself.
- **Recommended solution:** adopt `deal_pipeline_engine.py`'s `DealPipelineStageCode`/`DealStage` as
  canonical (already the most mature — tenant-configurable, real SLA, real audit trail); publish a
  `CanonicalStageMapping` lookup for the other five (`docs/CANONICAL_PROCESS_MODEL.md`, CQ-19) — no
  code migration required for Phase 0.
- **Migration difficulty:** S for the lookup-table phase; XL if full consolidation is ever attempted.
- **Risk:** Low for Phase 0 (pure documentation); High if a future sprint attempts a real merge without
  the phased approach `docs/SPRINT_CQ_19_RESULT.md` §7 lays out.
- **Expected benefit:** any future cross-system reporting, AI reasoning, or integration work becomes
  immediately tractable instead of requiring six-way special-casing.
- **Priority:** P1.

### 2. Seven workflow engines, one disconnected frontend (`TD-48`)

- **Current architecture:** six backend engines plus a real, substantial frontend `workflowRuntime`
  with zero calls into any of them.
- **Problem:** the frontend engine executes real workflow logic (node graphs, approvals, retries) that
  never actually reaches the backend systems that are supposed to be authoritative.
- **Why it's a problem:** a user watching a "workflow" run in the UI may be watching pure client-side
  state with no backend record — a correctness and audit-trail gap, not just a duplication cost.
- **Recommended solution:** trace whether `workflowRuntime` is meant to be UI-only orchestration over
  backend-triggered work (fine) or is meant to *be* the execution (needs a bridge) — this is a product
  decision this audit cannot make unilaterally; document the answer once decided.
- **Migration difficulty:** M to document current behavior; L–XL to bridge if the answer is "should
  call the backend."
- **Risk:** Medium — silent client-only execution could already be misleading users about what actually
  ran.
- **Expected benefit:** closes a real trust gap between what the UI shows and what the backend recorded.
- **Priority:** P1.

### 3. No real backend `Project` entity (`TD-51`)

- **Current architecture:** the sales pipeline (six systems, item 1) ends at "won"; execution has only
  the frontend `ProjectParticipant` (participation only, no status/budget).
- **Problem:** there is no real record answering "what happened after we won this deal."
- **Why it's a problem:** every one of this audit's Value Chain / Project Lifecycle findings (CQ-18)
  traces back to this single missing entity.
- **Recommended solution:** add a `Project` table + nullable `Deal.project_id` FK
  (`docs/PROJECT_LIFECYCLE.md` §2, CQ-18) — deliberately minimal, composes existing entities.
- **Migration difficulty:** M (new table + one FK column, no backfill required since it's nullable).
- **Risk:** Low — additive only, no existing behavior changes.
- **Expected benefit:** unblocks Resource Allocation, Quality Gates, and Business Value Metrics designs
  that currently have nowhere real to attach.
- **Priority:** P1 — the highest-leverage single schema change identified across this whole audit.

### 4. `src/domains` — 141 orphaned files (`TD-55`)

- **Current architecture:** a full Python domain-model tree under `src/`, parallel to root-level
  `platform_*`/`applications/*`.
- **Problem:** apparently zero real usage; a large maintenance surface with unclear purpose.
- **Why it's a problem:** violates `CLAUDE.md`'s own "every architectural decision must be documented"
  rule — nobody reading the repo today can tell if this is dead or dormant-intentional.
- **Recommended solution:** a five-minute decision, not an engineering task — confirm zero usage with
  `python -c "import src.domains"`-style smoke checks, then either (a) write one paragraph in
  `ARCHITECTURE_MAP.md` explaining why it's kept, or (b) delete it in a dedicated, reviewed PR.
- **Migration difficulty:** S (it's a decision, not a migration).
- **Risk:** Low either way, since it's confirmed unused — the only risk is deleting something a
  hidden/undiscovered consumer needs, hence "confirm" before "delete."
- **Expected benefit:** removes the single largest "what is this and why does it exist" question a new
  contributor would hit.
- **Priority:** P1 (cheap, high discoverability payoff).

### 5. Root-level directory sprawl (`TD-56`)

- **Current architecture:** ~100 top-level directories, ~106 Python packages among them, no grouping.
- **Problem:** discoverability tax on every task; two bare directories (`./platform`, `./workflow`) are
  actively confusable with prefixed packages.
- **Why it's a problem:** compounds every other collision finding in this audit — harder to notice "a
  seventh workflow engine already exists" when there are 100 sibling directories to scan.
- **Recommended solution:** not a restructure (explicitly out of scope per this audit's own "don't move
  files" instruction) — rename or clearly document the two bare `./platform`/`./workflow` directories
  first, since that's the lowest-risk, highest-confusion-reduction single step.
- **Migration difficulty:** S for the two bare-directory disambiguation; XL for any real grouping
  restructure (not recommended without a dedicated sprint and explicit user sign-off, given the blast
  radius of moving that many import paths).
- **Risk:** Low for the disambiguation step; High for any broader restructure attempt without careful
  planning.
- **Expected benefit:** meaningfully reduces the "which of these do I mean" tax at very low cost for
  the disambiguation step alone.
- **Priority:** P2 (disambiguation step); P3/deferred (broader restructure).

### 6. Header-only auth in Platform Builder middleware (`TD-08`)

- **Current architecture:** trusts `X-Principal`/`X-Platform-Role` headers with no token verification.
- **Problem:** any caller who can set these headers can claim any identity/role.
- **Why it's a problem:** this is a real trust-boundary gap, not a cosmetic one — see `SECURITY_
  REVIEW.md`.
- **Recommended solution:** extend with live identity (already the recommended action in `TECH_DEBT.md`
  — "extend with live identity — do not replace UI").
- **Migration difficulty:** L.
- **Risk:** currently P0-adjacent from a security standpoint even though `TECH_DEBT.md` scores it P0 —
  agreed with that scoring.
- **Expected benefit:** closes a real authentication bypass risk.
- **Priority:** P0.

### 7. Unvalidated second JWT-secret read path (`TD-57`, pending verification)

- **Current architecture:** `platform_configuration/configuration_center.py:100` reads `JWT_SECRET`
  with the same insecure default as the validated path, but without the validation guard.
- **Problem:** if any real consumer signs/verifies tokens using this copy instead of the validated one,
  the platform's own startup safety check (`validate_iam_jwt_secret()`) doesn't protect it.
- **Why it's a problem:** a security control that only covers one of two read paths for the same secret
  provides false confidence.
- **Recommended solution:** trace every consumer of `PlatformSettings.jwt_secret`; either remove the
  duplicate read (have it delegate to `platform_identity.jwt_service.get_jwt_secret()`) or add the same
  validation guard at this site.
- **Migration difficulty:** S once the consumer trace is done.
- **Risk:** unknown until traced — potentially P0 if a real signing path uses the unvalidated copy.
- **Expected benefit:** closes a real (if currently unconfirmed) security gap cheaply.
- **Priority:** P1 pending verification, escalate to P0 if a real consumer is found.

### 8–18. Remaining representative items (condensed table)

| # | Item | Solution | Migration | Risk | Benefit | Priority |
|---|---|---|---|---|---|---|
| 8 | Three permission-scope vocabularies (`TD-52`) | Unify `Spatial`+`Asset` scopes into one rank table; keep `Visibility` separate (different concern) | L | Medium (rank reordering could silently change who's allowed what) | Removes a real "same word, different meaning" security footgun | P1 |
| 9 | Four Knowledge Graph systems (`TD-49`) | Build new work against Sprint 24.2's `ENTITY_TYPES`/`RELATION_TYPES`; document the other three as legacy | S (docs) | Low | Stops a fifth system from being built accidentally | P1 |
| 10 | `container.py` dead DI scaffold (`TD-18`) | Decide: wire in or retire | S (decide) | Low | Removes unused surface area | P2 |
| 11 | Two migration directories (`TD-31`) | Confirm `alembic.ini`'s target is authoritative; document/retire the other | S | Low | Removes a real "which migrations actually run" ambiguity | P1 |
| 12 | `platform_console` unrouted pages + unused `ProtectedRoute` (`TD-28`) | Wire in or remove | S | Low | Closes an unenforced-auth-by-omission gap | P1 |
| 13 | Two orphaned frontend command palettes (`TD-40`) | Retire the unimported copy | M | Low | Removes dead code with zero functional risk | P1 |
| 14 | Favorites/history implemented twice, unpersisted (`TD-41`) | Unify + add real persistence | M–L | Low | Real UX fix, not just cleanup | P1 |
| 15 | No `Deleted` event suffix anywhere (Event Vocabulary finding, CQ-20) | Keep it that way — codify `Retired`/`Archived` as the deliberate convention | S (docs) | None | Prevents an accidental future inconsistency | P3 |
| 16 | AI Production Center consent-gate sequencing risk (`TD-46`) | Build the consent-record gate before any real avatar/voice provider work | M | High if skipped | Prevents a governance failure in a legally-sensitive feature | P0 |
| 17 | `platform_builder`'s four near-identical center directories (`TD-27`) | Lowest-risk instance of the Command Center pattern to consolidate first (single app, not cross-repo) | M | Low | A concrete, bounded proof-of-concept for how to handle the bigger collisions | P2 |
| 18 | `src/kernel` TS ecosystem disconnected from Python backend (`TD-33`) | Write down the decision (intentional separation vs. future integration target) | S (docs) | None | Resolves the platform's most consequential undocumented architectural fork | P1 |

## Related documents

`docs/TECH_DEBT.md` (the full registry every item above is drawn from), `docs/ENTERPRISE_FULL_AUDIT.md`
(Phase 1/6 context), `docs/SECURITY_REVIEW.md` (items 6–7 in security depth), `docs/TOP_20_CRITICAL_
FIXES.md` (the further-condensed action list).
