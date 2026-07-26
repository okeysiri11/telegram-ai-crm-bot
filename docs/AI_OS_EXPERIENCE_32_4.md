# AI Operating System Experience — Sprint 32.4

Platform Builder **v1.50.0** · Sprint **32.4**

## Goal

Создать ощущение полноценной AI Operating System: AI Concierge сопровождает пользователя на всех основных экранах без новых Engine / Dashboard / Workspace.

## Constraints

- **No new Engine**
- **No new Dashboard**
- **No new Workspace**
- Reuse: AI Core, Workspace Engine, Mission Control, Dashboard, Enterprise City, AI Concierge, AI Team, Notification Center, Knowledge, Personalization / First Entry, Command Center (Ctrl+K), live-ops, contextEngine

## Delivered

### 1. Global AI Concierge

Compact dock in `FullLayout` (`AiOsExperienceChrome`): state, recommendations, active AI tasks, quick actions (AI / Search / Commands / Snapshot). Collapsible; no separate page required.

### 2. Context Awareness

`TelemetryRouterBridge` syncs pathname → `contextEngine` (workspace, organization, role, department/ecosystem, `currentModule` via `sectionKeyFromPath`). UI shows section · company · role · ecosystem.

### 3. Smart Suggestions

`smartSuggestions.ts` — 2–5 path-aware recommendations (CRM, Knowledge, City, Analytics, Dashboard, AI, Finance, default).

### 4. Workspace Pulse

Compact strip: AI · CRM · Automation · Notifications · Health (from live-ops + Notification Center).

### 5. Universal Command Palette

Extended `quickActions` + `aiCommands` + role/module-aware `suggestions` for Mission Control, City, Concierge, AI Team, Executive Dashboard, recommendations.

### 6. Executive Snapshot

In-chrome panel: what’s happening / needs attention / AI recommends — links to Executive Mode & Mission Control.

### 7. UX Polish

Chrome stays above page content with Global Workspace Bar; context preserved across routes; Concierge collapse without losing route.

## Architecture note

Presentational chrome over existing live-ops polling (shared fetch), first-entry personalization, command-center UI hooks, and workspace context helpers.
