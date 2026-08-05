# Enterprise Overnight Audit — Security Review

**Scope:** architecture-level security review only (permissions, roles, tenant isolation, identity,
audit, secrets, API exposure, trust boundaries). Documentation only, `src` not modified, no code
changed. Findings are evidence-based (file:line cited); anything not independently traced to a
confirmed exploit path is labeled **pending verification**, not asserted as broken.

## 1. Secrets handling — mostly sound, one path unverified

- Real JWT secret validation exists and works correctly: `platform_identity/jwt_service.py:36-41`'s
  `validate_iam_jwt_secret()` raises a hard `RuntimeError` at startup if `IAM_JWT_SECRET` is empty or
  still the literal default `"change-me-in-production"` — called from `startup.py:57-59`. This is
  good, deliberate defensive engineering, not an oversight.
- **TD-57 (new this audit, pending verification)**: a second, parallel read site,
  `platform_configuration/configuration_center.py:100`, sets `PlatformSettings.jwt_secret =
  getenv("JWT_SECRET", "change-me-in-production")` with **no visible equivalent validation at that
  read site**. Whether this unvalidated copy is ever actually used to sign/verify a real token was not
  traced to a specific consumer in this pass — flagged for a follow-up trace, not asserted as
  exploitable. If any real code path signs tokens using `PlatformSettings.jwt_secret` instead of the
  validated `IAM_JWT_SECRET`, that would be a real P0.
- No hardcoded real API keys/passwords were found committed to source in the files sampled — every
  credential-shaped read (`config.py`, `openrouter.py`, `platform_identity/*`) goes through
  `os.environ`/`getenv`, consistent with `platform_configuration`'s `ConfigurationCenter` pattern
  described in `CLAUDE.md`. (`TD-17` in `TECH_DEBT.md`, P0, already tracks that a handful of files —
  `platform_security/config.py:23-24`, `platform_security/secrets.py:30,80` — read `os.environ`
  *directly*, bypassing `ConfigurationCenter`, which is an architecture-governance violation, not a
  leaked-secret finding — restated here for completeness, not re-derived.)

## 2. Tenant isolation — the pattern exists; exhaustive coverage not verified

`middleware/tenant_middleware.py` is the real, designed tenant-scoping layer for the bot backend
(`CLAUDE.md`'s own description). This audit did **not** exhaustively check all ~100+ `repositories/*.py`
modules for consistent `tenant_id` filtering — that would require reading every query method in every
repository, out of scope for this pass. **TD-58 (new this audit)** records this as an open question:
whether tenant filtering is enforced centrally (e.g., at a session/query-builder level, which would be
safe by construction) or per-repository-method (which would need every method individually correct,
and is the riskier pattern). A future security-focused sprint should trace this specifically — this is
the single highest-value follow-up in this entire review, because a cross-tenant data leak is the
worst-case outcome for a multi-tenant platform and this audit could not rule it out or confirm it.

## 3. City / frontend permission gating — a real, previously-confirmed gap

Restated from this engagement's own earlier research (Sprint CG-6, `docs/CITY_INTEGRATIONS.md` §3):
Enterprise City's frontend had **zero permission/tenant gating** despite real `permissionManager`/
`roleManager`/`organizationManager` already existing and being usable. This audit did not re-verify
whether that gap has since closed — later sprints (CQ-16 onward) added real `spatialPermissions`/
`AssetPermissionScope` to the newer Spatial/Asset runtimes specifically, but whether the *original*
City building/district interaction surface now calls through any of them was not re-checked this pass.
Treat as still-open unless a specific commit/sprint closing it is found.

## 4. Three unreconciled permission-scope vocabularies (TD-52)

`SpatialPermissionScope`, `AssetPermissionScope`, and business `Visibility` are three real,
independently-authored access vocabularies with **different rank orderings for the same word** —
`company` sits at a different relative rank in `SpatialPermissionScope` vs. `AssetPermissionScope`.
This is a security-relevant finding, not just a naming one: composing two access checks whose
authors assumed different meanings for the same token is exactly the kind of gap that produces an
unintended-allow. Full detail: `docs/DIGITAL_TWIN_STANDARDS.md` §2 (CQ-16).

## 5. `/management/v1` and `/api/v1` — governed, not spot-broken

`CLAUDE.md` states `/api/v1`/`/management/v1` contracts are frozen and additive-only, enforced by a
dedicated security test suite (`tests/test_management_security.py`, `tests/test_api_v1_freeze.py`,
`tests/test_admin_security.py`, run as their own CI job). The existence of a dedicated, CI-enforced
freeze test for exactly this surface is a real positive signal — this is the one area of the platform
with an automated regression gate against accidental authorization drift. This audit did not read
every route handler individually; the CI-enforced test suite is the correct ongoing check, not a
manual one-time read.

## 6. Frontend demo-auth fallback — real, but scoped

`src/web` uses ISAM when reachable, falling back to Demo Auth (`VITE_DEMO_AUTH`) per `CLAUDE.md`. This
is a legitimate dev-experience feature, not inherently a vulnerability — the risk is entirely about
build/deploy discipline (does a production build definitely have `VITE_DEMO_AUTH` unset/false). This
was not traced to a specific CI/build-time guard in this pass; worth a five-minute check before any
production cutover, not treated here as a confirmed gap.

## 7. What this review did NOT cover (explicit scope limits)

- No exhaustive repository-by-repository tenant-filter audit (§2).
- No live penetration test or dependency-vulnerability scan (`pip-audit`/`npm audit` were not run).
- No trace of every `PlatformSettings.jwt_secret` consumer (§1).
- No verification of secrets-in-CI (GitHub Actions secrets configuration) — out of scope for a
  repo-content-only audit.

## Priority summary

| Finding | Severity | Status |
|---|---|---|
| TD-57 — unvalidated `PlatformSettings.jwt_secret` read path | P1 | **Hardened, Sprint 30.0** — see §8 |
| TD-58 — tenant-filter coverage across repositories | P1 | **In progress, Sprint 30.0** — 79 heuristic findings, see §8 |
| City frontend permission gating (§3) | P1 (if still open) | Pending re-verification |
| TD-52 — three permission-scope vocabularies | P1 | Confirmed |
| TD-17 — `os.environ` bypassing `ConfigurationCenter` | P0 | **Resolved, Sprint CQ-30** |

## 8. Sprint CQ-30.6 addition — independent re-verification

**JWT (TD-57):** `platform_security/jwt_secrets.py` now provides a single canonical
`resolve_iam_signing_secret()`/`validate_signing_secret()` path, consumed by `platform_identity/
jwt_service.py`'s `get_jwt_secret()`/`validate_iam_jwt_secret()` — the two-path split this document
originally flagged is gone; there is one real secret-resolution function now. Production validation
also checks the API JWT and `SECURITY_MASTER_KEY`. **Status: the fix this review previously
recommended has shipped** (Sprint 30.0) — confirmed by direct read of the current file content, not
assumed.

**Tenant isolation (TD-58):** a real audit tool now exists, `scripts/audit_tenant_isolation.py` (117
lines), producing `docs/TENANT_ISOLATION_AUDIT.md` — a real, dated (Sprint 30.0) scan of
`repositories/*.py` flagging **79** heuristic `query_without_tenant_mention` findings across dozens of
real repository files (`ai_advertising_agent_repository.py`, `audit_repository.py`,
`automotive_partner_repository.py`, `car_repository.py`, `commercial_billing_repository.py`, and more).
**This materially sharpens the prior "pending verification" status**: the question is no longer *whether*
a systematic check exists (it does), it's *whether each of the 79 flags is a real leak or a false
positive* — the tool is explicitly heuristic, not a confirmed-exploit list. This is now the single most
concrete, actionable security item in the platform: 79 named file/function/line targets, ready for
manual triage.

**Google Login:** confirmed absent (`docs/LOGIN_USER_FLOW.md` §1, CQ-30.1) — no OAuth/Google-specific
code found in `src/web/auth`. Not a security *weakness* (nothing broken), a real feature gap if Beta
marketing promises it.

**Refresh tokens:** real and correctly implemented — `platform_identity/jwt_service.py`'s
`verify_refresh_token()`/`rotate_refresh_token()` (rotation-on-use, revokes the old `jti`, chains to a
new one) — no rotation-replay vulnerability found in the sampled logic (old token is explicitly
revoked before the new pair is issued).

**Owner Mode / God Mode:** gated by real `useIsPlatformOwner()` (`platform-builder/managers/
platformOwner.ts`), consumed by real `Sidebar.tsx` to hide (not disable) Owner-only navigation —
correct pattern per `docs/ROLE_NAVIGATION.md` §2 (CQ-30.1). Whether every *backend* Owner-scoped
endpoint enforces the equivalent server-side check (not just the UI hiding the link) was **not**
independently re-verified this pass — flagged as the one remaining Owner Mode question, since a hidden
UI link is not itself an access control.

**Permission escalation:** no direct escalation vulnerability found in this pass's sampled code; the
three-way permission-scope vocabulary mismatch (`TD-52`) remains the platform's most plausible
escalation *vector* — composing two scopes that disagree on `company`'s relative rank is exactly the
kind of gap that could produce an unintended-allow, restated as still the top concern.

## 9. Sprint CQ-30.8 addition — OAuth/rate limiting/AI abuse/secrets

**OAuth / Google Login:** confirmed absent again this pass — no OAuth flow of any kind found anywhere
in the backend or frontend (not just Google-specific). `EngineRoleCode`/JWT-based auth is the only real
identity path. Not a vulnerability, a real feature gap, restated for this review's explicit OAuth ask.

**Rate limiting — two real, likely-complementary implementations found:**
`platform_integrations/rate_limiter.py` ("per provider, endpoint, and API key" — reads as *outbound*
rate limiting, e.g. respecting the OpenRouter provider's own limits) vs. `platform_security/rate_
limit/RateLimitProtection` (Sprint 21.4, "Rate limiting & protection," backed by real
`PROTECTION_CONTROLS`). These were not traced deeply enough this pass to confirm they're genuinely
complementary (outbound vs. inbound) rather than a duplicate — flagged as needing a five-minute
consumer check before assuming either way. **Separately, and more concretely: no rate limiting was
found at the nginx/edge layer** — the real, production-wired `nginx.conf` (confirmed mounted in
`docker-compose.prod.yml`) has no `limit_req` directive anywhere. Every request that reaches the `bot`
service relies entirely on application-level limiting.

**Prompt injection / AI abuse risk — RESOLVED, Sprint 30.9.** This finding (originally: "confirmed
absent, real gap," CQ-30.8) is now stale. Sprint 30.9 shipped a real "AI Security / Beta Hardening"
track (`docs/AI_SECURITY.md`): real deny-list prompt-injection heuristics (client `aiPromptSecurity.ts`
+ backend `prompt_firewall.py`), real prompt sanitization, real jailbreak/exfiltration detection, real
per-session AI abuse burst-window detection, real token limits, real audit logging — all composing
existing RBAC/org-isolation code rather than duplicating it. See `docs/SECURITY_ARCHITECTURE_REVIEW.md`
§1 (CQ-32.2) for full detail and the one honest caveat (heuristic, not semantic, detection).

- **Priority:** P1 for Beta (the AI surface is real and reachable; the risk is real even if no exploit
  has been observed). **Complexity:** M (a basic input-sanitization/moderation layer ahead of the
  provider call is a bounded, well-understood pattern, not a research problem).

**Secrets / environment variables — one new concrete finding:** `docker-compose.prod.yml`'s Grafana
service has a default weak-credential fallback: `GF_SECURITY_ADMIN_PASSWORD: ${GRAFANA_ADMIN_
PASSWORD:-admin}` — the same shape of risk as the JWT `"change-me-in-production"` default (`TD-57`),
now found in the monitoring stack specifically. Grafana access typically exposes real operational/
business metrics — a default `admin`/`admin` login left unrotated is a real, low-effort attack surface.

- **Priority:** P0 — trivial to fix, real exposure if deployed with the default.
- **Complexity:** S — require the env var with no fallback, or document mandatory rotation before
  first deploy.

**A second SQLite artifact found, alongside `TD-30`'s `memory.db`:** `backups/backup_2026_07_12_12_
55.db` — a real SQLite file sitting in the real `backups/` directory, despite `POSTGRES_ONLY=true`
policy. Not itself a security issue, but worth reconciling with the no-SQLite policy the same way
`TD-30` already flagged for `memory.db`.

## Related documents

`docs/TECH_DEBT.md` (TD-17, TD-52, TD-57, TD-58, TD-30 — this review's findings live there as the
canonical registry), `docs/DIGITAL_TWIN_STANDARDS.md` §2 (CQ-16), `docs/CITY_INTEGRATIONS.md` §3
(CG-6, the original permission-gap finding), `docs/CROSS_ORG_DAILY_COOPERATION.md` §2 (CQ-17, a
related permission-composition gap), `docs/TENANT_ISOLATION_AUDIT.md` (real, Sprint 30.0, the 79-item
scan), `docs/ARCHITECTURE_REVIEW_V2.md` (CQ-30.6 sibling), `nginx.conf`/`docker-compose.prod.yml`
(real, CQ-30.8 evidence).
