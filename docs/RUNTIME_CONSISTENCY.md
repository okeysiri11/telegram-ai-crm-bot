# Sprint CQ-30 — Runtime Consistency Review

**Scope:** duplicated runtime concepts, re-verified against the current repository state (not a repeat
of prior findings — every item below was re-checked this sprint). Documentation only, `src` not
modified.

## Issue 1 — A second real cross-runtime aggregator has materialized since the last audit

**Description:** The overnight audit (`docs/TOP_100_RECOMMENDATIONS.md` #97) explicitly recommended
"confirm no second cross-runtime aggregator is introduced alongside `cityVisualization`." Re-checking
this sprint: a second one now exists. `src/web/src/runtime/orchestrator/EnterpriseOrchestrator.ts`
(Sprint 29.8 — one sprint after `cityVisualization`'s Sprint 29.5) is a real "Central coordination layer
over existing Enterprise Runtimes." A third layer, `src/web/src/runtime/kernel/EnterpriseKernel.ts`
(Sprint 29.9), then wraps the orchestrator for platform bootstrap.

**Evidence:** `EnterpriseOrchestrator.ts:1-3` ("Central coordination layer over existing Enterprise
Runtimes (additive only)"); `orchestratorTypes.ts:10-20`'s real `RuntimeId` union registers ten of the
eleven base runtimes (`business_network`, `digital_citizen`, `asset`, `life`, `spatial`,
`city_visualization`, `interaction`, `intelligence`, `workflow`, `automation`); `KernelBootstrap.ts:1-3`
("Boot → Config → Registry → Deps → Orchestrator → Runtimes → Health → Ready"), which imports
`enterpriseOrchestrator` from `@/runtime/orchestrator` (`EnterpriseKernel.ts:8`).

**Impact:** three sequential integration layers now exist for the same eleven base runtimes:
`cityVisualization` (visualization-focused, 8-runtime fan-in), `orchestrator` (coordination-focused,
10-runtime registry), `kernel` (bootstrap-focused, wraps orchestrator). Each was built "additive only"
in isolation and each is individually well-reasoned, but together they are three different real answers
to "what coordinates the runtimes," none aware of being the second or third.

**Risk:** Medium. Not currently broken — each layer has a distinct stated purpose (render vs. coordinate
vs. boot) that could be read as complementary rather than redundant. The risk is a future contributor
adding a *fourth* layer without realizing three already exist, or two layers drifting to disagree about
runtime health/status.

**Recommendation:** document the three-layer stack explicitly as an intentional layering (boot →
coordinate → visualize), not a collision, if that is in fact the real relationship — or clarify why
`cityVisualization` doesn't route through the newer `orchestrator` if it should. This is a
documentation/decision task, not a merge.

**Priority:** P1.

**Estimated implementation cost:** S (one written decision + a short doc section) if the layering is
intentional; M if it turns out to need `cityVisualization` re-plumbed through `orchestrator`.

---

## Issue 2 — "Kernel" and "Orchestrator" now name two unrelated real systems each (new finding)

**Description:** `TD-33` (`docs/TECH_DEBT.md`) already tracks the standalone TS "ADOS OS" ecosystem
(`src/kernel`, `src/orchestrator`, real npm packages `@ados/kernel`/`@ados/orchestrator`) as
disconnected from the Python backend. This sprint found that **the same two names now also exist one
directory level into the frontend**, as fully independent, unrelated real systems:
`src/web/src/runtime/kernel/` and `src/web/src/runtime/orchestrator/` (Issue 1, above). No import
relationship exists between either pair — confirmed via a direct grep for `@ados/kernel`/`@ados/
orchestrator` inside the frontend runtime packages, zero hits.

**Evidence:** `src/kernel/package.json:2-4` (`"name": "@ados/kernel"`, `"version": "1.4.0"`,
`"description": "ADOS OS Enterprise Kernel — sprint 1.4 Runtime Server"`) vs.
`src/web/src/runtime/kernel/EnterpriseKernel.ts:2-3` (`"Enterprise Kernel — Sprint 29.9. Platform
bootstrap & lifecycle manager"`); `src/orchestrator/package.json:2-4` (`"name": "@ados/orchestrator"`,
`"version": "3.0.0"`, `"ADOS AI Orchestrator + Multi-Agent Collaboration Engine"`) vs.
`src/web/src/runtime/orchestrator/EnterpriseOrchestrator.ts:2-3`.

**Impact:** any future search for "kernel" or "orchestrator" in this repository now returns two
unrelated real hits each, at different path depths, in different languages, versioned independently
(sprint 1.4/3.0 vs. Sprint 29.9/29.8). This is a more acute version of the naming-collision pattern
`TD-01`–`TD-05`/`TD-49` already catalogued elsewhere, because "kernel" and "orchestrator" are
unusually load-bearing, generic architecture terms — collisions on them are more likely to mislead a
reader than a domain-specific term like "Digital Twin."

**Risk:** Medium — no functional risk today (fully disconnected code paths), but real risk of a future
contributor or AI agent conflating the two when reasoning about "the kernel" or "the orchestrator"
without checking which one a given conversation means.

**Recommendation:** add an explicit disambiguation note to both `TD-33`'s entry and any future doc
introducing either frontend package — e.g., "Enterprise Kernel (frontend, `src/web/src/runtime/kernel`)
is unrelated to `@ados/kernel` (`src/kernel`, the standalone TS ADOS OS ecosystem)." Do not rename
either — both names are locally sensible for what they do; the fix is documentation, not code.

**Priority:** P1.

**Estimated implementation cost:** S.

---

## Issue 3 — Seven workflow engines: recount confirms no change, one clarification added

**Description:** Re-verifying `TD-48`'s seven-way workflow-engine count (six backend + the frontend
`workflowRuntime`) — unchanged. New context found this sprint: the frontend `orchestrator`'s `RuntimeId`
union (Issue 1) includes `"workflow"` and `"automation"` as registered runtime IDs, meaning the new
orchestrator layer is now aware of and coordinates both, but per Issue 1's evidence, coordination here
means health/lifecycle tracking, not execution — it does not resolve `TD-48`'s core finding that
`workflowRuntime` never calls any backend engine.

**Evidence:** `orchestratorTypes.ts:19-20` (`"workflow" | "automation"` in `RuntimeId`);
`RuntimeDependencyGraph.ts:1-3` ("Read-only topology") — confirms the orchestrator's relationship to
workflow/automation is topological/health-tracking, not execution-routing.

**Impact:** none beyond what `TD-48` already records — restated for completeness since this document's
job is validation, not silence on unchanged items.

**Risk:** Unchanged from `TD-48`'s existing assessment.

**Recommendation:** unchanged — see `TD-48`.

**Priority:** P2 (down-weighted from P1 since this is a confirmation, not a new finding).

**Estimated implementation cost:** N/A (no new action beyond `TD-48`'s existing recommendation).

## Related documents

`docs/TECH_DEBT.md` (TD-33, TD-48), `docs/TOP_100_RECOMMENDATIONS.md` (#96–97, the recommendation this
sprint validates), `docs/CROSS_SYSTEM_SEMANTIC_MAPPING.md` (CQ-20, the original eleven-runtime
inventory this sprint extends to thirteen), `docs/DOMAIN_BOUNDARIES.md` (this sprint, the boundary
question behind Issue 1).
