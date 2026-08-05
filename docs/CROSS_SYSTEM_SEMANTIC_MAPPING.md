# Enterprise Semantic Model — Cross-System Mapping

**Sprint:** CQ-20 — Architecture Research + Ontology Design. Documentation only, `src` not modified.

**Do not duplicate:** This document does not re-derive any subsystem's internal vocabulary — every row
below points back to the sprint that already documented it. Its job is the thing no prior sprint did:
list all real runtimes side by side and confirm which of the brief's ten named systems are real
packages, and which are naming assumptions the brief made that don't correspond to anything real.

## 1. The real runtime inventory (confirmed this sprint)

`src/web/src/runtime/` contains eleven real, independently-versioned runtime packages: `assetRuntime`,
`automation`, `businessNetwork`, `cityVisualization`, `commandRuntime`, `digitalCitizen`,
`intelligenceRuntime`, `interactionRuntime`, `lifeEngine`, `spatialRuntime`, `workflowRuntime`. This is
the first time this engagement has enumerated the full real list in one place.

## 2. Per-system mapping (brief's ten)

| Brief system | Real mapping |
|---|---|
| Runtime | No single real package literally named `Runtime` — the brief means the composition root, real `enterpriseShellRuntime.ts` (`src/web/src/shell/enterprise/`), which boots the other ten |
| Automation | Real `src/web/src/runtime/automation` (`automationEngine`, Sprint 28.9, `AUTOMATION_ENGINE.md`) |
| Workflow | Real `src/web/src/runtime/workflowRuntime` (Sprint 29.4-ish, `ENTITY_RECONCILIATION.md` §3, CQ-19) — one of seven real workflow-shaped systems total, the only frontend one |
| Business Network | Real `src/web/src/runtime/businessNetwork` (Sprint 29.0, `ENTERPRISE_BUSINESS_NETWORK.md`) |
| Assets | Real `src/web/src/runtime/assetRuntime` (`DIGITAL_TWIN_STANDARDS.md`, CQ-16) |
| Citizens | Real `src/web/src/runtime/digitalCitizen` (Sprint 29.1, `DIGITAL_CITIZEN.md`) |
| Life Engine | Real `src/web/src/runtime/lifeEngine` (Sprint 29.2, `DAILY_OPERATIONS_MODEL.md`, CQ-17) |
| Spatial Runtime | Real `src/web/src/runtime/spatialRuntime` (Sprint 29.4, `REGIONAL_DIGITAL_TWIN.md`, CQ-16) |
| Visualization Runtime | Real `src/web/src/runtime/cityVisualization` (Sprint 29.5, previously uncited in this engagement) — see §3 |
| Executive Runtime | **No real package by this name** — the brief assumes a runtime parallel to the other nine; the real executive layer is dashboard/command-center-shaped (`EXECUTIVE_OPERATING_SYSTEM.md`, CQ-15), not a `src/web/src/runtime/` package. A genuine naming mismatch, not a gap to fill |

## 3. New finding: `cityVisualization` is the real, existing integration point

`src/web/src/runtime/cityVisualization/cityVisualizationRuntime.ts` (Sprint 29.5) is real and
previously uncited in this engagement — its own header states it is the "single source of truth for
future 2D/3D City clients," and it composes **all** of `commandRuntime`, `spatialRuntime`, `lifeEngine`,
`digitalCitizenEngine`, `businessNetworkEngine`, `assetRuntime`, `workflowRuntime`, and
`automationEngine`. This is the closest real thing to "one semantic language shared by every
subsystem" this whole engagement has found — not at the naming level (each subsystem still uses its
own vocabulary internally), but at the **integration** level: one real runtime already reads from all
eight others. Its own real `VisualizationLayerId`/`CityVisEventName` (`SEMANTIC_DICTIONARY.md`/
`EVENT_VOCABULARY.md`, this sprint) are the closest real precedent for a canonical cross-system
vocabulary that already exists in code, not just in this documentation.

## 4. Reconciliation table (SPEC) — one row per subsystem, pointing at real code and real docs

```ts
// SPEC — a documentation index, not a new registry service.
interface SubsystemSemanticEntry {
  brief_name: string;
  real_package?: string;        // undefined for "Executive Runtime" — no real package
  canonicalEntityKinds: string[]; // subset of ENTERPRISE_ONTOLOGY.md's 19
  canonicalRelations: string[];   // subset of RELATIONSHIP_MODEL.md's 10
  docRef: string;                 // the sprint doc that already covers this subsystem in depth
}
```

## Non-goals

- No new "Executive Runtime" package — the brief's naming assumption is corrected, not implemented.
- No new integration layer — `cityVisualization` is cited as the real existing one, not extended with
  new responsibilities in this pass.

## Related documents

`docs/ENTERPRISE_ONTOLOGY.md`/`docs/RELATIONSHIP_MODEL.md`/`docs/SEMANTIC_DICTIONARY.md`/`docs/EVENT_
VOCABULARY.md` (CQ-20 siblings), `docs/EXECUTIVE_OPERATING_SYSTEM.md` (CQ-15, the real executive layer),
`docs/AUTOMATION_ENGINE.md`/`docs/DAILY_OPERATIONS_MODEL.md`/`docs/REGIONAL_DIGITAL_TWIN.md`/`docs/
DIGITAL_CITIZEN.md`/`docs/ENTERPRISE_BUSINESS_NETWORK.md`/`docs/DIGITAL_TWIN_STANDARDS.md`/`docs/
ENTITY_RECONCILIATION.md` (the per-subsystem detail docs this table indexes).
