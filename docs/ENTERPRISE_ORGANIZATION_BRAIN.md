# Enterprise Organization Brain

Sprint **27.2** / Platform **v9.3.0** — digital intelligence of the company.

## Hub

`enterprise_organization_brain`

## API

`/api/organization-brain/v1`

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/health` | Health + readiness |
| POST | `/bootstrap` | Seed org model, board, knowledge |
| GET | `/inventory` | Architecture inventory |
| GET | `/dashboard` | Executive dashboard |
| GET | `/organization` | Companies, holdings, departments, people |
| GET | `/board` | CEO/COO/CFO/CTO/CMO/CHRO/CLO AI |
| GET | `/departments` | Department catalog |
| POST | `/departments/orchestrate` | Department orchestration |
| POST | `/decisions` | Business decision engine |
| GET/POST | `/meetings` | Executive meetings + protocol |
| GET/POST | `/knowledge` | Organization knowledge |
| GET | `/exec-dashboard` | Dashboard alias |

## Capabilities

1. **Organization Model** — holdings → companies → orgs → departments → teams → people
2. **Executive Board** — C-suite AI agents by domain
3. **Department Orchestration** — Sales through AI Department
4. **Business Decision Engine** — metrics, risks, proposals, KPI control
5. **Executive Meetings** — discuss, vote, protocol, owners
6. **Organization Knowledge** — structure, policies, KPI, processes
7. **Executive Dashboard** — company state, loads, finance, alerts

## Layout

- Library: `platform_organization_brain/`
- Hub: `applications/enterprise_hub/organization_brain/`
- Frontend: `src/web/organization-brain/`
- Knowledge: `knowledge/applications/enterprise_hub/organization_brain/`
