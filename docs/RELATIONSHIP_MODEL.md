# Enterprise Semantic Model — Relationship Model

**Sprint:** CQ-20 — Architecture Research + Ontology Design. Documentation only, `src` not modified.

**Do not duplicate:** `platform_enterprise_knowledge_graph/models.py`'s real `RELATION_TYPES` (14
values, Sprint 24.2, `ENTERPRISE_ONTOLOGY.md`'s recommended canonical) already covers four of the
brief's ten relationship verbs verbatim. This document maps the remaining six onto the real
relationship vocabularies of other subsystems (Spatial Runtime, Business Network, Digital Citizen)
rather than growing `RELATION_TYPES` to cover concepts it was never designed to hold.

## 1. Per-verb mapping (brief's ten)

| Brief verb | Real mapping |
|---|---|
| owns | Real `RELATION_TYPES: "owns"` — **exact match** |
| belongs_to | Real `RELATION_TYPES: "belongs_to"` — **exact match** |
| located_in | **Absent from `RELATION_TYPES`** — real precedent is `SpatialRelationKind: "inside"`/`"contains"` (Sprint 29.4, CQ-16), a structurally different real vocabulary (spatial containment, not knowledge-graph relation) |
| works_for | **Absent** — real precedent is `Membership` (Sprint 29.1, CQ-12) — an entity with a `role` field, not a named relation verb |
| assigned_to | Real `RELATION_TYPES: "assigned_to"` — **exact match**; also literally the real column name on `Task`/`DealTask` (`ENTITY_RECONCILIATION.md` §2, CQ-19) |
| operates | **Absent** — closest real precedent is `TERRITORIAL_GOVERNANCE.md`'s (CQ-16) Infrastructure Operator role, itself a `Membership.role` value, not a relation verb |
| collaborates_with | **Absent** — real precedent is `CollaborativeSession` (Sprint 28.8, `ENTERPRISE_WAR_ROOM.md` §0, CQ-15) — a session entity, not a named relation |
| controls | **Absent from `RELATION_TYPES`** — real precedent is `OwnershipEdge.kind: "holding_subsidiary"` with `ownershipPct` (`EBN_BUSINESS_GRAPH.md`, CQ-10) — a richer real relation than a plain verb, carries a percentage |
| depends_on | Real `RELATION_TYPES: "depends_on"` — **exact match**; also the literal term `ARCHITECTURE_MAP.md` §11 already uses for governed module dependency direction — the same word means two different real things (entity relation vs. code-module dependency), worth noting as a scope distinction, not a collision |
| manages | Real `RELATION_TYPES: "managed_by"` (inverse form already exists) — recommend `manages` as the forward alias, not a new relation |

## 2. `CanonicalRelation` (SPEC) — a thin wrapper, not a new relation engine

```ts
// SPEC — every canonical relation resolves to one real subsystem's own relation record.
// No relation is ever stored twice.
interface CanonicalRelation {
  verb: "owns" | "belongs_to" | "located_in" | "works_for" | "assigned_to"
      | "operates" | "collaborates_with" | "controls" | "depends_on" | "manages";
  realSource: "knowledge_graph.RELATION_TYPES" | "spatialRegistry.SpatialRelationKind"
            | "Membership" | "CollaborativeSession" | "OwnershipEdge";
  fromEntityId: string;
  toEntityId: string;
}
```

`located_in`/`works_for`/`operates`/`collaborates_with`/`controls` are **not** proposed as new
`RELATION_TYPES` values — each already has a real, more specific home (spatial containment, org
membership, a governance role, a session, a percentage-carrying ownership edge respectively) that
would lose information if flattened into a generic knowledge-graph relation.

## Non-goals

- No growth of `RELATION_TYPES` for the six non-matching verbs — each keeps its real, more specific
  home.
- No merge of `ARCHITECTURE_MAP.md`'s code-dependency sense of "depends_on" with the entity-relation
  sense — different scope, same word, noted not conflated.

## Related documents

`docs/ENTERPRISE_ONTOLOGY.md` (CQ-20 sibling, real `ENTITY_TYPES`/`RELATION_TYPES` and the four-system
knowledge-graph lineage), `docs/REGIONAL_DIGITAL_TWIN.md` (CQ-16, real `SpatialRelationKind`),
`docs/CITIZEN_ORGANIZATION_MEMBERSHIP.md` (CQ-12, real `Membership`), `docs/ENTERPRISE_WAR_ROOM.md`
(CQ-15, real `CollaborativeSession`), `docs/EBN_BUSINESS_GRAPH.md` (CQ-10, real `OwnershipEdge`),
`docs/CROSS_SYSTEM_SEMANTIC_MAPPING.md` (CQ-20 sibling).
