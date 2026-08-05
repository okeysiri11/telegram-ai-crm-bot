# The Enterprise City Bible
### Phase 1 — Spatial Operating System

**Status:** the canonical, highest-level design authority for Enterprise City. Documentation only — no
source code should be modified as a result of reading this document. Every future UI, UX, and 3D
implementation decision for the City should trace back to a rule in this document or one of its
subordinate specifications. Where this document and a subordinate spec appear to disagree, **this
document wins** — the subordinate specs should be updated to match, not the other way around.

**Document hierarchy this Bible sits atop:**

```
ENTERPRISE_CITY_BIBLE.md          ← this document. Canonical authority. Philosophy, world, evolution.
        │
        ├── ENTERPRISE_CITY_ARCHITECTURE.md   ← the v1 rollout architecture (navigation-paradigm elevation)
        │         ├── ENTERPRISE_CITY_STATES.md       ← building state model, full detail
        │         ├── ENTERPRISE_CITY_ANIMATIONS.md   ← motion/event mapping, full detail
        │         └── ENTERPRISE_CITY_UI_RULES.md     ← composition rules, full detail
        │
        ├── ENTERPRISE_CITY_CORE.md          ← REAL implementation architecture (Sprint 27.8)
        │         ├── CITY_ENGINE.md                  ← real camera/viewport controller (cityEngine.ts)
        │         └── CITY_DISTRICTS.md                ← real 12-district catalog (cityDistricts.ts, cityNavigation.ts)
        │
        └── ENTERPRISE_CITY.md               ← the shipped 2D implementation reference (v0)
```

This document does not repeat shipped coordinates, CSS class names, or token values — those live in
the documents below it, referenced by name throughout. This document's job is philosophy, world
structure, the building template, navigation modes, visual language *principles* (not values), runtime-
as-place design, AI and multiplayer experience, accessibility posture, and the five-year evolution
path. Everything here inherits `ENTERPRISE_DESIGN_SYSTEM.md`'s tokens and `02_PRODUCT_PHILOSOPHY.md`'s
nine principles without exception — a Bible that contradicted the platform's own philosophy would not
be a Bible, it would be a competing product.

**Reality update (Sprint 27.7–27.9 — read this before trusting any status label below without
re-checking it):** an Enterprise Desktop OS shell now exists for real (`DESKTOP.md`,
`WINDOW_MANAGER.md`, `src/web/src/enterprise-desktop/`) — real window management (move/resize/
minimize/maximize/snap-left-right-fullscreen/reopen-closed), a real Dock, a real Launcher
(`Cmd/Ctrl+Space`), all session-persisted (`ews_desktop_session_v1`). Enterprise City itself gained a
real camera engine (`cityEngine.ts` — viewport clamp/pan/zoom, session-persisted
`ews_city_viewport_v1`) and real navigation memory (`cityNavigation.ts` — history/recent/favorites/
breadcrumbs, `localStorage`-persisted, bridging into the shared `favoritesManager`). Two corrections
this creates versus this document's original speculative design:

1. **The real district taxonomy is 12 districts, not this document's originally-proposed 14** — §2
   below reconciles the two directly rather than pretending the vision number was exactly right.
2. **The real hierarchy is Desktop (the OS) → City (the primary spatial navigation space within it) →
   individual routes** — City did not replace Desktop as the outermost shell; it became the OS's
   headline navigation app, reached from the Dock/Launcher like any other app, with its own
   `/enterprise-city` and `/city` routes also directly reachable outside the Desktop shell. §8 below
   corrects this document's earlier "City becomes the OS" framing to match.

---

## 1. Philosophy

### Why Enterprise City exists

Every enterprise system before this one has made the same bet: that a person can hold their entire
business in their head as a list. A sidebar of modules. A table of reports. A folder of dashboards.
That bet fails exactly when it matters most — when a business gets large enough that no single person
can enumerate everything happening inside it from memory. Enterprise City exists because a **place** is
easier to hold in your head than a **list**. You don't remember your city by reciting street names in
order; you remember it by the shape of the skyline, by which part of town feels busy at 9am, by where
the courthouse is relative to the harbor. Enterprise City gives a business owner, an operator, and an
AI agent the same kind of durable, spatial memory of their own organization.

This is not a metaphor applied after the fact for polish. It is the platform's answer to a real,
specific failure mode: enterprise software today is a collection of disconnected tools wearing one
login screen (`01_VISION.md`). Enterprise City is the platform's rejection of that failure mode made
literal — one place, not many pages.

### Why spatial navigation is superior to menu navigation

Not universally — this Bible does not claim a spatial map is the better interface for every task, and
says so plainly in §9 and §10. But for the specific job Enterprise City is built to do — **give a human
a true sense of the whole organization's state in a few seconds** — spatial navigation wins for three
concrete reasons:

1. **Parallel perception beats sequential scanning.** A menu must be read one item at a time; a skyline
   is perceived all at once. A dashboard with fifteen status widgets asks you to scan fifteen times. A
   city with fifteen buildings asks you to *look* once.
2. **Spatial relationships encode organizational relationships for free.** Two buildings near each
   other in the same district are related; a workflow route crossing half the map is visibly a
   cross-functional process. A menu has no equivalent way to show relationship without a diagram
   bolted on afterward — Enterprise City's map *is* the diagram.
3. **Spatial memory is more durable than list memory.** A returning user forgets a menu order faster
   than they forget where a place is — this is a well-established property of how people navigate
   physical space, and Enterprise City is a deliberate bet that the same durability applies to
   navigating an organization's software.

Where spatial navigation is *not* the better choice — dense data entry, exhaustive search, screen-reader
use, small viewports — the platform provides equally first-class non-spatial alternatives (the List
View, `ENTERPRISE_CITY_ARCHITECTURE.md` §20; the Command Palette, `ENTERPRISE_NAVIGATION.md` §8) rather
than forcing the spatial metaphor where it doesn't fit. A Bible that pretended otherwise would be
making a worse product to win an argument.

### How Enterprise City becomes the operating system (corrected against Sprint 27.7–27.8 reality)

This section originally argued the City itself should become "the desktop" of the OS metaphor. Real
implementation has since answered this more precisely than the original argument did: **a literal
Enterprise Desktop now exists** (`DESKTOP.md`, `src/web/src/enterprise-desktop/`) — real wallpaper,
icon grid, window manager, dock, and launcher, all session-persisted. The City did not need to *become*
the desktop; the platform built a real one. Enterprise City's actual, corrected role is **the OS's
headline navigation app** — the one an operator is most likely to pin to the Dock and reach for first,
opened like any other app (standalone at `/enterprise-city`/`/city`, or windowed at
`/enterprise-city?embed=1` inside a Desktop window), not the outermost shell itself. This is a more
coherent OS metaphor than the original argument, not a lesser one: a real OS has both a desktop *and* a
signature flagship app you spend most of your time in (a file manager, a browser) — City is ADOS's
version of that flagship app, and Desktop is the shell around it. `03_ENTERPRISE_OS.md` and `DESKTOP.md`
now describe the outer OS; this document describes the app inside it that matters most.

---

## 2. World Structure

### The reconciliation this Bible makes explicit (updated post-Sprint-27.8)

`ENTERPRISE_CITY.md` originally shipped five districts (Commerce, Ops, People, Intel, Hub). **As of
Sprint 27.8, the real shipped taxonomy is 12 districts** (`CITY_DISTRICTS.md`): Enterprise, CRM, ERP,
AI, Production, Marketplace, Analytics, Knowledge, Finance, Developer, Security, Settings. This is
closer to this Bible's original fourteen-district vision than the old five ever were — eight of this
Bible's originally-proposed districts are now real, verbatim or near-verbatim: **Business Centers →
CRM** (real), **Finance District → Finance** (real), **Security District → Security** (real),
**Developer District → Developer** (real), **AI District → AI** (real), **Marketplace → Marketplace**
(real), **Production District → Production** (real), and **Industrial Areas** is now folded into
**Production** rather than kept separate. Three of this Bible's proposed districts remain vision, not
yet shipped: **Government**, **Cloud District**, **Innovation District**. One, **Training Campus**, is
not present in the real 12 and is not currently planned — folded conceptually into **Knowledge** until
a real Academy-specific district is warranted. The table below is updated to reflect this.

### The twelve real districts (shipped, Sprint 27.8) + remaining vision districts

| District | Status | Real platform tie |
|---|---|---|
| **Enterprise** | **Shipped** | The plaza/hub district — Plaza, Hub, Dashboard, HR (`CITY_DISTRICTS.md`); the map's central, always-anchored district, direct descendant of this Bible's original "Hub" concept |
| **CRM** | **Shipped** | CRM, Sales, Marketing — the direct realization of this Bible's proposed "Business Centers" |
| **ERP** | **Shipped** | ERP Center — realizes this Bible's proposed ERP building without needing its own "Business Centers" umbrella |
| **AI** | **Shipped** | AI Team, AI Studio, Concierge — direct realization of this Bible's "AI District" |
| **Production** | **Shipped** | Production, Mission Control — absorbs this Bible's separate "Industrial Areas" concept; also the City-side home for the real AI Production Center (`AI_PRODUCTION_CENTER_BIBLE.md`) |
| **Marketplace** | **Shipped** | Direct realization of this Bible's proposed "Marketplace" district |
| **Analytics** | **Shipped** | Analytics Center — not originally named as its own district in this Bible's vision list (was folded into a generic Intel concept); real implementation gave it independent status |
| **Knowledge** | **Shipped** | Knowledge, Documents — absorbs this Bible's proposed "Training Campus" until a dedicated Academy district is warranted |
| **Finance** | **Shipped** | Direct realization of this Bible's proposed "Finance District" |
| **Developer** | **Shipped** | Developer Tools (routed via Command Center) — direct realization of this Bible's proposed "Developer District" |
| **Security** | **Shipped** | Security Center — direct realization of this Bible's proposed "Security District" |
| **Settings** | **Shipped** | Settings, Admin — not originally its own district in this Bible's vision list; real implementation gave it independent status rather than folding it into People/Enterprise |
| **Government** | Vision, not shipped | `ENTERPRISE_CITY.md` §23 tier 4; compliance, public-service, and audit-heavy capability clusters — remains a future district for Government-tier deployments specifically |
| **Cloud District** | Vision, not shipped | The literal home of the platform's own runtime (dual bot+API runtime, TS kernel ecosystem, §6) — still not realized; the real Desktop/City work has not yet turned its gaze on visualizing the platform's own infrastructure |
| **Innovation District** | Vision, not shipped | A living view of `10_ROADMAP.md` — what's in progress, what's next — still a design idea, not a shipped district |

**Districting rule, inherited and restated:** a district exists because a cluster of real capabilities
shares one shape/character language (`ENTERPRISE_CITY.md` §2, §8, `CITY_DISTRICTS.md`) — the district
count is not fixed; new districts open the way `ENTERPRISE_CITY.md` §22 already specifies (past ~6–8
buildings, split rather than crowd), which is exactly how the real count grew from 5 to 12 between
Sprints 32.3.3 and 27.8.

### A deliberate omission worth naming

This Bible does **not** define a "Cafe District," "Legal District," or similarly named zone per
vertical application. Verticals (`auto`, `agro`, `legal`, `crypto`, `port`, `drone`) live inside
**Industrial Areas**, **Marketplace**, or a future **Verticals District**
(`ENTERPRISE_CITY.md` §23 tier 3) depending on their character, tenant by tenant — a fixed
district-per-vertical scheme would not survive a tenant who has three verticals enabled and another who
has eleven. Districts group by *character*, never by a fixed enumerated business list.

---

## 3. Buildings

### The building template — the schema every building, present or future, is defined by

| Field | Definition |
|---|---|
| **Purpose** | What this building is for, in one sentence a non-technical reader understands |
| **Owner** | The business role/persona accountable for this domain (not a code-repository owner — see `MODULES.md` for that) |
| **Users** | Who actually opens this building, and why |
| **Modules inside** | The real platform capability(ies) this building's route leads to (`MODULES.md`/`API_MAP.md` cross-reference) |
| **Relationships** | Which other buildings this one shares a district link line or workflow route with (`ENTERPRISE_CITY.md` §13, §21) |
| **Animations** | Which entries in `ENTERPRISE_CITY_ANIMATIONS.md` apply to this building specifically, if any beyond the universal set |
| **Status colors** | Which states from `ENTERPRISE_CITY_STATES.md` are meaningful for this building (not every building needs every state — see the Cloud District entry below for an example of a building that is mostly never "Warning") |
| **Expansion rules** | When this building splits into a Department (`ENTERPRISE_CITY.md` §10) or the district it lives in splits (§2 above, §22 there) |
| **Future evolution** | Which `10_ROADMAP.md`/§10-below horizon this building's next real capability lands in |

**This template is the actual contribution of this section** — not an exhaustive listing of every
building in every district (that would duplicate `ENTERPRISE_CITY.md` §9, which remains the living
catalog). Below, one **flagship building** per district is fully specified against this template, both
to demonstrate the schema in use and because these fourteen are the buildings most future
implementation work will touch first.

### Flagship buildings, one per district

**Business Centers — CRM Center** *(already shipped, `ENTERPRISE_CITY.md` §9.1)*
Purpose: home for client relationships and deal pipelines. Owner: Head of Sales/Customer Success.
Users: sales reps, account managers, owners checking pipeline health. Modules inside: CRM workspace,
`services/crm_*`. Relationships: linked to Sales and Marketing within Business Centers; workflow routes
from Marketplace often terminate here. Animations: standard state-flash + focus-breathe only. Status
colors: all six states meaningful (a CRM sees real load variance). Expansion rules: splits into
Departments (Pipeline / Accounts / Renewals) before a second building is added. Future evolution:
Roadmap Horizon 2's persistent-layout work directly benefits this building's most-visited-surface status.

**Industrial Areas — Mission Control** *(already shipped)*
Purpose: live operations command point. Owner: Head of Operations. Users: ops managers during active
incidents, executives checking live health. Modules inside: `platform_operations`, live-ops dashboards.
Relationships: linked to Production; frequently the destination of workflow routes representing
escalations. Animations: state-flash is highest-stakes here — Critical transitions on this building
should never be missed, meriting the strongest (still non-decorative) treatment in
`ENTERPRISE_CITY_ANIMATIONS.md`. Status colors: Warning/Critical/Busy dominate; Offline here is a
serious signal, not routine. Expansion rules: unlikely to split — this building's value is being one
unified command point, not many. Future evolution: Runtime Visualization (§6) surfaces here first.

**Government — Compliance Hall** *(new, Phase 1 vision)*
Purpose: the seat of regulatory/compliance oversight for Government-tier deployments. Owner: Chief
Compliance Officer / agency director persona. Users: auditors, compliance officers, public-sector
administrators. Modules inside: audit trails, `platform_security`'s compliance surfaces, records
management. Relationships: tightly linked to Security District and Infrastructure (audit logs).
Animations: deliberately minimal — a compliance surface should never feel like it's "selling" activity
with motion. Status colors: Offline here is treated with the highest urgency of any building in the
Bible (a compliance system going dark is a regulatory event, not an inconvenience). Expansion rules:
this building only exists at all once a tenant's scale tier reaches Government (`ENTERPRISE_CITY.md`
§23) — it is the clearest example of a building that is tenant-conditional not just on a vertical, but
on organizational tier itself. Future evolution: Version 2 (§10).

**Infrastructure — Observability Deck** *(elevates the proposed building, `ENTERPRISE_CITY.md` §9.2)*
Purpose: the platform's own health, made visible. Owner: Head of Platform Engineering. Users:
SREs, platform engineers, and — uniquely among these fourteen — the platform's own AI agents consulting
it before making decisions elsewhere in the city. Modules inside: `platform_observability`,
`platform_reliability`. Relationships: feeds the city-wide ambient runtime signal (§6) rather than
only its own tile. Animations: the health-ambient-shift animation (`ENTERPRISE_CITY_ANIMATIONS.md` §3)
originates conceptually here even though it renders city-wide. Status colors: this building's own state
should almost never show anything but Active/Warning — if the Observability Deck itself goes Offline,
that is a signal failure worth its own alert path outside the City. Expansion rules: splits into Metrics
/ Logs / Traces departments as `platform_observability`'s own surface grows. Future evolution: Runtime
Visualization (§6) is this building's entire reason for existing.

**Cloud District — The Engine Room** *(new)*
Purpose: literal, honest visualization of what actually runs the platform. Owner: Head of
Infrastructure/DevOps. Users: engineers debugging runtime issues, rarely business users. Modules
inside: the real dual bot+API runtime (`ARCHITECTURE_MAP.md` §2.1) **and, visualized as an honestly
separate structure**, the TS kernel ecosystem (`ARCHITECTURE_MAP.md` §15) — this building must never
render the two as connected, since they are not (§6 restates this constraint). Relationships: none by
design — this is the one district where the "everything is connected" spatial metaphor is deliberately
allowed to show a real seam, because hiding it would be dishonest, not tidy. Animations: minimal;
gauges update on the platform's real telemetry cadence, no decorative flourish. Status colors: this is
the one building where "Offline" for one half (the bot+API runtime) and "Disconnected" for the other
(the TS kernel) must be visually distinguishable states, not the same treatment. Expansion rules: exists
mainly for engineering audiences — arguably the one district that should be hidden from most business
users' default view (RBAC-gated, `ENTERPRISE_CITY.md` §17). Future evolution: this building's honest
depiction of the TS-kernel seam is exactly the kind of fact `00_MASTER_PRODUCT_BIBLE.md`'s documentation
gaps (§3.2 there, the undocumented kernel-relationship decision) should resolve before this building is
built for real.

**Marketplace — Marketplace Plaza** *(elevates the proposed building)*
Purpose: the storefront face of every vertical marketplace the tenant runs. Owner: Head of Commerce.
Users: marketplace operators, external partners via Portals (`ENTERPRISE_CITY.md` §12). Modules
inside: `auto_marketplace`, `agro_marketplace`, `applications/marketplace`. Relationships: the primary
building connected to Portals — a partner organization's shared view most often terminates here.
Animations: transaction-volume-driven Busy states are common and expected, not alarming. Status colors:
Busy is this building's "normal Tuesday," distinct from Mission Control where Busy is more notable.
Expansion rules: splits per active marketplace vertical once more than ~6–8 are enabled for one tenant.
Future evolution: `AI_PRODUCTION_STUDIO.md`'s Social Content Studio output (campaigns, listings)
visually originates from here once Publishing is real.

**Training Campus — Builder Academy** *(new, real module tie)*
Purpose: where people (and, notably, new AI agents being configured) learn the platform. Owner: Head of
Enablement/Learning. Users: new employees, citizen-developers using Platform Builder, new hires
onboarding. Modules inside: `academy.py`/`academy_v2` (`applications/platform_builder`), `platform_
learning`. Relationships: linked to Developer District and AI District (agent training touches both).
Animations: the calmest building in the Bible by design — a learning environment should never feel
urgent. Status colors: rarely shows Warning/Critical; mostly Active/Offline (a course/module
available or not). Expansion rules: splits by curriculum track. Future evolution: this is the natural
home for onboarding a *new user to the City itself* (§1's district-first onboarding design,
`ENTERPRISE_CITY_ARCHITECTURE.md` §8) — the Campus should eventually teach the City, inside the City.

**AI District — AI Studio** *(elevates the proposed building)*
Purpose: where AI agents are configured, trained, and observed — distinct from where they're merely
used. Owner: Head of AI/Automation. Users: AI engineers, prompt authors, agent-configuration
specialists. Modules inside: `platform_orchestrator`, `platform_agents`, `platform_reasoning`,
`platform_planning`, `platform_decision`, `platform_collaboration`. Relationships: linked to every
other district via the AI-dot overlay (`ENTERPRISE_CITY_STATES.md` §6) — this is the one district whose
influence is meant to be visible everywhere, not contained to its own tile. Animations: agent transit
markers (`ENTERPRISE_CITY_ANIMATIONS.md` §3) most often originate or terminate here. Status colors:
"AI working" as an overlay state is definitionally always relevant to this district. Expansion rules:
splits into per-capability departments (Reasoning / Planning / Collaboration) as the underlying
packages mature independently. Future evolution: the AI Director concept
(`AI_PRODUCTION_STUDIO.md` §20) is architecturally headquartered here once built.

**Finance District — Finance Tower** *(elevates the existing Finance building)*
Purpose: financial operations and reporting. Owner: CFO/Finance lead. Users: finance teams, executives
reviewing financial health. Modules inside: `finance_enterprise`, `services/pg_*` finance engines.
Relationships: tightly linked to Business Centers (revenue) and Security District (financial controls/
audit). Animations: standard set; no special treatment beyond the universal rules. Status colors: all
six meaningful, with particular weight on the distinction between Busy (month-end close, expected) and
Warning (an actual reconciliation problem) — this pairing is worth calling out because it's the
clearest example in the Bible of two states that must never be visually confusable despite both being
"high activity." Expansion rules: splits into Treasury / AP-AR / Reporting departments — the exact
example already used in `ENTERPRISE_CITY.md` §10. Future evolution: Version 2 (§10).

**Security District — Security & Trust Keep** *(elevates the proposed building)*
Purpose: identity, access, and audit — the platform's own trust boundary, made visible. Owner: CISO/
Head of Security. Users: security engineers, compliance auditors, RBAC administrators. Modules inside:
`platform_security`, `platform_identity`. Relationships: linked to every district conceptually (RBAC
governs visibility everywhere, `03_ENTERPRISE_OS.md`) but visually connected most directly to
Government and Infrastructure. Animations: deliberately restrained — a security surface earning trust
through calm precision, not urgency theater, even when reporting a real incident. Status colors: this
building's Critical state should be the most visually serious in the entire Bible (a security incident
outranks a business-metrics warning anywhere else). Expansion rules: splits into Identity / Access /
Audit departments. Future evolution: the CI-blocking architecture violation already tracked
(`TECH_DEBT.md` TD-17, `platform_security` bypassing `ConfigurationCenter`) is the kind of fact this
building's own health signal should eventually be able to surface honestly.

**Developer District — Extension Yard** *(new)*
Purpose: where the platform is extended by its own developers and partners, not just operated by
end users. Owner: Head of Platform/Ecosystem Engineering. Users: internal engineers, plugin authors,
SDK consumers. Modules inside: `platform_plugin_sdk`, `platform_sdk`, `plugins/`. Relationships: linked
to Training Campus (SDK documentation/learning) and AI District (agent tool registration,
`platform_tools`). Animations: standard set. Status colors: mostly Active/Offline — a plugin is
enabled or it isn't; Warning is reserved for a plugin failing its own health check. Expansion rules:
splits per plugin category once the real (currently scaffolding-only, `TECH_DEBT.md` TD-29) plugin
ecosystem has enough real installed plugins to warrant it. Future evolution: this building's honest
state should reflect that today's example plugins are not actually loaded in production
(`TECH_DEBT.md` TD-29) — it should show "available, not installed," never a false "Active."

**Production District — Production Studio** *(elevates the proposed building)*
Purpose: the home of `AI_PRODUCTION_STUDIO.md` in its entirety — image, video, voice, avatar, 3D, and
every creative production capability. Owner: Head of Creative/Marketing Production. Users: creative
teams, marketers, brand managers. Modules inside: the full Studio (`AI_PRODUCTION_STUDIO.md` §§4–26).
Relationships: linked to Marketplace (published output) and AI District (Creative Agents, AI Director).
Animations: the Production Queue/Rendering Farm (`AI_PRODUCTION_STUDIO.md` §23–24) is visualized here as
a literal, real queue-depth indicator — the closest thing in the entire Bible to a "conveyor belt,"
justified because it represents a real, literal queue of jobs, not a decorative flourish. Status colors:
Busy is this building's most common non-Active state by a wide margin (rendering jobs). Expansion
rules: given the Studio's own 26-section scope, this district should split into sub-buildings by
modality (Image/Video/Voice, a Brand Library building, a Publishing Center building) well before the
generic 6–8-building threshold, since its internal complexity already exceeds most other districts'.
Future evolution: this entire district *is* Roadmap Horizon 2's largest body of work
(`10_ROADMAP.md`).

**Innovation District — The Roadmap Room** *(new)*
Purpose: a living visualization of where the platform is going, not just where it is. Owner: Head of
Product/CPO persona. Users: executives, product leadership, and — deliberately — every employee curious
about what's next. Modules inside: no backend module exists for this yet; it visualizes `10_ROADMAP.md`
directly, sourced from the same document rather than a separate roadmap database (`02_PRODUCT_
PHILOSOPHY.md` principle 9 — never invent a second source of truth). Relationships: conceptually linked
to every district, since every district has a "next" entry in the roadmap. Animations: the
one-time growth/materialization animation (`ENTERPRISE_CITY_ANIMATIONS.md` §3) is this building's
signature moment — watching a new building appear here first, before it appears anywhere else, is the
most literal way the City can show the platform growing. Status colors: a bespoke, narrower vocabulary
(Planned / In Progress / Shipped) rather than the standard six — this is the one building in the Bible
explicitly permitted a different state set, because it represents *plans*, not *running systems*, and
forcing the operational vocabulary onto it would be dishonest. Expansion rules: this is the
literal implementation of §10 below — its own building list *is* this Bible's roadmap. Future evolution:
by construction, always current — see §10.

---

## 4. Navigation

Extends `ENTERPRISE_CITY_ARCHITECTURE.md` §§6–11 and `ENTERPRISE_NAVIGATION.md` in full — this section
adds the modes not yet covered there.

- **Walking (new, 3D vision only).** A literal, first/third-person ground-level traversal mode along
  the same street/link-line paths already established (`ENTERPRISE_CITY.md` §13) — slower and
  exploratory, the opposite of the fast camera-flight default. **Walking is never the default or
  required path anywhere** — it exists specifically for briefing-room and deliberate-exploration
  scenarios (echoing `01_VISION.md`'s "walking a factory floor" instinct), always paired with an
  instant-teleport escape hatch, exactly like camera flight's existing skip toggle
  (`ENTERPRISE_CITY.md` §13). A platform whose daily-use navigation required walking would have failed
  its own OS-speed promise (`ENTERPRISE_NAVIGATION.md` §1).
- **Zoom, Teleport** — unchanged from `ENTERPRISE_CITY.md` §14, §13; teleport (instant click-to-navigate)
  remains the default, walking and flight are the deliberate-pace alternatives.
- **Bookmarks** — the City's application of the platform's existing Favorites mechanism
  (`ENTERPRISE_NAVIGATION.md` §0, once TD-41 is resolved) to specific buildings/districts/zoom
  states — never a City-specific bookmarking system.
- **Global Search, AI navigation, Voice navigation, Command Center integration** — all inherited
  unchanged from `ENTERPRISE_NAVIGATION.md` §6, §19–§20, §8 — the City is a surface these systems reach
  *into*, never a parallel implementation of any of them.
- **Desktop integration — now real, in-browser (corrected from "open decision").** This section
  originally treated desktop-shell presence as a future, technology-undecided aspiration. A real
  Enterprise Desktop now exists (`DESKTOP.md`) — the City is pinned to its real Dock, launched from its
  real Launcher (`Cmd/Ctrl+Space`), and opens inside a real, moveable/resizable/snappable window
  (`WINDOW_MANAGER.md`) via `/enterprise-city?embed=1`. **What remains genuinely open** is only the
  narrower, more ambitious idea this section originally gestured at — a native OS-level presence (a
  system-tray icon, a widget visible when the browser itself isn't focused) via a technology like
  Electron — which still has not been decided anywhere in this platform's documentation and remains a
  candidate for a future ADR (`00_MASTER_PRODUCT_BIBLE.md` §4).
- **Map integration.** Two distinct things: (1) the in-City minimap, real and shipped
  (`ENTERPRISE_CITY.md` §15); (2) a **real-world geographic overlay**, vision-only, relevant once
  International Enterprise-tier tenants (`ENTERPRISE_CITY.md` §23 tier 3) need Enterprise nodes pinned
  to actual locations rather than an abstract layout — this is the concrete mechanism behind that
  tier's "geography as an organizing dimension" language.

---

## 5. Visual Language

Every value referenced below is defined once in `ENTERPRISE_DESIGN_SYSTEM.md`; this section defines
**principles for 3D-specific visual dimensions that don't exist in the 2D token system yet**, plus how
existing 2D concepts extend.

- **Glass** — unchanged rule: chrome only, never content (`ENTERPRISE_CITY_UI_RULES.md` §4).
- **Lighting (new, 3D vision).** Each district's lighting character extends its existing shape language
  (§2 here, `ENTERPRISE_CITY.md` §8) into a light quality: Industrial Areas read harsh/functional;
  Business Centers and Finance read warm/inviting; AI District and Infrastructure read cool-toned and
  precise; Hub reads brightest, reinforcing its "always visually anchored" role. Lighting is a
  district-identity signal, never a mood/ambiance effect layered on for its own sake.
- **Fog (new, 3D vision).** A depth cue only — buildings distant from the current camera focus recede
  into soft atmospheric fog, exactly mirroring the existing `is-dimmed` overlay-filter treatment in 2D
  (`ENTERPRISE_CITY.md` §20). Fog communicates *distance from current attention*, never weather (§5's
  Weather entry below is a fully distinct concept and must never be implemented as the same mechanism).
- **Depth** — the existing elevation/shadow system (`ENTERPRISE_DESIGN_SYSTEM.md` §7–§8) extends
  directly into 3D z-depth; no second depth system is introduced.
- **Materials (new, 3D vision).** District-appropriate surface materials reinforce identity precisely
  the way silhouettes do in 2D (`ENTERPRISE_CITY_UI_RULES.md` §7): glass/metal for Cloud and Developer
  districts, warm stone/wood tones for Training Campus and People-adjacent buildings, precise brushed
  metal for Security District. Materials follow the same "one glyph, one meaning, forever" constancy
  rule §7 already establishes for silhouettes.
- **Day, Night** — unchanged, `ENTERPRISE_CITY_ARCHITECTURE.md` §17.
- **Weather (optional, unchanged constraint)** — `ENTERPRISE_CITY_ARCHITECTURE.md` §18's rule holds
  without exception: data-bound health metaphor only, cosmetic/randomized weather rejected outright.
- **Season (new, treated with the same discipline as Weather).** If built at all, Season maps to the
  tenant's real fiscal calendar (a subtle visual shift at fiscal quarter/year boundaries) — never a
  literal spring/summer/autumn/winter cosmetic cycle. Like Weather, this is lowest priority and
  acceptable to omit indefinitely (§10's evolution path does not schedule it in any named version).
- **Animation principles** — unchanged, `ENTERPRISE_CITY_ANIMATIONS.md` §1.
- **Motion hierarchy (new contribution of this Bible).** When more than one animation could plausibly
  trigger at once, this precedence resolves which one takes visual priority, mirroring
  `ENTERPRISE_CITY_STATES.md` §5's state-precedence logic applied to motion instead of state:

  ```
  State-change flash (a real health transition)
        >  Navigation motion (camera flight / viewport pan)
        >  Presence/collaboration motion (join/leave fades)
        >  Ambient environmental motion (health-tint shift, Day/Night cross-fade)
        >  AI-pulse / idle overlays
  ```
  A building transitioning to Critical while simultaneously being panned-to and gaining a new present
  viewer shows its state-flash first and most prominently — the platform's single most important fact
  (something is wrong) must never be visually subordinated to a navigation or presence cue.

---

## 6. Runtime Visualization

Directly answers the Bible's mandate: **CPU, memory, providers, jobs, AI agents, runtime, queues,
pipelines, and notifications should exist physically inside the city.** Extends
`ENTERPRISE_CITY_ARCHITECTURE.md` §13 with a concrete "where":

| Technical concept | Physical home in the city | Real source |
|---|---|---|
| CPU / memory (aggregate) | The Engine Room, Cloud District (§3) | `platform_observability` metrics |
| Providers (LLM/generation providers) | AI Studio, AI District — rendered as connector lines to external-provider icons, never a fabricated internal building for an external vendor | `platform_ai.provider_registry` (`ARCHITECTURE_MAP.md` §5) |
| Jobs, Queues, Pipelines | Production District's queue-depth indicator (§3) for creative jobs; a parallel indicator in Infrastructure for platform-wide jobs | `platform_jobs.JobEngine` (`AI_PRODUCTION_STUDIO.md` §0, §23) |
| AI Agents | AI District (home) + the AI-dot overlay on any building they're actively working in (`ENTERPRISE_CITY_STATES.md` §6) | `platform_orchestrator`/`platform_agents` |
| Runtime (the dual bot+API process, and separately the TS kernel) | The Engine Room, Cloud District — **rendered as two honestly separate structures**, never merged | `ARCHITECTURE_MAP.md` §2.1, §15 |
| Notifications | The existing per-building badge count (`ENTERPRISE_CITY.md`, real today) — unchanged | `notificationStore` (`ENTERPRISE_NAVIGATION.md` §12) |

**The one rule that governs every row above:** a technical concept gets a physical home only where a
**real, live signal** exists to drive it (`02_PRODUCT_PHILOSOPHY.md` principle 9) — an indicator with no
real telemetry behind it should not be built ahead of the telemetry, even if this table names where it
would eventually live.

---

## 7. AI

- **Where agents live:** AI District (§3) is their conceptual home; they are visible working *anywhere*
  in the city via the AI-dot overlay, never confined to one building while actually operating elsewhere.
- **How they move:** agent transit markers along real workflow-route paths
  (`ENTERPRISE_CITY_ANIMATIONS.md` §3) — the one sanctioned "traveling object" in the Bible, because it
  represents a real orchestration hand-off, never a decorative wandering character.
- **How they communicate:** through the same `PlatformEventBus`/event architecture every other system
  in the platform uses (`ARCHITECTURE_MAP.md` §5) — agents do not get a private communication channel
  invisible to the rest of the platform's architecture.
- **How conversations become visible:** a lightweight indicator (not a full transcript rendered on the
  map) shows *that* an AI conversation is active on a given building — e.g., a small annotation near the
  AI dot — with the actual conversation content reachable by focusing the building and opening its
  inspector, consistent with the hover-inspects/click-acts model (`ENTERPRISE_CITY.md` §17). The map
  itself stays uncluttered; depth is one interaction away, not painted onto the skyline.
- **How workflows appear:** unchanged, `ENTERPRISE_CITY.md` §21 — the workflow route line, extended in
  3D by the agent transit marker traveling along it (§3, `ENTERPRISE_CITY_ANIMATIONS.md` §3).

---

## 8. Multiplayer

Builds directly on `WORKSPACE_INTERACTIONS.md` §20–§24 and `ENTERPRISE_CITY_STATES.md` §4 (the "User
present" state) — all four items below are **vision**, with zero existing presence infrastructure
anywhere in the platform (`WORKSPACE_INTERACTIONS.md` §0), stated here as plainly as in every prior
document rather than implied as closer to shipped than it is.

- **Multiple users, Presence:** the avatar-stack indicator (`ENTERPRISE_CITY_STATES.md` §4) is the
  concrete mechanism — ambient, never blocking, never creating an exclusive lock.
- **Live cursors:** scoped specifically to the City map (and, per `WORKSPACE_INTERACTIONS.md` §22, to
  other spatial/canvas surfaces like a future Workflow Builder) — named, color-coded, dismissed as soon
  as a colleague navigates away.
- **Meetings (new).** A designed "shared focus" session — multiple users' viewports synchronize to one
  presenter's pan/zoom/focus, the City's equivalent of Figma's multiplayer "follow" mode — useful
  specifically for the briefing-room scenario `ENTERPRISE_CITY_ARCHITECTURE.md` §18 (controller
  navigation) already names. A meeting session is explicitly opt-in and exitable at any time by any
  participant — no user's viewport is ever hijacked without consent.
- **Shared buildings, Collaboration:** a building reached via a Portal (`ENTERPRISE_CITY.md` §12) is
  visually marked as a **shared** object distinct from a normal building tile — a subtle
  bordering/badge treatment communicating "this view is being shown across an organizational boundary,"
  which is a governance-relevant fact, not a cosmetic one (per Portals' own access-boundary rule,
  `ENTERPRISE_CITY.md` §12).

---

## 9. Accessibility

Restates and extends `ENTERPRISE_CITY_ARCHITECTURE.md` §20 and `ENTERPRISE_CITY_UI_RULES.md` §11–§12
with the explicit mode list this Bible was asked to define:

| Mode | Status | Rule |
|---|---|---|
| Keyboard | Designed, real shortcuts exist today (`ENTERPRISE_NAVIGATION.md` §16) extended by City-specific bindings (`ENTERPRISE_CITY_ARCHITECTURE.md` §9) | Every mouse/touch/spatial interaction has a keyboard equivalent, no exceptions |
| Screen readers | Designed via the List View (§below) | The map itself is never the only path to any piece of information |
| List mode | Designed, first-class parallel surface (`ENTERPRISE_CITY_ARCHITECTURE.md` §20, `ENTERPRISE_CITY_UI_RULES.md` §12) | Not a fallback — column-for-column parity with the map, verified, not asserted |
| Performance mode (new) | Designed | An explicit low-fidelity rendering toggle — 3D off, animation minimized — distinct from Reduce Motion (which governs *duration*, not *rendering complexity*); serves both low-powered devices and users who simply prefer it |
| 2D mode / 3D mode | 2D shipped; 3D vision (`ENTERPRISE_CITY.md` §7) | A first-class user/tenant preference, not a one-way migration — switching preserves focus/viewport context (`ENTERPRISE_CITY.md` §7.2) |
| Mobile mode | Designed, List-View-default (`ENTERPRISE_CITY_ARCHITECTURE.md` §22) | The considered exception to "one primary paradigm everywhere" — documented as deliberate, not an oversight |

---

## 10. Evolution — the next five years

Reframes `10_ROADMAP.md`'s three horizons as four City-specific versions. **`CLAUDE.md`'s gating rule —
Enterprise City is sequenced after platform-module completion — governs the *pace* of this plan in
full; nothing below authorizes building ahead of that rule.**

### Version 1 — The Spatial Home (near-term, = `10_ROADMAP.md` Horizons 1–2)
Login lands in the City; the five shipped districts remain the foundation; building-catalog
completeness reaches every real platform capability; the List View ships as a true parallel surface
before the map becomes default; performance/virtualization hardening lands. **This version does not yet
include any of the fourteen new districts** — it completes and stabilizes what exists today at greater
scale and higher stakes (`ENTERPRISE_CITY_ARCHITECTURE.md` §24).

### Version 2 — The Full District (mid-term)
The fourteen-district taxonomy (§2) is realized — Finance, Security, Production, AI, Marketplace,
Infrastructure, Developer, and Training districts split out from their current single-building or
proposed-building form. Runtime Visualization (§6) goes live, gated on real telemetry. Multiplayer
presence (§8) ships, contingent on the presence infrastructure this document repeatedly notes does not
exist yet anywhere in the platform. Day/Night ships.

### Version 3 — The Living World (long-term)
3D mode (`ENTERPRISE_CITY.md` §7.2) ships for tenants at Holding scale and above. Lighting, Fog,
Materials (§5) are realized. Walking (§4) becomes available as an optional briefing-room mode. Desktop
integration (§4) is resolved as a real architectural decision (via the ADR process this Bible
recommends, §4) and, if pursued, built.

### Ultimate Vision
Enterprise City is the literal, universal interface to ADOS at every scale defined in
`ENTERPRISE_CITY.md` §23 — small company through ecosystem — with the Innovation District (§3)
perpetually showing the platform's own next steps, Portals connecting a real network of organizations'
cities, and every one of this Bible's fourteen districts populated by tenants whose scale genuinely
warrants them. At this point, "opening ADOS" and "entering the City" are the same sentence.

---

## How this document changes the roadmap

`10_ROADMAP.md` is not rewritten by this Bible, but it is now read differently: Horizon 3's City-related
items ("3D mode," "Departments, Enterprises, Portals," "the full five-tier scaling model") should be
understood as this Bible's Version 3 and Ultimate Vision, not a flat, undifferentiated "someday" bucket.
This Bible also adds real scope `10_ROADMAP.md` did not previously enumerate — the fourteen-district
taxonomy, Runtime Visualization, Multiplayer/Meetings, and the Version 2 milestone that sits between the
Roadmap's existing Horizon 2 and Horizon 3 — meaning a future update to `10_ROADMAP.md` should insert
this Bible's Version 2 as an explicit new step, not fold it silently into either existing horizon.

## Related documents

`ENTERPRISE_CITY_ARCHITECTURE.md`, `ENTERPRISE_CITY_STATES.md`, `ENTERPRISE_CITY_ANIMATIONS.md`,
`ENTERPRISE_CITY_UI_RULES.md`, `ENTERPRISE_CITY.md` (the full document hierarchy this Bible sits atop —
see the diagram at the top of this document), `ENTERPRISE_CITY_CORE.md`, `CITY_ENGINE.md`,
`CITY_DISTRICTS.md` (the real Sprint 27.8 implementation reference, also part of this hierarchy),
`DESKTOP.md`, `WINDOW_MANAGER.md` (the real Enterprise Desktop OS this City is a headline app within),
`AI_PRODUCTION_CENTER_BIBLE.md` (the sibling Bible for the Production District's other half),
`AI_AGENTS_BIBLE.md` (the AI ecosystem this City's building "aiAssistant" labels connect to),
`01_VISION.md`, `02_PRODUCT_PHILOSOPHY.md`, `03_ENTERPRISE_OS.md`, `08_AI_PERSONALITY.md`,
`AI_PRODUCTION_STUDIO.md`, `WORKSPACE_INTERACTIONS.md`, `ENTERPRISE_NAVIGATION.md`,
`ENTERPRISE_DESIGN_SYSTEM.md`, `10_ROADMAP.md`, `00_MASTER_PRODUCT_BIBLE.md`.
