# Enterprise Vertical Federation

Sprint **27.3** / Platform **v9.4.0** — unified control plane for industry verticals.

## Hub

`enterprise_vertical_federation`

## API

`/api/verticals/v1`

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/health` | Health + readiness |
| POST | `/bootstrap` | Seed registry, directors, marketplace |
| GET | `/inventory` | Architecture inventory |
| GET | `/dashboard` | Unified federation dashboard |
| GET/POST | `/registry` | List / register custom verticals |
| GET | `/directors` | Vertical Executive AI directors |
| POST | `/directors/act` | Director actions + Executive AI link |
| GET | `/links` | Cross-vertical communication graph |
| GET/POST | `/communicate` | Cross-vertical messages |
| GET/POST | `/marketplace` | Publish / list vertical assets |
| GET/POST | `/knowledge` | Knowledge federation |
| POST | `/search` | Semantic search |
| GET | `/exec-dashboard` | Dashboard alias |

## Capabilities

1. **Vertical Registry** — Auto…Drone + custom verticals
2. **Vertical Executive AI** — per-vertical AI Director
3. **Cross-Vertical Communication** — CRM↔Finance, Agro↔Drone, …
4. **Unified Dashboard** — states, KPI, agents, AI usage, alerts
5. **Vertical Marketplace** — apps, agents, dashboards, workflows, …
6. **Knowledge Federation** — shared / industry / local / AI memory / semantic

## Layout

- Library: `platform_vertical_federation/`
- Hub: `applications/enterprise_hub/vertical_federation/`
- Frontend: `src/web/vertical-federation/`
- Knowledge: `knowledge/applications/enterprise_hub/vertical_federation/`
