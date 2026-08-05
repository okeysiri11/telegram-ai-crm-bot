# Enterprise City — User Journeys

**Sprint:** CG-5 — Research & Specification only. No source code was modified.

**Do not duplicate:** `USER_JOURNEYS.md` already documents ten platform-wide personas end-to-end
(login → logout) across every surface (Desktop, City, Command Center, Production Center, Dashboard).
This document does **not** repeat that — it exists only for the slice `USER_JOURNEYS.md` treats as one
line ("lands in Enterprise City at ...") and expands it into the real, City-specific sequence: which
buildings, which district, which navigation surface, which AI assistant. Login/MFA/logout and every
non-City stop stay owned by `USER_JOURNEYS.md` §0 and are linked, not restated.

Brief requests nine roles: CEO, Manager, Sales, Developer, Administrator, Operator, Client, Partner,
Guest. Six of these already have a named counterpart in `USER_JOURNEYS.md` (CEO, Sales→"Sales
Manager", Developer, Administrator, Client, Partner); this document reuses those exact real/vision
groundings rather than re-deriving them. Three are genuinely new here: **Manager** (generic, not
already split by department), **Operator**, **Guest**.

## 0. Shared City substrate (real, reused by every persona below)

| Stage | Real mechanism |
|---|---|
| Entry into City | `/enterprise-city` route (`EnterpriseCityPage.tsx`) — reached from Desktop Launcher/Dock, Command Palette, or as the post-login landing surface (`USER_JOURNEYS.md` §0) |
| Building open | Click/Enter a building tile → `openBuilding()` → real route navigation (`b.route`), portal effect plays first (CG-3) |
| District jump | Click a district label or the quick-jump chip row → real `jumpDistrict()`, animated camera (CG-3) |
| Search | Local `.ec-search` panel (real, `searchBuildings()`) + global `searchProvider` results in the same panel |
| AI interaction | Every building carries a real `aiAssistant` name (`cityCatalog.ts`) or falls back to "City Concierge"; the sidebar "Advisor · City" card (real, `cityAdvice`) is always present regardless of persona |
| Exit | Navigating to a building's route leaves the City page entirely (real — City is not a persistent frame around other pages, per `EnterpriseCityPage.tsx`'s structure); returning re-enters at the last camera position (`ews_city_viewport_v1`, real) |

## 1. CEO

Real profile: **CEO** (`USER_JOURNEYS.md` §1). City-specific expansion:

| Stage | City-specific detail |
|---|---|
| First screen in City | Plaza (real `kind: "plaza"` building) → Dashboard building, `enterprise` district |
| Daily workflow | Plaza → glance at header strip (`glance.critical`/`glance.attention` counts, real `cityGlance()`) → jump directly to whichever district shows non-zero critical/attention → open the flagged building |
| Navigation | District quick-jump chips (fastest path for a CEO who already knows "something's wrong in Finance") over building search |
| Notifications | Header "Крит."/"Увага" badges (real) are the CEO's primary read — City is used as an ambient status board, not a work surface, for this persona |
| AI interaction | Building-level `advisorHintForBuilding` on whichever building is flagged; sidebar Advisor card for cross-district suggestions |
| Completion of work | Opens the flagged building's real route to act — City itself is a router, not where the CEO's work happens |

## 2. Manager (generic — see department-specific real profiles below)

**No single real "Manager" Dashboard profile exists** — `USER_JOURNEYS.md` already splits this into
Sales Manager (real profile), Marketing Manager and Production Manager (both vision, per
`USER_JOURNEYS.md`'s own cross-journey finding #1). This document does not re-split that; it documents
the one City-specific pattern common to all department managers regardless of which department:

| Stage | City-specific detail |
|---|---|
| First screen in City | Their department's district (CRM for Sales Manager, Production for Production Manager, etc.) — **not** the Enterprise district's Dashboard building the CEO lands on; a manager's City entry is scoped, not citywide |
| Daily workflow | Stay within one district most of the day; the district's own buildings (e.g. CRM district: `crm`, `sales`, `marketing`) cover their whole scope; cross-district visits are the exception, not the routine |
| Navigation | Favorites/Pinned buildings (`CITY_NAVIGATION_GUIDE.md` §5–6) matter most for this persona — a manager revisits the same 3–4 buildings daily, which is exactly what Favorites is for |
| Notifications | District-scoped attention, not citywide — the header glance strip's per-district read (via clicking into the district) matters more than the aggregate count a CEO watches |
| AI interaction | Their district's buildings' own `aiAssistant` (e.g. CRM's real assistant name) — rarely the citywide Advisor card, which is tuned for cross-district synthesis a single-district manager doesn't need |
| Completion of work | Opens a building's route to do the actual work (pipeline review, campaign edit, etc.) — same router role as CEO's journey, scoped to one district |

## 3. Sales

Real profile: **Sales** (`USER_JOURNEYS.md` §4, "Sales Manager"). City-specific expansion:

| Stage | City-specific detail |
|---|---|
| First screen in City | CRM district, `crm` or `sales` building directly (often via a deep link from a notification, skipping Plaza entirely — see `CITY_NAVIGATION_GUIDE.md` §7 Deep Linking) |
| Daily workflow | `crm` (pipeline) ↔ `sales` (follow-ups) ↔ `marketing` (campaign context) — a tight three-building loop within one district, real per `CITY_STATUS_SEED`'s `crm`/`sales`/`marketing` entries |
| Navigation | Recent (real, `cityNavigation.recent()`) is the dominant navigation pattern for this persona — the same handful of buildings, all day |
| Notifications | `crm`'s real seed shows the highest default notification/task load of any building (`tone: "busy", notifications: 5, tasks: 8`) — Sales is the persona for whom the building-level notification badge is most load-bearing |
| AI interaction | `crm`/`sales` buildings' real `aiAssistant` — pipeline-specific, not the general Advisor |
| Completion of work | Exits City into the real CRM module route for the actual deal/follow-up work |

## 4. Developer

Real profile: **Developer** (`USER_JOURNEYS.md` §3). City-specific expansion:

| Stage | City-specific detail |
|---|---|
| First screen in City | Developer district, `developer` building — **real routing note**: `developer`'s route is `/command-center`, not a dedicated developer-tools page (confirmed, `cityCore.test.ts`) — City's Developer building is a doorway into Command Center, not a separate surface |
| Daily workflow | Often the persona least likely to linger in City at all — the Developer district exists mainly as one entry point into Command Center, which has its own much deeper navigation (`ENTERPRISE_NAVIGATION.md`) once entered |
| Navigation | Command Palette (`⌘K`, real, platform-wide) more than City's own map — a developer is the persona most likely to skip the spatial metaphor entirely in favor of keyboard-first navigation, see `CITY_NAVIGATION_GUIDE.md` §3 |
| Notifications | Security district's real buildings (`security`) are the more relevant notification source for this persona than the Developer building itself |
| AI interaction | Command Center's own AI surface (`aios-dock`, real, platform-wide) takes over once the Developer building is entered — City's per-building `aiAssistant` for `developer` is a brief handoff, not where this persona's AI interaction actually happens |
| Completion of work | Work happens entirely inside Command Center after the one-time City → Developer building hop |

## 5. Administrator

Real profile: **Administrator** (`USER_JOURNEYS.md` §2). City-specific expansion:

| Stage | City-specific detail |
|---|---|
| First screen in City | Settings district, `admin` or `settings` building |
| Daily workflow | Least "citywide" of all personas covered so far — an Administrator's real work (tenant config, permissions) is almost entirely inside the `admin`/`settings` routes themselves, City is a two-click entry, not a returning surface |
| Navigation | Direct building open (search or quick-jump), rarely camera pan/drag — this persona has no reason to explore the map spatially |
| Notifications | System-health-flavored (`healthService`-sourced, per `CITY_BUILDING_STATES.md` §3.2) rather than task/notification-count-flavored — the Administrator is the persona for whom the **Health axis**, not the Lifecycle axis, is the primary read |
| AI interaction | `admin`'s real `aiAssistant` ("Admin Advisor", confirmed in `cityCatalog.ts`) |
| Completion of work | Exits into the real admin/settings route |

## 6. Operator (new — maps to the real Mission Control building)

No existing real Dashboard profile named "Operator" in `USER_JOURNEYS.md` — grounded instead in the
real `mission_control` building (`cityCatalog.ts`: `district: "production"`, real identity purpose
"Живые операции" / "Live operations").

| Stage | City-specific detail |
|---|---|
| First screen in City | Production district, `mission_control` building directly — this persona's City entry is the single most building-specific of any persona documented here |
| Daily workflow | Watches `productionRuntime.monitor()`-sourced queue states (real, already joined into Production-district `CityLiveStatus` by `useCityLiveStatus.ts`: `prod_render`, `prod_publish`, `prod_image`/`prod_video`/`prod_reels` generation queues) — this is the persona `CITY_SIMULATION.md` §2.4's queue-depth badges exist for |
| Navigation | Stays within the Production district almost exclusively; district-internal building-to-building moves (e.g. `prod_render` → `prod_publish` following a job's real pipeline stage) matter more than citywide navigation |
| Notifications | Queue-depth and job-failure signals (`JobLifecycle: "failed"`, real) are this persona's primary notification type — distinctly more operational than the CEO's aggregate-glance or the Manager's district-scoped reading |
| AI interaction | `mission_control`'s own real `aiAssistant`; also the persona most likely to benefit from `CITY_SIMULATION.md` §2.2's agent-movement visualization once built, since it directly represents the thing an Operator is watching for |
| Completion of work | Rarely "completes" in the sense other personas do — this is a monitoring persona whose City session is long-lived and ambient, closer to how the CEO uses the header glance strip than to how Sales works through a building queue |

## 7. Client

Real profile: **Client** (`USER_JOURNEYS.md` §8 — marked mostly vision there; **honesty preserved
here, not upgraded**). City-specific expansion:

| Stage | City-specific detail |
|---|---|
| First screen in City | **Vision** — no confirmed real customer-facing City view exists. `USER_JOURNEYS.md` §8 already establishes the Client journey depends on Portal infrastructure (`FUTURE_RUNTIME.md`) that isn't built; this document does not invent a City-specific counter-finding |
| Daily workflow | **Vision** — if/when a Client Portal exists, the honest design intent (not a commitment) would be a single-district, heavily-scoped view (their own account inside CRM/Marketplace only), never the full 12-district City a tenant employee sees |
| Navigation | **Vision** — no navigation model to specify without the underlying portal existing first |
| Notifications | **Vision** |
| AI interaction | **Vision** — would plausibly reuse the real per-building `aiAssistant` pattern once scoped, since that mechanism is already generic enough to extend, but this is a design compatibility note, not a build recommendation |
| Completion of work | **Vision** |

## 8. Partner

Real profile: **Partner** (`USER_JOURNEYS.md` §9 — also marked mostly vision there). Same honesty
posture as Client (§7):

| Stage | City-specific detail |
|---|---|
| First screen in City | **Vision** — depends on the same unbuilt cross-company/Portal capability `USER_JOURNEYS.md` §9 already names |
| Daily workflow / Navigation / Notifications / AI interaction / Completion | **Vision**, for the same reason — this document does not fabricate City-specific detail `USER_JOURNEYS.md` itself declines to invent |

## 9. Guest (new)

No real unauthenticated/trial access mode exists for the platform generally, and none for City
specifically. The closest real analog: the developer-facing **Demo Auth Provider**
(`VITE_DEMO_AUTH`, `owner@demo.corp / demo`, used when the real ISAM identity service is unreachable —
`CLAUDE.md`, `SPRINT_27_1_1_AUTH_RECOVERY.md`) — but that is a *developer fallback for local work*, not
a product-facing Guest role, and this document does not conflate the two.

| Stage | City-specific detail |
|---|---|
| First screen in City | **Vision** — no real Guest role exists. If built, the honest design intent would be a read-only City view (camera pan/zoom/focus allowed, all `onOpen` navigation disabled) rather than a scoped-data view like Client/Partner, since a Guest by definition has no account-specific data to scope to |
| Daily workflow | **Vision** — most plausibly a single session, not a returning pattern; Recent/Favorites/History (`CITY_NAVIGATION_GUIDE.md` §5–6, all `sessionStorage`/persisted-per-session today) would need explicit "do not persist across Guest sessions" handling, flagged here as a real privacy consideration for whichever future sprint builds this, not as a current gap |
| Navigation / Notifications / AI interaction / Completion | **Vision** in full — this document takes no position on Guest AI interaction (a Guest asking the Advisor questions about a tenant's real operational data would be a real access-control question, not a UX one, out of this document's scope) |

## 10. Cross-journey findings (City-specific)

1. **Three personas are meaningfully vision-only for City specifically** (Client, Partner, Guest) —
   consistent with `USER_JOURNEYS.md`'s own honesty about these roles platform-wide, not a new finding,
   but restated here because a reader of only this document should not come away thinking City has
   customer-facing access today.
2. **Developer is the one persona whose City journey is designed to be as short as possible** — a
   single hop into Command Center. This is worth stating explicitly: City's spatial metaphor is not
   meant to compete with keyboard-first navigation for every persona; §3 (`CITY_NAVIGATION_GUIDE.md`)
   should not assume every persona wants to "live" in the map view.
3. **Operator is the persona most dependent on still-unbuilt Simulation features** (`CITY_SIMULATION.md`
   §2's agent movement, queue visualization) — of everyone documented here, an Operator's daily
   workflow benefits most directly from `SPRINT_CG_4_RESULT.md`'s Phase 3 roadmap items.

## Related documents

`USER_JOURNEYS.md` (the platform-wide journeys this document expands one stop of), `CITY_RUNTIME.md`/
`CITY_BUILDING_STATES.md`/`CITY_EVENTS.md`/`CITY_CAMERA.md`/`CITY_SIMULATION.md` (Sprint CG-4, the
mechanism behind every "real" claim about building/district state above), `CITY_NAVIGATION_GUIDE.md`
(the navigation surfaces referenced throughout), `FUTURE_RUNTIME.md` (where Client/Partner/Guest
become real).
