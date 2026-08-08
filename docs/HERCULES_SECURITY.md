# Hercules Security

- **Sandbox** default on (`HERCULES_SANDBOX`)
- **Rate limits** per actor (default 120/min)
- **Role validation** helper for owner/admin
- **Audit log** of complete/cancel actions
- Secrets stay in Provider Vault / platform_security — Hercules does not store API keys
- Execution isolation: in-process lease + queue; production can bind to container quotas

Telegram Hercules panel is Owner/Developer gated (`_is_developer`).
