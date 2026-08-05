# Enterprise Overnight Audit — Enterprise v1 Readiness

**Scope:** Phase 5 (readiness by deployment shape) and Phase 9 (what's missing before v1), evidence-
based, not aspirational. Documentation only, `src` not modified.

## Phase 5 — Readiness by deployment shape

| Shape | Verdict | Evidence |
|---|---|---|
| Small companies | **Ready** | Single-tenant flows (Deal pipeline, Life Engine, City) are real and functional; no multi-tenant complexity needed |
| Medium businesses | **Mostly ready** | Real `Membership`/roles, real Calendar, real per-vertical extensions (`Deal.module`) cover most needs; Department/Role as first-class ontology entities are still absent (`docs/ENTERPRISE_ONTOLOGY.md`) |
| Large enterprises | **Partially ready** | Real `multi_company.Company`/`Branch`/`IntercompanyTransaction` (CQ-15) is a solid foundation; three unreconciled permission-scope vocabularies (`TD-52`) and no generic history/versioning (`TD-54`) are real gaps at this scale |
| Holdings | **Partially ready** | Real `OwnershipEdge` (holding_subsidiary/internal_department, CQ-10) + real `multi_company.Branch` cover the structural model; `docs/CROSS_COMPANY_OPERATIONS.md` (CQ-15) already found this is the one place two structurally different access models must be composed carefully — not yet implemented, only designed |
| Government organizations | **Not ready** | No real government-integration precedent found anywhere (`docs/DIGITAL_TWIN_STANDARDS.md` §3, CQ-16, explicitly left this SPEC and undesigned pending a real compliance review); real `ComplianceRiskProfile`/`VerificationLevel` (CQ-10) is a partial foundation but two unreconciled verification-tier enums exist (original `TECHNICAL_DEBT_REPORT.md` collision) |
| International companies | **Partially ready** | Real `Company.currency`/`.country` fields exist (`multi_company.py`); no real localization/i18n framework was confirmed in this audit's scope; real `TerritoryProfile` (CQ-16) anticipates multi-country but is unseeded beyond Ukraine/Odessa |
| Multi-city deployment | **Designed, not seeded** | Real Spatial Runtime hierarchy (Country→Region→City→District..., Sprint 29.4) is architecturally generic; `seedOdessaSpatial()` is the only real seed function, called once, hardcoded (`docs/REGIONAL_DIGITAL_TWIN.md` §2, CQ-16) — the runtime doesn't need a redesign, it needs a second real `TerritoryProfile` exercised |
| Multi-country deployment | **Designed, not seeded** | Same gap one level up — `country`/`region` are generic `SpatialEntityKind` values with exactly one real instance each |

## Phase 9 — What's still missing before Enterprise v1

### Critical

1. **A real `Project` entity** (`TD-51`) — the single missing link between the real sales pipeline and
   real execution tracking; almost every other gap in this list depends on it existing first.
2. **Consent-record infrastructure before any AI Production Center avatar/voice provider work**
   (`TD-46`) — a governance prerequisite, not a feature gap; sequencing this wrong is a real legal/
   trust risk.
3. **Resolution (or explicit documentation) of the header-only Platform Builder auth** (`TD-08`) — a
   live trust-boundary gap.
4. **A traced, resolved answer for the second JWT-secret read path** (`TD-57`) — cheap to fix, must be
   confirmed before any claim of production security readiness.

### High

5. Generalized Supplier/Contractor/Subcontractor entity (`docs/SUPPLY_CHAIN.md` §2, CQ-18) — currently
   automotive-only.
6. `CustomerFeedback` entity (`docs/CUSTOMER_JOURNEY.md` §2, CQ-18) — no real satisfaction signal
   exists anywhere today.
7. A decision on the six-way deal-pipeline and seven-way workflow-engine collisions (`TD-47`/`TD-48`)
   — not because they need to be merged, but because a v1 customer-facing report layer needs to know
   which one is authoritative.
8. Tenant-filter completeness verification across `repositories/` (`TD-58`) — a confirmed multi-tenant
   platform needs this confirmed, not assumed.
9. A written decision on `src/kernel`'s relationship to the Python backend (`TD-33`) — affects how much
   future investment is rational there.

### Medium

10. Unified regional/city sync scoping for events once a second city is seeded (`docs/DIGITAL_TWIN_
    STANDARDS.md` §4, CQ-16) — currently global broadcast, would flood subscribers with cross-city noise.
11. Real vector/search engine — every "semantic search" claim today is backed by hash-based fake
    embeddings.
12. Real distributed job queue — seven workflow engines and the Automation Engine currently share no
    real cross-process execution infrastructure.
13. `src/domains`'s 141 files — decide keep-and-document or remove.
14. `Deleted` avoidance convention codified across future event vocabularies (cheap, prevents future
    drift).

### Low

15. Root-level directory disambiguation (`./platform`, `./workflow` vs. prefixed packages) — real cost,
    low urgency.
16. Two dead links in `src/web/README.md` (`TD-34`).
17. CODEOWNERS coverage for root infra (`TD-35`).

### Nice-to-have

18. A consolidated OpenAPI index across Platform Builder/verticals (`TD-13`, already flagged by `docs/
    00_MASTER_PRODUCT_BIBLE.md`'s own gap analysis).
19. Generalizing the real CPL Loyalty/Membership Center (`docs/CUSTOMER_JOURNEY.md` §3, CQ-18) beyond
    cafe/beauty.
20. Rename disambiguation for `applications/port_enterprise`/`applications/port_erp` package
    docstrings (§6.2, `ENTERPRISE_FULL_AUDIT.md`).

## What NOT to do before v1 (explicit, matching this repo's own stated policy)

Per `docs/TECHNICAL_DEBT_REPORT.md`'s own "Explicit non-actions" (still valid, still real policy):
do not delete the legacy CRM API, do not merge vertical apps into one monolith, do not replace God
Mode/Mission Control/Twin engines, do not rewrite Telegram handlers into web. This audit adds one more:
**do not attempt to consolidate the six-way deal or seven-way workflow collisions in a single sprint** —
every prior successful reconciliation in this codebase (`TECH_DEBT.md`/`TECHNICAL_DEBT_REPORT.md`
itself, the four knowledge-graph systems each choosing "additive") was incremental. A rushed merge is
the highest-risk single action available to a team picking this codebase up.

## Related documents

`docs/TECH_DEBT.md`, `docs/ENTERPRISE_FULL_AUDIT.md`, `docs/PROJECT_LIFECYCLE.md`/`docs/SUPPLY_CHAIN.md`/
`docs/CUSTOMER_JOURNEY.md` (CQ-18), `docs/REGIONAL_DIGITAL_TWIN.md`/`docs/CROSS_COMPANY_OPERATIONS.md`
(CQ-16/CQ-15), `docs/SECURITY_REVIEW.md`.
