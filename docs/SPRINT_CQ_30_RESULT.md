# Sprint CQ-30 Result — Enterprise Architecture Consistency Review

**Mode:** repository-wide consistency validation against `docs/FINAL_AUDIT_RESULT.md` (the overnight
audit). Documentation only, `src` not modified, no production code written.

## 1. What this sprint produced

| Document | Covers |
|---|---|
| [`ARCHITECTURE_CONSISTENCY.md`](./ARCHITECTURE_CONSISTENCY.md) | Master validation: status of every headline audit finding, re-checked |
| [`API_CONSISTENCY.md`](./API_CONSISTENCY.md) | Duplicated/undocumented API surfaces |
| [`ENTITY_CONSISTENCY.md`](./ENTITY_CONSISTENCY.md) | Duplicated entities, re-verified |
| [`RUNTIME_CONSISTENCY.md`](./RUNTIME_CONSISTENCY.md) | Duplicated runtime concepts — **the sprint's headline new finding** |
| [`DOMAIN_BOUNDARIES.md`](./DOMAIN_BOUNDARIES.md) | Boundary questions raised by the new findings |
| [`TOP_50_REMAINING_REFACTORINGS.md`](./TOP_50_REMAINING_REFACTORINGS.md) | Re-prioritized action list |
| `SPRINT_CQ_30_RESULT.md` | This document, including the executive summary (§4) |

Also updated: `docs/TECH_DEBT.md` (TD-17 closed as resolved, TD-57 re-scoped with a precise one-line
fix, TD-59/TD-60 added for the new runtime-layer findings).

## 2. Methodology

Every claim in the overnight audit's `FINAL_AUDIT_RESULT.md` and `TOP_20_CRITICAL_FIXES.md` that could
be re-checked cheaply (a grep, a targeted file read) was re-checked this sprint rather than restated.
Items not re-verified are explicitly marked "not re-derived this pass" rather than silently carried
forward as if confirmed — see `docs/ENTITY_CONSISTENCY.md` Issue 2 for an example of this discipline
applied.

## 3. Headline result: one real finding materialized exactly as warned

The overnight audit's `TOP_100_RECOMMENDATIONS.md` #97 said: "Confirm no second cross-runtime
aggregator is introduced alongside `cityVisualization`." This sprint found that a second (Sprint 29.8's
`orchestrator`) **and** a third (Sprint 29.9's `kernel`) have since been introduced — and that the new
`orchestrator` package reuses the exact name of the pre-existing, unrelated, already-tracked (`TD-33`)
standalone TS `@ados/orchestrator` ecosystem, with `kernel` doing the same against `@ados/kernel`. This
is the clearest possible validation that the audit's underlying concern (naming/architecture collisions
recur because nothing checks before building) is not hypothetical — it happened again, on schedule,
using the exact two names the platform had already flagged as sensitive (`TD-33`).

## 4. Executive summary

**Bottom line:** the platform's core governance signal remains good — a real, previously CI-failing
violation (`TD-17`) is now confirmed fixed, and the JWT-secret validation logic has genuinely improved
since the last audit (it just isn't wired to block yet, a one-line fix). The collision pattern this
engagement keeps finding is still the dominant risk, and this sprint provides its sharpest evidence yet:
the exact failure mode predicted for "kernel"/"orchestrator" specifically was not just theoretical — it
recurred within one to two sprints of the warning being written down.

**If I were the CTO reading only this section:** ship fix #1 from `docs/TOP_50_REMAINING_REFACTORINGS.md`
today — it is one line, already has a passing test, and closes a live production-security gap. Then
require the "does this already exist" check (`docs/EXECUTIVE_SUMMARY.md`'s top recommendation from the
last audit) as an actual PR-template checkbox, not just a stated principle — this sprint is the second
piece of direct evidence that the principle alone isn't sufficient.

**What's better than the last audit found:** `TD-17` resolved; JWT validation logic matured and gained
real test coverage; `API_MAP.md` and `TECH_DEBT.md` remain accurate, current, and internally
consistent under a second sprint of scrutiny.

**What's worse:** two new real naming/architecture collisions (`TD-59`, `TD-60`), found in exactly the
category the last audit most wanted to prevent.

**What's unchanged:** `TD-51` (no `Project` entity), `TD-55` (`src/domains` orphaned), `TD-08`
(header-only auth), `TD-58` (tenant-filter coverage still unverified) — none regressed, none resolved.

## 5. Risks

1. `TD-59`/`TD-60` should be resolved by documentation, not a rename — per this engagement's standing
   discipline, renaming either "Kernel" or "Orchestrator" risks more churn than the collision itself
   causes.
2. The `startup.py:54` fix (`TOP_50` #1) is cheap enough that it may be tempting to batch it with other
   unrelated startup changes — recommend shipping it alone, given it's a one-line security fix with an
   existing test.
3. This sprint's re-verification was still sampling-based, not exhaustive (`TD-47`'s six-way count and
   `TD-58`'s tenant-filter question were both explicitly not re-derived this pass) — a future sprint
   should not assume "validated by CQ-30" means "exhaustively re-proven," only "re-checked where cheap."

## 6. Validation checklist

- [ ] `startup.py:54` changed to a blocking `fail_fast` value; existing test
      `test_validation_fail_fast_on_insecure_production_jwt` still passes
- [ ] `TD-17` confirmed green in a real `scripts/validate_architecture.py` CI run, not just by source
      re-reading
- [ ] `TD-59`/`TD-60`'s disambiguation notes added wherever "Kernel"/"Orchestrator" next appear in new
      documentation
- [ ] `API_MAP.md` updated with the five missing Knowledge Graph/Digital Twin prefixes
- [ ] No further cross-runtime aggregator introduced without a documented relationship to the existing
      three (`cityVisualization`, `orchestrator`, `kernel`)

## Related documents

`docs/FINAL_AUDIT_RESULT.md` (the document this sprint validates), `docs/TECH_DEBT.md`,
`docs/TOP_50_REMAINING_REFACTORINGS.md`, and every CQ-30 sibling listed in §1.
