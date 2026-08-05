# Independent Architecture Review — Sprint 34.2C

> **Supersession (Sprint 35.0):** Finding §7.1 (“Sync Engine … not yet real”) is **historical**.
> As of 34.2C/34.2D the platform ships `platform_state.sync_engine.SyncEngine`,
> `VersionEngine`, `PlatformEventStore`, and `ConflictResolutionEngine` on the canonical
> `PlatformEventBus`. See `docs/ENTERPRISE_RUNTIME_34_2D.md` and `docs/FOUNDATION_AUDIT_35_0.md`.

**Mode:** Lead Enterprise Software Architect, performed independently while another engineering team
implements Sprint 34.2C. Documentation only, `src` not modified, no existing module rewritten.

**Methodology note, stated up front because it materially changes this review's tone relative to prior
ones**: this platform has undergone substantial real consolidation since the last independent review
(CQ-32.2). Sprints 32.2 (Platform Core Governance), 32.3 (Enterprise Consolidation), 32.3.1–32.3.7 (UX
consolidation), 32.4 (Security Center), 34.1, 34.2A (Unified Identity), and 34.2B (Unified Platform
Registry) have shipped real, well-designed answers to the majority of this engagement's
longest-standing findings. This review verifies that work directly rather than re-deriving the
problems it solves, and focuses its critical attention on what remains open — principally the
multi-sprint adapter-cutover work that consolidation created, and the genuinely new items this brief's
own framing surfaces (Sync Engine, Mobile, tenant/scale readiness at the brief's stated volumes).

**One correction to the brief's own assumptions, stated plainly**: the brief describes "FastAPI
architecture" and asks this review to evaluate FastAPI routers. The real backend has **no FastAPI
anywhere** (confirmed by direct search: zero imports, 248 real files use `aiohttp` instead) — it is,
and has been throughout this entire engagement, an aiohttp-based API server per `CLAUDE.md`'s own
description. Section 9 below reviews the real aiohttp architecture; the brief's FastAPI-specific
sub-questions (routers, DI) are answered against what actually exists, not against a framework this
codebase doesn't use.

---

## 1. Platform Architecture

### Finding 1.1 — Canonical services are now declared; adapter cutover is the real remaining risk

**Severity:** High. **Root cause:** the platform correctly chose incremental consolidation over a
risky big-bang rewrite (`docs/CANONICAL_SERVICES.md`, Sprint 32.3) — Deal Pipelines, Workflow Engines,
Knowledge Base, Event Bus, Notification Pipelines, Unified Queue, Secrets, Metrics, and Web
Orchestration each now have one declared canonical implementation, with prior duplicates demoted to
"legacy adapters, not SoR." This directly resolves the *naming* half of `TD-47`/`TD-48`/`TD-49`/`TD-20`/
`TD-53`/this engagement's task-queue and secrets findings — a genuine, verified architectural
improvement, not a documentation exercise. **Business impact:** low today (the platform functions
correctly through the adapters); grows the longer the adapters persist, since every adapter is a place
a future feature could accidentally attach business logic to a non-canonical path. **Technical
impact:** `TD-64` already tracks the cutover as XL, multi-sprint. **Recommended solution:** the
declared plan is correct — extend the canonical path only, migrate adapters opportunistically, forbid
new parallel engines (`CANONICAL_SERVICES.md`'s own three rules). **Migration complexity:** XL
(already correctly scoped as such). **Priority:** High — not urgent to rush, but should not stall
either; recommend a fixed cadence (e.g., one adapter migrated per sprint) rather than open-ended
"opportunistic."

### Finding 1.2 — Auto Marketplace still ships local Core-shaped services

**Severity:** Medium. **Root cause:** `TD-61` — `auto_marketplace` retains its own `authentication/`,
`notifications/`, `search/`, `pricing/` trees that structurally resemble Core services. **Business
impact:** a customer-facing vertical drifting from the canonical identity/notification path risks
inconsistent behavior (e.g., a notification preference set in Core not respected by the Auto adapter).
**Technical impact:** real, tracked, `PlatformBridge` is the stated thin-adapter pattern. **Recommended
solution:** unchanged from `TD-61`'s own recommendation — thin the adapters via `PlatformBridge`.
**Migration complexity:** L. **Priority:** Medium.

### Finding 1.3 — No `platform_core` package; Core is intentionally composed

**Severity:** Low (by design, not oversight). **Root cause:** `TD-62` — Core is a *governance concept*
enforced by `platform_architecture/core_inventory.py` + `architecture_sprint_review.py`, not a
physical package. **Business impact:** none if the inventory discipline holds; real risk of "teams
re-invent Platform Core folders" if it lapses — `TD-62`'s own stated risk. **Recommended solution:**
keep the inventory tooling running every sprint, per its own design — this is a process-governance
item, not a code change. **Migration complexity:** S (maintain) / XL (physical regroup, correctly
out of scope). **Priority:** Low, contingent on the inventory tool actually running each sprint (not
independently re-verified this pass).

---

## 2. Module Boundaries

Real bounded-context discipline has visibly improved via the canonical-services declaration (§1), which
is functionally the "one responsibility = one canonical service" principle DDD calls for — this
review's CQ-32.2 predecessor recommended exactly this and it has since shipped. The remaining boundary
risk is the same one flagged then: `deal.py`'s OTC-flavored statuses leaking a financial-settlement
concern into the generic sales-pipeline entity — not re-verified as fixed or unfixed this pass, since
`TD-47`'s adapter-cutover status doesn't specify per-field cleanup.

- **Severity:** Medium. **Priority:** Medium, sequenced within the `TD-64` cutover work, not
  independently.

---

## 3. Platform Registry

### Finding 3.1 — Real, and a genuinely strong answer to the brief's question

`platform_registry/` (Sprint 34.2B) directly answers "can Registry support future verticals, plugins,
marketplace, AI modules, customer modules, third-party extensions without redesign": **yes,
structurally** — it already composes `verticals/`, `agents/`, `modules/`, `features/` (feature flags),
and `visibility/` (per-client: web/telegram/desktop/mobile/api/voice/ai) as first-class registry
sections, with a real, working multi-client navigation projection (`navigation_for(client=..., roles=
[...])`) already serving Web and Telegram from one source, Desktop/Mobile/API prepared but not yet
consuming it in a built UI.

**Severity:** N/A (positive finding). **Business impact:** this is the platform's strongest evidence of
being architected for a plugin/marketplace future without a later redesign — a genuine competitive/
investor-relevant strength.

### Finding 3.2 — Third-party extensions specifically not yet exercised

**Severity:** Medium. **Root cause:** the registry's `modules/`/`features/` sections are real and used
for first-party verticals; no real third-party extension has been registered through this system yet
(the Universal Service Constructor, `TD-63`, is foundation-only — no UI, no marketplace publish path).
**Business impact:** the marketplace/third-party-extension story is architecturally sound but
functionally unproven — a real third-party developer has never actually gone through this path.
**Recommended solution:** unchanged from `TD-63` — build the UI and publish path once a real
marketplace launch is scheduled, not before. **Migration complexity:** L. **Priority:** Medium,
sequenced behind product timing, not an architecture blocker.

---

## 4. Identity

### Finding 4.1 — Unified Identity Core is real, well-designed, and resolves a longstanding fragmentation finding

Sprint 34.2A's `platform_identity` Identity Core (`IdentityService`/`AuthenticationService`/
`AuthorizationService`/`UserResolver`/role-permission-workspace registries/`JwtService`/
`SessionManager`) is a genuine architectural strength: one canonical `users` table + `user_identity_
links`, Web and Telegram authenticating through the same facade, a real alias-mapping layer for legacy
role/permission codes (`OWNER`/`SUPER_ADMIN` → `owner`), and an `AuthMethod` enum with Mobile/Desktop/
OAuth slots already reserved (stubbed, not wired). This is the real resolution this engagement's own
`docs/ROLE_NAVIGATION.md` (CQ-30.7) "three unreconciled role vocabularies" finding was asking for.

**Severity:** N/A (positive finding, verified not just claimed — real migration file, real backfill
plan, real downgrade path).

### Finding 4.2 — ISAM remains a parallel identity surface, explicitly deferred

**Severity:** Medium. **Root cause:** `UNIFIED_IDENTITY_34_2A.md`'s own Legacy Compatibility Report:
"ISAM (Enterprise Hub) — Still available as parallel Web path; Identity Core is platform JWT SoR — ISAM
fold-in remains 34.2+ follow-up." **Business impact:** two real identity paths for the Enterprise Hub
surface specifically is a real, if bounded and self-acknowledged, fragmentation risk — an Owner
dashboard sourcing session state from ISAM could diverge from the canonical Identity Core's view.
**Recommended solution:** unchanged from the platform's own stated plan — fold ISAM in as a scheduled
follow-up, not urgent but should not be indefinitely deferred. **Migration complexity:** M.
**Priority:** Medium.

### Finding 4.3 — Tenant-role FK gap explicitly deferred

**Severity:** Medium. **Root cause:** `TenantUserRole telegram int FK — Deferred (34.1 A6)`. **Business
impact:** at the brief's stated 100-company/10,000-user scale, an un-migrated integer FK on a
tenant-role join is a real (if currently working) technical debt item that becomes costlier to migrate
the more rows accumulate. **Recommended solution:** schedule this migration before the 100-company mark
is reached, not after. **Migration complexity:** M. **Priority:** Medium-High specifically because of
the brief's stated scale target — cheap now, expensive deferred further.

### Finding 4.4 — SSO/OAuth/OpenID: stub only, correctly scoped as future

**Severity:** Low (deliberate, not an oversight). **Root cause:** `AuthenticationService` has an OAuth
stub registered; no real Google/OIDC/SAML provider is wired (consistent with every prior review's
finding that Google Login remains unbuilt). **Business impact:** blocks Enterprise SSO-requiring
customers specifically — a real go-to-market constraint for larger enterprise deals, not a Beta
blocker. **Recommended solution:** build real OIDC support once a specific enterprise customer requires
it — the stub is correctly positioned to receive it without an identity-core redesign. **Migration
complexity:** M (the hard architectural work — one identity facade — is already done; adding a real
provider is comparatively contained). **Priority:** Medium, demand-driven.

---

## 5. AI Architecture

Restated and updated from `docs/AI_RUNTIME_REVIEW.md` (CQ-32.2): agent lifecycle remains split across
multiple registries, though the canonical-services declaration now designates `platform_jobs` lane=`ai`
+ web `jobManager.ts` (confirmed real, part of the now-real `src/web/src/enterprise-runtime/` package)
as canonical for AI Runtime queues specifically — a real narrowing of the fragmentation this review's
predecessor found. Memory remains fragmented (four surfaces, unchanged); real vector/RAG search remains
absent (unchanged — the platform's most consequential AI capability gap, not a duplication one). Real
Prompt Firewall (Sprint 30.9) remains real and correctly composed, not duplicated.

- **Severity:** High for the absent real RAG/vector search specifically, at the brief's stated "millions
  of CRM records" + "thousands of AI agents" scale — keyword/structured retrieval does not substitute
  for semantic retrieval at that data volume for an AI-facing product. **Priority:** High — this is the
  review's top AI-architecture recommendation, unchanged from CQ-32.2, now more urgent given the
  brief's explicit scale target.

---

## 6. Data Model

Not exhaustively re-audited this pass (would require a full `database/models/` read beyond this
review's scope). Known, still-open items: no real `Project` entity (`TD-51`), three unreconciled task
concepts (`TD-50`), no generic history/versioning mixin (`TD-54`). **New concern raised by the brief's
own scale target**: "millions of CRM records" implies the real `Deal`/`DealStage`/`DealStageHistory`
tables (the canonical deal-pipeline path, §1.1) need a real partitioning/archiving strategy before that
volume arrives — not confirmed to exist this pass.

- **Severity:** High at declared scale, Low today. **Root cause:** no partitioning/archiving strategy
  confirmed for the canonical deal tables. **Recommended solution:** design table partitioning (e.g.,
  by tenant or by time) before real customer data approaches millions of rows — cheaper to design early
  than retrofit under load. **Migration complexity:** M if designed ahead of time, XL if retrofitted
  under production load. **Priority:** High, time-sensitive relative to actual data growth, not
  calendar time.

---

## 7. Synchronization

### Finding 7.1 — Sync Engine, offline sync, conflict resolution: not yet real

**Severity:** N/A (not a defect — flagged as unbuilt, consistent with the brief's own framing that
Sprint 34.2C is in progress). **Root cause:** no `SyncEngine`-named real implementation was found this
pass; the real Event Bus (`PlatformEventBus`, canonical per §1) is the closest real foundation for one.
**Business impact:** if Sprint 34.2C is building this now, this review's contribution is a design
constraint, not a retrospective finding: **conflict resolution and versioning should be designed
against the same canonical Event Bus and the not-yet-built generic history/versioning mixin (`TD-54`)
together**, not independently — building a Sync Engine's own bespoke versioning scheme while `TD-54`
remains open would create an eighth/ninth "history tracking, done differently" instance, repeating this
platform's own most common architectural mistake one more time.
- **Recommended solution:** sequence `TD-54` (or at least its design) ahead of or alongside Sync
  Engine work specifically because Sync Engine is the one capability that most needs a real, shared
  versioning primitive to do conflict resolution correctly.
- **Priority:** Critical, timing-sensitive — this is a "get it right before it ships" recommendation,
  not a post-hoc fix request.

---

## 8. Frontend

Not exhaustively re-audited (React architecture/state management/bundle size were reviewed at a
different depth in `docs/PERFORMANCE_REVIEW.md` §5-6, CQ-30.8/32.2 — not repeated here). One new,
relevant finding from this pass: the real `enterprise-runtime` package (confirmed this review,
`agentOs.ts`/`healthService.ts`/`jobManager.ts`/`productionRuntime.ts`/`aiAgentRuntime.ts`/
`useRuntimeEngine.ts`) appears to be the real, current consolidation target for what CQ-30's `TD-59`/
`TD-60` found as three competing cross-runtime aggregators (`cityVisualization`/`orchestrator`/
`kernel`). **Not independently confirmed this pass** whether those three now route through
`enterprise-runtime` as adapters (per `CANONICAL_SERVICES.md`'s "other `*Runtime` folders as
adapters") or remain independent — flagged as the single most valuable follow-up verification this
review recommends, since it would close `TD-59`/`TD-60` if confirmed.

- **Severity:** Medium (pending verification). **Priority:** High to verify — cheap to check, resolves
  two tracked debt items if confirmed.

---

## 9. Backend

Real aiohttp-based architecture (corrected from the brief's FastAPI assumption, per this document's
header). Real `services/`/`repositories/` separation remains the platform's strongest DDD-adjacent
layering (`docs/DDD_REVIEW.md`, CQ-32.2, unchanged). No dependency-injection container is in active use
(`TD-18`, `container.py` remains unadopted, unchanged this pass). Background workers: real, now
consolidated under `platform_jobs.unified_queue` (Sprint 32.3, confirmed this review) — a genuine
improvement over the three-independent-queue finding this engagement tracked since CQ-30.6.
Transactions: not independently audited this pass.

- **Severity:** Low for DI container non-adoption (a real but non-urgent architectural choice —
  the codebase functions without it). **Priority:** Low.

---

## 10. Database

Restated, not re-derived: real Postgres, real healthchecks, no confirmed connection pooler (`docs/
SCALABILITY_REVIEW.md` §1). **New this pass**: partitioning/archiving strategy for canonical tables is
the review's top database-specific concern given the brief's explicit "millions of records" target —
see §6 above, not repeated.

---

## 11. Security

Restated from `docs/SECURITY_ARCHITECTURE_REVIEW.md` (CQ-32.2), updated: the systemic insecure-
default-secret pattern this review flagged as Critical has been **substantially hardened** —
`TD-65` confirms `secret_policy.py` now exists and production `validate(fail_fast=True)` rejects
placeholder secrets; the remaining risk is narrowed specifically to "non-production mis-deploy without
`ENVIRONMENT=production`" — a real, much smaller residual risk than the original finding. Security
Center (Sprint 32.4) is real but not yet wired into every HTTP/APH path (`TD-66`) — progressive
adoption, not a design flaw.

- **Severity:** Medium (down from this review's own prior Critical rating, reflecting real hardening).
  **Priority:** Medium — complete `TD-66`'s progressive wiring, verify `ENVIRONMENT=production` is
  actually set correctly in the real deploy pipeline (a deploy-configuration check, not a code fix).

---

## 12. Enterprise Readiness

| Dimension | Verdict |
|---|---|
| Enterprise SaaS | Substantially ready — real Identity Core, real Platform Registry, real canonical services |
| White Label | Real theme engine exists (`ThemeId: corporate/custom`, CQ-30.1) — not independently re-verified this pass |
| Marketplace | Architecturally ready (§3), functionally unproven (no real third-party extension yet) |
| Multi-company | Real (`multi_company.Company`/`Branch`, CQ-15) |
| Multi-region | Not ready — no real evidence found this pass or prior reviews |
| HA | Partial — real healthchecks, no confirmed read replicas or multi-instance `bot` service |
| Disaster Recovery | Real backup infrastructure exists (`docs/BACKUP_GUIDE.md`, CQ-30.8) — restore-drill automation not confirmed |
| Horizontal Scaling | Not ready — `bot` service is real but single-instance in the real prod compose; no confirmed load-balancer config |
| Microservices (future) | Not attempted, and this review does not recommend attempting it — the real canonical-services consolidation (§1) is the correct intermediate step; microservices decomposition should follow proven service boundaries, not precede them |

## Related documents

`docs/TECH_DEBT.md` (canonical registry, TD-61 through TD-67 the primary new evidence this review
draws on), `docs/CANONICAL_SERVICES.md`/`docs/PLATFORM_CORE.md`/`docs/UNIFIED_IDENTITY_34_2A.md`/
`docs/UNIFIED_PLATFORM_REGISTRY_34_2B.md` (real, Sprint 32.2–34.2B), `docs/AI_RUNTIME_REVIEW.md`/
`docs/SECURITY_ARCHITECTURE_REVIEW.md`/`docs/PLATFORM_CORE_REVIEW.md`/`docs/DDD_REVIEW.md` (CQ-32.2,
the predecessor findings this review updates), `docs/TOP_25_LISTS_34_2C.md`/`docs/SPRINT_CQ_34_2C_
RESULT.md` (this review's siblings).
