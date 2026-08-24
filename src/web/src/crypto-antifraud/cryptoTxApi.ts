/**
 * Sprint 48.0/48.1 — Crypto/OTC transaction idempotency & duplicate-payout
 * protection (security-critical). Canonical HTTP client for
 * /management/v1/crypto-tx/* — the same backend surface the Telegram bot's
 * decision is derived from (services.crypto_payout_orchestrator
 * .CryptoPayoutOrchestrator, itself wrapping
 * services.pg_crypto_tx_antifraud_engine.CryptoTxAntifraudEngine). Do not
 * re-implement duplicate detection or a state transition here — this file
 * only calls the canonical deal-scoped endpoints and types their response.
 *
 * Sprint 48.1: the old generic `POST /crypto-tx/register` (no deal
 * validation — a direct-API bypass of the orchestrator) is gone. Every
 * payout goes through `confirmCryptoPayout(dealId, ...)` instead, which maps
 * to `POST /crypto-tx/deals/{deal_id}/confirm-payout`.
 */

import { apiFetch } from "@/integrations/apiClient";

export type CryptoTxStatus = "PENDING" | "RESERVED" | "COMPLETED" | "CANCELLED";
export type CryptoPayoutResultStatus = "confirmed" | "duplicate" | "already_confirmed";

export type CryptoTransaction = {
  id: string;
  network: string;
  tx_hash: string;
  token: string;
  log_index: string;
  wallet_address: string;
  amount: string;
  deal_id: string | null;
  payout_id: string | null;
  legacy_deal_id: number | null;
  legacy_payment_id: number | null;
  customer_id: number | null;
  status: CryptoTxStatus;
  first_seen_at: string | null;
  registered_by: number;
  approved_by: number | null;
};

export type DuplicateWarning = {
  tx_hash: string;
  network: string;
  token: string;
  amount: string;
  wallet_address: string;
  previous_deal_id: string | null;
  previous_payout_id: string | null;
  previous_legacy_deal_id: number | null;
  previous_legacy_payment_id: number | null;
  previous_customer_id: number | null;
  previous_operator_id: number;
  previous_status: string;
  first_seen_at: string | null;
  anomalies: string[];
};

export type CryptoDealSummary = {
  id: number;
  client_id: number;
  amount: number | string;
  currency: string;
  status: string;
  payment_status: string;
  payment_id: number | null;
  can_confirm_payout: boolean;
};

export type ConfirmCryptoPayoutInput = {
  network: string;
  tx_hash: string;
  token: string;
  amount: string;
  wallet_address: string;
  log_index?: string;
};

export type ConfirmCryptoPayoutResult = {
  status: CryptoPayoutResultStatus;
  transaction: CryptoTransaction;
  warning: DuplicateWarning | null;
  deal_id: number;
  payment_id: number | null;
};

async function parse<T>(res: Response): Promise<T> {
  const body = await res.json().catch(() => ({}));
  if (!body?.success) {
    throw new Error(body?.error || `crypto-tx request failed (${res.status})`);
  }
  return body.data as T;
}

export async function getCryptoDealSummary(dealId: number): Promise<CryptoDealSummary> {
  const res = await apiFetch(`/management/v1/crypto-tx/deals/${dealId}`);
  return parse<CryptoDealSummary>(res);
}

/** The ONE way to confirm a crypto/OTC payout from the Web UI — routes
 * through the same canonical orchestrator the Telegram bot calls. Never
 * call a lower-level endpoint directly to "skip" the duplicate check. */
export async function confirmCryptoPayout(
  dealId: number,
  input: ConfirmCryptoPayoutInput,
): Promise<ConfirmCryptoPayoutResult> {
  const res = await apiFetch(`/management/v1/crypto-tx/deals/${dealId}/confirm-payout`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
  return parse<ConfirmCryptoPayoutResult>(res);
}

export async function cancelCryptoTx(txId: string, reason: string): Promise<CryptoTransaction> {
  const res = await apiFetch(`/management/v1/crypto-tx/${txId}/cancel`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ reason }),
  });
  const data = await parse<{ transaction: CryptoTransaction }>(res);
  return data.transaction;
}

export async function requestCryptoTxReview(
  txId: string,
  reason?: string,
): Promise<CryptoTransaction> {
  const res = await apiFetch(`/management/v1/crypto-tx/${txId}/review`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ reason }),
  });
  const data = await parse<{ transaction: CryptoTransaction }>(res);
  return data.transaction;
}

/**
 * Sprint 48.1 — override is disabled in production: no real step-up
 * authentication provider exists (see
 * services.pg_crypto_tx_antifraud_engine.CryptoTxAntifraudEngine
 * ._verify_step_up_token). This call always resolves to a 503 today; it
 * exists only so the seam is in place once a real provider is wired in.
 * There is deliberately no `reauth_verified` boolean anymore — Sprint 48.0
 * had one, and a client-supplied flag is not authentication.
 */
export async function approveCryptoTxOverride(
  txId: string,
  input: { reason: string; confirmed: boolean; step_up_token?: string },
): Promise<CryptoTransaction> {
  const res = await apiFetch(`/management/v1/crypto-tx/${txId}/override/approve`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
  const data = await parse<{ transaction: CryptoTransaction }>(res);
  return data.transaction;
}
