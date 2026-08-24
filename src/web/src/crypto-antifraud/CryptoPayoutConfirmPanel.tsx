/**
 * Sprint 48.1 — the minimal REAL Web crypto/OTC payout-confirmation surface.
 *
 * Deliberately minimal by design (not a demo entity, not a new product
 * area): it operates on an actual existing crypto/OTC deal (fetched from
 * the real backend — platform_management/crypto_tx_antifraud_routes.py ->
 * services.crypto_payout_orchestrator.CryptoPayoutOrchestrator ->
 * database_legacy.py's real crypto_deals/crypto_payments), and it goes
 * through the exact same canonical orchestrator the Telegram bot calls
 * (routers/crypto_tx_antifraud_router.py). Neither surface implements its
 * own duplicate-detection or state-transition rules.
 *
 * Route: /crypto-otc/payout/:dealId — see src/web/src/App.tsx.
 */

import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { Button, Card, FormField, Input } from "@/ui";
import { DuplicateTxWarningModal } from "./DuplicateTxWarningModal";
import {
  confirmCryptoPayout,
  getCryptoDealSummary,
  type CryptoDealSummary,
  type CryptoTransaction,
  type DuplicateWarning,
} from "./cryptoTxApi";

type FormState = {
  network: string;
  tx_hash: string;
  token: string;
  amount: string;
  wallet_address: string;
};

const EMPTY_FORM: FormState = { network: "TRC20", tx_hash: "", token: "USDT", amount: "", wallet_address: "" };

export function CryptoPayoutConfirmPanel() {
  const params = useParams<{ dealId: string }>();
  const dealId = Number(params.dealId);

  const [deal, setDeal] = useState<CryptoDealSummary | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [form, setForm] = useState<FormState>(EMPTY_FORM);
  const [busy, setBusy] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [successResult, setSuccessResult] = useState<CryptoTransaction | null>(null);
  const [duplicate, setDuplicate] = useState<{ transaction: CryptoTransaction; warning: DuplicateWarning } | null>(
    null,
  );

  useEffect(() => {
    if (!Number.isFinite(dealId)) {
      setLoadError("Некорректный номер сделки.");
      return;
    }
    getCryptoDealSummary(dealId)
      .then(setDeal)
      .catch((e) => setLoadError(e instanceof Error ? e.message : "Не удалось загрузить сделку."));
  }, [dealId]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitError(null);
    if (!form.tx_hash.trim() || !form.amount.trim() || !form.wallet_address.trim()) {
      setSubmitError("Заполните хэш транзакции, сумму и адрес кошелька.");
      return;
    }
    setBusy(true);
    try {
      const result = await confirmCryptoPayout(dealId, form);
      if (result.status === "duplicate" && result.warning) {
        setDuplicate({ transaction: result.transaction, warning: result.warning });
      } else {
        setSuccessResult(result.transaction);
        setDeal((prev) => (prev ? { ...prev, payment_status: "PAYMENT_RECEIVED", can_confirm_payout: false } : prev));
      }
    } catch (err) {
      setSubmitError(err instanceof Error ? err.message : "Не удалось подтвердить платёж.");
    } finally {
      setBusy(false);
    }
  }

  if (loadError) {
    return (
      <Card>
        <p className="eds-type-body text-[var(--eds-danger)]">{loadError}</p>
      </Card>
    );
  }
  if (!deal) {
    return (
      <Card>
        <p className="eds-type-body">Загрузка сделки #{params.dealId}…</p>
      </Card>
    );
  }

  return (
    <div className="space-y-4" data-testid="crypto-payout-confirm-panel">
      <Card>
        <h2 className="eds-type-heading">Сделка #{deal.id}</h2>
        <dl className="grid grid-cols-2 gap-x-4 gap-y-1 eds-type-small mt-2">
          <dt className="text-[var(--eds-text-muted)]">Сумма</dt>
          <dd>{deal.amount} {deal.currency}</dd>
          <dt className="text-[var(--eds-text-muted)]">Статус сделки</dt>
          <dd>{deal.status}</dd>
          <dt className="text-[var(--eds-text-muted)]">Статус платежа</dt>
          <dd data-testid="deal-payment-status">{deal.payment_status}</dd>
        </dl>
      </Card>

      {successResult ? (
        <Card>
          <p className="eds-type-body font-semibold" data-testid="payout-confirmed">
            ✅ Платёж подтверждён. Статус транзакции: {successResult.status}.
          </p>
        </Card>
      ) : deal.can_confirm_payout ? (
        <Card>
          <form className="space-y-3" onSubmit={handleSubmit}>
            <FormField label="Сеть">
              <Input
                value={form.network}
                onChange={(e) => setForm({ ...form, network: e.target.value })}
              />
            </FormField>
            <FormField label="Хэш транзакции">
              <Input
                value={form.tx_hash}
                onChange={(e) => setForm({ ...form, tx_hash: e.target.value })}
                data-testid="input-tx-hash"
              />
            </FormField>
            <FormField label="Токен">
              <Input value={form.token} onChange={(e) => setForm({ ...form, token: e.target.value })} />
            </FormField>
            <FormField label="Сумма">
              <Input
                value={form.amount}
                onChange={(e) => setForm({ ...form, amount: e.target.value })}
                data-testid="input-amount"
              />
            </FormField>
            <FormField label="Адрес кошелька">
              <Input
                value={form.wallet_address}
                onChange={(e) => setForm({ ...form, wallet_address: e.target.value })}
                data-testid="input-wallet-address"
              />
            </FormField>
            {submitError ? <p className="eds-type-small text-[var(--eds-danger)]">{submitError}</p> : null}
            <Button type="submit" disabled={busy} data-testid="submit-payout-confirm">
              ✅ Подтвердить платёж
            </Button>
          </form>
        </Card>
      ) : (
        <Card>
          <p className="eds-type-body text-[var(--eds-text-muted)]">
            Платёж по этой сделке уже подтверждён или сделка закрыта — новое подтверждение недоступно.
          </p>
        </Card>
      )}

      {duplicate ? (
        <DuplicateTxWarningModal
          open
          transaction={duplicate.transaction}
          warning={duplicate.warning}
          onClose={() => setDuplicate(null)}
          onResolved={() => setDuplicate(null)}
        />
      ) : null}
    </div>
  );
}
