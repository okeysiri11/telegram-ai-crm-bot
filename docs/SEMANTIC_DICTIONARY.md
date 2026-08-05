# Enterprise Semantic Model — Semantic Dictionary & City Semantics

**Sprint:** CQ-20 — Architecture Research + Ontology Design. Documentation only, `src` not modified.

**Do not duplicate:** Every preferred term below is chosen because it already has the most real
backing across this engagement's research — this document does not invent new preferred terms, it
picks winners among terms already in real use and records the losers as aliases
(`docs/SEMANTIC_VERSIONING.md` §2, this sprint, defines how aliases are carried forward).

## 1. Canonical dictionary (brief's six examples, plus the mismatches `ENTERPRISE_ONTOLOGY.md` found)

| Synonym pair | Preferred term | Why |
|---|---|---|
| Company / Organization | **Company** | Real `ENTITY_TYPES: "company"` (Sprint 24.2) and real `BusinessProfile` (Sprint 29.0) both use Company; `organizationManager`/`organizationId` remain real but as a binding field, not the preferred entity name |
| Worker / Citizen | **Citizen** | Real `Citizen` (Sprint 29.1, `DIGITAL_CITIZEN.md`) is deliberately broader than "Worker" — covers humans **and** AI assistants; `ENTITY_TYPES: "employee"` is the narrower, older real term, recommended as an alias, not the preferred one |
| Building / Facility | **Building** | Real `SpatialEntity: kind: "building"` (Sprint 29.4, CQ-16) and real `CityBuilding` (`cityCatalog.ts`) both use Building; "Facility" has no real precedent anywhere in this codebase |
| Workflow / Process | **Workflow** | Real across all seven engines (`ENTITY_RECONCILIATION.md` §3, CQ-19); "Process" is reserved for the canonical stage vocabulary itself (`CanonicalStage`, CQ-19) — using it for Workflow too would collide with a term this engagement already assigned a specific meaning |
| Deal / Opportunity | **Deal** | Real across all six pipeline systems (CQ-18); "Opportunity" is the canonical **stage name** (`CanonicalStage: "opportunity"`, CQ-19) for the deal's *earliest* stage, not a synonym for the whole entity — a scope distinction, not a straightforward alias |
| Project / Engagement | **Project** | Real `ENTITY_TYPES: "project"` (Sprint 24.2) and the SPEC `Project` entity (`PROJECT_LIFECYCLE.md`, CQ-18); "Engagement" has no real precedent |

## 2. Additional mismatches found this sprint (from `ENTERPRISE_ONTOLOGY.md`)

| Synonym pair | Preferred term | Why |
|---|---|---|
| Meeting / Appointment | **Meeting** | Real `LifeMeeting` (Sprint 29.2, CQ-17) is the richer, more current real entity; `ENTITY_TYPES: "appointment"` (Sprint 24.2) is the older, narrower real term |
| Employee / Citizen (again) | **Citizen** | Restated from §1 — the ontology's own `"employee"` value is the one recommended for alias status, not deprecation, since it is still real and queried |

## 3. City Semantics (brief §6) — real `VisualizationLayerId`, extended for the two gaps found

`src/web/src/runtime/cityVisualization/cityVisualizationTypes.ts`'s real `VisualizationLayerId`
(Sprint 29.5): `districts | buildings | citizens | companies | assets | activities | traffic |
overlays` — already covers six of the brief's eight items almost verbatim:

| Brief item | Real `VisualizationLayerId` |
|---|---|
| Buildings | `"buildings"` — exact |
| Districts | `"districts"` — exact |
| Organizations | `"companies"` — preferred-term alias of Organization, per §1 |
| Citizens | `"citizens"` — exact |
| Assets | `"assets"` — exact |
| Projects | `"activities"` is the closest real layer — no dedicated `"projects"` layer exists, consistent with `Project`'s SPEC-only backend status (`PROJECT_LIFECYCLE.md`, CQ-18) |
| Vehicles | `"traffic"` is the closest real layer — vehicles render as traffic-flow markers (`CITY_VISUAL_STATES.md`, CG-9), not a dedicated vehicle layer |
| Infrastructure | `"overlays"` is the closest real layer — consistent with `SMART_INFRASTRUCTURE.md`'s (CQ-16) finding that most infrastructure categories remain thin |

No new `VisualizationLayerId` value is proposed — the two partial matches (Projects→activities,
Vehicles→traffic) are accurate renderings of real, already-thinner backing, not naming gaps to fix.

## Non-goals

- No renaming of any real enum value (`"employee"`, `"appointment"`, `"company"`) — every preferred
  term above is a documentation-level dictionary entry, not a migration.
- No new `VisualizationLayerId` values — the real eight-layer set is reused as-is.

## Related documents

`docs/ENTERPRISE_ONTOLOGY.md` (CQ-20 sibling, the mismatches this dictionary resolves),
`docs/CANONICAL_PROCESS_MODEL.md`/`docs/ENTITY_RECONCILIATION.md` (CQ-19, `CanonicalStage`'s
"opportunity"/"process" terms this dictionary defers to), `docs/SEMANTIC_VERSIONING.md` (CQ-20
sibling, how aliases persist), real `cityVisualizationTypes.ts` (Sprint 29.5).
