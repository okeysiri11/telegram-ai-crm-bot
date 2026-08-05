# Sprint 29.1 — Enterprise Digital Citizen Foundation

**Phase:** Enterprise Platform v9  
**Priority:** CRITICAL  
**App:** `src/web` · sprint `29.1` + Hub suite `digital_citizen`  
**Constraint:** Human layer on Runtime + EBN — no City redesign / no social network.

## Implementation summary

- Runtime `src/web/src/runtime/digitalCitizen/` — citizens, membership, workspace, personal AI, presence, activity, permissions, City facades  
- REST `/api/enterprise-edc/v1` — Hub Python + Vite plugin  
- UI `/digital-citizens`  
- Wired: Shell, Desktop, module catalog, City building `digital_citizens`, AI Studio strip, EventBus `digital_citizen_update`  
- Linked to EBN via `businessProfileId` on memberships  

## Remaining

- City avatar rendering (Claude / later sprint)  
- Durable citizen store / HR sync  
- Deep meeting room presence  
- Richer Personal AI execution beyond registry  

## Tests / quality

| Check | Result |
|-------|--------|
| lint (`tsc -b`) | OK |
| test | **235 passed** |
| build | OK |
