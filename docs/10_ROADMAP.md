# 10 — Roadmap & Long-Term Platform Evolution

**Chapter of the Master Product Bible.** This chapter synthesizes every "vision," "designed," and
"proposed" section across the full documentation set into one sequenced view — it does not introduce
new scope, it orders scope that already exists in `TECH_DEBT.md`, `ENTERPRISE_CITY.md`,
`AI_PRODUCTION_STUDIO.md`, `ENTERPRISE_NAVIGATION.md`, and `WORKSPACE_INTERACTIONS.md`. Nothing here
should be read as a committed schedule with dates — it is a priority ordering, not a project plan.

## Reality update (Sprint 27.7–27.9) — read before trusting any "designed, not built" label below

A real implementation track, running in parallel with this documentation set, has already shipped a
meaningful slice of what this roadmap originally filed under Horizon 2/3 as speculative:

- **Enterprise Desktop OS shell** — real window management (move/resize/minimize/maximize/snap/reopen-
  closed), a real Dock, a real Launcher, session-persisted (`DESKTOP.md`, `WINDOW_MANAGER.md`). This
  was not explicitly itemized anywhere in the original Horizon 2/3 list below — it arrived from the
  real engineering track ahead of this roadmap's own sequencing, and is a stronger, more literal
  realization of "one operating system" (`03_ENTERPRISE_OS.md`) than this roadmap anticipated this
  soon.
- **Enterprise City restructured** — a real camera/viewport engine with session persistence
  (`CITY_ENGINE.md`), a real 12-district catalog (`CITY_DISTRICTS.md`, up from 5), and real
  `localStorage`-persisted navigation memory (history/recent/favorites/breadcrumbs, `cityNavigation.ts`)
  — this is real, partial progress on Horizon 3 item 2 below (district structure growing toward this
  Bible's vision taxonomy), achieved in 2D, without needing 3D mode at all.
- **AI Production Center frontend shell** — a real 17-studio catalog, a real approval-gated pipeline
  model, real Prompt/Media catalogs, real automation/queue UI, all reusing `platform_jobs` rather than
  duplicating it (`AI_PRODUCTION_CENTER_BIBLE.md`). **This does not move Horizon 2 items 1–3 below to
  "done"** — the actual generation providers, real publishing, and real Brand Library remain exactly as
  absent as before; only the navigation/orchestration shell around them is now real.

**Net effect on this roadmap:** treat every "Horizon 2/3" item below as still accurate for its stated
scope, but check `AI_PRODUCTION_CENTER_BIBLE.md` §0/§9, `ENTERPRISE_CITY_BIBLE.md` §2, and
`03_ENTERPRISE_OS.md` before assuming any specific item is still unbuilt — several structural
prerequisites this roadmap expected to build *toward* Horizon 2 work are now already in place, which
should accelerate items 2–4 below rather than requiring them to also build their own navigation shell
first.

## How to read this roadmap

Three horizons, ordered by dependency rather than calendar time: **fix what's cracked** (things that
undermine a principle the platform already claims to hold), **build what's designed** (real, specified,
not-yet-built product surfaces), and **grow what scales** (the multi-year ambition from `01_VISION.md`).
A later horizon's work generally assumes an earlier horizon's fixes are in place — building the Studio's
publishing layer on a still-fragmented navigation model, for instance, would just add a third
inconsistency to the two Navigation already tracks.

## Horizon 1 — Fix what's cracked

The platform's own tracked debt, prioritized by how directly each item undermines a stated principle
(`02_PRODUCT_PHILOSOPHY.md`):

1. **Fix the 4 critical CI-blocking architecture violations** (`platform_security` bypassing
   `ConfigurationCenter`, `TECH_DEBT.md` TD-17) — lowest effort, highest-confidence fix available in the
   entire registry.
2. **Retire the orphaned Command Palette** (`TECH_DEBT.md` TD-40) — the single clearest gap between
   the "one operating system" claim (`03_ENTERPRISE_OS.md`) and shipped reality.
3. **Unify favorites/recent-history** (`TECH_DEBT.md` TD-41) into one persisted system, extending the
   same `localStorage` mechanism the Dock already uses successfully.
4. **Stop `database/__init__.py`'s import of `database_legacy`** (`TECH_DEBT.md` TD-19) — closes the one
   concrete leak in the legacy-isolation boundary that's supposed to prevent modern code from depending
   on the legacy monolith.
5. **Generalize the tab bar's interaction primitives** (drag-and-drop, context menu, one-level
   history) into shared, reusable components (`TECH_DEBT.md` TD-42, `WORKSPACE_INTERACTIONS.md` §1,
   §5, §14) — **partially advanced** by the real Enterprise Desktop's window manager (real move/resize/
   minimize/maximize/snap, `WINDOW_MANAGER.md`), which is a second, independent real precedent for
   "drag/manage" interactions beyond the tab bar. This still does not close TD-42 — widget drag-and-drop,
   a general-purpose context menu, and a real undo/redo history remain unbuilt — but a future
   generalization pass now has two real patterns (tab bar + window manager) to draw from instead of one.

## Horizon 2 — Build what's designed

The large, specified-but-not-built product surfaces, roughly in the order their dependencies suggest:

1. **Real publishing behind `CrossPostingEngineV1`** (`AI_PRODUCTION_STUDIO.md` §26) — replacing
   simulated publish/analytics with real TikTok/Instagram/Facebook/Telegram API clients, then adding
   YouTube and LinkedIn as new channel types. Sequenced first among Studio work because every other
   Studio module (Reels, Social Content Studio, Marketing Campaign automation) is only as valuable as
   what it can actually publish to.
2. **The core generation modalities** (Image, Video, Voice, Avatar Production — `AI_PRODUCTION_STUDIO.md`
   §4–§7) — the provider architecture extension (§3) that every other Studio module depends on.
3. **Brand Library, Prompt Library, Asset Versioning** (§14–§15, §17) — the substrate the generation
   modalities and every downstream Studio feature need before they can be governed and traceable.
4. **Approval Workflow extended to every new asset type** (§25) — must land alongside, never after, the
   generation modalities above; this is `02_PRODUCT_PHILOSOPHY.md` principle 6 made schedulable.
5. **Persistent workspace/widget layouts** (`WORKSPACE_INTERACTIONS.md` §19) — extending the Dock's
   real persistence mechanism to dashboard/widget layout, closing the gap where `layoutManager`
   currently only simulates saving.
6. **Undo/redo, built on a real action-history log** (`WORKSPACE_INTERACTIONS.md` §14–§15) — the
   platform's largest single missing interaction primitive, deliberately scoped to exclude anything
   already published externally.
7. **Voice navigation and the AI Director** (`ENTERPRISE_NAVIGATION.md` §19, `AI_PRODUCTION_STUDIO.md`
   §20) — both are designed as thin layers over real existing machinery (the AI mode's NLU parser;
   `platform_planning`'s real plan/route engine) rather than new engines, which is what makes them
   Horizon 2 rather than Horizon 3 work.
8. **3D Asset Generator and UI Generator** (`AI_PRODUCTION_STUDIO.md` §10–§11) — the two Studio modules
   with the least existing precedent to build on (confirmed zero real geometry generation and
   catalog-only UI assembly today), sequenced last within this horizon because they carry the most
   open technical risk.

## Horizon 3 — Grow what scales

The long-term ambition from `01_VISION.md`, explicitly gated:

1. **Enterprise City 3D mode** (`ENTERPRISE_CITY.md` §7.2) — building the discrete zoom-level system
   (§14), volumetric district massing, and camera behavior (§18) once 2D's building catalog has grown
   enough (Horizon 2's platform-module growth) to justify it.
2. **Departments, Enterprises, Portals** (`ENTERPRISE_CITY.md` §10–§12) — the structural vocabulary for
   holding-company and multi-organization scale, built once real multi-vertical/multi-entity tenants
   exist to design against, not speculatively ahead of them. **Precedent already landed in 2D**: the
   district catalog itself grew from 5 to 12 real districts (`CITY_DISTRICTS.md`) without needing 3D —
   Departments/Enterprises/Portals are the next layer of that same growth pattern, not a 3D-only
   concern; they can and should be attempted in 2D first, exactly as districting itself was.
3. **The full five-tier scaling model** (`ENTERPRISE_CITY.md` §23) — small company through ecosystem —
   is the platform's multi-year horizon, not a near-term deliverable; it is included in the Bible now so
   every earlier decision (building catalog structure, permission model, City districting rules) is made
   compatible with it from the start, per `01_VISION.md`'s "same product at every scale" test.
4. **Live collaboration, presence, and cursor sharing** (`WORKSPACE_INTERACTIONS.md` §20–§23) —
   deliberately sequenced last: it is the newest, least-precedented category in the entire documentation
   set (zero existing code to extend), and its value compounds most once City/Studio/Workspace are
   mature enough to have something worth collaborating on together.

## The one gating rule that governs all three horizons

`CLAUDE.md`'s explicit rule — **Enterprise City is sequenced after platform-module completion** — is
restated here as the roadmap's master constraint: Horizon 3's City work (and by direct extension, any
Studio or Workspace feature whose primary showcase is the City) should not pull effort away from
Horizon 1/2's platform-module and governance work. This is not a statement that City/Studio ambition is
low priority — it is a statement about *sequencing*, made explicit so a future sprint doesn't
misread this Bible's enthusiasm for the vision chapters as license to build them ahead of the
foundation they depend on.

## How this roadmap should be maintained

Per `CLAUDE.md`'s sprint-closeout rule: any sprint that completes a Horizon-1 item should update
`TECH_DEBT.md` first (moving the item to resolved), then this chapter (removing it from Horizon 1).
Any sprint that begins Horizon-2/3 work should add a line to this chapter noting it's in progress,
so this roadmap never silently drifts out of sync with the sprint `RESULT.md` records that are the
platform's actual source of truth for what has shipped.

## Related chapters

`00_MASTER_PRODUCT_BIBLE.md` (documentation gaps and recommendations, which feed this roadmap's own
future revisions), `TECH_DEBT.md` (the living registry Horizon 1 is drawn from directly), every other
numbered chapter (each names its own "status honesty" section, which is this roadmap's raw material).
