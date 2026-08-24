/**
 * Sprint 48.1 — the minimal real Web crypto/OTC payout-confirmation surface.
 * Proves the panel loads a real deal, submits through the canonical
 * confirm-payout call (not a local implementation), and renders the shared
 * DuplicateTxWarningModal on a duplicate response rather than a second
 * warning UI.
 */

import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { CryptoPayoutConfirmPanel } from "./CryptoPayoutConfirmPanel";
import type { CryptoDealSummary, ConfirmCryptoPayoutResult } from "./cryptoTxApi";

vi.mock("./cryptoTxApi", async () => {
  const actual = await vi.importActual<typeof import("./cryptoTxApi")>("./cryptoTxApi");
  return {
    ...actual,
    getCryptoDealSummary: vi.fn(),
    confirmCryptoPayout: vi.fn(),
  };
});

import { getCryptoDealSummary, confirmCryptoPayout } from "./cryptoTxApi";

const DEAL: CryptoDealSummary = {
  id: 4242,
  client_id: 900001,
  amount: "1000",
  currency: "USD",
  status: "PAYMENT_PENDING",
  payment_status: "WAITING_PAYMENT",
  payment_id: 9999,
  can_confirm_payout: true,
};

function renderPanel(dealId = 4242) {
  return render(
    <MemoryRouter initialEntries={[`/crypto-otc/payout/${dealId}`]}>
      <Routes>
        <Route path="/crypto-otc/payout/:dealId" element={<CryptoPayoutConfirmPanel />} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("Sprint 48.1 — CryptoPayoutConfirmPanel", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (getCryptoDealSummary as any).mockResolvedValue(DEAL);
  });

  it("loads and renders the real deal, not a demo entity", async () => {
    renderPanel();
    await waitFor(() => expect(getCryptoDealSummary).toHaveBeenCalledWith(4242));
    expect(await screen.findByText(/Сделка #4242/)).toBeInTheDocument();
    expect(screen.getByTestId("deal-payment-status")).toHaveTextContent("WAITING_PAYMENT");
  });

  it("submits through the canonical confirm-payout call and shows success", async () => {
    const confirmed: ConfirmCryptoPayoutResult = {
      status: "confirmed",
      transaction: {
        id: "tx-1", network: "TRC20", tx_hash: "0xabc", token: "USDT", log_index: "0",
        wallet_address: "W", amount: "1000", deal_id: null, payout_id: null,
        legacy_deal_id: 4242, legacy_payment_id: 9999, customer_id: 900001,
        status: "COMPLETED", first_seen_at: null, registered_by: 1, approved_by: null,
      },
      warning: null,
      deal_id: 4242,
      payment_id: 9999,
    };
    (confirmCryptoPayout as any).mockResolvedValue(confirmed);
    renderPanel();
    await screen.findByText(/Сделка #4242/);

    fireEvent.change(screen.getByTestId("input-tx-hash"), { target: { value: "0xabc" } });
    fireEvent.change(screen.getByTestId("input-amount"), { target: { value: "1000" } });
    fireEvent.change(screen.getByTestId("input-wallet-address"), { target: { value: "W" } });
    fireEvent.click(screen.getByTestId("submit-payout-confirm"));

    await waitFor(() => expect(confirmCryptoPayout).toHaveBeenCalledWith(4242, expect.objectContaining({ tx_hash: "0xabc" })));
    expect(await screen.findByTestId("payout-confirmed")).toBeInTheDocument();
  });

  it("renders the shared DuplicateTxWarningModal on a duplicate response", async () => {
    const duplicate: ConfirmCryptoPayoutResult = {
      status: "duplicate",
      transaction: {
        id: "tx-1", network: "TRC20", tx_hash: "0xabc", token: "USDT", log_index: "0",
        wallet_address: "W", amount: "1000", deal_id: null, payout_id: null,
        legacy_deal_id: 111, legacy_payment_id: 222, customer_id: 900001,
        status: "RESERVED", first_seen_at: null, registered_by: 1, approved_by: null,
      },
      warning: {
        tx_hash: "0xabc", network: "TRC20", token: "USDT", amount: "1000", wallet_address: "W",
        previous_deal_id: null, previous_payout_id: null, previous_legacy_deal_id: 111,
        previous_legacy_payment_id: 222, previous_customer_id: null, previous_operator_id: 1,
        previous_status: "RESERVED", first_seen_at: "2026-08-09T00:00:00Z", anomalies: [],
      },
      deal_id: 4242,
      payment_id: 9999,
    };
    (confirmCryptoPayout as any).mockResolvedValue(duplicate);
    renderPanel();
    await screen.findByText(/Сделка #4242/);

    fireEvent.change(screen.getByTestId("input-tx-hash"), { target: { value: "0xabc" } });
    fireEvent.change(screen.getByTestId("input-amount"), { target: { value: "1000" } });
    fireEvent.change(screen.getByTestId("input-wallet-address"), { target: { value: "W" } });
    fireEvent.click(screen.getByTestId("submit-payout-confirm"));

    expect(await screen.findByTestId("crypto-duplicate-warning")).toBeInTheDocument();
    expect(screen.queryByTestId("payout-confirmed")).not.toBeInTheDocument();
  });
});
