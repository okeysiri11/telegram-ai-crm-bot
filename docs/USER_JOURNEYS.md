# User Journeys — Ten Personas Across the Enterprise AI OS

**Status:** permanent, living document. Documentation only — no source code should be modified as a
result of reading this document. Every journey below is grounded in real, shipped navigation surfaces
(`DESKTOP.md`, `ENTERPRISE_CITY_BIBLE.md`, `COMMAND_CENTER.md`, `DASHBOARD.md`,
`AI_PRODUCTION_CENTER_BIBLE.md`) — vision-only steps are marked explicitly, never blended in silently.

## 0. Shared journey substrate (real, reused by every persona below)

| Stage | Real mechanism every journey below reuses |
|---|---|
| Login | `/login` (`LoginPage`), MFA at `/auth/mfa`, session-expired/locked/access-denied states all real routes |
| Navigation | Desktop Launcher/Dock (`Cmd/Ctrl+Space`, `DESKTOP.md`) → City or direct app; Command Palette (`⌘K`, `ENTERPRISE_NAVIGATION.md` §8) from anywhere |
| AI interaction | The one Executive Advisor persona (`08_AI_PERSONALITY.md`), reachable via AI Dock, Palette AI mode (`⌘⇧P`), or the AI Command Center panel (`COMMAND_CENTER.md`) |
| Notifications | One `notificationStore` — toast (6s) + persistent panel + bell badge, identical across Desktop/Production/City/Command Center (`ENTERPRISE_NAVIGATION.md` §12, confirmed cross-module-unified by `INTEGRATION_HUB.md`) |
| Approvals | The real, structurally-enforced Approval stage in the Production Center pipeline (`AI_PRODUCTION_CENTER_BIBLE.md` §4) — the only real approval gate documented in this platform today; other domains (CRM deal approval, etc.) are not confirmed to have an equivalent real gate and are marked vision where assumed |
| Reports | Real Dashboard profiles (`DASHBOARD.md`: CEO/Manager/Sales/Developer/Finance/Administrator) and Analytics Center (`MODULES.md`) |
| End of session | `/auth/logout` (`LogoutPage`) — session state (Desktop windows, Workspace tabs, City viewport) persists across the *next* login via the Integration Hub's `sessionCoordinator` (`INTEGRATION_HUB.md`), it does not need to be manually saved |

**Six of the ten personas below map directly onto a real, shipped Dashboard profile** (`DASHBOARD.md`):
CEO, Administrator, Developer, Sales Manager (→ "Sales" profile). The remaining four (Marketing
Manager, Production Manager, Designer, Client, Partner, Investor — six, not four; see the honesty note
in each) have **no real profile yet** — their journeys are grounded in real generic navigation but their
role-specific dashboard view is marked vision.

---

## 1. CEO

Real profile: **CEO** (`DASHBOARD.md`: Health, finance, CRM, AI).

| Stage | Journey |
|---|---|
| Login | `/login` → MFA (real) → lands in Enterprise City at the Enterprise district's Dashboard building (`ENTERPRISE_CITY_BIBLE.md` §8's "login lands in City" navigation model) |
| Navigation | City for whole-org glance → Dashboard building for the Morning Brief (`EP_01_EXECUTIVE_EXPERIENCE.md`) → drills into a flagged district (e.g., Finance glowing amber) |
| AI interaction | Executive Advisor surfaces "Needs attention" items proactively (`08_AI_PERSONALITY.md`'s Observation→Why→Action→Impact); AI Command Center panel shows aggregate agent activity across the org |
| Decision points | Approve/escalate a flagged item from the Brief; ask the Advisor "why is Finance amber" and get a direct answer, not a redirect |
| Notifications | Executive-priority notifications surface first (real bucketing in `notificationStore`, `ENTERPRISE_NAVIGATION.md` §12) |
| Approvals | Real Production Center Approval stage if the flagged item is a creative/campaign asset (`AI_PRODUCTION_CENTER_BIBLE.md` §4); otherwise vision (no confirmed general cross-domain approval queue for a CEO today) |
| Reports | Real CEO Dashboard profile widgets: System Health, Finance Summary, CRM Summary, AI Status |
| End of session | `/auth/logout` — City focus and Dashboard layout restore automatically next login |

## 2. Administrator

Real profile: **Administrator** (`DASHBOARD.md`: full catalog).

| Stage | Journey |
|---|---|
| Login | `/login` → lands in Desktop (`/desktop`) rather than City by default, since an admin's daily work is configuration, not org glance |
| Navigation | Desktop Launcher → Settings app, Security Center (City's Security district, `ENTERPRISE_CITY_BIBLE.md` §2), Command Center's Developer section |
| AI interaction | AI Command Center panel used diagnostically — checking provider/voice/MCP/memory health probes (`COMMAND_CENTER.md`), not conversationally |
| Decision points | Enable/disable a vertical module (real `platform_management` vertical toggle, `MODULES.md` §4) — this decision changes which City buildings/districts render for every user, not just the admin |
| Notifications | System/error-priority notifications (job failures, health degradation) |
| Approvals | Reviews plugin install/enable requests (real `platform_plugins` management surface, `MODULES.md` §4) |
| Reports | Full Dashboard catalog — every widget, not a curated subset |
| End of session | Logout; admin-made configuration changes (vertical enablement, RBAC) persist server-side, independent of session state |

## 3. Developer

Real profile: **Developer** (`DASHBOARD.md`: CPU, memory, MCP, queue, agents).

| Stage | Journey |
|---|---|
| Login | Lands in Desktop, Dock pinned to Developer Tools / Command Center |
| Navigation | City's Developer district (`CITY_DISTRICTS.md`, real) → Command Center's Developer keyboard shortcuts (`ENTERPRISE_NAVIGATION.md` §16) |
| AI interaction | AI Command Center panel used to inspect real agent/job/queue state; the "Builder Agent" in the Multi-Agent OS's real Agent Registry (`ENTERPRISE_AI_OS.md`) is this persona's most relevant AI collaborator, once wired to a real frontend surface |
| Decision points | Retry a failed background job (`jobManager.retry`, real UI) vs. escalate to platform engineering |
| Notifications | Job/queue/error-priority notifications dominate this persona's bell badge |
| Approvals | N/A for this persona in most flows — a developer typically triggers work, not approves external publication |
| Reports | Developer Dashboard profile: CPU, memory, MCP, queue depth, active agents — **honesty note:** these are currently simulated client-side metrics (`ENTERPRISE_AI_OS.md` §6), not real host telemetry, which this persona specifically is positioned to notice first |
| End of session | Logout; open Desktop windows and their exact geometry restore next login (`WINDOW_MANAGER.md`) |

## 4. Sales Manager

Real profile: **Sales** (`DASHBOARD.md`: CRM, calendar, pipeline).

| Stage | Journey |
|---|---|
| Login | Lands in Workspace or City's CRM district building directly |
| Navigation | CRM Center (real Hub module) → Sales/Marketing buildings within the CRM district (`CITY_DISTRICTS.md`) |
| AI interaction | The Multi-Agent OS's real "Sales Agent" (qualify, CRM capabilities, `ENTERPRISE_AI_OS.md` reference section) is this persona's named AI collaborator — real backend capability, not yet wired to a real frontend consumer |
| Decision points | Reassign a deal, escalate a stalled pipeline stage |
| Notifications | CRM-priority: new lead, stalled deal, quota-risk flags |
| Approvals | Vision — a deal-approval workflow analogous to Production Center's Approval stage is not confirmed to exist for CRM specifically |
| Reports | Sales Dashboard profile: CRM, calendar, pipeline widgets |
| End of session | Logout; CRM filter/sort state is workspace-tab-scoped, restores with the tab |

## 5. Marketing Manager

**No real Dashboard profile exists for this persona** — honesty note, not an oversight this document is
hiding.

| Stage | Journey |
|---|---|
| Login | Lands in Workspace; no dedicated profile to land on (vision: a "Marketing" Dashboard profile) |
| Navigation | Production Center's Social Content Studio and Marketing Campaign Builder concepts (`AI_PRODUCTION_STUDIO.md` §13, still vision — the real Production Center shell has Reels/Ads studio cards but no real generation behind them, `AI_PRODUCTION_CENTER_BIBLE.md` §0) |
| AI interaction | Creative Brief Agent (vision, `AI_PRODUCTION_STUDIO.md` §19) would be this persona's primary AI collaborator once built |
| Decision points | Approve a campaign asset before it enters the real Approval pipeline stage |
| Notifications | Campaign performance / publish-status notifications — vision, since real publishing does not exist yet (`AI_PRODUCTION_CENTER_BIBLE.md` §0) |
| Approvals | The one real approval gate in the platform (Production Center, `AI_PRODUCTION_CENTER_BIBLE.md` §4) — this persona is its most natural real-world user once generation is real |
| Reports | Vision — no real marketing-specific analytics surface confirmed; Analytics Center (`MODULES.md`) is the generic real destination today |
| End of session | Logout; Production Center session state persists (`ews_ai_production_v1`) |

## 6. Production Manager

**No real Dashboard profile; "Production" here means operational/manufacturing production
(`ENTERPRISE_CITY_BIBLE.md`'s Production district's Ops half), not the AI Production Center** — a
naming collision worth flagging explicitly, since the City's Production district serves both meanings
(`ENTERPRISE_CITY_BIBLE.md` §2's note that Industrial Areas folded into Production).

| Stage | Journey |
|---|---|
| Login | Lands in City's Production district → Mission Control building (real, `ENTERPRISE_CITY.md` §9.1) |
| Navigation | Mission Control for live operations; vertical-specific operational apps (`drone_platform`, `port_erp`, `MODULES.md` §8) for domain detail |
| AI interaction | Ops Copilot (real name in the Multi-Agent OS's Agent Registry, `ENTERPRISE_AI_OS.md`) — triage/workflow capabilities |
| Decision points | Escalate a Mission Control alert; approve a workflow exception |
| Notifications | Operational alerts — highest urgency treatment in this persona's journey |
| Approvals | Workflow exception approvals via `platform_workflows` (real backend, `MODULES.md` §5) |
| Reports | Mission Control's live status view; no dedicated "Production Manager" Dashboard profile exists (vision gap) |
| End of session | Logout; Mission Control does not currently persist a "last viewed alert" state — a gap worth naming for a future sprint |

## 7. Designer

**No real Dashboard profile.** Primary real surface: Production Center's Creative/Brand/Asset studios
(shell real, generation vision, `AI_PRODUCTION_CENTER_BIBLE.md`).

| Stage | Journey |
|---|---|
| Login | Lands in Production Center directly (`/production-studio`) |
| Navigation | Studios tab → Image/Video/Creative/Brand/Template studio cards (real navigation, `PRODUCTION_CENTER.md`) |
| AI interaction | Brand Compliance Agent (vision, `AI_PRODUCTION_STUDIO.md` §19) checks output against brand rules before this persona's work reaches Approval |
| Decision points | Choose a Style Preset (vision, `AI_PRODUCTION_STUDIO.md` §18 — no real preset gallery exists, only the 3-theme + custom-brand system, `07_DESIGN_SYSTEM.md`) |
| Notifications | Render-complete notifications (real UI over currently-simulated job data, `ENTERPRISE_AI_OS.md` §12) |
| Approvals | Submits into the real Approval pipeline stage |
| Reports | Asset Library / Media Manager view (real catalog, no real blob storage yet, `MEDIA_MANAGER.md`) |
| End of session | Logout; draft work in the Prompt Library persists to `ews_ai_production_v1` (session-scoped, not durable long-term, `ENTERPRISE_AI_OS.md` §8) |

## 8. Client

External persona — real portal precedent exists (`CustomerPortalPage`, route `/portals/customer`).

| Stage | Journey |
|---|---|
| Login | `/login` with client-scoped credentials → real `CustomerPortalPage` |
| Navigation | Scoped to the Customer Portal shell — no Desktop/City access (RBAC-gated, `ENTERPRISE_AI_OS.md` §11) |
| AI interaction | Vision — no confirmed client-facing AI assistant surface distinct from the internal Executive Advisor |
| Decision points | Approve a quote, respond to a request — domain-specific, not confirmed as a generalized "client decision" mechanism |
| Notifications | Vision for client-facing notification delivery beyond in-portal state |
| Approvals | Client-side approval of an external-facing document/quote — vision |
| Reports | Vision — no confirmed client-facing reporting surface |
| End of session | Logout via the same `/auth/logout` mechanism, scoped session |

## 9. Partner

External persona — **no dedicated real portal exists** (only Customer/Employee/Owner portals are real,
`App.tsx`). The closest real structural concept for a partner relationship is a City Portal
(`ENTERPRISE_CITY_BIBLE.md` §12) — vision, not built.

| Stage | Journey |
|---|---|
| Login | Vision — a real partner-scoped login path is not confirmed to exist distinctly from Customer Portal |
| Navigation | Vision — City Portals (`ENTERPRISE_CITY_BIBLE.md` §12) are the designed mechanism for a partner organization to see only explicitly-shared buildings; not built |
| AI interaction | Vision |
| Decision points | Vision — e.g., accepting a shared marketplace listing |
| Notifications | Vision |
| Approvals | Vision |
| Reports | Vision — cross-organization reporting has no real precedent anywhere in this documentation set |
| End of session | Vision |

**This entire journey is more vision than real** — flagged explicitly rather than papered over with
plausible-sounding steps, per `02_PRODUCT_PHILOSOPHY.md` principle 9. Building a real Partner journey
is downstream of `FUTURE_RUNTIME.md`'s Cross-company collaboration section.

## 10. Investor

External/read-only persona — **no real surface exists for this persona at all.** The closest real
analog is the Owner Portal (`OwnerPortalPage`, route `/portals/owner`), which this document does not
assume is investor-appropriate without a real access-scope decision (an investor should almost
certainly see less than an owner).

| Stage | Journey |
|---|---|
| Login | Vision — no confirmed investor-scoped credential/portal |
| Navigation | Vision |
| AI interaction | Vision — an investor-facing summarization persona would need its own tone calibration distinct from the internal Executive Advisor (a real design question, not answered here) |
| Decision points | Vision |
| Notifications | Vision |
| Approvals | None expected — an investor persona is read-only by nature |
| Reports | Vision — the real CEO Dashboard profile's financial widgets are the closest existing precedent for what an investor report might reuse, but no real investor-scoped, read-only reporting surface exists |
| End of session | Vision |

**Like Partner, this journey is almost entirely vision.** It is included in full, rather than omitted,
specifically so a future sprint building investor-facing reporting starts from an honest list of real
precedent (Owner Portal, CEO Dashboard profile) instead of inventing one from nothing.

---

## Cross-journey findings

1. **Six of ten personas have a real Dashboard profile; four do not** (Marketing Manager, Production
   Manager, Designer, and — more fundamentally — Client/Partner/Investor lack any comparable
   role-specific view). Adding Marketing/Production/Designer profiles to `DASHBOARD.md`'s real profile
   list is a low-effort, high-value near-term recommendation.
2. **Partner and Investor are almost entirely vision journeys.** Both depend on capabilities
   (`FUTURE_RUNTIME.md`'s Cross-company collaboration, Portals) that don't exist yet — this is the
   correct, honest status, not a documentation gap to quietly fill with plausible fiction.
3. **The Production district naming collision** (operational Production vs. AI Production Center) is
   real and should be resolved in `ENTERPRISE_CITY_BIBLE.md`'s next update — the Production Manager and
   Designer journeys above land in genuinely different places despite sharing the word "Production."
4. **Only one real, cross-domain approval gate exists today** (Production Center). Every journey above
   that assumes a domain-specific approval step (CRM deal approval, workflow exceptions) is marking
   that step as vision unless it names real backend evidence — a future audit should confirm whether
   `platform_workflows`' approval-action pattern (noted in `AI_PRODUCTION_STUDIO.md` §0's research)
   extends to any of these domains for real today.

## Related documents

`ENTERPRISE_AI_OS.md` (the OS-level lifecycle every journey above moves through), `DASHBOARD.md` (the
six real profiles), `DESKTOP.md`, `ENTERPRISE_CITY_BIBLE.md`, `COMMAND_CENTER.md`,
`AI_PRODUCTION_CENTER_BIBLE.md` (the real navigation surfaces every journey names), `08_AI_
PERSONALITY.md` (the one AI voice every journey's "AI interaction" row assumes), `FUTURE_RUNTIME.md`
(where Partner/Investor journeys become real), `TECH_DEBT.md` (candidate new items: missing Marketing/
Production/Designer Dashboard profiles; the Production naming collision).
