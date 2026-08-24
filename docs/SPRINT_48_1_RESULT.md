# Sprint 48.1 — Crypto Anti-Fraud Real Payout Wiring — RESULT

Scope: wire Sprint 48.0's `CryptoTxAntifraudEngine` into a real, canonical, deal-scoped payout
path used by both Telegram and Web, and disable override until real step-up authentication exists.
Stayed on `develop`. No commits, no pushes, no resets, no branch switches. Did **not** start Sprint
47.2 and did **not** migrate crypto/OTC into DealEngineV1 (see "Explicitly deferred" below).

## 1. Original problem

Sprint 48.0 built a correct, well-tested anti-fraud engine with zero callers on any real payout path
(see `docs/SPRINT_48_0_RESULT.md`). This sprint's job was to make duplicate-payout protection
actually enforced in production, not just provable in isolation.

## 2. Architecture discovered (before writing any code)

Traced every real, operator-reachable path that could complete a crypto/OTC payout:

- **Telegram bot**: `database_legacy.py::update_crypto_payment_status(..., "PAYMENT_RECEIVED", ...)`
  had exactly one caller in the whole codebase — `run_crypto_erp_cycle_test`, a synthetic self-test
  (`/crypto_test` command). No real operator action ever triggered it.
- **Web**: zero frontend usage of `DealEngineV1`/`PaymentEngineV1` anywhere in `src/web`.
- **Concierge** (`services/telegram_ai_super_app/concierge.py`): a content/copy-generation planner
  (`plan_from_text`, `vertical_playbook`) that classifies messages into topics — no transactional
  capability at all. Confirmed non-transactional; not given one this sprint (see §6).

The only real, operator-facing surface displaying a real crypto/OTC deal is the Telegram deal-detail
screen (`handlers.py::crypto_otc_deal_or_request`, backed by `database_legacy.py`'s
`crypto_deals`/`crypto_payments` SQLite tables).

## 3. Why legacy crypto IDs were not mapped onto DealEngineV1 UUIDs

`database/models/deal_engine_v1.py`: `DEAL_ENGINE_V1_SUPPORTED_VERTICALS = frozenset({"auto", "agro"})`.
Crypto has no presence in `DealEngineV1`/`PaymentEngineV1` at all — no vertical support, no existing
deal has ever been created there for crypto. Sprint 48.0's `CryptoIncomingTransaction.deal_id`/
`payout_id` are UUID FKs into those tables regardless — a design gap, not a deliberate choice (never
validated against real usage). Mapping legacy integer deal/payment IDs onto those UUID columns was
rejected for three reasons, per explicit instruction:
1. It would require adding `"crypto"` to `DEAL_ENGINE_V1_SUPPORTED_VERTICALS` and creating real
   `DealEngineV1Deal` rows going forward — silently starting the Sprint 47.5.4-shaped "Crypto
   persistence backfill" migration project (from `docs/SPRINT_47_MULTI_DOMAIN_EXPANSION_PLAN.md`,
   itself unapproved) inside an anti-fraud sprint.
2. It would create two parallel "crypto deal" records (legacy + DealEngineV1) that could drift.
3. Overloading a UUID column with an integer or string ID is a correctness bug, not a shortcut.

**Decision:** two new nullable integer columns (`legacy_deal_id`, `legacy_payment_id`, no FK — the
referenced row lives in a different, SQLite, database) preserve the real reference without touching
the UUID columns, which stay reserved for a real future DealEngineV1 migration (tracked as debt below,
explicitly not performed here).

## 4. Final canonical payout path

```
Telegram deal-detail screen ─┐
                              ├──> CryptoPayoutOrchestrator.confirm_payout()
Web payout-confirm panel ────┘              │
                                             ├─> validate deal/payment + current state (legacy read)
                                             ├─> idempotent-retry check (same deal+payment+tx already
                                             │   COMPLETED? return ALREADY_CONFIRMED, no re-execution)
                                             ├─> CryptoTxAntifraudEngine.register_incoming()
                                             │     (atomic claim via session.begin_nested() +
                                             │     IntegrityError on the real UNIQUE constraint —
                                             │     this is still the final concurrency guarantee,
                                             │     not an application lock)
                                             ├─ if duplicate: STOP — return warning, no state
                                             │   transition, Cancel/Send-for-review/Override offered
                                             └─ if allowed: database.update_crypto_payment_status()
                                                (the existing legacy transition) ->
                                                CryptoTxAntifraudEngine.complete_payout() ->
                                                immutable audit row -> success
```

`services/crypto_payout_orchestrator.py::CryptoPayoutOrchestrator` is this single canonical path.
Its public contract (`confirm_payout`, `get_deal_summary`, `cancel`, `request_review`,
`approve_override`) does not expose `database_legacy.py` internals — it imports through
`database/__init__.py`'s existing legacy shim (`from database import get_crypto_deal, ...`), the same
sanctioned pattern `services/crypto_erp.py` already used before this sprint. When crypto is migrated
into DealEngineV1 later, only this module's body changes — Telegram/Web's calls into it do not.

## 5. Backend wiring

- **`database/models/crypto_tx_registry.py`** — added `legacy_deal_id`/`legacy_payment_id` (nullable
  int) to `CryptoIncomingTransaction` and `CryptoTxOverrideLink`.
- **Migration `migrations/versions/x7r890123456_crypto_tx_legacy_refs_48_1.py`** — chained after
  Sprint 48.0's head (`w6q789012345`). **Bug found and fixed during verification, not just written
  and assumed correct:** the first version crashed on `alembic upgrade head` after
  `alembic downgrade -1` (`DuplicateColumnError`) because `downgrade()` is a deliberate no-op (same
  non-destructive precedent as `u4o567890123`/`v5p678901234`) — the columns survive a downgrade, so
  `upgrade()` must be idempotent by column existence, not just table existence. Fixed by checking
  `information_schema.columns` before `ADD COLUMN`. Re-verified with a real
  `downgrade -1` → `upgrade head` round trip against the live Postgres database after the fix; it now
  succeeds.
- **`database_legacy.py`** — added `get_crypto_payment_for_deal(deal_id)`, a small read-only helper
  (mirrors an existing inline query already used by `run_crypto_erp_cycle_test`); no behavior change
  to any existing function.
- **`services/pg_crypto_tx_antifraud_engine.py`** — `register_incoming()` gained
  `legacy_deal_id`/`legacy_payment_id` params (status becomes `RESERVED` when either the UUID or
  legacy reference is set); `DuplicateWarning` gained `previous_legacy_deal_id`/
  `previous_legacy_payment_id`. **Override rewritten**: `reauth_verified: bool` (Sprint 48.0, a
  client-supplied flag — not authentication) removed; replaced with `step_up_token: str | None` and
  `_verify_step_up_token()`, which always returns `False` today because no real step-up provider
  exists in this codebase (confirmed: `platform_security/` has no MFA/step-up verifier, only a
  passing comment mentioning "optional MFA / trusted device"). `approve_override()` still validates
  role → confirmation → reason in that order (for correctly-specific audit reasons), then always
  raises the new `CryptoTxOverrideUnavailableError` — a fully privileged, fully confirmed, fully
  reasoned request is still rejected, by construction, until `_verify_step_up_token` is given a real
  implementation. This is the single seam a future real provider plugs into.
- **`services/crypto_payout_orchestrator.py`** (new) — the canonical path described in §4.
- **Layering violation fixed**: `services/crypto_tx_antifraud_router.py` (an aiohttp HTTP module
  living in `services/`, contradicting CLAUDE.md's "services/ — business logic, no direct HTTP
  exposure") deleted; replaced by **`platform_management/crypto_tx_antifraud_routes.py`**, which
  delegates every handler to `CryptoPayoutOrchestrator` and adds `GET deals/{deal_id}` +
  `POST deals/{deal_id}/confirm-payout`. The old generic `POST /register` (no deal validation — a
  direct-API bypass of the orchestrator) was removed, not carried over.
- **`platform_management/management_router.py`** — import path updated to the new module.

## 6. Telegram integration

`routers/crypto_tx_antifraud_router.py` rewritten: `start_payout_confirmation()` (called from
`handlers.py`) begins an FSM that collects network/tx_hash/token/amount/wallet_address, then calls
`CryptoPayoutOrchestrator.confirm_payout()` — never `CryptoTxAntifraudEngine` directly (verified by
an architectural test that inspects the shipped module's actual attributes, not by convention).
`handlers.py::crypto_otc_deal_or_request` (the deal-detail screen) now offers a
"✅ Подтвердить платёж (tx_hash)" button only when a real, non-terminal deal with an unconfirmed
payment is on screen — presentation-only logic (which deal, when to show the button); zero
antifraud/state-transition logic added to `handlers.py` itself, per explicit instruction.
`keyboards.py::crypto_otc_menu()` gained an additive, optional `extra_row` parameter (default `None`
reproduces the exact prior keyboard for every existing caller). Override's FSM path and its inline
button were removed entirely — not hidden, removed — since it can never succeed server-side now.

## 7. Web integration status

Real, not a demo: **`src/web/src/crypto-antifraud/CryptoPayoutConfirmPanel.tsx`** (new), routed at
`/crypto-otc/payout/:dealId` (`src/web/src/App.tsx`). Fetches the real deal via
`GET /management/v1/crypto-tx/deals/{dealId}`, submits through
`POST /management/v1/crypto-tx/deals/{dealId}/confirm-payout` — the same orchestrator Telegram calls
— and renders the existing `DuplicateTxWarningModal` on a duplicate response (not a second warning
UI). `cryptoTxApi.ts` updated to match (generic `registerCryptoTx`/`useCryptoTxRegistration` removed
— they called the now-deleted bypass endpoint). `DuplicateTxWarningModal.tsx` no longer offers an
override button (server rejects it unconditionally now); shows an explanatory note instead.

## 8. Concierge — deliberately not transactional

No payout capability was added to Concierge. It remains a content/copy-generation planner. The
integration boundary is `CryptoPayoutOrchestrator` itself: if a future Concierge command needs to
initiate a payout, it should call `CryptoPayoutOrchestrator.confirm_payout()` (or route/hand off to
the Telegram/Web flow that does) exactly like Telegram and Web do — never re-implement duplicate
detection or a state transition inside Concierge's own code. This is a documented boundary, not
built infrastructure, per explicit instruction not to invent transactional capability there.

## 9. Security — override

Per explicit instruction: a second button-tap is not reauthentication, and if real step-up auth
doesn't exist, override must be disabled, not faked. Implemented exactly that (§5) — verified end to
end at three layers, not just unit-tested in isolation:
- Engine: `approve_override()` raises `CryptoTxOverrideUnavailableError` for a fully privileged,
  fully confirmed, fully reasoned request.
- HTTP: `POST .../override/approve` returns `503` for a genuine OWNER-role caller (proven via a real
  aiohttp request/response round trip against a real JWT, not a mocked call).
- UI: both Telegram and Web stopped offering an override button at all.
Send-for-review remains fully available at every layer, unaffected.

## 10. Tests

New: `tests/test_crypto_payout_orchestrator_48_1.py` (17 tests) — first payout, duplicate blocks
before the legacy state transition runs, 2-way concurrent race (exactly one winner), idempotent
retry (no re-execution), legacy reference integrity, deal-not-found/terminal-state validation,
unauthorized override, override-unavailable-even-for-owner, send-for-review, an architectural check
that the bot router and `handlers.py` never touch the raw engine/orchestrator inappropriately, and
HTTP-layer coverage (deal summary, confirm→duplicate, the removed bypass endpoint's 404, unauthorized
and unavailable override at the HTTP layer).

Updated: `tests/test_crypto_tx_antifraud_48_0.py` (16 tests) — override tests rewritten for the
disabled-override behavior; old `/register`-endpoint HTTP tests removed (endpoint gone); one new test
for `legacy_deal_id`/`legacy_payment_id` registration.

**Why these tests fake the legacy persistence layer**: discovered mid-sprint, not assumed —
`tests/conftest.py` line 12 unconditionally sets `POSTGRES_ONLY=true` for the entire test session
("Tests always use PostgreSQL policy; SQLite must not bootstrap"), which makes
`database_legacy.py`'s module-level `conn`/`cursor` `None` for every test, always. No test file
before this sprint had ever called a `database_legacy.py` crypto function, so there was no precedent
either way. Followed Sprint 46.6's documented precedent for the same class of problem ("mocking out
the one incidental DB call") with a small, faithful in-memory fake (`_FakeLegacyCryptoStore`,
row-shape-verified against the real `SELECT *` column order) patched onto the real `database_legacy`
module object. What's real and unmocked: the Postgres-backed `CryptoTxAntifraudEngine`/
`CryptoTxRegistryRepository` and the actual DB unique constraint.

### Test results

| Suite | Result |
|---|---|
| `tests/test_crypto_payout_orchestrator_48_1.py` (new) | 17 passed |
| `tests/test_crypto_tx_antifraud_48_0.py` (updated) | 16 passed |
| `tests/test_database_stabilization_37_1.py`, `test_memory_scope_47_1.py`, `test_ai_command_scoping_47_0.py`, `test_vertical_nav_46_5.py` | 68 passed |
| `tests/test_management_security.py`, `test_api_v1_freeze.py`, `test_admin_security.py` | 37 passed |
| Full `pytest tests/ -q -m "not slow"` | 5289–5293 passed, 389 failed, 9–13 skipped (see below) |
| Frontend `npx vitest run src/crypto-antifraud` | 10 passed |
| Frontend full `npx vitest run` | 525 passed, 9 failed (see below) |
| `npx tsc -b --pretty false` | pre-existing unrelated errors only; zero errors in any Sprint 48.x file (verified by grep) |
| `npx vite build` (frontend production bundle) | succeeds |
| Live localhost smoke test | see §11 |

### Full backend regression — exact classification (not just counts)

`grep "^FAILED" | grep -v test_crypto_tx_antifraud_48_0 | grep -v test_crypto_payout_orchestrator_48_1 | wc -l` → **363**, matching Sprint 47.1's documented baseline count exactly (verified by count, both runs of the full suite reproduced 363 non-crypto failures). **Zero non-crypto regressions.**

The remaining ~26 lines are every Sprint 48.0/48.1 crypto test — but **only when run as part of the
full ~5,700-test suite**; the same files pass 100% (33/33) standalone, in the targeted-suite run
above, and in a realistic ~1,460-test reproduction batch that precedes them alphabetically. Traced
the actual traceback (not assumed): two *different* underlying errors surfaced across separate full-
suite runs for the same tests —
1. `RuntimeError: ... Future ... attached to a different loop` (the exact class of shared-AsyncEngine-
   across-pytest-asyncio's-per-test-event-loops issue Sprint 46.6's RESULT doc already documented for
   a different file), and
2. `sqlalchemy.exc.InvalidRequestError: Multiple classes found for path "RolePermission" ... Please
   use a fully module-qualified path` — traced to two **separate, pre-existing** SQLAlchemy model
   classes both named `RolePermission`, both registered on the same `database.base.Base` declarative
   registry: `database/models/role_permission.py` (`__tablename__ = "permission_engine_role_permissions"`)
   and `database/models/permissions.py` (`__tablename__ = "role_permissions"`) — different tables, so
   not a table collision, but an ambiguous short-name collision for SQLAlchemy's string-based
   relationship resolution. Both files predate Sprint 48.0. This is a genuine, pre-existing
   architectural defect (two classes, one domain concept, violating this repo's own "one canonical
   implementation per domain" rule) that lies dormant until some test's mapper-configuration cascade
   happens to run after both ambiguous classes are already registered by earlier tests in the same
   process — inherently order-dependent, which is exactly why the *same* crypto tests hit *two
   different* error signatures across separate full-suite runs. This is test-infrastructure/model-
   registry fragility, not a logic defect in the crypto engine or orchestrator (which is proven
   correct by 33/33 passing whenever this collision isn't triggered). **Not fixed in this sprint** —
   fixing a naming collision between `database/models/permissions.py` and `role_permission.py` is
   unrelated-module work outside a crypto anti-fraud sprint's scope; recorded as debt below.
   Applied a partial, contained mitigation (disposing the cached DB engine both before and after each
   test in these two files, not just after) since that was the previously-documented fix pattern for
   the first error class; verified by actually re-running the reproduction batch that it does not fix
   the second, unrelated error class — so it's disclosed here as attempted-but-insufficient, not
   claimed as a fix.

### Full frontend regression — exact classification

9 failures, all pre-existing and unrelated to any Sprint 48.x file (confirmed: none of the 9 failing
test files were touched this sprint): `closedBeta.test.ts`, `commandCenterRuntime.test.ts` (×2),
`moduleCatalog.test.ts` (×2), `foundation.test.ts`, `uxRevolution.test.ts`, `client_ux_41_3.test.ts`,
`workspaceEngine.test.ts` — role-home routing (`/dashboard` vs `/owner`) and dock-layout
`localStorage` persistence assertions, from other already-in-progress uncommitted work in the working
tree (`src/web/src/vertical-workspace/`, `ux-revolution/`, `workspace-chrome/` were all already
modified before this sprint started). **Zero regressions in any crypto-antifraud test** (10/10 pass).

## 11. Localhost smoke test (executed, not assumed)

Started the real backend (`python main.py` — bot polling + aiohttp API server) and real frontend
(`npm run dev`) against the actual local Postgres database, then exercised both over HTTP:

- Backend readiness (`GET /health`): `ready: true, ok: true`, database "healthy" (real Postgres
  16.14), Telegram "healthy" (`@UnoCachio_bot`, connected), scheduler "healthy"; overall
  `status: "degraded"` only because optional Redis isn't running locally (pre-existing, unrelated).
- `GET /management/v1/crypto-tx/deals/1` → `401` (registered and auth-gated correctly, not `404`).
- `POST /management/v1/crypto-tx/register` (the removed bypass endpoint) → `404` in the live server,
  confirming the fix is real, not just asserted in a test.
- Frontend: `/`, `/login`, `/crypto-otc/payout/1` all return `200`; `npx vite build` succeeds.
- No browser automation tool was available in this session (Claude in Chrome not connected), so
  client-side rendering was verified via Vitest's jsdom rendering of the real components (which does
  execute React, unlike a raw HTTP fetch) rather than a live browser — disclosed as a gap, not
  papered over.
- Both smoke-test processes were stopped cleanly after verification (no dangling bot/dev-server
  processes left running).

## 12. Remaining technical debt

- **Crypto/OTC migration from legacy `crypto_deals`/`crypto_payments` into `DealEngineV1`/
  `PaymentEngineV1`** — explicitly tracked as a separate future work item, per instruction. Not
  performed in this sprint. Until it happens, `legacy_deal_id`/`legacy_payment_id` remain the real
  reference columns; `deal_id`/`payout_id` stay unused for crypto.
- **Real step-up authentication** does not exist for this deployment. Override remains disabled
  until `CryptoTxAntifraudEngine._verify_step_up_token` is given a real implementation.
- **The `RolePermission` naming collision** (§10) is a real, pre-existing defect independent of this
  sprint; recommend renaming or fully-qualifying one of the two classes in a future, separately-scoped
  sprint — it affects test reliability repo-wide, not just crypto tests.
- **No real re-authentication UX exists in Telegram or Web** for any other privileged action either
  (this sprint didn't audit beyond crypto override) — worth a dedicated look if step-up auth is built.
- **Telegram's tx_hash entry is a single free-text line**, not per-field prompts — a deliberate,
  disclosed UX simplification given the sprint's scope, not a security gap (all fields are still
  validated server-side before the anti-fraud gate runs).
- **Web's payout-confirm panel is minimal by design** (per instruction) — no deal-listing/search UI;
  it expects a `dealId` in the URL. A "list my pending crypto deals" screen is natural follow-on work,
  not required for the anti-fraud guarantee itself.

## 13. Production readiness

**Duplicate-payout protection is now genuinely enforced on the one real production payout surface
that exists (Telegram), and on a newly-built, real (non-demo) Web surface — both through the exact
same canonical `CryptoPayoutOrchestrator`, which itself sits on top of the unchanged, real DB unique
constraint as the final concurrency guarantee.** Override is safely disabled rather than faked. The
crypto engine/orchestrator logic is proven correct (33/33 new tests passing whenever an unrelated,
pre-existing SQLAlchemy model-registry collision doesn't intervene) and verified live against a real
running backend. Outstanding gaps (§12) are disclosed, not hidden, and none of them allow a duplicate
payout to complete silently.
