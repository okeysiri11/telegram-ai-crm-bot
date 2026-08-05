# Navigation Improvements

**Status:** permanent, living document. Documentation only — no source code was modified to produce
this file. This consolidates every navigation-specific finding scattered across `docs/UX_REVIEW.md`,
`docs/USER_EXPERIENCE_BACKLOG.md`, `ENTERPRISE_NAVIGATION.md`, and `ARCHITECTURE_DECISIONS_BACKLOG.md`
into one navigation-only view — **how a user moves between places**, distinct from what they do once
they arrive (`docs/UX_REVIEW.md`) or the full engineering backlog (`ARCHITECTURE_DECISIONS_BACKLOG.md`).
Items already tracked elsewhere are referenced by ID, not re-described; only genuinely new
navigation-specific findings get a new ID here (`NAV-##`).

**Severity vocabulary:** Critical / High / Medium / Low, matching `docs/UX_REVIEW.md` and
`docs/USER_EXPERIENCE_BACKLOG.md`.

---

## 1. The real navigation map today

Full detail: `ENTERPRISE_NAVIGATION.md`. Summarized here only as the baseline this review works
against:

| Layer | Real mechanism |
|---|---|
| Global fast-path | Command Palette, 5 summon shortcuts (`⌘K`/`⌘P`/`⌘⇧P`/`⌘/`/`⌘Space`), `⌘Tab` Quick Switcher |
| OS shell | Enterprise Desktop — Dock (pinned/running apps), Launcher (`⌘Space`) |
| Spatial | Enterprise City — 12 districts, buildings, minimap, local search |
| Structural | Sidebar (tenant-filtered menu tree), breadcrumbs (route-derived) |
| Search | One global index (`searchIndex`/`searchProvider`), extended by `registerIntegrationSearch` (Sprint 28.0) to cover projects/CRM/knowledge/production/documents/agents/city buildings/settings/recent activity |

**The real, positive finding this section leads with:** Sprint 28.0's Integration Hub genuinely
unified deep-linking, session restore, and search registration across every one of these layers
(`INTEGRATION_HUB.md`) — the navigation *substrate* is more coherent than a surface-level look would
suggest. Every finding below is friction *on top of* that real substrate, not evidence the substrate
is missing.

---

## 2. Findings

### 2.1 Fragmented command layer

- **NAV-01 — Two Command Palettes exist; only one runs.** `TECH_DEBT.md` TD-40,
  `docs/USER_EXPERIENCE_BACKLOG.md` UXB-10. **Severity: High.** The dead palette
  (`navigation/components/CommandPalette.tsx`) has its own catalog that could silently diverge from the
  live one if ever re-enabled by accident — the clearest structural risk in this section.
- **NAV-02 — Five palette-summon shortcuts, equal weight, no guidance.**
  `docs/USER_EXPERIENCE_BACKLOG.md` UXB-18. **Severity: Medium.**
- **NAV-03 — "Create X" quick actions don't create anything.**
  `docs/USER_EXPERIENCE_BACKLOG.md` UXB-01. **Severity: Critical.** Restated here specifically because
  it is, at root, a *navigation* promise (the palette says it will take you somewhere/do something) that
  silently fails to deliver — not just an interaction bug.

### 2.2 Redundant routes

- **NAV-04 — Enterprise City has three route aliases** (`/enterprise-city`, `/city`, `/city-hub`), and
  the Production Center has two (`/production-studio`, `/production`). `TECH_DEBT.md` TD-43.
  **Severity: Medium.** `ENTERPRISE_CITY_CORE.md` itself calls `/city-hub` "legacy... optional" — the
  implementing sprint already leans toward deprecating it; this review recommends actually doing so
  rather than leaving three live paths to the same destination indefinitely.
- **NAV-05 — No canonical-route enforcement.** Nothing currently redirects a legacy alias to the
  canonical path, so bookmarks/muscle memory built on any of the three City aliases (or two Production
  aliases) all remain independently "correct" forever unless one is picked and the others start
  redirecting.
  - **Severity: Low** (works today; becomes a real migration cost the longer it's deferred).

### 2.3 Cross-surface navigation gaps

- **NAV-06 — Generic Hub modules don't link to the specific real capability behind them.**
  `docs/USER_EXPERIENCE_BACKLOG.md` UXB-07 (Marketplace is the clearest instance: the generic
  `/marketplace` hub has no link into a tenant's actually-enabled vertical marketplace applications).
  **Severity: High.** This is a navigation *dead end*, not just a content gap — a user has nowhere
  further to click.
- **NAV-07 — City's "Production" district and the AI Production Center share a name with no
  disambiguating navigation cue.** `ARCHITECTURE_DECISIONS_BACKLOG.md` ADB-05,
  `docs/USER_EXPERIENCE_BACKLOG.md` UXB-11. **Severity: Medium.**
- **NAV-08 — Two AI destinations (AI Studio, AI Team Center) with no stated distinction.**
  `docs/USER_EXPERIENCE_BACKLOG.md` UXB-21. **Severity: Low.**

### 2.4 Missing onboarding-as-navigation

- **NAV-09 — No district-first onboarding before a user is dropped onto the City map.**
  `ENTERPRISE_CITY_BIBLE.md` §8 (designed, not built), `docs/USER_EXPERIENCE_BACKLOG.md` UXB-08.
  **Severity: High.** From a pure navigation angle, this is the gap between "here is a map" and "here is
  how to read this map" — the single biggest first-time-navigation cost in the platform.
- **NAV-10 — No onboarding for the Desktop window/Dock/Launcher metaphor.**
  `docs/USER_EXPERIENCE_BACKLOG.md` UXB-12. **Severity: Medium.**

### 2.5 Shortcut discoverability

- **NAV-11 — Reopen-closed-window shortcut (`⌘⇧T`) has no visible affordance.**
  `docs/USER_EXPERIENCE_BACKLOG.md` UXB-19. **Severity: Low.**
- **NAV-12 — City zoom has three equivalent inputs, no in-product hint.**
  `docs/USER_EXPERIENCE_BACKLOG.md` UXB-20. **Severity: Low.**
- **NAV-13 — No consolidated, in-product shortcut reference.** Every shortcut in the platform is real
  and documented (`ENTERPRISE_NAVIGATION.md` §16), but only in written documentation — there is no
  in-app "show me every shortcut" surface (a `?` key overlay, common in comparable products: VS Code,
  Linear, Notion — all named as this platform's own aspirational quality bar in
  `ENTERPRISE_CITY_ARCHITECTURE.md` §1). **Severity: Medium.** This is the single highest-leverage new
  finding in this document: one small feature would resolve NAV-02, NAV-11, and NAV-12 simultaneously.

### 2.6 Breadcrumb depth

- **NAV-14 — City breadcrumbs stop at "City," don't descend to district/building.** The real
  `breadcrumbEngine` (`ENTERPRISE_NAVIGATION.md` §11) generates a trail from the URL path structure;
  since City's internal navigation (district focus, building focus) is client-side state rather than
  distinct URL segments for every level, the breadcrumb can't reflect "City → AI District → AI Team
  Center" the way a Workspace module's breadcrumb reflects its own nested route structure.
  **Severity: Medium.** This is a new finding, not previously tracked — likely resolved naturally once
  `ARCHITECTURE_DECISIONS_BACKLOG.md` ADB-15 (camera URL sync) lands, since that would give district/
  building focus a real URL segment to breadcrumb from.

---

## 3. Ranked recommendations

| ID | Recommendation | Severity | Cross-reference |
|---|---|---|---|
| NAV-03 | Fix "Create X" quick actions to actually create something | **Critical** | UXB-01 |
| NAV-01 | Retire the orphaned Command Palette | High | TD-40, UXB-10 |
| NAV-06 | Link generic Hub modules to their real underlying capability (Marketplace first) | High | UXB-07 |
| NAV-09 | Build district-first City onboarding | High | UXB-08 |
| NAV-13 | Build one in-product shortcut reference (`?` overlay) | Medium | resolves NAV-02/11/12 at once |
| NAV-04 | Pick one canonical route per surface, deprecate the rest | Medium | TD-43 |
| NAV-14 | Extend City camera URL sync to also carry district/building focus, enabling real breadcrumbs | Medium | ADB-15 |
| NAV-07 | Disambiguate the "Production" name collision | Medium | ADB-05 |
| NAV-10 | Build Desktop metaphor onboarding | Medium | UXB-12 |
| NAV-02 | Add first-run guidance on which palette shortcut to remember | Medium | UXB-18 (superseded by NAV-13 if built) |
| NAV-05 | Add redirect-to-canonical for deprecated route aliases | Low | — |
| NAV-11 | Surface the reopen-closed-window shortcut | Low | UXB-19 (superseded by NAV-13 if built) |
| NAV-12 | Hint the City zoom shortcut equivalents | Low | UXB-20 (superseded by NAV-13 if built) |
| NAV-08 | Clarify AI Studio vs. AI Team Center | Low | UXB-21 |

**The one sequencing note worth stating plainly:** NAV-13 (a single in-product shortcut reference) is
the highest-leverage item on this list relative to its cost — building it resolves three separate Low/
Medium findings (NAV-02, NAV-11, NAV-12) as a side effect, which is a better return than fixing each
individually.

## Related documents

`docs/UX_REVIEW.md`, `docs/USER_EXPERIENCE_BACKLOG.md` (the source findings this document consolidates
under a navigation lens), `ENTERPRISE_NAVIGATION.md` (the full navigation philosophy this document
reviews against), `ARCHITECTURE_DECISIONS_BACKLOG.md` (ADB-05, ADB-15 — the architecture-level work
some findings here depend on), `TECH_DEBT.md` (TD-40, TD-43), `ENTERPRISE_CITY_BIBLE.md` §8.
