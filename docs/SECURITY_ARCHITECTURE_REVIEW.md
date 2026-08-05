# Sprint CQ-32.2 — Security Architecture Review

**Scope:** API security, prompt injection, tenant isolation, permission escalation, secrets, key
management, audit logging, AI abuse, rate limiting, MCP security, Knowledge Base isolation. Documentation
only, `src` not modified. Distinct from `docs/SECURITY_REVIEW.md` (CQ-30.6/30.8) — that document
remains the canonical security-debt tracker; this one is architecture-level (is the *design* sound),
not item-level.

## 1. Correction to the record: Prompt Injection protection is now real (Sprint 30.9)

`docs/SECURITY_REVIEW.md` (CQ-30.8) found **zero** prompt-injection/AI-abuse protection anywhere in
the repository. Re-checked this sprint: **this finding is now stale.** Sprint 30.9 shipped a real,
substantial "AI Security / Beta Hardening" track (`docs/AI_SECURITY.md`):

- Real Prompt Injection Protection (deny-list heuristics, both client `aiPromptSecurity.ts` and backend
  `applications/enterprise_hub/ai_provider_hub/prompt_firewall.py`).
- Real Prompt Sanitizer (strips nulls, bidi overrides, script tags).
- Real Unsafe Prompt Detection (jailbreak / exfiltration / SQLi-ish patterns).
- Real AI Abuse Detection (per-session/per-actor burst window).
- Real Token Usage Limits (truncate to `maxTokens`, default 4096).
- Real AI Request Logging + Audit Trail (`auditAiPrompt`/`auditAiTask` → audit vault).
- Real tests: `tests/test_prompt_firewall_30_9.py`, `aiRuntime.test.ts`'s Sprint 30.9 section.

**Architecture-level assessment (not just "does it exist"):** the design explicitly avoids a parallel
engine — `docs/AI_SECURITY.md`'s own "Extends (no parallel engine)" section confirms it composes real
`aiTaskSecurity.ts` (RBAC/org isolation) and `middleware/security_middleware.validate_input_string`
rather than duplicating them. This is good architecture, not just a good feature.

**One real caveat, stated honestly per this engagement's confidence-labeling discipline
(`docs/ETHICS_GOVERNANCE.md`, CQ-14):** deny-list heuristics are pattern-matching, not a learned or
semantic understanding of intent — real, useful, and also bypassable by a sufficiently novel prompt.
This should be described to stakeholders as "meaningful first-line defense," not "solved."

## 2. A systemic pattern: insecure-default-secret fallbacks, found a third time

`docs/TECH_DEBT.md` TD-57 already tracked the JWT secret default (`"change-me-in-production"`,
resolved Sprint 30.0). This review found the **identical pattern in two more places**:

- `platform_configuration/configuration_center.py:131`:
  `api_jwt_secret=getenv("API_JWT_SECRET", "change-me-in-production-api-jwt-secret")`
- `docker-compose.n8n.yml:22`:
  `N8N_ENCRYPTION_KEY: ${N8N_ENCRYPTION_KEY:-change-me-ados-n8n-key}`

**Architecture-level finding:** this is not three isolated bugs, it's evidence of a missing
**governance control** — nothing in CI or code review catches "a secret env var has a guessable
literal default" as a category, so it recurs every time a new secret is introduced. The JWT case got
fixed because a prior review found it manually; the pattern itself was never closed off.

- **Problem:** no automated check for insecure-default-secret patterns.
- **Evidence:** three real instances across two different subsystems (core config, n8n sidecar).
- **Why it matters:** each instance is individually cheap to exploit if deployed with the default
  ("guess the default" is a real, trivial attack).
- **Risk:** High if any instance reaches production undetected — and the pattern's recurrence proves
  manual review alone isn't catching it reliably.
- **Recommended solution:** add a CI lint rule (a simple regex over `getenv\(.*,\s*["\'].*(change-?me|
  default|admin)` is a reasonable first pass) that fails the build on any new instance, plus fix the two
  found this pass.
- **Effort:** S (lint rule) + S (two fixes).
- **Priority:** Critical.

## 3. MCP Security — real, substantial, not independently audited before

`src/mcp/` (the standalone TS kernel ecosystem, per `CLAUDE.md`) has real, dedicated security-adjacent
modules: `MCPAuthentication.ts`, `MCPPermissions.ts`, `MCPSession.ts`, `MCPGateway.ts` — a
purpose-built auth/permission layer for the Model Context Protocol surface, separate from the Python
backend's identity stack. This is architecturally correct (MCP is a distinct protocol boundary and
should have its own gate), but **its relationship to the Python backend's real tenant/permission model
was not confirmed this pass** — given `TD-33`'s already-established finding that the TS kernel
ecosystem has no runtime connection to the Python backend, it's worth confirming MCP's authentication
doesn't quietly assume a different (or absent) tenant-isolation model than the rest of the platform.

- **Priority:** High (verify). **Effort:** S (trace `MCPAuthentication.ts`'s actual tenant-scoping
  logic).

## 4. Knowledge Base isolation

Real `SpatialPermissionScope`/`AssetPermissionScope`/`Visibility` composition (`TD-52`) is the
platform's general permission model; whether the real Knowledge Graph systems (`TD-49`'s four
implementations) apply per-tenant isolation to *knowledge* specifically — i.e., can Tenant A's AI
context ever surface Tenant B's knowledge-graph entities — was not confirmed this pass. This is a
distinct question from general tenant isolation (`TD-58`'s 79 findings, which scope to `repositories/`)
because knowledge retrieval for AI context assembly is a different code path than a typical CRUD query.

- **Priority:** Critical (verify) — AI context leakage across tenants is a severe, customer-visible
  failure mode if it exists.
- **Effort:** M (trace the real RAG/context-assembly path specifically for tenant filtering).

## 5. Rate limiting — still two implementations, still unresolved

Restated from `docs/ARCHITECTURE_CONSISTENCY.md` Issue 4 (CQ-30.8): `platform_integrations/rate_
limiter.py` vs. `platform_security/rate_limit/RateLimitProtection`, relationship still unconfirmed.
**New this sprint:** `docs/N8N_ARCHITECTURE.md` explicitly reuses `platform_integrations.rate_
limiter` for n8n callback rate limiting — meaning this is the one confirmed real consumer of that
specific limiter, useful evidence for the eventual consumer trace.

## 6. Permission escalation — unchanged assessment

The three-way permission-scope vocabulary mismatch (`TD-52`) remains the platform's most plausible
escalation vector — restated, not re-derived.

## Non-goals

- No fix implemented for the two new insecure-default-secret instances — flagged with exact
  file:line, not resolved.
- No RAG/context-assembly code path traced in full — §4 is a flagged verification task, not a
  completed audit.

## Related documents

`docs/SECURITY_REVIEW.md` (CQ-30.6/30.8, the canonical security-debt tracker this review complements),
`docs/AI_SECURITY.md` (real, Sprint 30.9), `docs/TECH_DEBT.md` (TD-52, TD-57, TD-58), `docs/N8N_
ARCHITECTURE.md` (real), `docs/AI_RUNTIME_REVIEW.md` (CQ-32.2 sibling, RAG boundary detail).
