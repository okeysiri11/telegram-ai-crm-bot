# Sprint 29.0 — Enterprise Business Network Foundation

**Phase:** Enterprise Platform v9  
**Priority:** CRITICAL  
**App:** `src/web` · sprint `29.0` + Hub suite `business_network`  
**Constraint:** Compatible with Runtime · Workflow · Automation · City · Shell — no social-network redesign.

## Implementation summary

- Frontend runtime `src/web/src/runtime/businessNetwork/` — profiles, relationships, graph, comms, documents, permissions, events, City facade  
- REST `/api/enterprise-ebn/v1` — Hub Python suite + Vite local plugin  
- UI foundation `/business-network`  
- Wired: Shell startup, Desktop, launcher, module catalog, City building `business_network`, AI Studio strip, EventBus `business_network_update`  

## Architecture

```
Triggers / UI ──► Business Network Engine ──► Graph + Relationships
                         │
            EventBus · Command Runtime · REST
                         │
              Enterprise City building facades
```

## Remaining before next sprint

- Partner District visual map (Claude architecture)  
- Durable multi-tenant graph store  
- OCR for verified documents  
- Video rooms over communication foundation  
- Reputation engine beyond trustLevel heuristic  

## Tests / quality

| Check | Result |
|-------|--------|
| lint (`tsc -b`) | OK |
| test | **225 passed** |
| build | OK |
