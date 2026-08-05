# Architecture Governance

**Status:** living · **Sprint 32.2** (Platform Core Governance track)

## Mandatory Architecture Review

Every merge that touches platform structure should run:

| Gate | Command |
|---|---|
| Architecture validation | `python scripts/validate_architecture.py` |
| Sprint architecture review | `python scripts/architecture_sprint_review.py` |
| Consolidation scan | `python scripts/architecture_consolidation_scan.py` |
| Legacy migration | `python scripts/validate_legacy_migration.py` |
| Baseline refresh | `python scripts/generate_architecture_baseline.py` (CI) |

CI: `.github/workflows/architecture.yml` (Platform Core CI) includes sprint review + consolidation scan after validation.

## What the sprint review checks

| Check | Codes |
|---|---|
| Duplicate / parallel Platform Core | `PARALLEL_CORE` |
| Core service inventory completeness | `INVENTORY_*` |
| Module ownership (docs present) | `DOC_*` |
| Backward compatibility contracts | `COMPAT_*` |
| Auto bridge presence | `AUTO_BRIDGE_*` |
| Debt registry linkage | `DEBT_REGISTRY_*` |

Critical findings fail the gate. Warnings (e.g. missing Auto bridge) do not fail unless elevated later.

## Scopes covered by existing governance

`ArchitectureGovernance` already scans: dependency direction, circular imports (baseline), layer violations, plugins, workflows, API freeze, SDK, technical-debt related allowlists.

## Backward compatibility

Sprint review asserts presence of:

- `PlatformEventBus`
- `platform_workflow`
- `platform_security/permission_engine`
- `PricingEngine` + notification/search services
- `N8nBridge`
- web `aiAgentRuntime.ts`

API / route / entity / DTO / AI Runtime / n8n compatibility remain subject to existing freeze tests (`tests/test_api_v1_freeze.py`, Integration Hub docs).

## Module ownership

Ownership map: `platform_architecture/core_inventory.py` + [`CORE_SERVICES.md`](./CORE_SERVICES.md).  
Root `CODEOWNERS` gaps remain TD-35.

## Related

- [`PLATFORM_CORE.md`](./PLATFORM_CORE.md)
- [`PLATFORM_STANDARDS.md`](./PLATFORM_STANDARDS.md)
- [`TECH_DEBT_REGISTRY.md`](./TECH_DEBT_REGISTRY.md)
