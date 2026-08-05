# API Compatibility — Sprint 37.4

## Contract freeze

| Constant | Value | Location |
|----------|-------|----------|
| `PLATFORM_API_VERSION` | `v1` | `platform_api/contracts.py` |
| `API_CONTRACT_VERSION` | `1.0.0` | same |
| Management prefix | `/management/v1` | `platform_api/versioning.py` |
| Public prefix | `/api/v1` | same |

## OpenAPI

| Spec | Builder | Status |
|------|---------|--------|
| Management | `build_management_openapi_spec()` | PASS |
| Public | `build_public_openapi_spec()` | PASS |
| Served | `GET /management/v1/openapi.json` | Registered |

## Dual-prefix policy

Sprint 36+ engines register via `register_dual_prefix_routes`:

- Canonical: `/management/v1/<surface>`
- Public: `/api/<surface>`
- Legacy `/management/<surface>` retains deprecation headers

**No breaking API changes in 37.4.**

## Compatibility checks

| Check | Result |
|-------|--------|
| Frozen `/api/v1` register path | Present (`api/v1`) |
| Envelope / pagination contracts | Present |
| create_app mounts management + hub + verticals | PASS |
| Health contracts | `/liveness`, `/readiness`, `/health` |

## Residual

| Pri | Item | Effort |
|-----|------|--------|
| P2 | Generate and diff OpenAPI artifact in CI | 1d |
| P3 | Sunset timeline for legacy `/management` without v1 | 0.5d ops |
