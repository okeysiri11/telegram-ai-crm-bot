# Sprint 32.3 Result — Enterprise Consolidation & Canonical Platform Services

**Track:** Enterprise Consolidation / Canonical Services  
**Date:** 2026-08-02  
**Status:** Complete (consolidation track)

## Naming collision

Historical **Sprint 32.3.1–32.3.7** is the Platform Builder UX / first-entry / City / workspace track  
(`FIRST_ENTRY_32_3_1.md` … `PRODUCTION_READINESS_32_3_7.md`). Those docs are **untouched**.

This RESULT is the **Enterprise Consolidation** track only (same ID collision pattern as Sprint 32.2).

## Objective

Eliminate critical CTO Architecture Review findings: canonical services, secret hardening, unified queues, Event Bus policy, runtime consolidation, architecture checks, enterprise metrics.

## Delivered

### 1. Canonical Service Consolidation

- Registry: `platform_architecture/canonical_services.py`
- Docs: `CANONICAL_SERVICES.md`
- Deal entry facade: `services/canonical_deal_pipeline.py` → `DealPipelineEngineV2`
- Ownership extended in `core_inventory.py`

### 2. Secret Management Hardening

- `platform_security/secret_policy.py` — required secrets, placeholder vocabulary, repo scan
- Expanded insecure JWT set in `jwt_secrets.py`
- `docker-compose.n8n.yml`: **no** default `N8N_ENCRYPTION_KEY` (compose `${VAR:?msg}`)
- `ConfigurationCenter.validate` rejects placeholder N8N / provider secrets in production
- `.env.example` documents `N8N_ENCRYPTION_KEY`

### 3. Queue Consolidation

- `platform_jobs/unified_queue.py` — lanes: ai · workflow · background · notification · render
- Retry + dead-letter via existing `JobRetryManager` / `JobQueue`
- Doc: `QUEUE_ARCHITECTURE.md`

### 4. Platform Event Bus

- Policy: `events/event_bus_policy.py` + `docs/EVENT_BUS.md`
- Consolidation scanner forbids new EventBus classes in Core trees

### 5. Cross Runtime Consolidation

- Web map: `src/web/src/enterprise-runtime/runtimeConsolidation.ts`
- Enterprise Runtime remains the web orchestration hub

### 6. Architecture Rules

- `platform_architecture/consolidation_scanner.py`
- Wired into `sprint_review` + `scripts/architecture_consolidation_scan.py`

### 7. Enterprise Metrics

- `platform_observability/enterprise_metrics.py` — queue wait, API latency, AI cost, runtime health, provider usage, cache hit rate, workflow duration

### 8. Documentation

`PLATFORM_CORE.md` · `CANONICAL_SERVICES.md` · `QUEUE_ARCHITECTURE.md` · `EVENT_BUS.md` ·  
`ARCHITECTURE_MAP.md` · Product Bible · `TECH_DEBT.md` / registry · `SPRINT_32_3_RESULT.md`

## Debt

TD-64 (legacy deal/workflow/KG adapters remain until migrated) · TD-65 (settings still have load-time placeholder defaults for local boot — production validate rejects).

## Quality gates

```bash
./venv/bin/python scripts/architecture_sprint_review.py
./venv/bin/python scripts/architecture_consolidation_scan.py
./venv/bin/python -m pytest tests/test_sprint_32_3_consolidation.py -q
cd src/web && npm run lint && npm test && npm run build
```

## Definition of Done

| Criterion | Status |
|---|---|
| Canonical owners documented + scanned | ✓ |
| No insecure N8N compose default | ✓ |
| Unified queue lanes + DLQ | ✓ |
| Event Bus mandatory policy | ✓ |
| Runtime consolidation map | ✓ |
| Architecture checks green | ✓ |
| Docs updated | ✓ |
| UX 32.3.x docs preserved | ✓ |
