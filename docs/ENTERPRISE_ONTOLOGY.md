# Enterprise Ontology

**Version:** `5.3.2-enterprise`  
**API:** `POST /api/enterprise-kg/v1/graph` with `action: ontology`

Ontology management, graph versioning, and master knowledge graph publication under meta bases: master · ontology · memory · entity · relationship.

## Sprint CQ-20 addition — Architecture Research + Ontology Design (documentation only, `src` not modified)

**Do not duplicate:** This stub belongs to the Sprint 19.2 `UNIFIED_KNOWLEDGE_GRAPH.md` lineage
(same `5.3.2-enterprise` version, same `/api/enterprise-kg/v1` prefix family). This engagement's
research this sprint found **four** real, sequential, self-aware "unify the knowledge model" systems —
this is the largest and most on-the-nose collision this engagement has catalogued, because unifying
vocabulary is exactly this sprint's own brief. None of the four should be replaced by a fifth; this
section extends the most complete one (Sprint 24.2) with the brief's requested entity ontology.

### The four real systems, in chronological order

| Sprint | Doc | API | Real package | Stance on prior systems |
|---|---|---|---|---|
| 12.0 | `docs/KNOWLEDGE_GRAPH.md` | `/api/ai-ecosystem/v1/knowledge` | — | "merges application knowledge registries into one global graph" |
| 19.2 | `docs/UNIFIED_KNOWLEDGE_GRAPH.md` (this doc's own lineage) | `/api/enterprise-kg/v1` | `applications/enterprise_hub/knowledge/` | "Unified... consolidating entities, relationships, and ontology across all platforms" |
| 20.3 | `docs/ENTERPRISE_KNOWLEDGE_PLATFORM.md` | `/api/enterprise-ekp/v1` | `applications/enterprise_hub/knowledge_platform/` | explicitly renamed its own package because `knowledge/` was "reserved for Sprint 19.2" |
| 24.2 | `docs/ENTERPRISE_KNOWLEDGE_GRAPH.md` | `/api/enterprise-ekg/v1` | `platform_enterprise_knowledge_graph/` | **explicitly states**: "Additive to legacy `/api/enterprise-kg/v1` and `/api/enterprise-ekp/v1`" |

Every one of the last three systems announced itself as the unifying layer, and every one chose
addition over consolidation of the one before it. This document — and this sprint's other outputs —
follow that same real precedent deliberately: a fifth addition, never a replacement.

### The recommended canonical entity/relation vocabulary — real, Sprint 24.2

`platform_enterprise_knowledge_graph/models.py` already defines real `ENTITY_TYPES` (21 values) and
`RELATION_TYPES` (14 values) — the most complete real ontology in the codebase, and the direct
foundation for `docs/RELATIONSHIP_MODEL.md`/`docs/ENTERPRISE_ONTOLOGY.md` §"Brief's nineteen kinds"
below (this sprint). A second, thinner real system also exists —
`applications/enterprise_hub/knowledge_platform/ontology.py`'s `Ontology` class with its own
`ENTITY_KINDS` (8 values) and `DEFAULT_RELATIONS` (6 values) — confirmed to be a distinct, smaller,
independently-validated vocabulary, not derived from the Sprint 24.2 one. Recommendation: build new
ontology work against the Sprint 24.2 `ENTITY_TYPES`/`RELATION_TYPES`, treating
`knowledge_platform.ontology`'s smaller vocabulary as a legacy/narrower predecessor, mirroring exactly
the "pick the most mature real system, don't add a new one" discipline established for
`DealPipelineStageCode` (CQ-18/19).

### Brief's nineteen entity kinds, mapped onto real `ENTITY_TYPES` (Sprint 24.2) plus other real subsystems

| Brief kind | Real mapping |
|---|---|
| Organization | Real `ENTITY_TYPES: "company"` — naming mismatch (brief says Organization, real says company); `BusinessProfile.organizationId` (`ENTERPRISE_BUSINESS_NETWORK.md`, CQ-10) already binds the two |
| Citizen | Real `ENTITY_TYPES: "employee"` is the closest existing value — naming mismatch against the richer real `Citizen` (Sprint 29.1, humans **and** AI assistants, `DIGITAL_CITIZEN.md`); recommend `"citizen"` as an additive `ENTITY_TYPES` value, not a rename of `"employee"` |
| Department | **Absent from `ENTITY_TYPES`** — real precedent is `CalendarEvent.department` (a string field, `BUSINESS_CALENDAR.md`, CQ-17), not a first-class entity anywhere |
| Role | **Absent from `ENTITY_TYPES`** — real precedent is `EngineRoleCode` (CQ-12), a value enum, not an entity |
| Partner | **Absent from `ENTITY_TYPES`** — closest real entities are `"customer"`/`"supplier"` (Sprint 24.2) or the richer real `BusinessProfile`/`Relationship` (Sprint 29.0, CQ-10) |
| Asset | Real `ENTITY_TYPES: "asset"` — **exact match** |
| Building | **Absent from `ENTITY_TYPES`** — real entity is `SpatialEntity: kind: "building"` (Sprint 29.4, CQ-16), a different real subsystem entirely |
| District | **Absent** — real `SpatialEntity: kind: "district"` (CQ-16), same gap as Building |
| Territory | **Absent** — real `SpatialEntity` hierarchy generally (CQ-16) |
| Vehicle | **Absent from `ENTITY_TYPES`** — real `LifeVehicle` (Sprint 29.2, CQ-17) |
| Project | Real `ENTITY_TYPES: "project"` — **exact match**, notably even though no real backend `Project` table exists yet (`PROJECT_LIFECYCLE.md`, CQ-18) — the ontology named this entity before any table backed it |
| Task | Real `ENTITY_TYPES: "task"` — **exact match** (though `ENTITY_RECONCILIATION.md`, CQ-19, found at least three independent real task tables, none of which this ontology entry distinguishes) |
| Workflow | Real `ENTITY_TYPES: "workflow"` — **exact match** (same caveat: seven real workflow engines exist, CQ-19) |
| Contract | Real `ENTITY_TYPES: "contract"` — **exact match**, though no dedicated Contract table exists (CQ-18) |
| Meeting | **Absent from `ENTITY_TYPES`** — closest real value is `"appointment"`; the richer real entity is `LifeMeeting` (Sprint 29.2, CQ-17) |
| Event | Real `ENTITY_TYPES: "event"` — **exact match** |
| Document | Real `ENTITY_TYPES: "document"` — **exact match** |
| AI Agent | Real `ENTITY_TYPES: "ai_agent"` — **exact match** |
| Automation | **Absent from `ENTITY_TYPES`** — real precedent is the Automation Engine's job registry (Sprint 28.9), not a knowledge-graph entity |

**Net finding**: 8 of 19 brief entity kinds already exist verbatim in the real Sprint 24.2 ontology; 3
exist under a different name (Organization/company, Citizen/employee, Meeting/appointment); 8 are
entirely absent from this ontology because they belong to other real subsystems (Spatial Runtime,
Life Engine, Citizen/Role model) that Sprint 24.2's knowledge graph has never ingested. Closing that
last gap — not renaming the 3 mismatches — is this sprint's actual recommendation
(`docs/CROSS_SYSTEM_SEMANTIC_MAPPING.md`, this sprint).

### Non-goals

- No fifth knowledge-graph/ontology implementation — every recommendation above extends the real
  Sprint 24.2 `ENTITY_TYPES`/`RELATION_TYPES` additively.
- No rename of `"employee"`/`"company"`/`"appointment"` in the real Sprint 24.2 enum — aliases only
  (`docs/SEMANTIC_VERSIONING.md`, this sprint).

### Related documents

`docs/KNOWLEDGE_GRAPH.md`/`docs/UNIFIED_KNOWLEDGE_GRAPH.md`/`docs/ENTERPRISE_KNOWLEDGE_PLATFORM.md`/
`docs/ENTERPRISE_KNOWLEDGE_GRAPH.md` (real, the four-system lineage), `docs/RELATIONSHIP_MODEL.md`/
`docs/SEMANTIC_DICTIONARY.md`/`docs/CROSS_SYSTEM_SEMANTIC_MAPPING.md`/`docs/EVENT_VOCABULARY.md`/
`docs/SEMANTIC_VERSIONING.md`/`docs/SPRINT_CQ_20_RESULT.md` (CQ-20 siblings), `docs/PROJECT_
LIFECYCLE.md`/`docs/ENTITY_RECONCILIATION.md` (CQ-18/19, the Project/Task/Workflow/Contract gaps
restated here from the ontology's own point of view).
