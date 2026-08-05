# Enterprise Overnight Audit — Architecture Smells

**Scope:** pattern-level judgment calls — weak abstractions, over/under-engineering, temporary
solutions shipped as permanent — distinct from `docs/TECH_DEBT.md`'s duplication/inconsistency focus.
A smell is a shape that tends to cause problems, not a specific bug. Documentation only, `src` not
modified.

## 1. "Real-shaped data, simulated execution" — the platform's most recurring smell

Named first in Sprint CG-9, confirmed independently at least four more times across this engagement:
`workflowTemplates.ts`'s real `cityPath` field feeding only a simulated `deriveWorkflowAutomation()`
(CG-9); `platform_predictive_intelligence`'s hardcoded arithmetic behind a real-looking API surface
(CQ-14); `platform_ai/memory`'s fake SHA-256 "embeddings" behind a real `OpenAIEmbeddingProvider`
class name (CG-8); and this audit's own new finding, `src/web/src/runtime/workflowRuntime`'s real,
well-typed node-graph executor that has never called any of the six real backend workflow engines
(`TD-48`). The shape is consistent: a genuinely real, well-typed data model or API surface, wired to
either nothing or a simplified stand-in. This is not dishonest — every instance found was clearly
labeled in its own source comments — but it is a smell worth naming as a pattern, because a reader
encountering the ninth instance should recognize it faster than the first.

## 2. Readiness flags asserting capability the runtime doesn't have

`docs/TECHNICAL_DEBT_REPORT.md`'s own "Contradictions to resolve" section already names this: catalogs
claim "distributed cache / HA" while engines use process memory. This is the same smell as §1 at the
infrastructure-claims level rather than the feature level — a `"readiness": true` flag or a doc's
"Ready" badge is not the same claim as a load-tested production capability, and this platform's own
docs occasionally blur the two (`00_MASTER_PRODUCT_BIBLE.md`'s and many Sprint-doc's "X Ready · Y
Ready · Z Ready" footer convention, seen across dozens of docs including the four real
knowledge-graph docs `TD-49` covers, is foundation-readiness signaling, not production-readiness
signaling — worth being explicit about the distinction in doc footers going forward, not retroactively
fixing existing ones).

## 3. Sequencing risk: UI shipped ahead of the safety mechanism it will need

`TD-46` (`TECH_DEBT.md`) is the sharpest instance of this: the AI Production Center's 17-studio UI
shell is real and shipped, with no consent-record infrastructure yet for avatar/voice-likeness
generation — meaning the UI that will eventually need that gate already exists as "a plausible place a
future sprint could wire in avatar/voice generation before building the consent gate." This is an
under-engineering smell in a specific, consequential place: not "the feature is incomplete" (normal,
fine) but "the incomplete feature's shape actively invites the wrong build order." Worth flagging to
whoever picks up AI Production Center work next, explicitly, not just via the debt registry.

## 4. Header-only auth as a load-bearing trust boundary

`TD-08` (`TECH_DEBT.md`): Platform Builder middleware trusts `X-Principal`/`X-Platform-Role` headers
with no live identity/token round-trip. As a smell (beyond the security-debt framing already in
`SECURITY_REVIEW.md`): this is an abstraction that looks like real authentication (it has the shape of
header-based auth used in many real gateway architectures) but is currently unbacked by anything that
verifies the header wasn't simply set by the caller. The risk isn't just "insecure" — it's that the
abstraction's *appearance* of correctness makes it easy for future code to build on top of it assuming
real verification exists.

## 5. Over-fragmentation: ~106 top-level Python packages with no grouping layer

Repo root has roughly 76 `platform_*` + 30 `platform_enterprise_*` packages (per `CLAUDE.md`'s own
count) sitting flat at the repository root, alongside `api/`, `database/`, `services/`, `middleware/`,
and — per this audit's own `find` — a bare `./platform` and `./workspace`-adjacent `./workflow`
directory that are trivially confusable with the prefixed packages (`TD-56`). This is a scale smell,
not a correctness bug: a codebase can function fine with 100+ top-level packages, but every new
contributor (human or AI agent) pays a real "which of these ~15 similarly-named packages is the one I
want" tax on every task, which compounds across CLAUDE.md's own "prefer extension over replacement"
discipline — that discipline only works if the current owner of a capability is findable quickly, and
at this scale it often isn't without a search.

## 6. Under-used abstraction: `container.py`'s DI scaffold

`TD-18` (`TECH_DEBT.md`): `AppContainer`/`ServiceRegistry` has zero production consumers, exercised
only by its own scaffold test. As a smell: this is aspirational architecture (a DI container, a
generally sound pattern) introduced ahead of adoption and then never adopted — not wrong to have
built, but worth a real decision (commit to wiring it in, or retire it) rather than leaving it as
permanent unused surface area that every architecture-literate contributor has to evaluate and
mentally discard.

## 7. A large, apparently-abandoned parallel tree: `src/domains`

New finding this audit (`TD-55`): 141 real Python files under `src/domains`, essentially zero external
imports found. This is the most severe instance of §1's "real but disconnected" smell by sheer size —
larger in file count than most single `platform_*` package. Whether this was an earlier architectural
direction abandoned in favor of the current `platform_*`/`applications/*` layout, or is meant to be
picked up again, was not determinable from the code alone — this is exactly the kind of undocumented
architectural fork `CLAUDE.md`'s own "every architectural decision must be documented" rule exists to
prevent, and it's the clearest violation of that rule found in this audit.

## Non-goals

- This document does not recommend deleting or restructuring anything — per the audit's own brief
  ("do not invent new systems unless absolutely unavoidable," "documentation only").
- Every smell above already has (or now has, via `TECH_DEBT.md` §4) a corresponding tracked debt ID
  where applicable — this document is the narrative/pattern layer, not a duplicate registry.

## Related documents

`docs/TECH_DEBT.md` (the ID-tracked instances: TD-08, TD-18, TD-46, TD-48, TD-55, TD-56),
`docs/SECURITY_REVIEW.md` (§1 header-auth from the security angle), `docs/SCALABILITY_REVIEW.md` (§2/§5
readiness-flag and disconnected-engine findings from the scale angle), `docs/AI_PRODUCTION_CENTER_
BIBLE.md` (§3's source document).
