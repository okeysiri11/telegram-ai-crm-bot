# Release Candidate (RC1)

Sprint **26.8** / Platform **v9.1.0-rc1** — Enterprise Platform Release Candidate.

First full Release Candidate of the AI Enterprise Platform: final integration of web, identity, workspace, navigation, command center, applications, AI stack, security and observability into a single verified whole.

## API

Base: **`/api/release/v1`**

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/health` | RC readiness |
| POST | `/bootstrap` | Bootstrap RC suite |
| GET | `/inventory` | Architecture inventory |
| GET | `/dashboard` | Release Candidate Dashboard payload |
| GET | `/health-report` | Full Platform Health Report |
| GET | `/integration` | Module integration audit |
| GET | `/registry` | Application / platform registry scan |
| GET | `/routes` | React + API routes audit |
| GET | `/security` | RBAC / isolation review |
| GET | `/performance` | Performance surface review |
| GET | `/documentation` | Documentation completeness |

## Packages

- `platform_enterprise_release_candidate/`
- `applications/enterprise_hub/release_candidate/`
- `src/web/release/` → `/release`

## Gates

Platform Integration · Application Registry · Routes Audit · Security Review · Performance Review · Documentation Review · Platform Health Report · Final Validation

## Status

**Release Candidate Ready** when overall readiness ≥ 90% and zero critical security issues.
