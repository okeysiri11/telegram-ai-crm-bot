# Incident Response

**Sprint:** 32.4 · **Module:** `platform_security.incident_center.IncidentCenter`

## Actions

| Action | Method |
|---|---|
| Open incident | `open` |
| Auto lock / Emergency mode | `auto_lock` / `enable_emergency_mode` |
| Kill sessions | `kill_session` |
| Revoke tokens | `revoke_token` |
| Disable API keys | `disable_api_key` |
| Disable AI providers | `disable_ai_provider` |
| Threat escalation | `escalate` |

Emergency mode disables API keys and AI providers globally via `is_*_disabled` checks.

Wire callers (ISAM / APH / middleware) must consult Incident Center before executing privileged operations.
