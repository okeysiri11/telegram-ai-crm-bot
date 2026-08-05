# Enterprise City — Full Architecture Audit

**Mode:** Overnight architecture audit. Documentation only — `src` not modified, no production code
written. Roles assumed: Chief Enterprise Architect, Principal Engineer, CTO, Platform Auditor,
Technical Debt Reviewer.

**Methodology, stated plainly**: this audit combines (a) direct, sampling-based evidence gathered this
pass (file:line cited throughout) and (b) synthesis of a prior twenty-sprint architecture-research
engagement (Sprints CG-4 through CQ-20) that already produced ~100 grounded documents and independently
re-derived much of what a fresh audit would find. Given the repository's real scale (1,190 docs,
~106 top-level Python packages, 17 verticals, three largely-independent frontend/runtime systems),
this is not an exhaustive file-by-file read — it is evidence-based sampling with every claim traceable
to a real citation, and every gap in coverage stated explicitly rather than papered over.

## Phase 1 — Global architecture review

### 1.1 Three largely independent systems, correctly kept separate

Per `CLAUDE.md`'s own description, confirmed accurate: (1) the Python bot + platform backend at repo
root, (2) the `src/web` React frontend (primary) + `platform_console` (secondary), (3) a standalone
Node/TS "ADOS OS" kernel ecosystem (`src/kernel` + 6 packages) with no runtime connection to the other
two (`TD-33`). This separation is architecturally sound *as a boundary* — the problem is not that
these three are separate, it's that the separation was never written down as a deliberate decision
(`ARCHITECTURE_SMELLS.md` §7's broader point). **Verdict: boundary is correct, documentation of intent
is the gap.**

### 1.2 The `platform_*` capability-layer model — sound in concept, strained in practice

The intended dependency direction (Platform core → Providers → AI services → Business modules →
Vertical solutions → Customer applications, per `CLAUDE.md`) is a coherent, standard layered
architecture. In practice: `TD-24` records 29 non-critical `reverse_layer_dependency` warnings, and
`TD-19` records a direct violation (`database/__init__.py` importing `database_legacy`). The model is
right; enforcement is incomplete but not absent — `scripts/validate_architecture.py` running in CI is
real governance, not aspirational. **Verdict: the governance mechanism is the platform's strongest
architectural asset (see §10); the violations it currently tolerates should shrink, not the mechanism
be abandoned.**

### 1.3 Responsibility boundaries — the collision pattern, assessed at the meta level

Six independent real deal systems (`TD-47`), seven workflow engines (`TD-48`), five Digital Twin
implementations (`TD-04` + CQ-16 extension), four Command Centers (`TD-03` + CQ-15 extension), four
Knowledge Graph/ontology systems (`TD-49`). Assessed as a *pattern*, not five separate accidents: every
instance follows the same shape — a real team/sprint builds a genuinely working system, ships it, and a
later sprint builds a second one addressing a broader or updated need rather than extending the first.
`CLAUDE.md`'s own "prefer extension over replacement" principle exists specifically to prevent this,
and it is being followed inconsistently. **This is the single most consequential architectural finding
in this entire audit**: not any one collision, but the demonstrated organizational pattern that
produces them repeatedly. See `TOP_20_CRITICAL_FIXES.md` for the recommended structural fix (a
lightweight "does this already exist" check before any new `platform_*` package or major entity is
created — a process fix, not a code fix).

### 1.4 Coupling — mostly loose, with one legitimate exception

Cross-package coupling is generally disciplined: `events/event_bus.py::PlatformEventBus` is the
intended integration point, and most `platform_*` packages communicate through it or through
`services/` rather than direct imports. The one confirmed exception with unusually wide blast radius is
`src/web/src/runtime/cityVisualization/` (Sprint 29.5), which directly composes all eight other real
frontend runtimes (`docs/CROSS_SYSTEM_SEMANTIC_MAPPING.md` §3, CQ-20). This is a deliberate integration
point, not accidental coupling, but it means a change to any of the eight has a real chance of needing
a corresponding check in `cityVisualization` — worth naming explicitly so it gets proportionate review
care.

### 1.5 Future maintainability — the real risk is discoverability, not correctness

Most individual subsystems examined across this audit and the prior twenty sprints are internally
coherent and reasonably well-engineered (`deal_pipeline_engine.py`'s tenant-configurable stage machine,
the real Life Engine event bridge, the real Spatial Runtime hierarchy are all genuinely good work). The
compounding risk is that a new contributor — or a new AI agent session with no memory of this audit —
cannot easily tell, from the repository structure alone, which of six deal systems or seven workflow
engines is the one to extend. This is fixable without any code change: `TECH_DEBT.md` and this audit's
own documents are the fix, provided they're actually read before new work starts.

## Phase 6 — Code organization

### 6.1 Root-level directory sprawl (new finding, `TD-56`)

`find . -maxdepth 1 -type d` returns roughly 100 top-level directories. ~76 `platform_*` + ~30
`platform_enterprise_*` packages sit flat at the same level as core infrastructure (`api/`, `database/`,
`services/`, `middleware/`, `repositories/`, `events/`, `routers/`). Two bare directories, `./platform`
and `./workflow`, exist alongside and are trivially confusable with `platform_*`/`platform_workflow`/
`platform_workflows`. No grouping/namespace layer exists (e.g., nothing groups the 30
`platform_enterprise_*` packages under a common parent). **This does not block anything today** — Python
imports work fine regardless of directory count — but it is a real, measurable discoverability cost.

### 6.2 `port_enterprise` vs. `port_erp` — different scale, not simple duplication

`applications/port_enterprise` (57 `.py` files) and `applications/port_erp` (209 `.py` files) are not
equivalent-sized systems — `port_erp` is roughly 3.7x larger, consistent with prior research finding it
owns real AIS/GPS/geofence maritime tracking while `port_enterprise` owns warehouse/multimodal
logistics. **Verdict: likely two genuinely different products sharing an unfortunate name prefix, not
wasteful duplication** — but the shared "port_" prefix is a real discoverability tax matching §6.1's
broader point, worth a naming-only fix (e.g., a one-line disambiguation note in each package's own
`__init__.py` docstring) rather than a restructure.

### 6.3 `src/domains` — 141 files, orphaned (`TD-55`, detailed in `ARCHITECTURE_SMELLS.md` §7)

The most significant code-organization finding of this audit. Restated briefly here, detailed there:
a 141-file Python package tree with effectively zero external imports found repo-wide.

### 6.4 `applications/platform_builder`'s four near-identical directories

`TD-27` (`TECH_DEBT.md`, real, pre-existing): `command_center/`, `control_center/`, `mission_control/`,
`operations_center/` — same file shape, different name, within a single application. This is the
clearest within-one-app instance of the broader Command Center collision pattern (§1.3), worth fixing
first if any Command Center consolidation is ever undertaken, since it has the smallest blast radius
(one application, not a cross-repo rename).

### 6.5 API naming consistency

`TD-06` (unversioned legacy CRM `/api/*` beside frozen `/api/v1`) and `TD-07` (`/api/ai-os/v1` shared
across three different real packages) are the two confirmed real API-naming inconsistencies. This
audit's own research (CQ-16 through CQ-20) found the pattern extends further: `/api/enterprise-kg/v1`
vs `/api/enterprise-ekg/v1` vs `/api/enterprise-ekp/v1` (three visually-similar prefixes for three of
the four real knowledge-graph systems, `TD-49`) is a genuine "did I typo this prefix" risk for any
future integration work.

## Non-goals

- No restructuring, renaming, or deletion performed or specifically scheduled by this document — every
  finding routes to `ARCHITECTURE_IMPROVEMENTS.md` for the actual recommendation with migration
  difficulty/risk/priority attached.
- No claim of exhaustive coverage — §-level scope limits are stated inline throughout.

## Related documents

`docs/TECH_DEBT.md` (the ID-tracked registry every finding above cites), `docs/ARCHITECTURE_SMELLS.md`
(pattern-level detail on §6.3), `docs/ARCHITECTURE_IMPROVEMENTS.md` (recommendations for every finding
here), `docs/CROSS_SYSTEM_SEMANTIC_MAPPING.md` (CQ-20, §1.4's `cityVisualization` coupling detail),
`docs/DEPENDENCY_MAP.md`/`docs/MODULES.md`/`docs/API_MAP.md` (the real four-document set this audit
builds on).
