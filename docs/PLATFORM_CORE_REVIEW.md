# Sprint CQ-32.2 — Platform Core Review

**Scope:** should each of the brief's thirteen services live inside Platform Core instead of
verticals? Documentation only, `src` not modified.

## Verdict, per service

| Service | Current real location | Should be Core? | Assessment |
|---|---|---|---|
| Authentication | `platform_identity/` — already Core | **Already correct** | Real, centralized, no vertical has its own auth stack |
| Notification | Real, mostly centralized (`NOTIFICATION_CENTER.md`, `/api/enterprise-comms/v1`) but `TD-53`'s three unreconciled vocabularies mean the *taxonomy* is fragmented even though the *transport* is centralized | **Already Core, taxonomy needs unification** | The service lives in the right place; the label set does not |
| Workflow | **Fragmented across seven real engines** (`TD-48`), none canonically "Core" | **Should be Core, is not** | The clearest violation of this review's own question — workflow execution is exactly the kind of cross-cutting capability that belongs in one place, and it's the platform's most-duplicated capability instead |
| Permissions | Fragmented — three real, unreconciled scope vocabularies (`TD-52`) plus `platform_security`'s RBAC | **Should be Core, partially is** | The mechanism (`platform_security`) is Core-located; the vocabulary is not unified across the runtimes that consume it |
| Pricing | **Not independently confirmed this pass** — likely lives per-vertical (e.g., automotive commission logic in `commission.py`) given the pattern every other service in this table shows | **Likely should be Core, not verified** | Flagged for a follow-up trace, not asserted |
| Marketplace | Fragmented — at least four real systems (`docs/BUSINESS_MARKETPLACE.md`, CQ-13) plus the City marketplace district | **Should be Core, is not** | Same shape as Workflow — a cross-cutting concept duplicated per-context |
| Knowledge Base | Fragmented — four real systems (`TD-49`) | **Should be Core, is not** | Same shape again |
| AI Runtime | Fragmented — `platform_ai_os`/`platform_agents`/`platform_orchestrator` (three registries, CG-8) plus the disconnected frontend runtime layer (`TD-59`/`TD-60`) | **Should be Core, is not** | The most consequential fragmentation given this review's own §6 AI Runtime deep-dive (`docs/AI_RUNTIME_REVIEW.md`) |
| Event Bus | Canonical real implementation exists (`events/event_bus.py::PlatformEventBus`) but `TD-20` tracks 6+ competing `EventBus` classes | **Already Core in principle, violated in practice** | Same shape as Notification — the right answer exists, isn't universally used |
| Search | **No real search/vector engine exists anywhere** (confirmed CQ-20/CQ-30.6) | **N/A — nothing to relocate, needs to be built** | Different kind of finding: not fragmented, absent |
| Catalog | Fragmented — real `productionCatalog.ts`, `MODULE_LABEL_RU`, design-system `catalog/index.ts`, and per-vertical catalogs (`business_capabilities/capabilities/*.py`) all use "catalog" independently | **Should be Core (as a pattern/convention, not necessarily one data store)** | Lower-severity than Workflow/Marketplace/Knowledge Base — each catalog serves a genuinely different concern; the finding is naming convergence, not data duplication |
| Media | Real, already Core — `services/storage/__init__.py`'s multi-backend (Telegram/Local/S3/CDN) provider system | **Already correct** | No vertical was found reimplementing media storage independently |
| Storage | Same as Media — already Core | **Already correct** | — |

## Pattern across the table

Of thirteen services reviewed, **five already live correctly in Core** (Authentication, Notification's
transport, Event Bus's canonical implementation, Media, Storage) and **five are genuinely fragmented
and should be centralized** (Workflow, Permissions' vocabulary, Marketplace, Knowledge Base, AI
Runtime) — the same five capabilities this entire engagement has independently found duplicated across
CQ-18 through CQ-32.2, now confirmed from the specific "which layer should own this" angle the brief
asked for. **Search is absent, not fragmented.** Pricing and Catalog need more specific follow-up.

## Recommendation

Do not attempt to relocate all five fragmented services into Core in one effort — per this
engagement's standing discipline (`docs/TECHNICAL_DEBT_REPORT.md`'s original "prefer documentation
ownership, extension, and composition" policy, still valid), the correct sequence is:

1. Pick the single most mature real implementation for each (already done for Workflow via `TD-48`'s
   analysis, Marketplace via CQ-13, Knowledge Base via `TD-49`, AI Runtime via this sprint's own
   `docs/AI_RUNTIME_REVIEW.md`).
2. Publish it as the Core-owned canonical service.
3. Require new work to extend it, not add a sixth/eighth/fifth alternative — enforced by the same
   "does this exist" check this engagement has recommended since `docs/EXECUTIVE_SUMMARY.md` (CQ-30.6).

## Non-goals

- No service relocation implemented — every recommendation above is architectural guidance for a
  future sprint.
- No Pricing/Catalog deep-dive performed — both flagged as needing dedicated follow-up research.

## Related documents

`docs/TECH_DEBT.md` (TD-20, TD-48, TD-49, TD-52, TD-53), `docs/AI_RUNTIME_REVIEW.md` (CQ-32.2 sibling,
AI Runtime detail), `docs/BUSINESS_MARKETPLACE.md` (CQ-13), `docs/DDD_REVIEW.md` (CQ-32.2 sibling,
Bounded Contexts recommendation this table's five fragmented services would each become).
