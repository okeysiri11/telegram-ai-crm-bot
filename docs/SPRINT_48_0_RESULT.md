# Sprint 48.0 — Crypto/OTC Transaction Idempotency & Duplicate-Payout Protection — RESULT

**Retroactive documentation.** Sprint 48.0 was implemented on 2026-08-09 without a corresponding
`RESULT.md`, without an entry in `docs/SPRINT_47_MULTI_DOMAIN_EXPANSION_PLAN.md`'s roadmap, and
without the explicit per-sprint approval that Sprint 47.0/47.1 both recorded. This document was
written during Sprint 48.1's verification pass (2026-08-10) to close that documentation gap, based
on reading the actual shipped code, not on reconstructing intent after the fact from memory. Stayed
on `develop` throughout; no commits, no pushes.

## Original problem

Crypto/OTC payouts (USDT and other on-chain transfers used to justify a manual payout/deal) had no
protection against the same transaction hash being used to justify two different payouts — the
classic double-spend-adjacent fraud pattern for manual OTC desks: an attacker (or a confused
operator) submits the same on-chain transfer receipt against two different deals.

## What was implemented

1. **`database/models/crypto_tx_registry.py`** — `CryptoIncomingTransaction`, with a
   `UniqueConstraint(network, tx_hash, token, log_index)`. This constraint **is** the idempotency
   mechanism — a real Postgres unique index, not an application-level lock, so it holds under
   concurrent processes/pods. `CryptoTxOverrideLink` — an append-only table for approved overrides,
   which never mutates the original transaction's `deal_id`/`payout_id`.
2. **`repositories/crypto_tx_registry_repository.py`** — thin data access; does not catch the
   `IntegrityError` from the unique constraint itself (that decision belongs to the service layer,
   which needs the transaction still open to look up the pre-existing row).
3. **`services/pg_crypto_tx_antifraud_engine.py`** — `CryptoTxAntifraudEngine`, the canonical
   anti-fraud service: `register_incoming()` (atomic claim via `session.begin_nested()` +
   `IntegrityError` catch), `check_duplicate()`, `complete_payout()`, `cancel()`, `request_review()`,
   `approve_override()`, `reject_override()`, plus anomaly checks (resubmission after cancellation,
   same wallet/amount in a short window, multi-customer linkage, repeated operator attempts).
4. **Telegram bot integration** — `routers/crypto_tx_antifraud_router.py`: renders the duplicate
   warning and Cancel/Send-for-review/Override buttons; override gated behind an FSM (reason +
   explicit confirmation).
5. **Management HTTP API** — originally `services/crypto_tx_antifraud_router.py` (see "Architectural
   decisions" below for why this placement was wrong).
6. **Web UI** — `src/web/src/crypto-antifraud/{cryptoTxApi.ts, DuplicateTxWarningModal.tsx,
   useCryptoTxRegistration.tsx}`.
7. **Audit trail** — new `AuditAction` members (`CRYPTO_TX_REGISTERED`, `DUPLICATE_TX_DETECTED`,
   `DUPLICATE_TX_BLOCKED`, `DUPLICATE_TX_REVIEW_REQUESTED`, `DUPLICATE_TX_OVERRIDE_APPROVED`,
   `DUPLICATE_TX_OVERRIDE_REJECTED`, `PAYOUT_COMPLETED`).
8. **Migration** — `migrations/versions/w6q789012345_crypto_tx_registry_48_0.py`, chained after Sprint
   47.1's head (`v5p678901234`).
9. **Tests** — `tests/test_crypto_tx_antifraud_48_0.py` (17 tests, engine + old HTTP surface).

## Architectural decisions actually made (recorded now, not at the time)

- **`deal_id`/`payout_id` are UUID FKs into `deal_engine_v1_deals`/`payment_engine_v1_payments`.**
  This was never validated against what "crypto/OTC deal" means in this codebase at the time — see
  Sprint 48.1's finding that `DEAL_ENGINE_V1_SUPPORTED_VERTICALS = {"auto", "agro"}` only, i.e.
  crypto has no presence in DealEngineV1 at all. Every Sprint 48.0 test that exercises `deal_id`
  therefore had to construct a synthetic `DealEngineV1Deal` row with `vertical="crypto_otc"` purely
  for the test — nothing in real bot/web code has ever populated this field with a real value. This
  was a design gap, not a deliberate decision; Sprint 48.1 resolved it (see its own RESULT doc).
- **Override design (`reauth_verified: bool`)** accepted a caller-supplied boolean as proof of
  re-authentication. This was flagged during Sprint 48.1's audit as not a real security control (a
  client can always set a boolean to `True`) and was removed in Sprint 48.1 in favor of disabling
  override entirely until real step-up authentication exists.

## What was NOT verified at the time (found during Sprint 48.1's audit)

- **No caller.** `register_incoming_for_bot` (the bot-side entry point) and `registerCryptoTx`/
  `useCryptoTxRegistration` (the web-side entry point) had zero callers anywhere outside their own
  module and tests. The engine was real and well-tested in isolation, but nothing in the actual
  crypto/OTC deal flow (`services/crypto_erp.py`, `database_legacy.py`'s `crypto_deals`/
  `crypto_payments` tables, the Telegram deal-detail screen) ever called it. **Duplicate-payout
  protection was not enforced on any real production payout path as of the end of Sprint 48.0.**
- **Layering violation.** `services/crypto_tx_antifraud_router.py` was an aiohttp HTTP route module
  living in `services/` — this repo's own convention (CLAUDE.md: "services/ — business logic, no
  direct HTTP exposure") puts HTTP surface in `platform_management/`/`routers/`, not `services/`.
- **No `docs/SPRINT_48_0_RESULT.md`**, despite four separate source files' code comments citing it by
  name as the source of record for specific decisions.
- **Not in the approved roadmap.** `docs/SPRINT_47_MULTI_DOMAIN_EXPANSION_PLAN.md` stops at 47.9 and
  states "47.2 onward not started; require explicit approval per sprint before starting." Sprint 48.0
  was built without an entry there and without the explicit-approval-per-sprint discipline Sprint
  47.0/47.1 both followed.

## Tests and results (as inherited by Sprint 48.1, after its fixes)

`tests/test_crypto_tx_antifraud_48_0.py`: 16 passed (one test added, one HTTP test class removed and
superseded — see Sprint 48.1 RESULT's "Files changed"). Engine-level idempotency, concurrency (2-way
and 10-way race), anomaly detection, and audit trail all verified against the real Postgres unique
constraint, not mocked.

## Production readiness at the end of Sprint 48.0

**Not production-enforced.** The engine was correct and well-tested in isolation, but disconnected
from every real payout-initiating surface. See `docs/SPRINT_48_1_RESULT.md` for what closed this gap.
