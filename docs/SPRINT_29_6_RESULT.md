# Sprint 29.6 — Enterprise Interaction Runtime

**Phase:** Enterprise Platform v9  
**Priority:** CRITICAL  
**App:** `src/web` · sprint `29.6`  
**Constraint:** Real Runtime ops only · foundation UI · reusable clients.

## Implementation summary

- `src/web/src/runtime/interactionRuntime/` — engine · registry · selection · navigation · context actions · permissions · cache · events  
- Integrates Viz · Spatial · Life · EBN · Citizens · Assets · Workflow · Automation · Shell · City  
- EventBus `interaction_runtime_update` · UI `/interactions` · REST `/api/enterprise-interaction/v1`

## Remaining (future)

- Gesture / voice bindings for twin clients  
- Command Center deep context sync  
- Durable session persistence  

## Tests / quality

| Check | Result |
|-------|--------|
| lint (`tsc -b`) | OK |
| test | **270 passed** |
| build | OK |
