# Sprint CQ-30.1 — UX Architecture: Global Information Architecture & AI Experience

**Sprint:** CQ-30.1 — Architecture + UX Design. Documentation only, `src` not modified.

**Do not duplicate:** `docs/ENTERPRISE_NAVIGATION.md` (real, Sprint 26.5, `src/web/navigation/` —
Navigation Manager, Menu Engine, Command Palette, Global Search, Search Index, Favorites, History,
Shortcuts, Breadcrumbs) already specifies most of the platform's navigation engine layer in depth.
This document does not re-specify it — it composes the real engine layer into the Beta's global IA and
adds the one layer that engine doesn't own: which surfaces exist, in what hierarchy, for a first-time
Beta user. Confirmed this sprint: `src/web/src/navigation/` (Sidebar.tsx/TopNavigation.tsx/
Breadcrumbs.tsx — the rendered shell) correctly imports `navigationManager` from `src/web/navigation/
managers/` — **not a duplication**, a legitimate two-layer split (engine vs. rendered shell), checked
explicitly so this document doesn't misreport it as one.

## 1. Global Information Architecture (brief §1)

| Surface | Real foundation | Beta design |
|---|---|---|
| Main Menu | Real `shellModuleRegistry`/`useShellPreferences` (`src/web/src/shell/enterprise/`) | Module registry driven — every top-level destination is a registered shell module, not a hardcoded list; this is already the real pattern, reused |
| Sidebar | Real `src/web/src/navigation/Sidebar.tsx`, category-grouped (`ShellModuleCategory`) | Beta grouping: **Дашборд** (Dashboard) → **Город** (City) → **Бизнес** (Business Network/CRM/Deals) → **Операции** (Operations/Calendar/Tasks) → **AI** (Agents/Production) → **Аналитика** (Intelligence) → **Организация** (Settings/Team) — see `RUSSIAN_UI_DICTIONARY.md` for the canonical term per item |
| Top Navigation | Real `TopNavigation.tsx` | Org switcher (left) · global search (center) · notifications + user menu (right) — a standard, low-risk layout, not a novel one |
| Breadcrumbs | Real `Breadcrumbs.tsx` + `CITY_NAVIGATION_GUIDE.md` §7 (City-specific breadcrumbs, real) | Reused unchanged; Beta adds no new breadcrumb source |
| Quick Actions | Real Command Palette (`⌘/Ctrl+K`, `UniversalCommandPalette.tsx`, live per `TD-40`'s finding that this is the *live* one, not the orphaned `navigation/components/CommandPalette.tsx`) | Beta must launch from the **live** palette only — `TD-40`'s orphaned copy must not be resurrected by a Beta polish pass |
| Search | Real Global Search / Search Index (`ENTERPRISE_NAVIGATION.md`) | Unchanged; Beta scope is wiring result categories (City buildings, Deals, Citizens, Documents), not a new search engine |
| Notifications | Real three-vocabulary composition (`docs/OPERATIONAL_NOTIFICATIONS.md`, CQ-17) | Beta surfaces `NotificationBucket` (`unread/mentions/warnings/errors/success/jobs/all`, real, `notificationStore.ts`) — no new bucket taxonomy |
| User Menu | Real `useAuthStore`/`identityManager.ts` | Profile · Settings · Language (see `RUSSIAN_UI_DICTIONARY.md`) · Sign out |
| Organization Switcher | Real `organizationManager` (`CITY_INTEGRATIONS.md` §3, CG-6) | Beta: single-org default, switcher visible but simplified for users with exactly one org (per `docs/ENTERPRISE_V1_READINESS.md`'s "medium businesses: mostly ready" finding — most Beta users will have one org) |

## 2. AI Experience (brief §7)

**Do not duplicate:** real `aiAgentRuntime` (simulated status model: `idle/busy/waiting/error/offline`,
CG-8), real `PersonalAiAssistant` registry (`PERSONAL_AI.md`, CQ-12), real `AITeamCenterPage.tsx`
(`src/web/platform-builder/ai-team/`) and `AITeamCollaborationPanels.tsx`
(`src/web/src/ai-team-collaboration/`) already implement agent cards, team collaboration panels, and
real Collaborative AI Decision Engine capability (Sprint 28.8). This section composes them for the
Beta's user-facing flow, not a new agent framework.

| Brief item | Real foundation | Beta UX |
|---|---|---|
| Agent cards | Real `AITeamCenterPage.tsx` card grid | Status badge uses real `aiAgentRuntime` status enum directly — no new status vocabulary |
| Agent profile | Real `PersonalAiAssistant` fields (kind, assignedCitizenId, active) | A profile panel: name, kind (7 real kinds, `PERSONAL_AI.md`), assigned citizen, memory summary (§ below), permissions (§ below) |
| Conversation | **No dedicated real chat UI confirmed this sprint** — flagged, not designed further; likely composes `src/chat_bridge` (TS kernel, per `CLAUDE.md`) once that connection is decided (`TD-33`) | Beta scope: text input + response stream, no voice/video — matches the platform's real, single-wired AI provider (`openrouter.py`) |
| Task assignment | Real `ProjectParticipant.assignments` (string labels, CQ-17) / real `DealTask.assigned_to` | A simple "assign to agent" action on any task-shaped real entity — reuses existing assignment fields, no new task-routing engine |
| Progress | Real `LifeEventKind`s (`workflow_executed`/`workflow_completed`, CQ-17) | A progress indicator driven by real Life Engine events for the agent's active work |
| Memory | Real `PersonalAiAssistant` + the real (if fragmented, `TD-21`) memory stacks | Beta UX shows a memory summary as a **read-only** list of recent real `AuditLog`/timeline entries tied to the agent — not a new memory browser |
| Permissions | Real composed `SpatialPermissionScope`/`AssetPermissionScope`/`Visibility` (`DIGITAL_TWIN_STANDARDS.md`, CQ-16) | An agent's permission panel is a read view over the same real composition every other entity uses — no agent-specific permission model |

## 3. Non-goals

- No new navigation engine, search engine, or notification taxonomy — every Beta surface composes a
  real, already-cited system.
- No new chat/conversation backend designed — flagged as an open gap (§2), not invented here.
- No new agent memory browser — Beta shows a read-only summary of real existing audit/timeline data.

## Related documents

`docs/ENTERPRISE_NAVIGATION.md`/`docs/WORKSPACE_INTERACTIONS.md` (real, Sprint 26.5+), `docs/TECH_
DEBT.md` (TD-40, TD-41), `docs/UI_NAVIGATION.md`/`docs/ROLE_NAVIGATION.md`/`docs/RUSSIAN_UI_DICTIONARY.
md` (CQ-30.1 siblings), `docs/PERSONAL_AI.md` (CQ-12), `docs/OPERATIONAL_NOTIFICATIONS.md` (CQ-17).
