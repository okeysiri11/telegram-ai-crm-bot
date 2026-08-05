# Architecture Backlog — Before Sprint 37

Ordered by priority, drawing on `docs/ENTERPRISE_ARCHITECTURE_REVIEW_36_0.md`'s findings and the real,
self-reported remaining-debt list in `docs/FOUNDATION_AUDIT_35_0.md`. Documentation only — this is a
backlog for planning, not an implementation.

## Critical

None. This is a genuine, evidence-based finding, not an omission: every item this Board reviewed after
Sprint 36.0 that was previously Critical (the JWT secret hardening, the Sync Engine gap, the `sqlite3`
policy violation) has been resolved by real, verified work in Sprints 30.0–35.0. This is the first
review in this Board's history with an empty Critical tier — stated plainly because it is itself a
significant signal about the platform's trajectory, not because this review went easy.

## High

1. **Decide and register Voice Runtime's foundation** in the Service Builder registry, even as a
   seeded/placeholder entry — before any voice feature work begins, so it isn't built outside the
   canonical registry. *Why:* every prior instance of "build first, register later" in this platform's
   history became a multi-sprint cutover debt item; registering first is now cheap and proven.
2. **Decide and register Project Memory's foundation**, sequenced after (or alongside) the real
   `Project` entity (`TD-51`) since Project Memory has no coherent anchor without it. *Why:* same
   reasoning as #1, compounded by a real entity dependency.
3. **Retrofit `VersionMixin` onto existing SQLAlchemy models** (`FOUNDATION_AUDIT_35_0.md` remaining-
   debt item 1). *Why:* the primitive is real and proven; every model not yet retrofitted continues
   accumulating its own ad hoc history-tracking debt in the meantime.
4. **Design table partitioning for canonical Deal tables** ahead of real production data volume. *Why:*
   carried forward from `docs/ARCHITECTURE_REVIEW_34_2C.md`, still unaddressed, and cheaper the earlier
   it's designed.
5. **Trace whether the Service Builder's seeded AI Runtime / Multi-Agent Runtime / Enterprise City
   Runtime entries are wired to real execution paths or are registry-only placeholders.** *Why:* cheap
   to verify, and the answer changes how much weight to put on "compatibility" claims for these three
   systems in any customer- or investor-facing material.

## Medium

6. **Bridge the Web menu catalog / `shellModuleRegistry`** to the real Registry API, eliminating the
   hand-mirrored TypeScript copy (`FOUNDATION_AUDIT_35_0.md` remaining-debt item 2).
7. **Begin an opportunistic `TD-20` EventBus cutover** — no fixed deadline, but a scheduled cadence
   rather than indefinite allowlisting, per this review's §4 finding.
8. **Fold Hub ISAM into Identity Core** (`FOUNDATION_AUDIT_35_0.md` remaining-debt item 4; also
   `docs/ARCHITECTURE_REVIEW_34_2C.md` §4.2).
9. **Review the new Service Builder ORM tables' indexing** against the same discipline as the
   canonical Deal tables, while the tables are still young and cheap to adjust.
10. **Generalize the Service Builder's real lifecycle/registry/versions/dependencies/loader/sandbox/
    health/permissions/audit shape** as the template for the still-missing Deal-cluster aggregate root
    (§5 of the main review).
11. **Continue the deal/workflow/knowledge adapter cutover** (`TD-64`) on its already-recommended fixed
    cadence.
12. **Exercise the third-party plugin/marketplace publish path at least once**, even with an internal
    test extension, to validate the Service Builder's sandbox isolation claims under real (not just
    theoretical) conditions.

## Low

13. **Multi-instance durable VersionEngine heads (HA)** — real, tracked, correctly not urgent until
    horizontal scaling of the state layer is actually attempted.
14. **Evaluate a Postgres-backed Event Store table** once JSONL's write-volume ceiling is actually
    approached — not before, per Sprint 35.0's own deliberate, correct sequencing.
15. **Revisit Zero Trust architecture** only if/when microservice decomposition is later pursued —
    explicitly not before, per this review's §8 finding.
16. **Continue Security Center's progressive HTTP/APH path wiring** (`TD-66`) — already in motion, no
    change to its existing pace recommended.

## What this backlog deliberately does not include

- Microservice decomposition — not recommended before Sprint 37 or several sprints beyond, per the main
  review's §6 finding.
- A rewrite of any canonical service chosen in Sprints 32.2–36.0 — every one of those decisions is
  confirmed sound by this review.
- Deleting any allowlisted legacy adapter (EventBuses, Hub ISAM, shell registries) — explicitly a
  scheduled cutover item (#7, #8, #11), never a delete-now action.

## Related documents

`docs/ENTERPRISE_ARCHITECTURE_REVIEW_36_0.md` (the source of every item above), `docs/FOUNDATION_
AUDIT_35_0.md`/`docs/SPRINT_36_0_RESULT.md` (real, Sprint 35.0/36.0), `docs/TECH_DEBT.md` (canonical
registry).
