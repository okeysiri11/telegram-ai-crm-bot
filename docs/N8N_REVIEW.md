# Sprint CQ-32.2 — n8n Integration Review

**Scope:** verify no business logic lives inside n8n; n8n remains orchestration only; Platform Runtime
remains the source of truth. Documentation only, `src` not modified.

## Verdict: the constraint is real, enforced by design, not just policy

`docs/N8N_ARCHITECTURE.md` (real, Sprint 31.2) states the constraint explicitly: **"Platform Runtime =
system of record. No business logic in n8n."** This review's job is confirming that constraint is
actually load-bearing in the implementation, not just asserted in a doc header — and it is.

## Evidence the constraint is enforced, not just stated

1. **The real `WorkflowTemplate` dataclass bakes the constraint into its own data shape**
   (`platform_integrations/n8n_bridge.py`): every template carries `platform_owned: bool = True` and
   its `to_dict()` explicitly emits `"business_logic_in_n8n": False` — the constraint is a real,
   serialized field on every workflow record, not just a comment.
2. **The real execution flow is one-directional for business logic**: `n8n trigger → HTTP call to
   platform API → platform applies business logic → n8n receives callback status only`
   (`N8N_ARCHITECTURE.md`'s own diagram). n8n never receives domain state back, only a status — it
   cannot make a business decision it doesn't have the data to make.
3. **Credentials are vault-referenced, not embedded**: `vault://n8n/...` — n8n holds credential
   *references*, not the platform's real secrets, limiting what an n8n workflow could even do if it
   tried to act autonomously on platform data.
4. **Rate limiting and the real Prompt Firewall are both explicitly extended to the n8n path**, per
   `docs/AI_SECURITY.md`/`N8N_ARCHITECTURE.md` — n8n-triggered AI invocations go through the same real
   security gates as any other invocation, not a bypass path.

## The one real gap found this review: the insecure-default encryption key

`docker-compose.n8n.yml:22`: `N8N_ENCRYPTION_KEY: ${N8N_ENCRYPTION_KEY:-change-me-ados-n8n-key}` — the
same systemic pattern `docs/SECURITY_ARCHITECTURE_REVIEW.md` §2 (CQ-32.2) found twice elsewhere. This
key encrypts n8n's own credential store — if a Beta deployment runs with the default, n8n's stored
integration credentials are only as safe as this well-known literal string.

- **Priority:** Critical (same category as the JWT/API-JWT-secret findings).
- **Effort:** S — same fix pattern as the other two instances, ideally closed by the same CI lint rule
  recommended in `docs/SECURITY_ARCHITECTURE_REVIEW.md` §2.

## Architecture assessment

n8n is deployed as an **optional sidecar** (`--profile n8n`, not part of the default compose stack) —
a deliberately low-risk integration posture: the platform functions fully without it, and enabling it
doesn't change the platform's own trust boundary (n8n calls in through the same real API surface any
other integration would). This is the correct shape for an orchestration-only external tool.

## What this review recommends

1. Fix the encryption-key default (Critical, cheap).
2. Confirm the "Prompt Firewall remains on APH invoke path" claim (`N8N_ARCHITECTURE.md`'s own
   Security section) is specifically exercised by n8n-triggered AI calls in a real test, not just
   architecturally true — a one-test gap-check, not a design concern.
3. No structural change recommended — the orchestration-only boundary is well-designed and, per the
   evidence in this review, actually held to in the implementation.

## Non-goals

- No re-architecture of the n8n integration — the design is sound.
- No fix implemented for the encryption-key default — flagged with exact location, not resolved.

## Related documents

`docs/N8N_ARCHITECTURE.md`/`docs/INTEGRATION_HUB.md`/`docs/WORKFLOW_LIBRARY.md`/`docs/SPRINT_31_2_
RESULT.md` (real), `docs/AI_SECURITY.md` (real, Sprint 30.9), `docs/SECURITY_ARCHITECTURE_REVIEW.md`
§2 (CQ-32.2 sibling, the systemic default-secret pattern this review's one gap belongs to).
