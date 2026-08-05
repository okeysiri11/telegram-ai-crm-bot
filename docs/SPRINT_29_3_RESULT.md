# Sprint 29.3 — Enterprise Asset Runtime

**Phase:** Enterprise Platform v9  
**Priority:** CRITICAL  
**App:** `src/web` · sprint `29.3`  
**Constraint:** Extend Runtime — integrate City · Life · Citizens · EBN.

## Implementation summary

- `src/web/src/runtime/assetRuntime/` — model, registry, ownership, location, lifecycle, permissions, events  
- Types: buildings → digital products (17 types)  
- Ownership: citizen · company · shared · department · partner · rental · lease · temporary  
- City API: assets by building/company/citizen/district + status/availability  
- EventBus `asset_runtime_update` · UI `/assets` · REST `/api/enterprise-assets/v1`  

## Remaining

- Accounting / depreciation hooks  
- Maintenance SLA workflows  
- Monetization / marketplace listings  

## Tests / quality

| Check | Result |
|-------|--------|
| lint (`tsc -b`) | OK |
| test | **251 passed** |
| build | OK |
