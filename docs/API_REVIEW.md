# Sprint CQ-30.6 — API Review

**Scope:** REST structure, naming, resource grouping, versioning, pagination, filtering, GraphQL
readiness. Documentation only, `src` not modified.

## 1. Versioning — real, consistent where it matters most

`/api/v1` (frozen, per `CLAUDE.md`) and `/management/v1` are the two governed surfaces, both real and
CI-enforced (`tests/test_api_v1_freeze.py`, `tests/test_management_security.py`). Every other real
prefix sampled across this engagement follows `/api/<domain>/v1` consistently. The one confirmed
inconsistency remains `docs/TECH_DEBT.md` TD-06 (unversioned legacy CRM `/api/*`) — not re-derived,
carried forward.

## 2. Real OpenAPI/docs endpoints — a positive finding

`platform_management/management_router.py:642-648` registers real `v1_openapi`/`v1_docs` (Swagger UI)
routes, both gated by `require_role(ManagementRole.READ_ONLY)`. This is a genuine positive: the
platform doesn't just have ad hoc routes, it has a real, permission-gated, self-documenting API surface
for at least the management domain. `TD-13`'s "uneven OpenAPI coverage" finding is about coverage
breadth across verticals, not about the mechanism existing — worth stating both halves together rather
than only the gap.

## 3. Pagination — real, but inconsistent defaults

Real `PaginationParams.from_query()` and `PaginationMeta.build(page=, page_size=, total=)` exist and
are used consistently within `management_router.py`. **New finding this review**: sampled `limit`
query-param defaults vary across endpoints in the same file with no apparent standard — `50`, `100`,
and `500` all appear as different endpoints' defaults. Not a functional bug, but worth a documented
default (e.g., 50) with per-endpoint overrides justified explicitly, rather than each handler picking
its own number.

## 4. Filtering — real, ad hoc, not a shared query-DSL

Filtering is implemented per-endpoint via direct `request.query.get("event_type")`-style reads, not a
shared filter-parsing utility. This is consistent with the rest of the platform's "real per-domain
implementation, no shared abstraction yet" pattern (the same shape as the three task queues in
`docs/ARCHITECTURE_REVIEW_V2.md` §1.1) — functional today, a real consolidation opportunity later, not
urgent.

## 5. Resource naming and grouping

Real prefixes follow `/api/<domain-kebab-case>/v1` consistently across the sampled surface. The
confirmed real naming collisions (`TD-07`'s `/api/ai-os/v1` three-way share; `TD-49`'s four
Knowledge-Graph-adjacent prefixes `enterprise-kg`/`enterprise-ekg`/`enterprise-ekp`) remain this
platform's clearest resource-naming risk — visually similar prefixes for different real systems, a
real "did I typo this" hazard for anyone integrating by hand.

## 6. GraphQL readiness

**No real GraphQL server surface exists.** The only real GraphQL-related code found is
`applications/enterprise_hub/integrations/connectors/graphql.py` — a **client** connector for consuming
*external* GraphQL APIs as an integration source, not a GraphQL API the platform itself exposes. This
is a reasonable, honest starting point: the platform already models GraphQL as a concept (as a data
source), which is lower-risk groundwork than having no GraphQL awareness at all, but it does not
constitute "GraphQL-ready" in the sense of an exposable schema. **Recommendation for Beta**: do not
build a GraphQL server for Beta — the real, consistent REST surface is the correct near-term
investment; revisit GraphQL only if a specific enterprise customer's integration requirement demands
it.

## 7. Beta-relevant API risks, ranked

| Risk | Evidence | Priority |
|---|---|---|
| Similar-looking Knowledge Graph prefixes | `TD-49` | P1 |
| Inconsistent pagination `limit` defaults | §3, new this review | P2 |
| No shared filter-parsing utility | §4, new this review | P3 |
| Unversioned legacy CRM `/api/*` | `TD-06` | P2 |

## 8. Sprint CQ-30.8 addition — error responses, DTOs, permissions

**Error response consistency — real, but domain-scoped, not platform-wide.** `platform_management/
response_models.py`'s real `error_response()`/`success_response()` (consistent envelope: message,
`request_id` correlation, HTTP status) is reused across 12 real files within `platform_management`'s
own domain. Not confirmed whether other domains (`applications/auto_marketplace`, `applications/
port_erp`, etc.) use the same envelope or their own — a genuine, unverified inconsistency risk rather
than a confirmed one.

- **Why:** a consistent error shape matters more once external Beta customers start integrating
  directly against the API, not just the first-party frontend.
- **Impact:** Medium — inconsistent error shapes across domains would force every integrator to
  special-case per-domain error parsing.
- **Priority:** P2. **Complexity:** M (audit which domains diverge, then decide whether to unify).
- **Evidence:** `platform_management/response_models.py`, 12-file reuse count confirmed this pass.

**DTO consistency:** not independently audited this pass beyond the pagination/error findings above —
flagged as out of this review's evidence base, not claimed as reviewed.

**Permissions on API routes:** the real `require_role(ManagementRole.READ_ONLY)` pattern
(`management_router.py:642-648`, cited in §2) confirms per-route role gating exists and is applied
consistently to the sampled OpenAPI/docs routes. Broader per-route permission audit across all ~70 real
prefixes was not performed this pass.

## Non-goals

- No GraphQL server designed or recommended for Beta.
- No new filter-DSL or pagination-default change implemented — flagged as a future consolidation
  opportunity, not urgent enough to block Beta.
- No full DTO consistency audit performed — flagged as a gap in this review's own coverage, not
  resolved.

## Related documents

`docs/API_MAP.md` (real, the document these findings should be added to), `docs/TECH_DEBT.md` (TD-06,
TD-07, TD-13, TD-49), `docs/ARCHITECTURE_REVIEW_V2.md` (CQ-30.6 sibling), `docs/BETA_READINESS_
REVIEW.md`/`docs/PRODUCTION_GAPS.md` (CQ-30.8 siblings).
