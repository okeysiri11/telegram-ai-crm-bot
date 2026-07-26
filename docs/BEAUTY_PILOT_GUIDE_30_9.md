# Beauty Pilot Guide — Sprint 30.9

## How to run

1. Start API + `npm run dev` (web).
2. Login at `/login` with production credentials (ISAM; optional JWT).
3. Open `/workspace/beauty`.
4. Enter client name, email, service name.
5. Click **Execute Beauty pilot**.
6. Confirm every step is **ok** in the execution log.
7. Review reuse % card, `/pilot` metrics, Mission Control, AI Team.

## Validated capabilities

Salon CRM · Appointments · Clients · Employees · Services · Rooms/Resources · Working Hours · Calendars · Payments · Notifications · AI Team · Concierge · Marketing · Owner Dashboard · Mission Control · Analytics

## AI Team (configured, not duplicated)

| Role | Platform source |
|------|-----------------|
| AI Concierge | PB `/concierge/sessions` |
| AI Receptionist | BWS `/assistant` + AI Team assign_task |
| AI Marketing | AMO + AI Team Marketing specialist |
| AI Production | AI Team assign (utilization task) |
| AI Customer Success | AI Team assign (follow-up task) |
| AI Analytics | AI Team assign + owner dashboards |

## Observability

Bookings · conversions (workflow success) · customer sessions · AI conversations (concierge/team/AMO timings) · workflow completion · errors · performance · business events — via `pilotMetrics` + OBS.
