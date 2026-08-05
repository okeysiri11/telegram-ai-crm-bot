# 04 — Enterprise City (Chapter Summary)

**Chapter of the Master Product Bible.** The complete specification is `ENTERPRISE_CITY.md` (23
sections, both shipped-2D detail and 3D vision) — this chapter is a connecting summary, not a
duplicate. Read `ENTERPRISE_CITY.md` directly for anything beyond what's summarized here.

## What it is, in one line

Enterprise City is the spatial visual representation of the platform: buildings are real modules,
state reflects live data, every click is a real navigation — never a game, never decoration
(`ENTERPRISE_CITY.md` §0).

## Why it's in the Bible as its own chapter

Enterprise City is the platform's clearest embodiment of `02_PRODUCT_PHILOSOPHY.md` principle 9 (the
platform visualizes what exists, never gets ahead of itself) and principle 3 (calm, not decorative) —
it is worth a dedicated chapter because it is the single feature most likely to be misunderstood as a
gimmick by someone who hasn't read the full spec, and the Bible's job is to prevent that
misunderstanding at the first point of contact.

## The shape of the full specification

| Section range | Covers |
|---|---|
| §1–§6 | Vision, philosophy, why it exists, relationship to Dashboard/Workspace/AI Agents |
| §7 | The two modes: 2D (shipped, real) and 3D (vision, not implemented) |
| §8–§12 | Districts, Buildings, Departments, Enterprises, Portals — the structural vocabulary |
| §13–§19 | Transportation, zoom levels, minimap, interaction model, camera behavior, animations |
| §20–§22 | In-City navigation, workflow visualization, growth mechanics |
| §23 | The scaling model: small company → holding → international enterprise → government → ecosystem |

## The one fact worth repeating in every summary

**Every building in the City maps to one real, already-navigable route.** This rule (`ENTERPRISE_
CITY.md` §2.3, §9's "Rule for all future buildings") is what separates the City from a decorative map —
it is checked against reality in the full spec's §9.1 (15 shipped buildings, real routes) versus §9.2
(proposed buildings, explicitly labeled as not yet built).

## The scaling model, because it is this document's core original contribution

Five tiers — small company, holding, international enterprise, government, ecosystem
(`ENTERPRISE_CITY.md` §23) — served by the same building/district/status data model at every tier, via
two structural concepts introduced specifically to make that possible: **Enterprises** (a city-of-cities
view for multi-entity tenants, §11) and **Portals** (governed gateways between separate organizations'
cities, §12). No tier requires new backend architecture — this is a rendering and organization
question over one platform capability model, which is the direct application of `02_PRODUCT_
PHILOSOPHY.md` principle 2 to the spatial-navigation domain.

## Status honesty

2D mode, 15 buildings, districts, live status, workflow routes, and the interaction model are **real
and shipped**. 3D mode, Departments, Enterprises, Portals, and the full scaling model are **vision** —
designed, not built. `10_ROADMAP.md` sequences when the vision material becomes real, governed by
`CLAUDE.md`'s explicit rule that City work is gated behind platform-module completion.

## Related chapters

`03_ENTERPRISE_OS.md` (the City as the OS's spatial desktop), `06_DESIGN_LANGUAGE.md`/
`07_DESIGN_SYSTEM.md` (the City inherits, never reinvents, the platform's visual/motion canon),
`08_AI_PERSONALITY.md` (the City's AI building-focus hints use the one Executive Advisor voice).
