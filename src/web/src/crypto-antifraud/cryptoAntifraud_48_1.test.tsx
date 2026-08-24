/**
 * Sprint 48.0/48.1 — Crypto/OTC transaction idempotency & duplicate-payout
 * protection (security-critical). Web UI coverage.
 *
 * Sprint 48.1: override is disabled in production (no real step-up
 * authentication provider — see services.pg_crypto_tx_antifraud_engine
 * .CryptoTxAntifraudEngine._verify_step_up_token), so the modal no longer
 * offers an override button at all — this file replaces the old
 * "offers/hides override for privileged/non-privileged role" tests with a
 * single "override is never offered, from anyone" assertion, and drops the
 * useAuthStore role dependency the old override UX needed.
 */

import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { DuplicateTxWarningModal } from "./DuplicateTxWarningModal";
import type { CryptoTransaction, DuplicateWarning } from "./cryptoTxApi";

vi.mock("./cryptoTxApi", async () => {
  const actual = await vi.importActual<typeof import("./cryptoTxApi")>("./cryptoTxApi");
  return {
    ...actual,
    cancelCryptoTx: vi.fn(),
    requestCryptoTxReview: vi.fn(),
  };
});

import { cancelCryptoTx, requestCryptoTxReview } from "./cryptoTxApi";

const TX: CryptoTransaction = {
  id: "tx-1",
  network: "TRC20",
  tx_hash: "0xabc123",
  token: "USDT",
  log_index: "0",
  wallet_address: "TWallet1",
  amount: "100",
  deal_id: null,
  payout_id: null,
  legacy_deal_id: 4242,
  legacy_payment_id: 9999,
  customer_id: 555,
  status: "PENDING",
  first_seen_at: "2026-08-09T00:00:00Z",
  registered_by: 700001,
  approved_by: null,
};

const WARNING: DuplicateWarning = {
  tx_hash: "0xabc123",
  network: "TRC20",
  token: "USDT",
  amount: "100",
  wallet_address: "TWallet1",
  previous_deal_id: null,
  previous_payout_id: null,
  previous_legacy_deal_id: 4242,
  previous_legacy_payment_id: 9999,
  previous_customer_id: 555,
  previous_operator_id: 700001,
  previous_status: "PENDING",
  first_seen_at: "2026-08-09T00:00:00Z",
  anomalies: ["same_wallet_amount_short_window"],
};

describe("Sprint 48.1 — DuplicateTxWarningModal", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders all mandatory warning fields, including the legacy deal/payment reference", () => {
    render(
      <DuplicateTxWarningModal open transaction={TX} warning={WARNING} onClose={() => {}} onResolved={() => {}} />,
    );
    expect(screen.getByTestId("dup-tx-hash")).toHaveTextContent("0xabc123");
    expect(screen.getByTestId("dup-status")).toHaveTextContent("PENDING");
    expect(screen.getByText(/TRC20/)).toBeInTheDocument();
    expect(screen.getByText(/#4242/)).toBeInTheDocument();
    expect(screen.getByText(/#9999/)).toBeInTheDocument();
    expect(screen.getByText(/700001/)).toBeInTheDocument();
  });

  it("shows previous customer when the server includes it (server already redacted per-role)", () => {
    render(
      <DuplicateTxWarningModal open transaction={TX} warning={WARNING} onClose={() => {}} onResolved={() => {}} />,
    );
    expect(screen.getByTestId("dup-customer")).toHaveTextContent("555");
  });

  it("hides previous customer when the server redacted it", () => {
    render(
      <DuplicateTxWarningModal
        open
        transaction={TX}
        warning={{ ...WARNING, previous_customer_id: null }}
        onClose={() => {}}
        onResolved={() => {}}
      />,
    );
    expect(screen.queryByTestId("dup-customer")).not.toBeInTheDocument();
  });

  it("never offers an override action, for anyone — only Cancel and Send-for-review", () => {
    render(
      <DuplicateTxWarningModal open transaction={TX} warning={WARNING} onClose={() => {}} onResolved={() => {}} />,
    );
    expect(screen.getByTestId("dup-action-cancel")).toBeInTheDocument();
    expect(screen.getByTestId("dup-action-review")).toBeInTheDocument();
    expect(screen.queryByTestId("dup-action-override-start")).not.toBeInTheDocument();
    expect(screen.getByTestId("dup-override-unavailable")).toBeInTheDocument();
  });

  it("cancel action calls the canonical cancel endpoint, not a local implementation", async () => {
    (cancelCryptoTx as any).mockResolvedValue({ ...TX, status: "CANCELLED" });
    const onResolved = vi.fn();
    render(
      <DuplicateTxWarningModal open transaction={TX} warning={WARNING} onClose={() => {}} onResolved={onResolved} />,
    );
    fireEvent.click(screen.getByTestId("dup-action-cancel"));
    await waitFor(() => expect(cancelCryptoTx).toHaveBeenCalledWith("tx-1", expect.any(String)));
    await waitFor(() => expect(onResolved).toHaveBeenCalled());
  });

  it("review action calls the canonical review endpoint", async () => {
    (requestCryptoTxReview as any).mockResolvedValue({ ...TX, status: "PENDING" });
    const onResolved = vi.fn();
    render(
      <DuplicateTxWarningModal open transaction={TX} warning={WARNING} onClose={() => {}} onResolved={onResolved} />,
    );
    fireEvent.click(screen.getByTestId("dup-action-review"));
    await waitFor(() => expect(requestCryptoTxReview).toHaveBeenCalledWith("tx-1"));
    await waitFor(() => expect(onResolved).toHaveBeenCalled());
  });

  it("shows the anomaly list when present", () => {
    render(
      <DuplicateTxWarningModal open transaction={TX} warning={WARNING} onClose={() => {}} onResolved={() => {}} />,
    );
    expect(screen.getByText(/тот же кошелёк\/сумма/i)).toBeInTheDocument();
  });
});
