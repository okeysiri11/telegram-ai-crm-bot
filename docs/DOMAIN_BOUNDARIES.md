# Sprint CQ-30 — Domain Boundaries Review

**Scope:** whether real subsystem boundaries are being respected, focused on findings from this
sprint's re-verification pass. Documentation only, `src` not modified.

## Issue 1 — The new Orchestrator/Kernel layer's boundary relative to `cityVisualization` is undefined

**Description:** `docs/RUNTIME_CONSISTENCY.md` Issue 1 found three sequential integration layers over
the same eleven runtimes (`cityVisualization`, `orchestrator`, `kernel`). This document asks the
boundary question specifically: which layer owns "coordination" as a responsibility, and does the
newer `orchestrator` supersede, complement, or duplicate `cityVisualization`'s existing role.

**Evidence:** `EnterpriseOrchestrator.ts`'s own header claims "Central coordination layer" (definite
article, singular) — a claim of exclusivity that `cityVisualizationRuntime.ts`'s own header ("single
source of truth for future 2D/3D City clients") also makes, for a different concern (visualization vs.
coordination). Neither file's real code was found to import or reference the other.

**Impact:** two "the central X" claims for adjacent-but-distinct concerns is not itself a contradiction
(a coordination layer and a visualization layer can coexist), but the absence of any real relationship
means neither can currently answer "is the runtime healthy" consistently — `orchestrator`'s
`RuntimeHealth.ts` and `cityVisualization`'s own health-adjacent state (via `performanceLayer.ts`,
per prior research) are two independent sources of truth for what should be one fact per runtime.

**Risk:** Medium — a runtime reported "healthy" by one layer and "degraded" by the other is a real,
plausible future bug, not a hypothetical one, given both independently poll/derive runtime state.

**Recommendation:** define the boundary explicitly: `orchestrator` should likely be the single real
source of runtime health/lifecycle truth, with `cityVisualization` consuming it rather than deriving
its own — but this is a product/architecture decision this audit cannot make unilaterally. Document
whichever answer is chosen.

**Priority:** P1.

**Estimated implementation cost:** S to document the decision; M if `cityVisualization` needs to be
re-plumbed to consume `orchestrator`'s health state instead of deriving its own.

---

## Issue 2 — `src/domains`'s boundary relative to `platform_*`/`applications/*` remains undocumented

**Description:** re-confirms `TD-55` from a boundary-specific angle: which layer, if any, `src/domains`
was meant to occupy in the governed dependency direction (Platform core → Providers → AI services →
Business modules → Vertical solutions → Customer applications) that `CLAUDE.md` describes.

**Evidence:** `src/domains` sits under `src/`, alongside the unrelated TS kernel ecosystem and the
`src/web` frontend, but is itself Python (per prior research) — meaning it doesn't cleanly belong to
either of the two systems `src/` is documented to contain per `CLAUDE.md`'s own three-system
description. It is, structurally, a fourth thing living inside a directory documented as holding two.

**Impact:** the governed-dependency-direction model has no defined place for `src/domains` to slot
into, which is consistent with (and likely explains) its confirmed zero-usage status
(`docs/RUNTIME_CONSISTENCY.md`... no — `docs/TECH_DEBT.md` TD-55) — nothing was ever wired to depend on
it because its layer was never decided.

**Risk:** Low functionally (nothing depends on it), Medium as a repeated-pattern risk (an undocumented
fourth thing under `src/` is exactly how the kernel/orchestrator naming collision in `docs/RUNTIME_
CONSISTENCY.md` also happened — an addition made without checking against the existing three-system
boundary description).

**Recommendation:** unchanged from `TD-55` — confirm zero usage, then document-or-remove. This document
adds the boundary framing as the "why it matters" context for that existing recommendation.

**Priority:** P1 (unchanged from `TD-55`'s standing priority).

**Estimated implementation cost:** S.

---

## Issue 3 — `platform_*` vs. `platform_enterprise_*`: no discoverable rule, confirmed by sampling

**Description:** checked whether a clear naming rule governs when a capability is a bare `platform_X`
vs. a `platform_enterprise_X` package.

**Evidence:** sampling both groups (e.g. `platform_workflow`/`platform_ai`/`platform_security` vs.
`platform_enterprise_command_center`/`platform_enterprise_digital_twin`/`platform_enterprise_knowledge_
graph`) shows no consistent discriminator — some `platform_enterprise_*` packages are newer/larger-scope
successors to a `platform_*` package that still exists independently (Command Center, Digital Twin,
per `TD-03`/`TD-04`), but others (`platform_enterprise_onboarding`, `platform_enterprise_pilot_
readiness`) have no bare `platform_*` counterpart at all, suggesting the prefix is not a consistent
"is this a successor" signal.

**Impact:** the prefix alone cannot be used to infer a package's maturity or relationship to a
same-named bare package — a real discoverability cost matching `TD-56`'s broader root-sprawl finding.

**Risk:** Low — cosmetic/discoverability, not functional.

**Recommendation:** if a rule was originally intended, document it explicitly in `ARCHITECTURE_MAP.md`;
if none was intended (organic naming over time), state that plainly too, so future contributors stop
assuming a pattern that isn't there.

**Priority:** P3.

**Estimated implementation cost:** S.

## Related documents

`docs/TECH_DEBT.md` (TD-55, TD-56), `docs/RUNTIME_CONSISTENCY.md` (CQ-30 sibling, Issue 1's source
finding), `docs/CLAUDE.md`'s own governed-dependency-direction description, `docs/ARCHITECTURE_
CONSISTENCY.md` (CQ-30 sibling).
