# Technical Debt Registry (Categorized Index)

**Status:** living · **Sprint obligation:** every sprint updates this index **and** `docs/TECH_DEBT.md`.

## Canonical ID registry

All debt IDs (`TD-01` …) live only in **[`TECH_DEBT.md`](./TECH_DEBT.md)**.  
This file is a **categorized index** — do not invent parallel ID sequences here.

## Categories

### Architecture Debt

Duplicates, parallel engines, layer violations, naming collisions.

Examples: TD-01–TD-05, TD-20–TD-22, TD-24, TD-36–TD-39, TD-47–TD-52, TD-55–TD-56, TD-59–TD-60, **TD-61**, **TD-62**, **TD-63**, **TD-64**.

### Performance Debt

Unprofiled hotspots, sync fan-out, missing caches.

Examples: TD-32.

### Security Debt

Auth, secrets, tenant isolation, consent.

Examples: TD-08, TD-46, TD-57, TD-58, **TD-65**, **TD-66**, **TD-67**.

### UX Debt

Double chrome, orphan palettes, embed gaps, persistence.

Examples: TD-40–TD-44.

### Infrastructure Debt

Deploy story, dual runtimes, migrations dirs, SQLite residue, CODEOWNERS.

Examples: TD-14, TD-19, TD-25, TD-30–TD-31, TD-33–TD-35.

## Sprint 32.2–32.3 additions (see TECH_DEBT.md)

| ID | Category | Summary |
|---|---|---|
| TD-61 | Architecture | Auto marketplace pricing/auth/notif/search still local adapters vs Core SoR |
| TD-62 | Architecture | No single `platform_core` package — composed Core needs ongoing inventory discipline |
| TD-63 | Missing feature | Universal Service Constructor is foundation-only (no UI / no ServiceListing wire-up) |
| TD-64 | Architecture | Canonical owners declared; legacy deal/workflow/KG/notify engines still adapters |
| TD-65 | Security | Load-time placeholder JWT defaults remain for local boot — production validate rejects |
| TD-66 | Security | Security Center policies not yet wired into every HTTP/APH path |
| TD-67 | UX / Security | Owner securityCenter demo metrics when ISAM dashboard unreachable |

## How to update each sprint

1. Add or resolve rows in `TECH_DEBT.md` with next `TD-N`.
2. Refresh category bullets above if new IDs appear.
3. Reference IDs in `SPRINT_*_RESULT.md`.
4. Run `python scripts/architecture_sprint_review.py` (requires this file to link `TECH_DEBT.md`).

## Related

- [`ARCHITECTURE_GOVERNANCE.md`](./ARCHITECTURE_GOVERNANCE.md)
- [`PLATFORM_CORE.md`](./PLATFORM_CORE.md)
- [`TECHNICAL_DEBT_REPORT.md`](./TECHNICAL_DEBT_REPORT.md) (historical TD-01–TD-16 source)
