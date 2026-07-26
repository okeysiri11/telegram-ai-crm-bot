# CRM API Deprecation Schedule — Sprint 30.3

Legacy unversioned CRM routes remain **mounted** for backward compatibility.

| Surface | Path | Status |
|---------|------|--------|
| Legacy CRM | `/api/*` via `api/crm_api.py` | **Deprecated — still served** |
| Public API | `/api/v1/*` | **Preferred** |
| Vertical CRM | e.g. dealer CRM under auto prefixes | **Product** |

## Schedule

| Phase | Action |
|-------|--------|
| 30.3 (now) | Document deprecation; no removal |
| Next Web sprint | New portals call versioned / vertical APIs only |
| Later | Emit deprecation headers on legacy routes |
| Future freeze | Remove legacy only after zero traffic + migration note |

## Rule

Do **not** delete legacy CRM API in consolidation sprints.
