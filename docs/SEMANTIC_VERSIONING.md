# Enterprise Semantic Model — Versioning & Evolution Strategy

**Sprint:** CQ-20 — Architecture Research + Governance Design. Documentation only, `src` not modified.

**Do not duplicate:** `CLAUDE.md`'s own binding principle — "Never break existing APIs... Additive
changes only" — already governs this exactly. The real Sprint 24.2 knowledge graph's own self-description
("Additive to legacy `/api/enterprise-kg/v1` and `/api/enterprise-ekg/v1`") is the platform's own
precedent for everything in this document. Nothing here is a new policy; it is this sprint's semantic
vocabulary applying a rule this repo already lives by.

## 1. Per-item strategy (brief's five)

| Brief item | Strategy |
|---|---|
| Backward Compatibility | No real enum value, column, or API prefix is ever renamed by adopting the canonical vocabulary (`ENTERPRISE_ONTOLOGY.md`/`RELATIONSHIP_MODEL.md`, this sprint) — every canonical term is a read-projection lookup, exactly as `CANONICAL_PROCESS_MODEL.md` §1 (CQ-19) already established for `CanonicalStage` |
| Deprecation | A real term (e.g. `ENTITY_TYPES: "employee"`, `AssetEventName`'s absent `Deleted`) is never removed by this model — it is marked `preferred: false` in the dictionary (`SEMANTIC_DICTIONARY.md`, this sprint) and left running |
| Aliases | Every synonym pair in `SEMANTIC_DICTIONARY.md` §1–2 **is** the alias mechanism — `"employee"`↔`"citizen"`, `"appointment"`↔`"meeting"`, `"Finished"`↔`"Completed"` (`EVENT_VOCABULARY.md` §2) all resolve through the same lookup, never a code branch |
| Migration | Follows `SPRINT_CQ_19_RESULT.md`'s (CQ-19) four-phase incremental pattern exactly: Phase 0 lookup tables only, Phase 1 additive fields/bridges, Phase 2 new entities, Phase 3 explicit, documented, human-decided consolidation — never automatic |
| Extensions | A new vertical or subsystem registers new `ENTITY_TYPES`/`RELATION_TYPES`/event-suffix values additively, exactly as `CROSS_VERTICAL_EXTENSIONS.md`'s (CQ-19) `module` discriminator pattern already established for `Deal`/`CalendarEvent` |

## 2. `SemanticAlias` (SPEC) — the one new structure this document proposes

```ts
// SPEC — a lookup row, not a rename. Powers every alias relationship named across this sprint's docs.
interface SemanticAlias {
  preferredTerm: string;      // e.g. "citizen"
  aliasTerm: string;           // e.g. "employee"
  scope: "entity_kind" | "relation" | "event_suffix" | "canonical_stage";
  deprecatedSince?: string;     // ISO date — set only if the alias is being phased toward removal;
                                 // absent means "permanent alias," not "temporary tolerance"
}
```

Most aliases in this sprint's documents (`"employee"`, `"appointment"`, `"Finished"`) are **not**
marked for eventual removal — they remain real, queried values in production tables. `SemanticAlias`
defaults to permanence; `deprecatedSince` is the exception, not the rule, matching this platform's own
observed behavior (the Sprint 19.2/20.3 knowledge-graph APIs are still live years after Sprint 24.2
superseded them in completeness).

## 3. Versioning the canonical model itself

The canonical vocabulary documents (`ENTERPRISE_ONTOLOGY.md`, etc.) are themselves versioned the same
way every other sprint's docs are — by sprint number in the file header, per this engagement's own
established convention — not by a semver number on the vocabulary. Adding `"technology_park"` to
`SpatialDistrictKind` (CQ-16) or `"process_created"` to `LifeEventKind` (CQ-19) are both real precedents
for how this vocabulary grows: additive enum values, documented in the sprint that added them, never a
breaking rewrite.

## Non-goals

- No semver scheme for the ontology — sprint-numbered documentation versioning is reused, per
  `CLAUDE.md`'s own convention.
- No automatic deprecation/removal process — every alias defaults to permanent unless a future sprint
  explicitly marks `deprecatedSince`.
- No new migration tooling — `SPRINT_CQ_19_RESULT.md`'s four-phase pattern is reused exactly.

## Related documents

`docs/ENTERPRISE_ONTOLOGY.md`/`docs/SEMANTIC_DICTIONARY.md`/`docs/EVENT_VOCABULARY.md`/`docs/
RELATIONSHIP_MODEL.md`/`docs/CROSS_SYSTEM_SEMANTIC_MAPPING.md` (CQ-20 siblings), `docs/SPRINT_
CQ_19_RESULT.md` §7 (CQ-19, the four-phase migration strategy reused here), `docs/CROSS_VERTICAL_
EXTENSIONS.md` (CQ-19, the `module` extension pattern reused for Extensions).
