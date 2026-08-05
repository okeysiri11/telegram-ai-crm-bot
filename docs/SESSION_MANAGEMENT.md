# Session Management — Sprint 30.1

**Module:** `applications/enterprise_hub/security/session_manager.py`  
**API:** `/api/enterprise-isam/v1/sessions`

## Capabilities

| Feature | Implementation |
|---|---|
| Multiple sessions | One row per device/login |
| Session revocation | `action: terminate` |
| Logout from all devices | `action: terminate_all` |
| Trusted devices | `action: trust` → `trusted: true` |
| Remember me | TTL ≥ 30 days when `remember_me` |
| Last login | Derived from successful auth events |
| Active devices | `list_for_identity` / Owner Security Dashboard |

## Session record fields

`session_id`, `identity_id`, `device`, `browser`, `ip`, `ttl_seconds`, `remember_me`, `trusted`, `status`, `last_activity`, `at`

## Frontend

- `/identity/sessions` — session list UI
- Owner Security Dashboard — active sessions + «Выйти со всех устройств»
- `sessionManager.syncFromIsam` / `terminateAllRemote` / `trustRemote`

## Audit

`session_revoke_all` and related auth events land in ISAM audit store and appear on the Owner Security Dashboard.
