# Pilot Handbook — Sprint 32.0

## Unified pilot operation

1. **Organization onboarding** — Identity / Organizations pages; hub tenancy.
2. **Workspace creation** — `/workspace` list + ecosystem routes.
3. **User invitation** — Identity invite APIs exist; dedicated pilot invite UI deferred (document gap).
4. **Role assignment** — Roles / Permissions; validate journeys on `/pilot`.
5. **First login** — `/login` → JWT/ISAM session.
6. **Business activation** — Open ecosystem LiveWorkflow → Run workflow.
7. **AI activation** — `/platform-builder/ai-team` + Concierge (shared platform layers).

## Ecosystem entry points

| Ecosystem | Route |
|-----------|-------|
| Automotive | `/workspace/auto` |
| Beauty | `/workspace/beauty` |
| Cafe | `/workspace/cafe` |
| Agriculture | `/workspace/agro` |
| Legal | `/workspace/legal` |
| Bidex | `/workspace/crypto` |
| Drone | `/workspace/drone` |

## Feedback

Use Pilot Dashboard Central Feedback. Every item receives a trace id and severity.

## Production gate

Before inviting external pilot users, run `/pilot/production` → Refresh probes → Run EPD gate.
