# Security Checklist — Sprint 32.1

| Item | Status | Notes |
|------|--------|-------|
| Authentication | Ready | ISAM + JWT + ecosystem sessions |
| Authorization / RBAC | Ready | PermissionGuard + ecosystem roles |
| Audit trail | Ready | telemetry.audit + ISAM audit |
| API security | Ready | Existing gateway + middleware |
| Rate limiting | Ready | Gateway / platform_security |
| Input validation | Ready | Existing ValidationError paths |
| Secrets | Ready (probed) | ESH health; vault docs |
| Invitation tokens | Ready | One-time create response token |
| Password reset | Partial | UI pages; backend wiring deferred |
| Email verification | Partial | Capability listed; delivery deferred |
| JWT refresh | Ready | identityApi refresh |
| Session expiration | Ready | Ecosystem + ISAM sessions |

**Do not** log invitation tokens in shared OBS dashboards for production customers.
