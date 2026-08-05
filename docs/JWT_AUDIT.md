# JWT Audit — Sprint 37.2

## Implementation map

| Concern | Location |
|---------|----------|
| IAM signing secret | `platform_security.jwt_secrets.resolve_iam_signing_secret` |
| Access / refresh | `platform_identity.jwt_service.JWTService` |
| Management auth | Bearer JWT or `X-API-Key` |
| CRM tokens | `api/crm_api.py` (HS256 via `JWT_SECRET`) |
| Defaults | Rejected in production/staging by ConfigurationCenter + secret_policy |

## Controls verified

| Control | Status |
|---------|--------|
| Insecure defaults (`change-me-in-production`) blocked in prod/staging | PASS |
| Algorithm constrained (HS256) | PASS |
| Expiry (`exp`) enforced | PASS |
| Refresh rotation + jti revoke | PASS (single process) |
| Staging shares fail-closed gates | PASS (37.2) |
| JWT_SECRET not usable as CRM API key in prod | PASS (37.2) |

## Findings

| ID | Pri | Issue | Effort |
|----|-----|-------|--------|
| J1 | P1 | Revocation set is in-memory — multi-worker / restart gap | 2–3d (Redis denylist) |
| J2 | P2 | CRM uses legacy JWT path parallel to IAM | 1–2d migrate |
| J3 | P2 | Settings model still declares placeholder defaults (load-time only) | 0.5d |
| J4 | P3 | Access token default minutes tunable; document ops runbook | 0.5d |

## Verdict

**JWT validated** for enterprise fail-closed operation. No Critical signing/validation flaws after 37.2.
