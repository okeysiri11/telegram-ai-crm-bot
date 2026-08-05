# API Edge Governance Plan — Sprint 1.1.1

**Status:** Extension points + migration plan (no new Engine)  
**Product:** Enterprise Platform v1.1  
**Closes:** Final Grand Audit — Governance High Priority (plan + hooks)

---

## Current state (v1.0 / v1.1)

UI Governance composes **Policy → Permission → Approval → Execution** from existing Autonomy / RBAC / notifications.  
This is **compositional**, not hard API enforcement.

## Target state (Roadmap 2.0)

```
Client / Shell
    ↓  evaluateGovernanceEdge(ctx)   ← Sprint 1.1.1 hooks
API Gateway / Edge middleware
    ↓  policy match + RBAC
Deny | Allow | Require Approval
    ↓
Execution + Audit Vault append
```

## Extension points (shipped 1.1.1)

| Symbol | Path | Role |
|--------|------|------|
| `evaluateGovernanceEdge` | `src/web/src/enterprise-governance/governanceEdge.ts` | Client precheck |
| `registerGovernanceEdgeHook` | same | Inject gateway adapter / tests |
| `GOVERNANCE_EDGE_MIGRATION` | same | Phase metadata |

## Migration phases

1. **document_extension_points** — this doc  
2. **client_precheck_hooks** — current (default allow + admin sensitive → approval)  
3. **api_gateway_middleware** — Roadmap 2.0  
4. **hard_deny_on_critical** — Roadmap 2.0  

## Non-goals (1.1.1)

- New Policy Engine package  
- Changing Runtime / AI Core / Data Fabric  
- Claiming compliance-grade enforcement  

## Related

- [IMMUTABLE_AUDIT_VAULT_FOUNDATION.md](./IMMUTABLE_AUDIT_VAULT_FOUNDATION.md)  
- [KNOWN_LIMITATIONS_1_0.md](./KNOWN_LIMITATIONS_1_0.md) §1  
- [ROADMAP_2_0.md](./ROADMAP_2_0.md) §2  
