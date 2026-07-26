# Prioritized Implementation Backlog — Sprint 30.2 Audit

**Rules:** Prefer extension · reuse · composition · backward compatibility. No architecture redesign.

## P0 — Unblock Web + Production pilot (Automotive first)

1. **Live identity bridge** — wire Identity Center tokens into API middleware (PB + pilot vertical).  
2. **API ownership registry** — publish prefix → app → OpenAPI map; resolve `/api/ai-os/v1` documentation.  
3. **Automotive Customer + Dealer portals** — React pages composing universal modules + auto APIs.  
4. **Nav cleanup** — reconcile soft routes; distinguish Command Center labels.  
5. **Deploy topology doc** — API + web + bot + DB compose for staging.

## P1 — Platform hardening

6. Extend EAS OpenAPI coverage to Platform Builder hubs.  
7. Vitest smoke tests for critical PB pages + auth flows.  
8. Naming glossary (ecosystem / twin / mission / recommendation_engine).  
9. Deprecation schedule for unversioned CRM `/api/*` (keep serving).  
10. AI Growth Layer binding matrix (org → Concierge/Team/Production/Marketing/Sales/CS/Analytics).  
11. Strengthen AI Customer Success as platform capability (no industry fork).

## P2 — Ecosystem expansion

12. Beauty first-class application facade (optional) on existing `platform_beauty_*`.  
13. Cafe Business Ecosystem implementation sprint (new app extending foundation).  
14. Legal / Crypto / Drone / Agro portal shells after Automotive pattern proven.  
15. Fill PB frame builders (CRM/ERP/…) via Universal Builder Framework.  
16. Route-conflict CI scanner.  
17. Distributed cache/HA backends behind existing engine interfaces.

## Explicitly deferred (do not do now)

- Rewriting Telegram `handlers.py` into web  
- Merging vertical apps into one codebase  
- Replacing Mission Control / Digital Twin / Workflow / Knowledge / AI OS / Builder Studio  
- Forking Concierge per industry  

## Suggested sequence

```text
Identity bridge → Automotive portals → OpenAPI freeze → Pilot production gate
                 ↘ Nav/glossary/tests in parallel
Then: Agro/Legal/Crypto/Drone portals → Cafe/Beauty productization
```

## Success criteria for next delivery sprint

- [ ] Authenticated web user can open Automotive portal against live API  
- [ ] No broken existing PB or vertical API tests  
- [ ] Audit docs remain the source of truth for debt/backlog  
