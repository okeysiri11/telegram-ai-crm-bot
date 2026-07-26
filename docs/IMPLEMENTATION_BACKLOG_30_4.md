# Implementation Backlog — Sprint 30.4

Supersedes sequencing in `IMPLEMENTATION_BACKLOG_30_3.md` for delivery order.

## Completed in 30.4

- [x] Shared application shell / layouts / responsive foundation  
- [x] Module loader + seven ecosystem connection points  
- [x] Permission-aware navigation + PermissionGuard  
- [x] Identity context → API headers (`apiFetch`)  
- [x] Mission Control shell integration  
- [x] Telemetry → Enterprise Observability  
- [x] Pilot / production / deployment documentation  

## P0 — Next sprint (workflows, not architecture)

1. Automotive Customer + Dealer **live data views** on existing shells  
2. Real ISAM/EIC JWT validation (replace demo-token acceptance in middleware)  
3. OpenAPI freeze for Automotive portal contracts  
4. Staging deploy smoke (Deploy Topology + Deployment Notes 30.4)  

## P1

5. Beauty / Legal / Crypto read-only list screens against existing APIs  
6. Vitest coverage for PermissionGuard + telemetry client  
7. OBS browser ingest rate limiting  
8. EAS OpenAPI for Platform Builder  

## P2

9. Cafe product application (extend foundation — still no parallel stack)  
10. Drone ops workflows after catalog prioritization  
11. Fill PB frame builders via UBF  

## Deferred

- Redesign platform cores  
- Merge vertical monoliths  
- Delete legacy CRM API  
- Fork Concierge per industry  
