# Regional Digital Twin — Digital Twin Standards & Public/Private Layers

**Sprint:** CQ-16 — Architecture Research + Standards Design. Documentation only, `src` not modified.

**Do not duplicate:** This document's central finding is that the brief's eight standards categories
(Spatial/Business/Asset/Citizen/AI Model, Lifecycle, Permissions, Synchronization) are **not a
greenfield standard to invent** — they already exist as a consistent, repeated real architecture across
four sibling runtimes (`spatialRuntime`, `assetRuntime`, `businessNetwork`, `digitalCitizen`, all under
`src/web/src/runtime/`), each shaped as `Types → Registry → Events → Permissions → RuntimeApi → index`.
The job here is to name that convention explicitly and surface the one place it has quietly drifted:
**three real, unreconciled permission-scope vocabularies.**

## 1. Per-model mapping (brief's eight)

| Brief model | Real foundation |
|---|---|
| Spatial Model | Real `SpatialEntity`/`SpatialRelationship` (Sprint 29.4, `spatialTypes.ts`) — `REGIONAL_DIGITAL_TWIN.md` |
| Business Model | Real `BusinessProfile`/`Relationship`/`OwnershipEdge` (Sprint 29.0 + CQ-10) |
| Asset Model | Real `AssetProfile`/`AssetOwnership`/`AssetLocation` (`assetRuntime/assetTypes.ts`) — same runtime shape as Spatial Runtime, previously uncited in this engagement |
| Citizen Model | Real `Citizen`/`Membership` (Sprint 29.1, `digitalCitizen/facade.py`) |
| AI Model | **Still simulated** — real `PersonalAiAssistant` registry exists (`PERSONAL_AI.md`, CQ-12) but the broader `aiAgentRuntime` remains frontend-simulated (CG-8 finding, restated, not re-derived) |
| Lifecycle | Real, and consistently shaped: every one of the four runtimes stamps `createdAt`/`updatedAt` and a phase enum (`AssetLifecyclePhase`: `created→registered→assigned→in_use→maintenance→archived→disposed→transferred`; Spatial entities lack an explicit phase enum but the same states apply implicitly via `LocationAssignment.kind`) |
| Permissions | Real, but **three separate vocabularies** — see §2 |
| Synchronization | Real per-runtime EventBus publish (`spatial_runtime_update`, asset events, etc.) — see §3 |

## 2. The three-way permission-scope near-collision (new finding this sprint)

| Vocabulary | Real values | Where |
|---|---|---|
| `SpatialPermissionScope` | `public < citizen < company < assigned < enterprise_admin` | `spatialPermissions.ts` |
| `AssetPermissionScope` | `owner < assignee < department < company < partner < public < enterprise_admin` (note: not even internally rank-ordered the same way as Spatial's) | `assetTypes.ts:68-75` |
| `Visibility` (business) | `public \| network_only \| partners_only \| private` (SPEC, `ENTERPRISE_BUSINESS_NETWORK.md` §3.5) | — |

These are real, independently-authored, and **not identical** — `company` means "same tenant" in
`SpatialPermissionScope` but sits at a different rank relative to `partner` in `AssetPermissionScope`,
and neither has a direct equivalent of `Visibility`'s `network_only`. This is the same shape of finding
as the CQ-10 verification-tier collision (`VerificationLevel` vs `ComplianceVerificationLevel`) and the
CQ-15 Command Center collision: **flagged for a future reconciliation decision, not resolved
unilaterally here.** Recommended direction (not implemented): a single canonical
`EnterprisePermissionScope` rank that `SpatialPermissionScope`/`AssetPermissionScope` both become
type-aliases of, with `Visibility` kept as the business-specific vocabulary it already is (per
`CROSS_COMPANY_OPERATIONS.md`'s established "compose, don't merge, when the trust assumptions genuinely
differ" precedent, CQ-15) — Spatial/Asset scopes describe *who can act on a location or object*;
`Visibility` describes *what a business chooses to disclose*, a materially different question that
should stay a separate vocabulary even after Spatial/Asset are unified.

## 3. Public & Private Layers (brief §7) — composing the three vocabularies, not adding a fourth

| Brief layer | Composition |
|---|---|
| Public city information | `SpatialPermissionScope: "public"` — anyone, no auth |
| Private enterprise information | `SpatialPermissionScope: "company"` **and** `AssetPermissionScope: "company"` — same-tenant only |
| Partner-only information | `Visibility: "partners_only"` (business-relationship gate) **composed with** `AssetPermissionScope: "partner"` (object-level gate) — both must pass, per `CROSS_COMPANY_OPERATIONS.md` §2's composition discipline |
| Government integrations | **SPEC, not designed in depth** — no real government-data-sharing precedent exists in this codebase; flagged as a future scope requiring its own compliance review (parallels `ENTERPRISE_HEALTH.md` §2's explicit non-design pattern for sensitive scope) |
| Enterprise-only overlays | `SpatialPermissionScope: "enterprise_admin"` — reuses the real top rank as-is |

## 4. Synchronization (brief, standards §8)

Each real runtime publishes its own event name (`spatial_runtime_update`, asset events, etc.) onto the
one real shared `enterpriseEventBus` — synchronization infrastructure is real and already shared.
**Gap found this sprint**: none of these events carry a territory scope today, so once
`REGIONAL_DIGITAL_TWIN.md` §2's multi-city seeding is real, every subscriber receives every city's
events unfiltered. Recommend an additive `territoryId` field on published event payloads (all four
runtimes already carry an `entityId`/`cityBuildingId` that can populate it) — a payload field addition,
not a new bus.

## Non-goals

- No new runtime — this document names the standard four runtimes already follow; it does not add a
  fifth.
- No unification of the three permission vocabularies performed in this pass — recommendation only,
  per §2, exactly like every prior sprint's "flag, don't silently merge" discipline.
- No government-integration design — explicitly out of scope pending a real compliance review.

## Related documents

`docs/SPATIAL_RUNTIME.md` (real, Sprint 29.4), `docs/PERSONAL_AI.md`/`docs/CITIZEN_ORGANIZATION_
MEMBERSHIP.md` (CQ-12), `docs/ENTERPRISE_BUSINESS_NETWORK.md` §3.5 (CQ-10, real `Visibility`),
`docs/CROSS_COMPANY_OPERATIONS.md` (CQ-15, the composition discipline reused in §3),
`docs/ENTERPRISE_HEALTH.md` §2 (CQ-15, the non-design precedent for sensitive scope),
`docs/REGIONAL_DIGITAL_TWIN.md`/`docs/TERRITORIAL_GOVERNANCE.md` (CQ-16 siblings).
