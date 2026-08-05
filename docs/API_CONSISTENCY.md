# Sprint CQ-30 — API Consistency Review

**Scope:** duplicated/inconsistent API surfaces, validated against the real `docs/API_MAP.md` (350
lines, ~70 documented `/api/*` prefixes, real cross-references to `TECH_DEBT.md` IDs). Documentation
only, `src` not modified.

## Issue 1 — Four real Knowledge Graph API prefixes, none documented in `API_MAP.md`

**Description:** `docs/API_MAP.md` states any missing entry should be "treated as a bug, not a minor
omission." A direct check found it documents zero of the four real Knowledge Graph systems'
prefixes.

**Evidence:** `grep -c "/api/enterprise-kg\|/api/enterprise-ekg\|/api/enterprise-ekp" docs/API_MAP.md`
→ 0. The four real prefixes, per prior research (`docs/ENTERPRISE_ONTOLOGY.md`): `/api/ai-ecosystem/v1/
knowledge` (Sprint 12.0), `/api/enterprise-kg/v1` (Sprint 19.2), `/api/enterprise-ekp/v1` (Sprint 20.3),
`/api/enterprise-ekg/v1` (Sprint 24.2). A fifth, related prefix — `/api/enterprise-etw/v1`
(`platform_enterprise_digital_twin`, the recommended-canonical Digital Twin system) — is also absent.

**Impact:** the single document positioned to prevent a fifth Knowledge Graph system from being built
is silent on all four that already exist — directly undermining the platform's own "check before
building" discipline for exactly the collision category (`TD-49`) most likely to recur.

**Risk:** Medium. No functional break; the risk is purely a future duplicate build.

**Recommendation:** add all five prefixes to `API_MAP.md`'s prefix table, following the same
`TD-XX`-cross-reference pattern already used for `/api/ai-os/v1` (which correctly cites `TD-07`,
`API_MAP.md:127`) — this is the existing convention, not a new one.

**Priority:** P1.

**Estimated implementation cost:** S.

---

## Issue 2 — `/api/ai-os/v1` three-way sharing: correctly documented, unresolved

**Description:** re-validated, not new. `API_MAP.md:127,130` correctly documents that `/api/ai-os/v1`
is shared across `platform_ai_os`, hub MAOS, and (per line 130) `enterprise_hub`'s own
`enterprise_ai_os` routing "again shared, see TD-07."

**Evidence:** `API_MAP.md:127,130`; `docs/TECH_DEBT.md` TD-07.

**Impact:** none beyond `TD-07`'s existing assessment — cited here to confirm the documentation is
accurate and current, which is itself a useful validation result.

**Risk:** Unchanged.

**Recommendation:** unchanged — `TD-07`'s existing "document subpath ownership" recommendation stands.

**Priority:** P2.

**Estimated implementation cost:** S (unchanged from `TD-07`).

---

## Issue 3 — No frontend runtime API prefix collision found among the thirteen runtimes

**Description:** given `docs/RUNTIME_CONSISTENCY.md`'s Issue 1/2 finding (a new Orchestrator and Kernel
layer), this review checked whether their real API prefixes collide with any of the eleven original
runtimes' prefixes.

**Evidence:** each real runtime package (`spatialRuntime`, `lifeEngine`, `assetRuntime`, etc.) defines
its own `*_API_PREFIX`/`*_RUNTIME_VERSION` constant per the pattern already established in prior
research (e.g. `SPATIAL_API_PREFIX = "/api/enterprise-spatial/v1"`, `LIFE_API_PREFIX =
"/api/enterprise-life/v1"`) — this pass did not find a colliding prefix among the newer
`orchestrator`/`kernel` packages specifically (their API surfaces, per `orchestratorApi.ts`/
`kernelApi.ts`, were not individually re-derived route-by-route in this pass, but no shared-prefix
string was found via a name-pattern check).

**Impact:** none — recorded as a clean result, not padded into a false finding.

**Risk:** None found.

**Recommendation:** none required; worth a follow-up only if `API_MAP.md`'s own future update (Issue 1)
surfaces a real prefix string that does collide.

**Priority:** P3 (informational).

**Estimated implementation cost:** N/A.

## Related documents

`docs/API_MAP.md` (real, the document this review validates), `docs/TECH_DEBT.md` (TD-07, TD-49),
`docs/RUNTIME_CONSISTENCY.md` (CQ-30 sibling), `docs/ARCHITECTURE_CONSISTENCY.md` (CQ-30 sibling,
Issue 3 restated here in full).
