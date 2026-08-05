# Known Limitations — Closed Beta

**Sprint:** 32.5 · Also see [`KNOWN_LIMITATIONS_1_0.md`](./KNOWN_LIMITATIONS_1_0.md) (platform GA limitations).

## Accepted for Closed Beta

| Area | Limitation |
|---|---|
| Identity counts | Owner “Users/Orgs” show **session-derived** counts (1/0) until ISAM list APIs are wired into the dashboard |
| ERP / Analytics hubs | `/erp`, `/analytics` remain thin Enterprise Module shells — operational, not full ERP product UI |
| Finance workspace | `/workspace/finance` is a bound shell; deep finance enterprise remains separate |
| Platform Builder frames | Some builders still `frameOnly` / coming-soon — **excluded** from Closed Beta surface list |
| Security Center demo | Risk/MFA numbers may seed locally when ISAM owner dashboard is unreachable (TD-67) |
| Provider status | Derived from client health tones, not a live multi-provider probe |
| Dual sprint id 32.5 | Enterprise Intelligence docs remain; this is the Closed Beta launch track |

## Not accepted (fixed this sprint)

- City Security building → placeholder `/security` hub (now `/identity/security`)
- City HR → `/workspace/hr` placeholder (now `/identity/users`)
- City Marketing → marketplace mismatch (now Production Ads studio)
- Beta Home “city next release” copy (now live City CTAs)
- Owner metrics labels `"identity"` / `"live"`
