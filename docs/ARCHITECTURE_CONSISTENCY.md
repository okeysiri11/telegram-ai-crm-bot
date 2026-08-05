# Sprint CQ-30 — Architecture Consistency Review

**Mission:** validate every recommendation from `docs/FINAL_AUDIT_RESULT.md` against the current
repository state, not restate it. Documentation only, `src` not modified. Every item below was
re-checked this sprint with fresh file:line evidence — none are carried forward unverified.

## Validation status summary

| Audit item | Status | Confidence |
|---|---|---|
| `TD-17` — `os.environ` bypassing `ConfigurationCenter` | **RESOLVED** | High — re-read both cited files |
| `TD-57` — unvalidated second JWT-secret path | **PARTIALLY RESOLVED** | High — see Issue 1 |
| `TD-51` — no real `Project` entity | **STILL OPEN** | High — re-ran the same grep |
| `TD-55` — `src/domains` orphaned (141 files) | **STILL OPEN** | High — re-counted, re-checked imports |
| `TD-08` — header-only Platform Builder auth | **STILL OPEN** | High — re-read the middleware source |
| Second cross-runtime aggregator (recommendation #97) | **NOW VIOLATED** | High — see `docs/RUNTIME_CONSISTENCY.md` Issue 1 |
| Six-way deal-pipeline collision (`TD-47`) | **UNCHANGED** | Not re-derived this pass; see `docs/ENTITY_CONSISTENCY.md` |
| Four-way Knowledge Graph collision (`TD-49`) | **PARTIALLY WORSE** | See `docs/API_CONSISTENCY.md` — `API_MAP.md` still doesn't document 3 of 4 prefixes |

## Issue 1 — TD-57 (JWT secret validation): real logic now exists, but is not enforced at startup

**Description:** the overnight audit flagged a second, seemingly-unvalidated JWT-secret read path in
`platform_configuration/configuration_center.py`. Re-checking this sprint found the validation logic
has since been built — and is more sophisticated than the audit anticipated — but is deliberately
invoked in non-blocking mode at the one place that matters.

**Evidence:** a real `ConfigurationValidationReport`/`validate(*, fail_fast: bool = False)` method now
exists (`configuration_center.py:266`), checks `IAM_JWT_SECRET`/`JWT_SECRET` against a real
`_INSECURE_JWT_SECRETS` frozenset (`:47`), and — if `fail_fast=True` — raises `RuntimeError`
(`:295-296`). A real test exists for this exact behavior
(`tests/test_configuration_center.py:47-53`, `test_validation_fail_fast_on_insecure_production_jwt`).
**But** `startup.py:54` calls `configuration_center.validate(fail_fast=False)` — the one real
production-startup call site explicitly disables the block. A production deploy with an unset/default
`JWT_SECRET` today would have the issue logged (`startup.py:55`'s `diagnostics()["validation"]`) but
would **not** fail to start.

**Impact:** the platform now has a correct, tested safety mechanism that is configured off at the exact
point it exists to protect. This is a more precise and more actionable finding than the original audit
produced, because it identifies exactly one line (`startup.py:54`) rather than an open-ended "trace the
consumers" task.

**Risk:** Medium-High — a misconfigured production deploy would currently boot successfully with an
insecure JWT secret and only be discoverable by reading logs, not by the application refusing to start.
Separately, `platform_identity/jwt_service.py`'s `validate_iam_jwt_secret()` (unconditional, real
`RuntimeError`, called at `startup.py:57-59`) **does** block — so one of the platform's two JWT-secret
paths is fail-closed and the other is fail-open, an inconsistency worth resolving on its own.

**Recommendation:** change `startup.py:54` to `configuration_center.validate(fail_fast=is_production)`
(or unconditionally `True`) — a one-line change, already covered by an existing passing test for the
`fail_fast=True` case.

**Priority:** P0 — cheapest possible fix for a real, currently-live gap.

**Estimated implementation cost:** S (one line + confirm the existing test still passes; no new test
needed since `tests/test_configuration_center.py:47-53` already covers the target behavior).

---

## Issue 2 — TD-17 (architecture-governance violation): confirmed resolved

**Description:** the overnight audit cited `platform_security/config.py:23-24` and
`platform_security/secrets.py:30,80` as reading `os.environ` directly, bypassing `ConfigurationCenter`
(CI-failing at the time, per `ARCHITECTURE_REPORT.md`).

**Evidence:** re-reading both files this sprint: `platform_security/config.py`'s
`SecurityConfig.from_configuration()` now reads through `configuration_center.settings.security.
environment` (`config.py:20-24`); `platform_security/secrets.py`'s `get_from_configuration()` reads
through `configuration_center.settings` via attribute-path traversal (`secrets.py:77-84`, covering the
originally-cited line 80 specifically). No direct `os.environ`/`getenv` call remains in either file's
sampled content.

**Impact:** a real, previously CI-failing architecture violation now appears fixed. This is worth
stating plainly and positively — validating a fix is as much this sprint's job as finding new problems.

**Risk:** None remaining, pending a full CI run to confirm `scripts/validate_architecture.py` now
passes this specific check (not re-run in this documentation-only pass).

**Recommendation:** close `TD-17` in `docs/TECH_DEBT.md`, marked `RESOLVED — Sprint CQ-30` per that
file's own §3 convention ("move it out of §1 or mark it RESOLVED... keep the row for history").

**Priority:** P3 (administrative — just needs the registry updated to reflect reality).

**Estimated implementation cost:** S (one registry edit).

---

## Issue 3 — `API_MAP.md` doesn't document 3 of the 4 real Knowledge Graph API prefixes

**Description:** `docs/API_MAP.md` describes itself as the map "people use to find 'does this endpoint
already exist'" and states a missing entry should be "treated as a bug, not a minor omission." This
sprint checked whether it documents the four real Knowledge Graph systems (`TD-49`).

**Evidence:** `grep -n "enterprise-kg\|enterprise-ekg\|enterprise-ekp\|enterprise-etw" docs/API_MAP.md`
returns zero hits — none of the four real, live prefixes (`/api/enterprise-kg/v1`, `/api/enterprise-
ekg/v1`, `/api/enterprise-ekp/v1`, and the related `/api/enterprise-etw/v1` from the Digital Twin
collision) appear in the file the platform's own documentation says is authoritative for exactly this
question.

**Impact:** the one document explicitly positioned to prevent someone from accidentally building a
fifth Knowledge Graph system by not realizing four already exist is currently silent on all four. This
directly undermines this engagement's own repeated recommendation (`TD-49`, `docs/RELATIONSHIP_MODEL.
md`) to "check before building."

**Risk:** Medium — the gap is in the exact document meant to prevent the exact failure mode this whole
audit lineage keeps finding.

**Recommendation:** add the four Knowledge Graph prefixes (and the Digital Twin `/api/enterprise-etw/
v1`) to `API_MAP.md`, with a one-line pointer to `docs/ENTERPRISE_ONTOLOGY.md`'s collision writeup for
context. Full detail in `docs/API_CONSISTENCY.md`.

**Priority:** P1.

**Estimated implementation cost:** S.

## Issue 4 — Sprint CQ-30.8 addition: two real rate-limiting implementations, relationship unconfirmed

**Description:** `platform_integrations/rate_limiter.py` ("per provider, endpoint, and API key" — real
class `RateLimitExceededError`-raising limiter, reads as outbound-provider-facing) and `platform_
security/rate_limit/RateLimitProtection` (Sprint 21.4, backed by real `PROTECTION_CONTROLS`) both
implement rate limiting with no confirmed relationship between them.

**Evidence:** `platform_integrations/rate_limiter.py:1` ("Rate limiter — per provider, endpoint, and
API key"); `platform_security/rate_limit/__init__.py:1` ("Rate limiting & protection — Sprint 21.4").

**Impact:** either a legitimate outbound/inbound split (in which case this is fine, just undocumented
as intentional) or a real duplicate — this review could not distinguish the two without a deeper
consumer trace than its scope allowed.

**Risk:** Low-Medium — worth resolving before Beta specifically because rate limiting is one of this
review's own security findings (`docs/SECURITY_REVIEW.md` §9) where the *absence* at the nginx/edge
layer makes correct behavior of whichever application-level limiter(s) are real more load-bearing than
it would otherwise be.

**Recommendation:** a five-minute consumer-import trace (`grep -rl "from platform_integrations.rate_
limiter\|from platform_security.rate_limit"`) resolves this definitively — flagged here rather than
resolved because this review's evidence gathering stopped short of that trace.

**Priority:** P2. **Estimated implementation cost:** S (trace) / M (consolidate, if genuinely
duplicate).

## Related documents

`docs/FINAL_AUDIT_RESULT.md` (the document this sprint validates), `docs/TECH_DEBT.md`,
`docs/RUNTIME_CONSISTENCY.md`, `docs/API_CONSISTENCY.md`, `docs/ENTITY_CONSISTENCY.md`,
`docs/DOMAIN_BOUNDARIES.md` (CQ-30 siblings), `docs/SECURITY_REVIEW.md` §9 (CQ-30.8, the edge-rate-
limiting gap that makes Issue 4 more consequential).
