# Enterprise City 2D — UX Architecture

**Role:** Lead UX Architect. Documentation only, no code written.

**Grounding note:** role-based visibility below is designed against the real canonical Identity Core
role registry (`docs/UNIFIED_IDENTITY_34_2A.md`, Sprint 34.2A): `owner, ceo, administrator, manager,
employee, operator, partner, dealer, client, guest`. This is a direct, fortunate match — "CEO" is
already a real canonical role, not something this document invents. No second role vocabulary is
proposed anywhere in this document.

## 1. Role-based experiences — same city, different visibility

The city is one real object graph; every role sees a real, permission-filtered projection of it,
composed via the same real Visibility model this engagement has used since CQ-16
(`docs/DIGITAL_TWIN_STANDARDS.md` §3) — never a second city.

| Role | What's visible | Landing view | Notes |
|---|---|---|---|
| Owner | Everything, including Owner-only districts (Security, Developer Zone in Owner mode, Administration) | City-wide overview, zoomed to "City View" (`docs/CITY_NAVIGATION.md`'s named zoom levels, CG-9) | The one role with real cross-district visibility by design |
| CEO | Executive-relevant districts (Analytics, Finance, CRM at aggregate level) prioritized; operational districts visible but de-emphasized | Analytics/Command Center district, real `EnterpriseHealthSnapshot` composite overlay | Distinct from Owner — CEO sees business health, not platform internals (Developer Zone, Security Center hidden) |
| Manager | Own department's district(s) + cross-department districts their real `Membership.role` scope covers | Their department building, real `DashboardScope`-filtered (`docs/OPERATIONAL_DASHBOARDS.md`, CQ-17) | |
| Employee | Own building + "My Day" personal overlay (real `LifeEvent` stream scoped to them) | Their own desk/building, per real `DAILY_OPERATIONS_MODEL.md` | |
| Partner | Only districts/buildings covered by a real `Relationship` at sufficient trust tier, composed per `docs/CROSS_ORG_DAILY_COOPERATION.md` §2 | A "Shared with us" district view, not the full city | Never sees internal-only districts regardless of zoom |
| Customer/Client | A minimal city fragment — their own vendor's headquarters + their own deal/project buildings only | A single-building focused view, not a city-wide map | Per `docs/CLIENT_EXPERIENCE.md`'s (CQ-30.7) finding that Client needs a portal-shaped experience, not a smaller internal shell — the city view for this role should look and feel like "your relationship with this company," not "a smaller version of the employee city" |
| Developer | Developer Zone district + real Architecture/Kernel overlays (`docs/OWNER_EXPERIENCE.md`'s real `/kernel` route) | Developer Zone, with real system-health buildings emphasized | A technical lens on the same city, not a separate tool |
| AI Agent | Programmatic, not visual — an agent "moving through" the city is a real `LifeEvent`/`CityVisEventName` stream other roles observe, not a rendered viewport the agent itself consumes | N/A — agents are city *content*, not city *users* | Important distinction: "AI Agent experience" means how agents appear to humans, not a UI for the agent |

## 2. Interaction design

| Interaction | Design |
|---|---|
| Zoom | Reuses real named zoom levels (City View / District View / Building Focus, `docs/CITY_NAVIGATION.md`, CG-9) — continuous zoom with three semantic snap points, not free-floating |
| Pan | Drag, plus keyboard arrow-key nudge for accessibility (not confirmed in the current real implementation — a genuine new addition this document recommends) |
| Search | Reuses the real Global Search (`ENTERPRISE_NAVIGATION.md`), scoped to city-addressable entities (buildings, districts, companies, citizens) |
| Filters | New — toggle real `VisualizationLayerId` layers (`districts/buildings/citizens/companies/assets/activities/traffic/overlays`, Sprint 29.5) on/off, per `docs/CITY_NAVIGATION.md` §4 (CQ-30.1) |
| Selection | Click selects one building/district, opens a real object-information panel (composes real entity data, per CQ-30.1's design) |
| Multi-selection | **New** — shift-click or drag-rubber-band selects multiple buildings for a batch context action (e.g., "compare these three companies' HQ") — no real precedent exists today, genuinely new interaction |
| Context actions | Right-click menu — real actions already available elsewhere (Open, Focus, Favorite, Assign Citizen, View Timeline), per `docs/CITY_NAVIGATION.md` §4 |
| Keyboard shortcuts | Real `⌘/Ctrl+K` command palette (confirmed live, not the `TD-40` orphaned copy); recommend adding `+`/`-` for zoom, arrow keys for pan, `Esc` to deselect |
| Drag & Drop | **New, use with restraint** — the only real recommended use case is *assignment* (drag a citizen icon onto a building to assign them there), which should call the real `lifeEngine.enterOffice()`/`assignLocation()` API, never a visual-only drag; do not add drag-to-rearrange for buildings themselves, since building position is data-driven, not user-arranged |
| Mini-map | **New** — a small fixed-position overview showing the current viewport as a rectangle over the full city, using the same real percentage-space coordinates the main map uses (no new coordinate system) |
| Bookmarks | Reuses the real Favorites system (`favoritesManager`, `cityNavigation.ts`) |
| Live indicators | Reuses the real Life Engine → `city_update` bridge (`docs/DAILY_OPERATIONS_MODEL.md` §3) — a building's visual state (occupancy glow, activity pulse) is a direct read of real `BuildingOccupancy`/`LifeEvent` data |
| Animations | Governed by the real performance-budget discipline already established in the Graphics Engine's design (`docs/CITY_SIMULATION.md`, CG-4/CG-9) — fixed ceilings, not unbounded per-entity animation |

## 3. Live data — what "real time" means precisely

Every live signal in the city must trace to one of these real sources — this document does not invent
a new telemetry pipeline:

| Brief example | Real source |
|---|---|
| Employees online | Real `digitalCitizenEngine`/`LifePresence` (Sprint 29.1/29.2) |
| AI agents working | Real `aiAgentRuntime` status (`idle/busy/waiting/error/offline`) |
| Running workflows | Real `workflow_executed`/`workflow_completed` `LifeEvent`s |
| CRM activity | Real `businessInteractions`/`business_visit` events |
| Notifications | Real `NotificationBucket` (composed per `docs/OPERATIONAL_NOTIFICATIONS.md`, CQ-17) |
| Tasks | Real `Task`/`DealTask` status changes (pending the `TD-50` reconciliation, CQ-19) |
| Meetings | Real `LifeMeeting` status (`scheduled/active/ended`) |
| Files | Real document storage events, where they exist (`EBN_VERIFIED_DOCUMENTS.md`, CQ-10) |
| Projects | Real `ProjectParticipant`/future `Project` entity (`TD-51`) once it exists |
| Vehicle tracking | Real `LifeVehicle` status + `applications/port_erp`'s real AIS/GPS for logistics-district vehicles specifically |
| Drone missions | Real `drone_platform` — **not yet bridged into the city's event stream**, flagged as new integration work, not a re-use of an existing bridge |
| Manufacturing status | Real `workflow_executed` payload data, generic — no dedicated manufacturing-output model exists yet (`docs/COMPANY_OPERATING_MODES.md`, CQ-17) |
| Crypto deals | Real `crypto_enterprise` — **not yet bridged**, same flag as Drone missions |

**The pattern**: five of thirteen brief examples are already real and bridged; the rest are either real-
but-unbridged (Drone, Crypto — genuinely new integration work, not a redesign) or generically-real via
the workflow event stream (Manufacturing). No live-data signal in this document is proposed as
simulated or fabricated.

## Non-goals

- No AI-agent-facing UI — agents are content in this city, not consumers of it.
- No drag-to-rearrange building layout — position stays data-driven.
- No new telemetry/event system — every live signal composes a real, already-cited source.

## Related documents

`docs/ENTERPRISE_CITY_2D_VISION.md` (this document's companion), `docs/UNIFIED_IDENTITY_34_2A.md`
(real canonical roles), `docs/DAILY_OPERATIONS_MODEL.md`/`docs/OPERATIONAL_DASHBOARDS.md` (CQ-17),
`docs/CROSS_ORG_DAILY_COOPERATION.md`/`docs/CLIENT_EXPERIENCE.md` (CQ-17/CQ-30.7), `docs/CITY_
NAVIGATION.md`/`docs/CITY_NAVIGATION_GUIDE.md` (CG-5/CG-9/CQ-30.1).
