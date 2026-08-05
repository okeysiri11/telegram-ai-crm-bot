# Immutable Audit Vault — Foundation (Sprint 1.1.1)

**Status:** Foundation only — **not** a compliance vault  
**Closes:** Final Grand Audit — Audit Vault High Priority (architecture basis)

---

## Purpose

Prepare types and adapter seams so Roadmap 2.0 can add WORM / hash-chain storage without inventing a parallel Engine forest.

## Shipped (1.1.1)

| Piece | Location |
|-------|----------|
| `AuditVaultRecord` / `AuditVaultAdapter` | `src/web/src/audit-vault/foundation.ts` |
| `appendAuditVault` | same |
| Memory stub adapter | same (`immutable: false`) |
| Telemetry bridge | `telemetry.audit` → best-effort `appendAuditVault` |

## Guarantees today

**None** of: durability, immutability, crypto chain verification, legal hold, export.

## Target (Roadmap 2.0)

1. Server-side append-only store  
2. `prevHash` / `hash` chain verification  
3. Export for auditors  
4. Governance edge writes on deny / approval  

## Adapter registration

```ts
import { registerAuditVaultAdapter } from "@/audit-vault";
registerAuditVaultAdapter(myHttpAdapter);
```

## Related

- [API_EDGE_GOVERNANCE_PLAN.md](./API_EDGE_GOVERNANCE_PLAN.md)  
- [ROADMAP_2_0.md](./ROADMAP_2_0.md) §3  
