# The AI Production Center Bible

**Status:** the canonical, highest-level design authority for the AI Production Center. Documentation
only — no source code should be modified as a result of reading this document. Sits above
`PRODUCTION_CENTER.md`, `PRODUCTION_AUTOMATION.md`, `AI_PRODUCTION_CENTER_ARCHITECTURE.md`,
`PROMPT_LIBRARY.md`, `MEDIA_MANAGER.md` (the real Sprint 27.9 implementation references) and
`AI_PRODUCTION_STUDIO.md` (this platform's original 28-section vision spec). Where this document and a
subordinate spec disagree, this document wins; the subordinate specs should be updated to match.

```
AI_PRODUCTION_CENTER_BIBLE.md      ← this document. Canonical authority.
        │
        ├── AI_PRODUCTION_CENTER_ARCHITECTURE.md   ← real Sprint 27.9 architecture
        │         ├── PRODUCTION_CENTER.md                  ← real UI/section spec
        │         ├── PRODUCTION_AUTOMATION.md               ← real automation/queue spec
        │         ├── PROMPT_LIBRARY.md                      ← real creative prompt library
        │         └── MEDIA_MANAGER.md                       ← real media/asset catalog
        │
        └── AI_PRODUCTION_STUDIO.md          ← the original 28-section vision spec (generation,
                                                 brand kit, real publishing) — mostly still vision
```

## 0. The single most important fact in this document

**The Production Center's navigation/orchestration shell is real and shipped. The AI generation
underneath it is not.** Sprint 27.9 built a genuine, well-scoped frontend: 17 studio cards, a real
approval-gated pipeline model, real prompt/media catalogs, real automation/queue UI — all client-side,
all reusing existing platform surfaces rather than duplicating them
(`AI_PRODUCTION_CENTER_ARCHITECTURE.md`'s own explicit non-duplication list: AI Builder Studio's agent
prompts, Platform Builder's rendering/asset engines, and `platform_jobs`/`platform_workflows` backend
engines are all named as things this Center does *not* replace). What it does **not** yet have, because
nothing in the backend provides it: a real image/video/voice/avatar generation provider, a real
Content Factory HTTP route, or a real (non-simulated) social-publish trigger — the exact gap
`AI_PRODUCTION_STUDIO.md` §0 already documented and nothing since has closed. **Every studio card in
the real Production Center today is a real, working piece of UI around a generation step that is not
yet real.** This is not a criticism of the implementation — it is disciplined, honest scaffolding built
exactly the way `02_PRODUCT_PHILOSOPHY.md` principle 9 asks for (visualize what exists, never fake what
doesn't) — but every future sprint touching this Center must know which half is which.

## 1. Vision

The AI Production Center is the creative content OS of ADOS — the one place an idea becomes a finished,
governed, published piece of content, with a full record of what prompted it, who approved it, and
where it went. It is explicitly **not** a second platform (`AI_PRODUCTION_CENTER_ARCHITECTURE.md`'s own
principle): it is a navigation and orchestration layer over capability that mostly already exists
elsewhere in ADOS (Workflow Center, AI Runtime, AI Builder, Concierge, Themes, Assets, Documents,
Analytics, the Automation hub) plus, eventually, real generation providers this Bible's vision layer
(`AI_PRODUCTION_STUDIO.md`) specifies in full.

## 2. Architecture position (real, shipped)

| Layer | Real file | Role |
|---|---|---|
| Catalog | `productionCatalog.ts` | 17 studios + pipeline stage definitions |
| Store | `productionStore.ts` | Session state, `ews_ai_production_v1` |
| Shell | `AIProductionCenterPage.tsx` | Tab chrome: Studios / Pipeline / Prompts / Media / Automation |
| Studios | `StudioWorkspace.tsx` (lazy) | Per-studio workspace, one component parameterized by studio id |

**Routes:** `/production-studio` (canonical), alias `/production`. Deep links: `?studio=reels`,
`?tab=pipeline|prompts|media|automation`. Reachable from three places, per the platform's "one pattern,
many adopters" rule (`02_PRODUCT_PHILOSOPHY.md` principle 7): the Enterprise Desktop's Launcher/Dock
(Production / Reels / Ads / Prompt Studio apps, `DESKTOP.md`), the Enterprise City's Production
district (`ENTERPRISE_CITY_BIBLE.md` §2, §3), and direct navigation.

## 3. The 17 studios (real catalog, not-yet-real generation)

Image · Video · Audio · Voice · Avatar · Reels · Ads · Creative · Prompt · Brand · Asset Library ·
Template Center · Media Storage · Render · Publishing · Scheduler · Analytics
(`AI_PRODUCTION_CENTER_ARCHITECTURE.md`). Each is a real, navigable card with real agent-assignment UI
(`PRODUCTION_CENTER.md`: "Studios: 17 studio cards · agent assignment") — assigning an agent to a studio
is real state; the agent actually performing generation work in that studio is not, for the same reason
named in §0. `AI_PRODUCTION_STUDIO.md` §§4–13 remain the authoritative **vision** design for what each
studio should do once real providers exist — read this Bible for status, that document for target
design.

## 4. Pipeline (real model, governed by design)

`Draft → Review → Approval → Generation → Render → Publish → Archive`
(`AI_PRODUCTION_CENTER_ARCHITECTURE.md`). **The hard rule is enforced structurally, not just in
documentation: AI never publishes alone — an Approval stage is required before Publish.** This is the
single most important governance fact carried over unchanged from `AI_PRODUCTION_STUDIO.md` §2/§25,
and its presence in the real, shipped pipeline model (not merely this Bible's prose) is exactly the
outcome that principle was written to guarantee.

## 5. Automation & Production Queue (real UI, reused backend)

`PRODUCTION_AUTOMATION.md` states the architecture rule plainly: **"UI models jobs for creative
pipelines. Execution substrate remains `platform_jobs` (backend), AI Runtime/Workflow Center (existing
UI), Notification store. No second job engine."** This is `02_PRODUCT_PHILOSOPHY.md` principle 2
(extension over replacement) enforced at the exact point `AI_PRODUCTION_STUDIO.md` §23 predicted it
should be — the real `platform_jobs.JobEngine` (confirmed real: `JobType`, `JobState`, priority, a real
worker pool, and a real generic enqueue REST route) is the correct substrate, and the real
implementation used it rather than inventing a parallel queue. Jobs may reference a `pipelineId`;
publish schedules still require the Approval stage (§4) — automation controls *when*, never *whether*
a human reviews.

## 6. Prompt Library (real, correctly distinguished from a different existing library)

Real, session-store-backed (`useProductionStore.prompts`, `ews_ai_production_v1`), with categories,
versioning/history, favorites, search, tags, and template variables (`{{product}}`). Explicitly and
correctly distinguished in its own doc from AI Builder Studio's unrelated agent-prompt library — the
exact distinction `AI_PRODUCTION_STUDIO.md` §15 specified in advance. Named future work
(`PROMPT_LIBRARY.md`): semantic search via `platform_memory`, a shared corporate vault, a provider-side
evaluation harness — all still vision.

## 7. Media Manager (real catalog, explicitly not real storage)

Supports Images/Video/Audio/Documents/Templates/Brand Assets/Fonts/Icons/Animations as a real,
filterable, versioned-badge client catalog. Its own doc states its non-goals as plainly as this Bible
insists on: **"real blob storage · GPU render thumbnails · CDN publish"** are explicitly out of scope
for this sprint — this is the same status-honesty discipline this Bible itself is built on, arriving
independently in the implementation's own documentation, which is a good sign the discipline is
actually shared, not just written down in one place. Reuses Documents hub for storage destinations and
references (not duplicates) Platform Builder's Asset Registry for *visual UI* assets — correctly
treating that registry as a different asset class, exactly as `AI_PRODUCTION_STUDIO.md` §0 flagged.

## 8. Enterprise Desktop & City integration (real)

- **Desktop:** Production / Reels / Ads / Prompt Studio apps are real Launcher/Dock entries, opening
  `/production-studio` (embed-ready via `?embed=1`, `WINDOW_MANAGER.md`'s embed contract).
- **City:** the Production district's buildings deep-link into specific studios
  (`ENTERPRISE_CITY_BIBLE.md` §3's Production District flagship building entry, now real rather than
  proposed).
- **Workflow Center:** a `creative_campaign` template exists as the bridge into the platform's real
  workflow engine.
- **Status chips:** Notifications/runtime health surface in the Center's own chrome, reusing the real
  notification store rather than a Center-specific status system.

## 9. What genuinely remains vision (unchanged from `AI_PRODUCTION_STUDIO.md`)

Nothing in Sprint 27.9 closed the core gap `AI_PRODUCTION_STUDIO.md` §0 identified. Still absent,
platform-wide, as of this writing:

- Any real image/video/voice/avatar/3D generation provider (`platform_ai`'s registry remains
  text-only-LLM).
- Any real HTTP trigger for Content Factory generation.
- Any real (non-simulated) publish call behind Cross-Posting, or any real YouTube/LinkedIn channel
  integration.
- A real Brand Library, Style Presets gallery, or Creative Knowledge Base — the Production Center's
  Prompt/Media/Brand studios are real navigation destinations with no real backing data model behind
  the "Brand" concept specifically yet.
- Consent-record infrastructure for avatar/voice likeness (`AI_PRODUCTION_STUDIO.md` §6–§7) — not
  addressed by the frontend shell, and this Bible flags it as **the single highest-risk item to leave
  unaddressed** if/when real avatar or voice-clone generation is added, since the UI shell existing
  first creates real temptation to wire in a generation provider before the consent gate exists.

## 10. Recommended sequencing (extends `10_ROADMAP.md` Horizon 2)

1. **Real Content Factory + Cross-Posting HTTP routes** — the concrete backend prerequisite named in
   `AI_PRODUCTION_STUDIO.md` §0's own research, still the single highest-leverage next step.
2. **One real generation provider** (a single modality — image is the lowest-risk starting point) wired
   through the extended `platform_ai` provider registry (`AI_PRODUCTION_STUDIO.md` §1, §3) and the
   real Production Queue (§5 above) — proving the whole pipeline end-to-end on one studio before
   expanding to all 17.
3. **Consent-record infrastructure** (§9 above) — built *before*, never after, any avatar/voice
   generation provider lands, given the risk named in §9.
4. **Brand Library made real** — the Center already has a Brand studio destination; give it a real data
   model before generation providers need to consume brand constraints.
5. Everything else in `AI_PRODUCTION_STUDIO.md` §§4–26 follows once the above land, in the order that
   document's own §27 user-journey and §28 enterprise-workflow sections already lay out.

## Related documents

`AI_PRODUCTION_CENTER_ARCHITECTURE.md`, `PRODUCTION_CENTER.md`, `PRODUCTION_AUTOMATION.md`,
`PROMPT_LIBRARY.md`, `MEDIA_MANAGER.md` (the real implementation hierarchy this Bible sits above),
`AI_PRODUCTION_STUDIO.md` (the full vision spec, still authoritative for everything in §9),
`DESKTOP.md`, `WINDOW_MANAGER.md` (the Desktop integration in §8), `ENTERPRISE_CITY_BIBLE.md` (the City
integration in §8), `AI_AGENTS_BIBLE.md` (studio agent-assignment, §3), `08_AI_PERSONALITY.md`,
`02_PRODUCT_PHILOSOPHY.md`, `10_ROADMAP.md`, `TECH_DEBT.md` (§0's gap list should be cross-checked
against the debt registry's Production Studio entries at next update).
